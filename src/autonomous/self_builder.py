"""
Self-Builder: Adamus writes, tests, and commits its own Python code.

Adamus calls Claude to generate capability implementations, runs pytest
to validate them, retries on failure (up to 3 attempts), and commits
passing code via GitOps.

If no ANTHROPIC_API_KEY is present the builder falls back to generating
a well-structured stub so the rest of the system can still make progress.
"""

import logging
import os
import subprocess
import textwrap
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Constants ──────────────────────────────────────────────────────────────

REPO_ROOT = Path("/home/johan/adamus")
CAPABILITIES_DIR = REPO_ROOT / "src" / "capabilities"
TESTS_DIR = REPO_ROOT / "tests"
MAX_RETRIES = 3
CLAUDE_MODEL = "claude-sonnet-4-6"


# ── Result dataclasses ─────────────────────────────────────────────────────

@dataclass
class TestResult:
    """Outcome of running the pytest suite."""
    passed: bool
    output: str
    failed_tests: List[str] = field(default_factory=list)


@dataclass
class BuildResult:
    """Outcome of a full build-test-commit cycle."""
    success: bool
    capability_name: str
    file_path: Optional[str]
    test_output: str
    attempts: int
    error: Optional[str] = None


# ── Helper: read existing code style sample ───────────────────────────────

def _read_style_sample() -> str:
    """
    Return a short sample of existing project code so Claude can match style.
    Reads the first ~60 lines of capability_builder.py as a reference.
    """
    ref = REPO_ROOT / "src" / "tech_ai" / "capability_builder.py"
    try:
        lines = ref.read_text(encoding="utf-8").splitlines()[:60]
        return "\n".join(lines)
    except Exception:
        return ""


# ── SelfBuilder ────────────────────────────────────────────────────────────

