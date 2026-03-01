"""
SelfBuildAgent: Context-Aware Self-Improvement for Adamus.

Unlike the lower-level SelfBuilder (which just writes + tests code),
SelfBuildAgent:

1. Reads the relevant sections of the Adamus codebase before writing
   anything — so Claude has real context, not just a description.
2. Detects capability gaps automatically by inspecting what the
   SelfImprovementOrchestrator backlog contains vs what src/capabilities/
   already has.
3. Records every failure (error output + broken code) so that on retry
   the full failure history is passed to Claude.
4. Exposes a simple `run_cycle()` method for the AutonomousLoop heartbeat.
"""

import logging
import os
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.autonomous.self_builder import SelfBuilder, BuildResult

logger = logging.getLogger(__name__)

REPO_ROOT = Path("/home/johan/adamus")
CAPABILITIES_DIR = REPO_ROOT / "src" / "capabilities"
SRC_DIR = REPO_ROOT / "src"

# How many source files to include as codebase context per build
MAX_CONTEXT_FILES = 5
# Max chars from each context file
MAX_CHARS_PER_FILE = 2000


# ── Context helpers ────────────────────────────────────────────────────────

def _read_codebase_context(capability_name: str, description: str) -> str:
    """
    Return a multi-file context string from the Adamus codebase.

    Strategy:
    - Always include security/ppai_gateway.py (security contract).
    - Always include coordinator/ai_coordinator.py (coordination pattern).
    - Scan src/ for files whose names overlap with words in the description.
    - Return up to MAX_CONTEXT_FILES files, truncated to MAX_CHARS_PER_FILE each.
    """
    priority_files = [
        SRC_DIR / "security" / "ppai_gateway.py",
        SRC_DIR / "coordinator" / "ai_coordinator.py",
        SRC_DIR / "tech_ai" / "capability_builder.py",
    ]

    # Find relevant files by keyword matching
    keywords = set(
        w.lower() for w in description.split() + capability_name.split("_")
        if len(w) > 4
    )
    candidate_files: List[Path] = []
    for py_file in SRC_DIR.rglob("*.py"):
        stem = py_file.stem.lower()
        if any(kw in stem for kw in keywords):
            candidate_files.append(py_file)

    # Merge: priority first, then candidates, deduplicated
    seen = set()
    ordered: List[Path] = []
    for f in priority_files + candidate_files:
        if f not in seen and f.exists():
            seen.add(f)
            ordered.append(f)
        if len(ordered) >= MAX_CONTEXT_FILES:
            break

    parts: List[str] = []
    for f in ordered:
        try:
            content = f.read_text(encoding="utf-8")[:MAX_CHARS_PER_FILE]
            rel = str(f.relative_to(REPO_ROOT))
            parts.append(f"### {rel}\n```python\n{content}\n```")
        except Exception:
            pass

    return "\n\n".join(parts)


# ── Failure record ─────────────────────────────────────────────────────────

@dataclass
class FailureRecord:
    """Tracks a single failed build attempt for feedback loops."""
    attempt: int
    error_summary: str
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# ── CycleResult ────────────────────────────────────────────────────────────

@dataclass
class CycleResult:
    """Summary of one run_cycle() call."""
    capabilities_attempted: int = 0
    capabilities_built: int = 0
    capabilities_failed: int = 0
    details: List[Dict] = field(default_factory=list)


# ── SelfBuildAgent ─────────────────────────────────────────────────────────

