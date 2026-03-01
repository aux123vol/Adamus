"""
Adamus CLI Interface

Augustus's command-line tool for interacting with Adamus.

Commands:
    adamus status        — System health overview
    adamus memory        — Search persistent memory
    adamus task <desc>   — Assign a task to Adamus
    adamus review        — List recent decisions/tasks for review
    adamus approve <id>  — Approve a pending decision
    adamus rollback      — Undo last git commit (safe rollback)

Usage:
    python -m src.ui.adamus_interface <command> [args]
    # or after install:
    adamus <command> [args]
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

# Top-level import so tests can patch it
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from src.memory.adamus_persistent_memory import AdamusPersistentMemory  # noqa: E402

# ── Colour helpers (no dependencies) ─────────────────────────────────────────
_GREEN  = "\033[32m"
_YELLOW = "\033[33m"
_RED    = "\033[31m"
_CYAN   = "\033[36m"
_BOLD   = "\033[1m"
_RESET  = "\033[0m"

def _g(s): return f"{_GREEN}{s}{_RESET}"
def _y(s): return f"{_YELLOW}{s}{_RESET}"
def _r(s): return f"{_RED}{s}{_RESET}"
def _b(s): return f"{_BOLD}{s}{_RESET}"
def _c(s): return f"{_CYAN}{s}{_RESET}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _adamus_root() -> Path:
    return Path("~/.adamus").expanduser()


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _git(cmd: str) -> str:
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=str(_repo_root())
        )
        return result.stdout.strip()
    except Exception as e:
        return str(e)


def _pytest_summary() -> str:
    """Quick test health check."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", "tests/", "-q", "--tb=no"],
            capture_output=True, text=True, cwd=str(_repo_root()), timeout=30
        )
        last = result.stdout.strip().split("\n")[-1]
        if "passed" in last:
            return _g(last)
        elif "failed" in last:
            return _r(last)
        return _y(last)
    except Exception as e:
        return _y(f"tests: {e}")


# ── Commands ──────────────────────────────────────────────────────────────────

def cmd_status(_args) -> None:
    """Print system health overview."""
    print(f"\n{_b('ADAMUS STATUS')} — {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")

    # Git state
    branch = _git("git rev-parse --abbrev-ref HEAD")
    last_commit = _git("git log -1 --oneline")
    dirty = _git("git status --porcelain")
    git_status = _r("uncommitted changes") if dirty else _g("clean")
    print(f"  {_b('Git')}    {branch} | {last_commit} | {git_status}")

    # Tests
    print(f"  {_b('Tests')}  {_pytest_summary()}")

    # Memory stats
    try:
        stats = AdamusPersistentMemory().get_stats()
        print(
            f"  {_b('Memory')} {stats['total_memories']} memories | "
            f"{stats['total_size_mb']} MB | "
            f"{stats['archived_memories']} archived"
        )
        recent = AdamusPersistentMemory().get_recent(days=1)
        print(f"  {_b('Recent')} {len(recent)} memories in last 24h")
    except Exception as e:
        print(f"  {_b('Memory')} {_y(f'unavailable ({e})')}")

    print()


def cmd_memory(args) -> None:
    """Search persistent memory."""
    query = " ".join(args.query) if args.query else ""

    mem = AdamusPersistentMemory()

    if not query:
        # Show recent
        results = mem.get_recent(days=7)
        print(f"\n{_b('Recent memories (last 7 days):')}\n")
    else:
        results = mem.search(query, limit=10)
        print(f"\n{_b(f'Search: {query}')}\n")

    if not results:
        print(f"  {_y('No memories found.')}\n")
        return

    for r in results:
        date = r["created_at"][:10]
        cat  = _c(r["category"])
        title = r["title"]
        summary = r.get("summary", "")[:80]
        print(f"  {_b(date)} [{cat}] {title}")
        if summary:
            print(f"           {summary}")
    print()


def cmd_task(args) -> None:
    """Assign a task — saves it to memory and prints guidance."""
    desc = " ".join(args.description)
    if not desc:
        print(_r("Error: provide a task description"))
        sys.exit(1)

    mem = AdamusPersistentMemory()

    # Pull relevant context
    context = mem.get_context_for_task(desc, max_items=3)

    # Save as pending task
    mem.save_memory(
        title=f"Task: {desc[:60]}",
        content=f"## Task\n{desc}\n\n## Relevant Context\n{context or 'None'}",
        category="task",
        tags=["task", "pending"],
    )

    print(f"\n{_b('Task assigned:')} {desc}")
    if context:
        print(f"\n{_b('Relevant memory found:')}")
        print(context)
    print(_g("\nSaved to Adamus memory.\n"))


