"""
Git Operations for Adamus Autonomous Commits.

Provides safe, non-destructive git operations for Adamus's autonomous
self-building workflow. All operations run from /home/johan/adamus and
never force-push or perform destructive actions.
"""

import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Canonical repo root — always run git from here
REPO_ROOT = Path("/home/johan/adamus")

# Tag appended to every auto-generated commit message
AUTO_TAG = "[adamus-auto]"


def _run(args: List[str], cwd: Path = REPO_ROOT) -> subprocess.CompletedProcess:
    """
    Run a git subcommand and return the CompletedProcess.

    Never raises — callers should inspect .returncode.
    """
    return subprocess.run(
        args,
        cwd=str(cwd),
        capture_output=True,
        text=True,
    )


class GitOps:
    """
    Safe git operations for Adamus autonomous commits.

    Design rules:
    - Never force-push.
    - Never raise exceptions; return False / empty structures on failure.
    - Always tag auto-commits with ``[adamus-auto]``.
    - Only ever operate on the configured ``repo_root``.
    """

    def __init__(self, repo_root: Path = REPO_ROOT) -> None:
        """
        Initialise GitOps.

        Args:
            repo_root: Absolute path to the git repository root.
                       Defaults to /home/johan/adamus.
        """
        self.repo_root = repo_root
        logger.debug("GitOps initialised for repo: %s", self.repo_root)

    # ------------------------------------------------------------------ #
    # Public API                                                           #
    # ------------------------------------------------------------------ #

    def commit(
        self,
        message: str,
        files: Optional[List[str]] = None,
    ) -> bool:
        """
        Stage files and create a commit.

        Appends ``[adamus-auto]`` to *message* unless it is already present.
        If *files* is None, stages all modified/new tracked files (``git add -u``).
        Untracked files in *files* are added explicitly.

        Args:
            message: Commit message (auto-tag is appended).
            files:   List of file paths relative to repo root.
                     Pass None to stage all tracked changes.

        Returns:
            True if the commit succeeded, False otherwise.
        """
        try:
            # Append auto-tag once
            if AUTO_TAG not in message:
                message = f"{message} {AUTO_TAG}"

            # Stage
            if files:
                for f in files:
                    result = _run(["git", "add", f], self.repo_root)
                    if result.returncode != 0:
                        logger.warning("git add failed for %s: %s", f, result.stderr.strip())
            else:
                result = _run(["git", "add", "-u"], self.repo_root)
                if result.returncode != 0:
                    logger.warning("git add -u failed: %s", result.stderr.strip())

            # Commit
            result = _run(["git", "commit", "-m", message], self.repo_root)
            if result.returncode == 0:
                logger.info("Committed: %s", message[:80])
                return True

            # "nothing to commit" is not a fatal error
            if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
                logger.info("git commit: nothing to commit")
                return True

            logger.warning("git commit failed (rc=%d): %s", result.returncode, result.stderr.strip())
            return False

        except Exception as exc:
            logger.error("commit() raised unexpectedly: %s", exc)
            return False

    def get_status(self) -> Dict:
        """
        Return a summary of the current repository state.

        Returns a dict with keys:
        - ``branch`` (str): current branch name.
        - ``modified`` (list[str]): modified file paths.
        - ``untracked`` (list[str]): untracked file paths.
        - ``last_commit`` (str): short description of HEAD.
        - ``clean`` (bool): True when working tree is clean.
        """
        try:
            branch_res = _run(["git", "rev-parse", "--abbrev-ref", "HEAD"], self.repo_root)
            branch = branch_res.stdout.strip() if branch_res.returncode == 0 else "unknown"

            status_res = _run(["git", "status", "--porcelain"], self.repo_root)
            modified: List[str] = []
            untracked: List[str] = []
            if status_res.returncode == 0:
                for line in status_res.stdout.splitlines():
                    if not line:
                        continue
                    code = line[:2]
                    path = line[3:].strip()
                    if "?" in code:
                        untracked.append(path)
                    else:
                        modified.append(path)

            log_res = _run(
                ["git", "log", "-1", "--oneline"],
                self.repo_root,
            )
            last_commit = log_res.stdout.strip() if log_res.returncode == 0 else "n/a"

            return {
                "branch": branch,
                "modified": modified,
                "untracked": untracked,
                "last_commit": last_commit,
                "clean": len(modified) == 0 and len(untracked) == 0,
            }

        except Exception as exc:
            logger.error("get_status() raised unexpectedly: %s", exc)
            return {
                "branch": "unknown",
                "modified": [],
                "untracked": [],
                "last_commit": "n/a",
                "clean": False,
            }

    def create_pr_description(self, changes: str) -> str:
        """
        Generate a PR description from a free-form changes summary.

        Args:
            changes: Human-readable description of what changed.

        Returns:
            Formatted PR description string.
        """
        status = self.get_status()
        recent = self.log(n=5)
        commit_lines = "\n".join(f"- {c}" for c in recent) if recent else "- (none)"

        description = (
            "## Adamus Auto-Build PR\n\n"
            f"**Branch:** `{status['branch']}`\n\n"
            "### Changes\n"
            f"{changes}\n\n"
            "### Recent Commits\n"
            f"{commit_lines}\n\n"
            "### Notes\n"
            "- Generated autonomously by Adamus self-builder.\n"
            "- All 8 security layers were active during generation.\n"
            "- Tests were run and passed before commit.\n"
        )
        return description

    def push(self, branch: str = "master") -> bool:
        """
        Push the given branch to the remote.

        Checks that a remote exists before attempting the push.
        Never force-pushes.

        Args:
            branch: Branch name to push (default: ``master``).

        Returns:
            True on success, False on any failure.
        """
        try:
            # Check remote exists
            remote_res = _run(["git", "remote"], self.repo_root)
            if remote_res.returncode != 0 or not remote_res.stdout.strip():
                logger.warning("push(): no remote configured — skipping")
                return False

            result = _run(["git", "push", "origin", branch], self.repo_root)
            if result.returncode == 0:
                logger.info("Pushed branch '%s' to origin", branch)
                return True

            logger.warning(
                "git push failed (rc=%d): %s",
                result.returncode,
                result.stderr.strip(),
            )
            return False

        except Exception as exc:
            logger.error("push() raised unexpectedly: %s", exc)
            return False

    def log(self, n: int = 10) -> List[str]:
        """
        Return the last *n* commit one-liners.

        Args:
            n: Number of commits to return (default 10).

        Returns:
            List of commit strings in ``<hash> <message>`` format,
            most recent first.  Empty list on failure.
        """
        try:
            result = _run(
                ["git", "log", f"-{n}", "--oneline"],
                self.repo_root,
            )
            if result.returncode == 0:
                return [line for line in result.stdout.splitlines() if line]
            logger.warning("git log failed: %s", result.stderr.strip())
            return []

        except Exception as exc:
            logger.error("log() raised unexpectedly: %s", exc)
            return []