class SelfBuilder:
    """
    Autonomous capability builder.

    Workflow for each capability:
    1. Prompt Claude (claude-sonnet-4-6) with a full implementation request.
    2. Write the returned code to ``src/capabilities/<name>.py``.
    3. Run ``pytest tests/ -v --tb=short``.
    4. On failure: ask Claude to fix the error and retry (max 3 attempts).
    5. On success: git-commit via GitOps.

    Falls back to generating a template stub when ANTHROPIC_API_KEY is absent.
    """

    def __init__(self) -> None:
        self._api_key: Optional[str] = os.environ.get("ANTHROPIC_API_KEY")
        self._client = self._init_client()
        # Lazy import to avoid circular dependency
        from src.autonomous.git_ops import GitOps
        self._git = GitOps()
        CAPABILITIES_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(
            "SelfBuilder ready (API key %s)",
            "present" if self._api_key else "MISSING — stub mode",
        )

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def build_capability(
        self,
        capability_name: str,
        description: str,
    ) -> BuildResult:
        """
        Generate, test, and commit a new capability module.

        Args:
            capability_name: Snake-case name (e.g. ``email_notifier``).
            description:     Plain-English description of what the module does.

        Returns:
            BuildResult describing success/failure and attempt count.
        """
        logger.info("SelfBuilder: building '%s'", capability_name)
        target_path = CAPABILITIES_DIR / f"{capability_name}.py"

        code = self._generate_code(capability_name, description)
        last_error = ""

        for attempt in range(1, MAX_RETRIES + 1):
            logger.info("  Attempt %d/%d for '%s'", attempt, MAX_RETRIES, capability_name)

            # Write generated code
            try:
                target_path.write_text(code, encoding="utf-8")
            except OSError as exc:
                msg = f"Could not write {target_path}: {exc}"
                logger.error(msg)
                return BuildResult(
                    success=False,
                    capability_name=capability_name,
                    file_path=None,
                    test_output="",
                    attempts=attempt,
                    error=msg,
                )

            # Run tests
            test_result = self.run_tests(str(target_path))

            if test_result.passed:
                committed = self.commit_capability(capability_name, str(target_path))
                logger.info(
                    "  Built '%s' on attempt %d (committed=%s)",
                    capability_name,
                    attempt,
                    committed,
                )
                return BuildResult(
                    success=True,
                    capability_name=capability_name,
                    file_path=str(target_path),
                    test_output=test_result.output,
                    attempts=attempt,
                )

            # Tests failed — ask Claude to fix
            last_error = test_result.output
            logger.warning(
                "  Tests failed (attempt %d): %s",
                attempt,
                last_error[:200],
            )
            if attempt < MAX_RETRIES:
                code = self._fix_code(
                    capability_name=capability_name,
                    description=description,
                    broken_code=code,
                    error_output=last_error,
                )

        # All retries exhausted
        logger.error("SelfBuilder: failed to build '%s' after %d attempts", capability_name, MAX_RETRIES)
        return BuildResult(
            success=False,
            capability_name=capability_name,
            file_path=str(target_path),
            test_output=last_error,
            attempts=MAX_RETRIES,
            error=f"Tests failed after {MAX_RETRIES} attempts",
        )

    def run_tests(self, file_path: str) -> TestResult:
        """
        Run the full pytest suite.

        Args:
            file_path: Path to the newly-generated file (used for logging only).

        Returns:
            TestResult with pass/fail status, raw output, and failed test names.
        """
        logger.debug("Running tests (new file: %s)", file_path)
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                timeout=120,
            )
            combined = result.stdout + result.stderr
            passed = result.returncode == 0

            failed: List[str] = []
            for line in combined.splitlines():
                if "FAILED" in line:
                    # Extract test node id, e.g. "FAILED tests/test_foo.py::test_bar"
                    parts = line.strip().split()
                    for part in parts:
                        if part.startswith("tests/"):
                            failed.append(part)
                            break

            return TestResult(passed=passed, output=combined, failed_tests=failed)

        except subprocess.TimeoutExpired:
            msg = "pytest timed out after 120 seconds"
            logger.error(msg)
            return TestResult(passed=False, output=msg, failed_tests=[])
        except Exception as exc:
            msg = f"pytest raised: {exc}"
            logger.error(msg)
            return TestResult(passed=False, output=msg, failed_tests=[])

    def commit_capability(self, capability_name: str, file_path: str) -> bool:
        """
        Commit a successfully-built capability file via GitOps.

        Args:
            capability_name: Used to form the commit message.
            file_path:       Absolute path of the file to commit.

        Returns:
            True if the commit succeeded.
        """
        # Make path relative to repo root for git add
        try:
            rel = str(Path(file_path).relative_to(REPO_ROOT))
        except ValueError:
            rel = file_path

        message = f"Auto-built: {capability_name} [adamus-self-build]"
        return self._git.commit(message=message, files=[rel])

    def build_from_backlog(self, backlog_item: Dict) -> BuildResult:
        """
        Build a capability from a SelfImprovementOrchestrator backlog item dict.

        Expects keys: ``name``, ``description`` (both str).

        Args:
            backlog_item: Dict with at least ``name`` and ``description`` keys.

        Returns:
            BuildResult from :meth:`build_capability`.
        """
        name = backlog_item.get("name", "unnamed_capability")
        description = backlog_item.get("description", "No description provided.")
        return self.build_capability(name, description)

    # ------------------------------------------------------------------ #
    # Private helpers                                                      #
    # ------------------------------------------------------------------ #

    def _init_client(self):
        """Attempt to create an Anthropic client; return None if unavailable."""
        if not self._api_key:
            return None
        try:
            import anthropic  # type: ignore
            return anthropic.Anthropic(api_key=self._api_key)
        except ImportError:
            logger.warning("anthropic package not installed — stub mode active")
            return None
        except Exception as exc:
            logger.warning("Could not create Anthropic client: %s — stub mode active", exc)
            return None

    def _generate_code(self, capability_name: str, description: str) -> str:
        """
        Ask Claude to produce a complete Python module for the capability.

        Falls back to :meth:`_stub_code` if the client is unavailable.
        """
        if self._client is None:
            logger.info("No API client — generating stub for '%s'", capability_name)
            return self._stub_code(capability_name, description)

        style_sample = _read_style_sample()
        prompt = textwrap.dedent(f"""
            You are an expert Python developer building a module for the Adamus AI system.

            ## Task
            Generate a complete, production-quality Python module for the capability:

            **Name:** `{capability_name}`
            **Description:** {description}

            ## Requirements
            1. Full type hints throughout.
            2. Google-style docstrings on every class and public method.
            3. A module-level docstring explaining the purpose.
            4. A main class named `{_to_class_name(capability_name)}` with sensible public methods.
            5. Graceful error handling — no uncaught exceptions in public methods.
            6. Logging via `logging.getLogger(__name__)`.
            7. No external API calls unless essential; use environment variables for credentials.
            8. The module must be importable with zero side-effects.

            ## Code Style (match this existing module)
            ```python
            {style_sample}
            ```

            ## Output format
            Return ONLY the raw Python source code with no markdown fences,
            no explanation, and no extra commentary.
        """).strip()

        try:
            response = self._client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}],
            )
            code = response.content[0].text.strip()
            # Strip accidental markdown fences
            if code.startswith("```"):
                lines = code.splitlines()
                code = "\n".join(
                    line for line in lines
                    if not line.startswith("```")
                )
            return code
        except Exception as exc:
            logger.error("Claude generation failed for '%s': %s — falling back to stub", capability_name, exc)
            return self._stub_code(capability_name, description)

    def _fix_code(
        self,
        capability_name: str,
        description: str,
        broken_code: str,
        error_output: str,
    ) -> str:
        """
        Ask Claude to repair broken code given the pytest error output.

        Falls back to the original broken code if the client is unavailable
        (at least we don't regress).
        """
        if self._client is None:
            return broken_code

        prompt = textwrap.dedent(f"""
            You are an expert Python debugger.

            The following Python module was generated for capability `{capability_name}`:

            ```python
            {broken_code}
            ```

            Running `pytest tests/ -v --tb=short` produced this error:

            ```
            {error_output[:3000]}
            ```

            Fix ALL errors so that the test suite passes.
            Return ONLY the corrected Python source code — no markdown, no explanation.
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
                fixed = "\n".join(
                    line for line in lines
                    if not line.startswith("```")
                )
            return fixed
        except Exception as exc:
            logger.error("Claude fix failed for '%s': %s — keeping previous code", capability_name, exc)
            return broken_code

    @staticmethod
    def _stub_code(capability_name: str, description: str) -> str:
        """
        Generate a well-structured stub module when the API is unavailable.

        The stub is importable and provides the expected class interface
        so downstream code does not break.
        """
        class_name = _to_class_name(capability_name)
        timestamp = datetime.utcnow().isoformat()
        return textwrap.dedent(f'''
            """
            {capability_name}: {description}

            AUTO-GENERATED STUB — {timestamp}
            Replace this implementation with a real one.
            """

            import logging
            from typing import Any, Dict, Optional

            logger = logging.getLogger(__name__)


            class {class_name}:
                """
                {description}

                This is a generated stub.  Implement the methods below.
                """

                def __init__(self) -> None:
                    logger.info("{class_name} initialised (stub)")

                def run(self, *args: Any, **kwargs: Any) -> Dict:
                    """Execute the capability (stub implementation).

                    Args:
                        *args:   Positional arguments (ignored by stub).
                        **kwargs: Keyword arguments (ignored by stub).

                    Returns:
                        Dict with ``status`` and ``message`` keys.
                    """
                    logger.warning("{class_name}.run() called on stub — not implemented")
                    return {{"status": "stub", "message": "Not implemented yet"}}

                def get_status(self) -> Dict:
                    """Return capability status.

                    Returns:
                        Dict with health/readiness information.
                    """
                    return {{"ready": False, "reason": "stub implementation"}}
        ''').strip() + "\n"


# ── Utility ────────────────────────────────────────────────────────────────

def _to_class_name(snake: str) -> str:
    """Convert ``snake_case`` to ``PascalCase``."""
    return "".join(word.capitalize() for word in snake.split("_"))