class SelfBuildAgent:
    """
    Context-aware self-improvement agent.

    Wraps SelfBuilder with:
    - Codebase context injection into every prompt.
    - Automatic gap detection (what's missing vs what's in src/capabilities/).
    - Per-capability failure history passed back to Claude on retries.
    - A `run_cycle(max_capabilities)` method for the heartbeat.
    """

    def __init__(self) -> None:
        self._builder = SelfBuilder()
        # failure_history[capability_name] = list of FailureRecord
        self._failure_history: Dict[str, List[FailureRecord]] = {}
        logger.info("SelfBuildAgent ready")

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def run_cycle(self, max_capabilities: int = 2) -> CycleResult:
        """
        Detect gaps and build up to *max_capabilities* missing capabilities.

        Called by AutonomousLoop on every heartbeat.

        Args:
            max_capabilities: Maximum number of capabilities to attempt
                              building in this cycle.

        Returns:
            CycleResult summarising what was attempted and built.
        """
        result = CycleResult()
        gaps = self._detect_gaps()

        if not gaps:
            logger.info("SelfBuildAgent: no capability gaps detected")
            return result

        logger.info(
            "SelfBuildAgent: %d gap(s) detected, building up to %d",
            len(gaps),
            max_capabilities,
        )

        for gap in gaps[:max_capabilities]:
            name = gap["name"]
            desc = gap["description"]
            result.capabilities_attempted += 1

            build_result = self.build_with_context(name, desc)
            detail = {
                "name": name,
                "success": build_result.success,
                "attempts": build_result.attempts,
                "error": build_result.error,
            }
            result.details.append(detail)

            if build_result.success:
                result.capabilities_built += 1
                logger.info("SelfBuildAgent: built '%s'", name)
                # Clear failure history on success
                self._failure_history.pop(name, None)
            else:
                result.capabilities_failed += 1
                self._record_failure(name, build_result.error or "unknown error")
                logger.warning("SelfBuildAgent: failed to build '%s'", name)

        return result

    def build_with_context(
        self,
        capability_name: str,
        description: str,
    ) -> BuildResult:
        """
        Build a capability with codebase context injected into the prompt.

        Reads relevant source files, injects them into the description
        passed to SelfBuilder so Claude can match project style and patterns.

        Args:
            capability_name: Snake-case capability name.
            description:     Plain-English description.

        Returns:
            BuildResult from SelfBuilder.
        """
        context = _read_codebase_context(capability_name, description)
        failures = self._failure_history.get(capability_name, [])

        failure_section = ""
        if failures:
            lines = [f"- Attempt {f.attempt}: {f.error_summary[:200]}" for f in failures[-3:]]
            failure_section = (
                "\n\n## Previous Failures (learn from these)\n"
                + "\n".join(lines)
            )

        enriched_description = textwrap.dedent(f"""
            {description}

            ## Codebase Context (match this style exactly)
            {context}
            {failure_section}
        """).strip()

        return self._builder.build_capability(capability_name, enriched_description)

    def get_failure_history(self, capability_name: str) -> List[FailureRecord]:
        """Return the failure history for a given capability."""
        return self._failure_history.get(capability_name, [])

    def get_status(self) -> Dict:
        """Return agent status summary."""
        existing = self._list_existing_capabilities()
        return {
            "capabilities_built": len(existing),
            "capabilities_with_failures": len(self._failure_history),
            "failure_history_size": sum(
                len(v) for v in self._failure_history.values()
            ),
        }

    # ------------------------------------------------------------------ #
    # Gap detection                                                        #
    # ------------------------------------------------------------------ #

    def _detect_gaps(self) -> List[Dict]:
        """
        Return a list of missing capabilities that should be built.

        Strategy:
        1. Ask SelfImprovementOrchestrator for its backlog (if available).
        2. Filter out capabilities that already exist in src/capabilities/.
        3. Fall back to a hard-coded seed list if no orchestrator is available.
        """
        existing = self._list_existing_capabilities()

        # Try to get backlog from orchestrator
        try:
            from src.tech_ai.self_improvement import SelfImprovementOrchestrator
            orch = SelfImprovementOrchestrator()
            backlog = orch.get_backlog() if hasattr(orch, "get_backlog") else []
            if backlog:
                return [
                    item for item in backlog
                    if item.get("name") not in existing
                ]
        except Exception as exc:
            logger.debug("Could not load SelfImprovementOrchestrator backlog: %s", exc)

        # Seed gaps: capabilities Adamus always needs
        seed_gaps = [
            {
                "name": "health_monitor",
                "description": (
                    "Monitor the health of Adamus components (coordinator, memory, "
                    "security layers). Returns a dict with component name → status. "
                    "Checks each component's get_status() method if available."
                ),
            },
            {
                "name": "cost_tracker",
                "description": (
                    "Track cumulative LLM API spending across Claude, OpenAI, and "
                    "Groq providers. Reads from ~/.adamus/cost_log.json, writes new "
                    "entries with timestamp/model/tokens/cost_usd. Enforces a "
                    "$200/month budget cap."
                ),
            },
            {
                "name": "credential_vault",
                "description": (
                    "Secure read-only access to API keys via environment variables. "
                    "Provides get(key_name) → str | None. Never logs values. "
                    "Raises PermissionError if a Level 4 key is accessed without "
                    "VAULT_MASTER_TOKEN being set."
                ),
            },
        ]

        return [g for g in seed_gaps if g["name"] not in existing]

    def _list_existing_capabilities(self) -> set:
        """Return the set of capability names already built (file stems)."""
        try:
            return {
                f.stem
                for f in CAPABILITIES_DIR.glob("*.py")
                if f.stem != "__init__"
            }
        except Exception:
            return set()

    # ------------------------------------------------------------------ #
    # Failure tracking                                                     #
    # ------------------------------------------------------------------ #

    def _record_failure(self, capability_name: str, error: str) -> None:
        """Record a build failure for future retries."""
        if capability_name not in self._failure_history:
            self._failure_history[capability_name] = []
        attempt = len(self._failure_history[capability_name]) + 1
        self._failure_history[capability_name].append(
            FailureRecord(attempt=attempt, error_summary=error[:500])
        )