def cmd_review(_args) -> None:
    """Show recent decisions and tasks pending review."""
    mem = AdamusPersistentMemory()

    print(f"\n{_b('REVIEW — pending decisions & tasks')}\n")

    for category in ("decision", "task"):
        items = mem.get_recent(category=category, days=7)
        if not items:
            continue
        print(f"  {_b(category.upper())}S ({len(items)})")
        for item in items[:5]:
            date = item["created_at"][:10]
            print(f"    {_c(date)} {item['title']}")
            print(f"           {item.get('file_path', '')}")
        print()


def cmd_approve(args) -> None:
    """Approve a decision by file path."""
    if not args.path:
        print(_r("Error: provide the file path of the decision to approve"))
        sys.exit(1)

    path = Path(args.path)
    if not path.exists():
        print(_r(f"File not found: {path}"))
        sys.exit(1)

    content = path.read_text()
    if "Augustus Approved**: False" in content:
        content = content.replace(
            "Augustus Approved**: False",
            "Augustus Approved**: True"
        )
        path.write_text(content)
        print(_g(f"\nApproved: {path.name}\n"))
    else:
        print(_y(f"Already approved or not a decision file: {path.name}"))


def cmd_rollback(_args) -> None:
    """Undo last git commit (keeps changes in working tree)."""
    last = _git("git log -1 --oneline")
    print(f"\n{_b('Last commit:')} {last}")

    confirm = input(_y("Rollback this commit? [y/N] ")).strip().lower()
    if confirm != "y":
        print("Aborted.")
        return

    result = _git("git reset HEAD~1")
    print(_g(f"\nRolled back. Changes are unstaged.\n"))
    print(_git("git status --short"))


# ── Interactive REPL (used by main.py --cli) ──────────────────────────────────

class AdamusInterface:
    """
    Async interactive CLI — lets Augustus chat with Adamus from the terminal.

    Used when running: python -m src.main --cli
    """

    BANNER = f"""
{_b('ADAMUS')} — AI CTO  {_c('(CLI mode)')}
Type a task or question. Commands: /status /queue /quit
"""

    def __init__(self, coordinator):
        self.coordinator = coordinator
        self._loop_ref = None  # set by caller if autonomous loop is running

    async def run(self) -> None:
        """Run the interactive REPL until the user quits."""
        print(self.BANNER)
        while True:
            try:
                raw = await asyncio.get_event_loop().run_in_executor(
                    None, lambda: input(_b("you> ")).strip()
                )
            except (EOFError, KeyboardInterrupt):
                print("\nBye.")
                break

            if not raw:
                continue

            if raw.lower() in ("/quit", "/exit", "quit", "exit"):
                print("Shutting down.")
                break

            if raw.lower() == "/status":
                cmd_status(None)
                continue

            if raw.lower() == "/queue":
                if self._loop_ref:
                    m = self._loop_ref.get_metrics()
                    print(f"  queue={m['queue_size']}  state={m['state']}  processed={m['tasks_processed']}")
                else:
                    print("  Autonomous loop not running.")
                continue

            # Send to coordinator
            print(_c("adamus> "), end="", flush=True)
            try:
                result = await self.coordinator.execute_task(raw)
                print(result.result)
            except Exception as e:
                print(_r(f"Error: {e}"))


import asyncio  # noqa: E402 (needed for AdamusInterface.run)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        prog="adamus",
        description="Adamus AI CTO — command-line interface",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status", help="System health overview")

    p_mem = sub.add_parser("memory", help="Search persistent memory")
    p_mem.add_argument("query", nargs="*", help="Search terms (omit for recent)")

    p_task = sub.add_parser("task", help="Assign a task to Adamus")
    p_task.add_argument("description", nargs="+", help="Task description")

    sub.add_parser("review", help="Review recent decisions and tasks")

    p_approve = sub.add_parser("approve", help="Approve a decision by file path")
    p_approve.add_argument("path", nargs="?", help="Path to decision file")

    sub.add_parser("rollback", help="Undo last git commit")

    args = parser.parse_args()

    dispatch = {
        "status":   cmd_status,
        "memory":   cmd_memory,
        "task":     cmd_task,
        "review":   cmd_review,
        "approve":  cmd_approve,
        "rollback": cmd_rollback,
    }
    dispatch[args.command](args)


if __name__ == "__main__":
    main()
