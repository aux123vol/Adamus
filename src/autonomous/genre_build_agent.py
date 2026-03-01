"""
GenreBuildAgent: Turns scaffolded Genre features into real implementations.

Workflow for each feature:
1. Read the Genre feature spec (from a queue or passed directly).
2. Detect what already exists in the Genre codebase (if accessible).
3. Generate a Python/TypeScript implementation via Claude.
4. Run the Adamus test suite to confirm nothing broke.
5. Commit via GitOps with a [genre-build] tag.
6. Return a GenreBuildResult with full audit trail.

If ANTHROPIC_API_KEY is absent the agent generates a well-structured
stub so downstream tracking still works.
"""

import json
import logging
import os
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.autonomous.git_ops import GitOps
from src.autonomous.self_builder import SelfBuilder

logger = logging.getLogger(__name__)

REPO_ROOT = Path("/home/johan/adamus")
# Where Genre feature stubs are scaffolded by Adamus
GENRE_FEATURES_DIR = REPO_ROOT / "src" / "genre_features"
# Queue file: list of {name, description, priority} dicts
GENRE_QUEUE_FILE = Path.home() / ".adamus" / "genre_build_queue.json"

CLAUDE_MODEL = "claude-sonnet-4-6"


# ── Result dataclasses ─────────────────────────────────────────────────────

@dataclass
class GenreFeatureSpec:
    """Specification for a Genre feature to build."""
    name: str
    description: str
    priority: int = 5
    feature_type: str = "backend"   # backend | frontend | full-stack
    queued_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GenreBuildResult:
    """Outcome of a full Genre feature build cycle."""
    success: bool
    feature_name: str
    file_path: Optional[str]
    test_output: str
    attempts: int
    committed: bool = False
    error: Optional[str] = None
    built_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class GenreCycleResult:
    """Summary of one run_cycle() call."""
    features_attempted: int = 0
    features_built: int = 0
    features_failed: int = 0
    details: List[Dict] = field(default_factory=list)


# ── GenreBuildAgent ────────────────────────────────────────────────────────

class GenreBuildAgent:
    """
    Autonomous Genre feature builder.

    Takes a scaffolded feature spec → generates real implementation →
    tests → commits.  Designed to run on the AutonomousLoop heartbeat.
    """

    def __init__(self) -> None:
        self._api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")
        self._client = self._init_client()
        self._git = GitOps()
        self._builder = SelfBuilder()    # reuse test runner & git ops
        GENRE_FEATURES_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(
            "GenreBuildAgent ready (API key %s)",
            "present" if self._api_key else "MISSING — stub mode",
        )

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def run_cycle(self, max_features: int = 1) -> GenreCycleResult:
        """
        Dequeue and build up to *max_features* Genre features.

        Called by AutonomousLoop on every heartbeat.

        Args:
            max_features: Max number of features to attempt this cycle.

        Returns:
            GenreCycleResult summarising what was attempted and built.
        """
        result = GenreCycleResult()
        queue = self._load_queue()

        pending = [f for f in queue if f.get("status", "pending") == "pending"]
        if not pending:
            logger.info("GenreBuildAgent: queue empty")
            return result

        logger.info(
            "GenreBuildAgent: %d feature(s) pending, building up to %d",
            len(pending),
            max_features,
        )

        for raw in pending[:max_features]:
            spec = GenreFeatureSpec(
                name=raw.get("name", "unnamed_feature"),
                description=raw.get("description", "No description"),
                priority=raw.get("priority", 5),
                feature_type=raw.get("feature_type", "backend"),
            )
            result.features_attempted += 1
            build_result = self.build_feature(spec)

            detail = {
                "name": spec.name,
                "success": build_result.success,
                "committed": build_result.committed,
                "attempts": build_result.attempts,
                "error": build_result.error,
            }
            result.details.append(detail)

            if build_result.success:
                result.features_built += 1
                self._mark_done(spec.name, queue)
                logger.info("GenreBuildAgent: built '%s'", spec.name)
            else:
                result.features_failed += 1
                self._mark_failed(spec.name, queue)
                logger.warning("GenreBuildAgent: failed to build '%s'", spec.name)

        self._save_queue(queue)
        return result

    def enqueue_feature(
        self,
        name: str,
        description: str,
        priority: int = 5,
        feature_type: str = "backend",
    ) -> None:
        """
        Add a Genre feature to the build queue.

        Args:
            name:         Snake-case feature name (e.g. ``lore_editor``).
            description:  Plain-English description of the feature.
            priority:     1 (urgent) … 10 (low), default 5.
            feature_type: ``backend`` | ``frontend`` | ``full-stack``.
        """
        queue = self._load_queue()
        # Avoid duplicates
        existing_names = {item.get("name") for item in queue}
        if name in existing_names:
            logger.info("GenreBuildAgent: '%s' already in queue", name)
            return

        queue.append({
            "name": name,
            "description": description,
            "priority": max(1, min(10, priority)),
            "feature_type": feature_type,
            "status": "pending",
            "queued_at": datetime.utcnow().isoformat(),
        })
        # Sort by priority
        queue.sort(key=lambda x: x.get("priority", 5))
        self._save_queue(queue)
        logger.info("Enqueued Genre feature '%s' (priority %d)", name, priority)

    def build_feature(self, spec: GenreFeatureSpec) -> GenreBuildResult:
        """
        Generate, test, and commit a Genre feature implementation.

        Args:
            spec: GenreFeatureSpec with name, description, and type.

        Returns:
            GenreBuildResult with full build audit trail.
        """
        logger.info("GenreBuildAgent: building '%s' (%s)", spec.name, spec.feature_type)
        target_path = GENRE_FEATURES_DIR / f"{spec.name}.py"

        code = self._generate_feature_code(spec)
        last_error = ""

        for attempt in range(1, 4):  # max 3 attempts
            logger.info("  Attempt %d/3 for Genre feature '%s'", attempt, spec.name)

            try:
                target_path.write_text(code, encoding="utf-8")
            except OSError as exc:
                return GenreBuildResult(
                    success=False,
                    feature_name=spec.name,
                    file_path=None,
                    test_output="",
                    attempts=attempt,
                    error=f"Write failed: {exc}",
                )

            # Run full test suite
            test_result = self._builder.run_tests(str(target_path))

            if test_result.passed:
                rel = str(target_path.relative_to(REPO_ROOT))
                committed = self._git.commit(
                    message=f"Genre feature: {spec.name} [genre-build]",
                    files=[rel],
                )
                logger.info(
                    "  Built Genre feature '%s' (attempt %d, committed=%s)",
                    spec.name, attempt, committed,
                )
                return GenreBuildResult(
                    success=True,
                    feature_name=spec.name,
                    file_path=str(target_path),
                    test_output=test_result.output,
                    attempts=attempt,
                    committed=committed,
                )

            last_error = test_result.output
            logger.warning("  Tests failed (attempt %d): %s", attempt, last_error[:200])
            if attempt < 3 and self._client:
                code = self._fix_feature_code(spec, code, last_error)

        return GenreBuildResult(
            success=False,
            feature_name=spec.name,
            file_path=str(target_path),
            test_output=last_error,
            attempts=3,
            error=f"Tests failed after 3 attempts",
        )

    def get_queue_status(self) -> Dict:
        """Return a summary of the Genre build queue."""
        queue = self._load_queue()
        by_status: Dict[str, int] = {}
        for item in queue:
            s = item.get("status", "pending")
            by_status[s] = by_status.get(s, 0) + 1
        return {
            "total": len(queue),
            "by_status": by_status,
            "pending": by_status.get("pending", 0),
            "done": by_status.get("done", 0),
            "failed": by_status.get("failed", 0),
        }

    # ------------------------------------------------------------------ #
    # Code generation                                                      #
    # ------------------------------------------------------------------ #

    def _generate_feature_code(self, spec: GenreFeatureSpec) -> str:
        """Generate implementation code for a Genre feature."""
        if self._client is None:
            return self._stub_feature(spec)

        prompt = textwrap.dedent(f"""
            You are an expert Python developer building a feature for Genre,
            a SaaS product for creators (Lore, Saga, Bible modules).

            ## Feature to Build
            **Name:** `{spec.name}`
            **Type:** {spec.feature_type}
            **Description:** {spec.description}

            ## Requirements
            1. Production-quality Python module with full type hints.
            2. Google-style docstrings on every class and public method.
            3. Main class named `{_to_class_name(spec.name)}`.
            4. Graceful error handling — no uncaught exceptions.
            5. Logging via `logging.getLogger(__name__)`.
            6. The module must be importable with zero side-effects.
            7. Include a `get_status() -> dict` method returning health info.
            8. No external API calls in __init__; use lazy initialisation.

            ## Output format
            Return ONLY the raw Python source code with no markdown fences.
        """).strip()

        try:
            response = self._client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            code = response.content[0].text.strip()
            if code.startswith("```"):
                lines = code.splitlines()
                code = "\n".join(l for l in lines if not l.startswith("```"))
            return code
        except Exception as exc:
            logger.error(
                "Claude generation failed for Genre feature '%s': %s — stub fallback",
                spec.name, exc,
            )
            return self._stub_feature(spec)

    def _fix_feature_code(
        self, spec: GenreFeatureSpec, broken_code: str, error_output: str
    ) -> str:
        """Ask Claude to fix broken feature code."""
        if self._client is None:
            return broken_code

        prompt = textwrap.dedent(f"""
            Fix this Python module for Genre feature `{spec.name}`.

            ```python
            {broken_code}
            ```

            pytest error:
            ```
            {error_output[:2000]}
            ```

            Return ONLY corrected Python source — no markdown, no explanation.
        """).strip()

        try:
            response = self._client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            fixed = response.content[0].text.strip()
            if fixed.startswith("```"):
                lines = fixed.splitlines()
                fixed = "\n".join(l for l in lines if not l.startswith("```"))
            return fixed
        except Exception as exc:
            logger.error("Claude fix failed for '%s': %s", spec.name, exc)
            return broken_code

    @staticmethod
    def _stub_feature(spec: GenreFeatureSpec) -> str:
        """Generate a well-structured stub when the API is unavailable."""
        class_name = _to_class_name(spec.name)
        ts = datetime.utcnow().isoformat()
        return textwrap.dedent(f'''
            """
            {spec.name}: {spec.description}

            Genre Feature — AUTO-GENERATED STUB ({ts})
            Replace this with a real implementation.
            """

            import logging
            from typing import Any, Dict, Optional

            logger = logging.getLogger(__name__)


            class {class_name}:
                """
                {spec.description}

                Genre feature stub — implement before shipping.
                """

                def __init__(self) -> None:
                    logger.info("{class_name} initialised (stub)")

                def run(self, *args: Any, **kwargs: Any) -> Dict:
                    """Execute the feature (stub).

                    Returns:
                        Dict with status and message.
                    """
                    logger.warning("{class_name}.run() called on stub")
                    return {{"status": "stub", "message": "Not implemented yet"}}

                def get_status(self) -> Dict:
                    """Return feature health status.

                    Returns:
                        Dict with ready flag and reason.
                    """
                    return {{"ready": False, "reason": "stub implementation"}}
        ''').strip() + "\n"

    # ------------------------------------------------------------------ #
    # Queue persistence                                                    #
    # ------------------------------------------------------------------ #

    def _load_queue(self) -> List[Dict]:
        try:
            if GENRE_QUEUE_FILE.exists():
                return json.loads(GENRE_QUEUE_FILE.read_text(encoding="utf-8"))
        except Exception as exc:
            logger.error("Could not load genre queue: %s", exc)
        return []

    def _save_queue(self, queue: List[Dict]) -> None:
        try:
            GENRE_QUEUE_FILE.parent.mkdir(parents=True, exist_ok=True)
            GENRE_QUEUE_FILE.write_text(
                json.dumps(queue, indent=2, default=str), encoding="utf-8"
            )
        except Exception as exc:
            logger.error("Could not save genre queue: %s", exc)

    def _mark_done(self, name: str, queue: List[Dict]) -> None:
        for item in queue:
            if item.get("name") == name:
                item["status"] = "done"
                item["done_at"] = datetime.utcnow().isoformat()

    def _mark_failed(self, name: str, queue: List[Dict]) -> None:
        for item in queue:
            if item.get("name") == name:
                item["status"] = "failed"
                item["failed_at"] = datetime.utcnow().isoformat()

    # ------------------------------------------------------------------ #
    # Client                                                               #
    # ------------------------------------------------------------------ #

    def _init_client(self):
        if not self._api_key:
            return None
        try:
            import anthropic
            return anthropic.Anthropic(api_key=self._api_key)
        except Exception as exc:
            logger.warning("Could not create Anthropic client: %s", exc)
            return None


# ── Utility ────────────────────────────────────────────────────────────────

def _to_class_name(snake: str) -> str:
    return "".join(w.capitalize() for w in snake.split("_"))
