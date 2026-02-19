"""
Adamus Persistent Memory System

File-based TB+ capable memory with:
- Hierarchical structure at ~/.adamus/
- Progressive disclosure (load relevant chunks only)
- Fast index-based retrieval
- Auto-archiving (30d → compress, 90d → archive)
- Markdown files for human-readable memories

Structure:
    ~/.adamus/
    ├── memory/
    │   ├── adamus.db          (SQLite active memory)
    │   ├── memories/          (markdown by date)
    │   │   ├── 2026-02/
    │   │   └── archive/       (gzip compressed)
    │   ├── decisions/
    │   ├── conversations/
    │   └── project_index.md
    ├── knowledge/
    │   ├── docs/
    │   ├── genre/
    │   └── external/
    └── data/
        ├── metrics/
        ├── competitors/
        └── users/
"""

import gzip
import json
import logging
import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Root of all Adamus persistent data
ADAMUS_ROOT = Path("~/.adamus").expanduser()


class AdamusPersistentMemory:
    """
    Persistent memory system for Adamus.

    Stores everything on disk in a structured, searchable way.
    Supports TB+ of data via progressive disclosure — only loads
    what's relevant to the current task, not everything at once.
    """

    def __init__(self, root: Path = ADAMUS_ROOT):
        self.root = root
        self._setup_structure()
        self._init_index_db()

    # ─────────────────────────────────────────
    # Setup
    # ─────────────────────────────────────────

    def _setup_structure(self) -> None:
        """Create the full directory hierarchy."""
        dirs = [
            self.root / "memory" / "memories" / "archive",
            self.root / "memory" / "decisions",
            self.root / "memory" / "conversations",
            self.root / "knowledge" / "docs",
            self.root / "knowledge" / "genre",
            self.root / "knowledge" / "external",
            self.root / "data" / "metrics",
            self.root / "data" / "competitors",
            self.root / "data" / "users",
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

        index = self.root / "memory" / "project_index.md"
        if not index.exists():
            index.write_text(
                "# Adamus Project Index\n\n"
                f"Created: {datetime.now().isoformat()}\n\n"
                "## Active Projects\n\n"
                "## Completed Projects\n\n"
            )

    def _init_index_db(self) -> None:
        """
        SQLite index for fast full-text search across all markdown files.
        This is lightweight metadata only — actual content stays in files.
        """
        db_path = self.root / "memory" / "index.db"
        with sqlite3.connect(db_path) as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS memory_index (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    category TEXT NOT NULL,
                    title TEXT NOT NULL,
                    tags TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    size_bytes INTEGER DEFAULT 0,
                    archived INTEGER DEFAULT 0,
                    summary TEXT DEFAULT ''
                )
            """)
            db.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memory_fts
                USING fts5(title, tags, summary, content='memory_index', content_rowid='id')
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_category ON memory_index(category)"
            )
            db.execute(
                "CREATE INDEX IF NOT EXISTS idx_created ON memory_index(created_at)"
            )
            db.commit()
        self._index_db_path = db_path

    # ─────────────────────────────────────────
    # Write Memory
    # ─────────────────────────────────────────

    def save_memory(
        self,
        title: str,
        content: str,
        category: str = "general",
        tags: Optional[List[str]] = None,
        date: Optional[datetime] = None,
    ) -> Path:
        """
        Save a memory as a markdown file.

        Args:
            title: Short human-readable title
            content: Markdown content
            category: One of: general, decision, conversation, metric, competitor, user
            tags: List of search tags
            date: Date to file under (defaults to now)

        Returns:
            Path to saved file
        """
        if date is None:
            date = datetime.now()

        tags = tags or []
        month_dir = self.root / "memory" / "memories" / date.strftime("%Y-%m")
        month_dir.mkdir(parents=True, exist_ok=True)

        # Slugify title for filename
        slug = title.lower().replace(" ", "-").replace("/", "-")[:50]
        filename = f"{date.strftime('%d')}-{slug}.md"
        file_path = month_dir / filename

        # Write markdown with frontmatter
        frontmatter = (
            f"---\n"
            f"title: {title}\n"
            f"category: {category}\n"
            f"tags: [{', '.join(tags)}]\n"
            f"created: {date.isoformat()}\n"
            f"---\n\n"
        )
        file_path.write_text(frontmatter + content)

        # Index it
        self._index_file(file_path, title, category, tags, content[:200])
        logger.info(f"Memory saved: {file_path}")
        return file_path

    def save_decision(
        self,
        decision: str,
        reasoning: str,
        context: str = "",
        augustus_approved: bool = False,
    ) -> Path:
        """Save a major decision to decisions/."""
        now = datetime.now()
        slug = decision.lower().replace(" ", "-")[:40]
        filename = f"{now.strftime('%Y-%m-%d')}-{slug}.md"
        file_path = self.root / "memory" / "decisions" / filename

        content = (
            f"# Decision: {decision}\n\n"
            f"**Date**: {now.isoformat()}\n"
            f"**Augustus Approved**: {augustus_approved}\n\n"
            f"## Context\n{context}\n\n"
            f"## Reasoning\n{reasoning}\n"
        )
        file_path.write_text(content)
        self._index_file(
            file_path, decision, "decision",
            ["decision", "approved" if augustus_approved else "pending"],
            reasoning[:200]
        )
        return file_path

    def save_metric_snapshot(self, metrics: Dict[str, Any]) -> Path:
        """Save a metrics snapshot to data/metrics/."""
        now = datetime.now()
        filename = f"{now.strftime('%Y-%m-%d-%H%M')}-metrics.json"
        file_path = self.root / "data" / "metrics" / filename
        file_path.write_text(json.dumps(metrics, indent=2))
        return file_path

    def save_competitor_intel(self, competitor: str, intel: Dict[str, Any]) -> Path:
        """Save competitor intelligence to data/competitors/."""
        now = datetime.now()
        slug = competitor.lower().replace(" ", "-")
        filename = f"{now.strftime('%Y-%m-%d')}-{slug}.json"
        file_path = self.root / "data" / "competitors" / filename
        file_path.write_text(json.dumps({"competitor": competitor, "date": now.isoformat(), **intel}, indent=2))
        return file_path

    # ─────────────────────────────────────────
    # Read Memory (Progressive Disclosure)
    # ─────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Full-text search across all indexed memories.

        Returns lightweight metadata + summary, NOT full content.
        Use load_memory() to get the full text of a specific result.
        """
        with sqlite3.connect(self._index_db_path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                """
                SELECT m.file_path, m.title, m.category, m.tags,
                       m.created_at, m.summary, m.archived
                FROM memory_index m
                JOIN memory_fts f ON f.rowid = m.id
                WHERE memory_fts MATCH ?
                ORDER BY m.created_at DESC
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def load_memory(self, file_path: str) -> Optional[str]:
        """Load full content of a specific memory file."""
        path = Path(file_path)
        if not path.exists():
            # Try archived (gzip)
            gz = Path(str(path) + ".gz")
            if gz.exists():
                with gzip.open(gz, "rt") as f:
                    return f.read()
            return None
        return path.read_text()

    def get_recent(self, category: Optional[str] = None, days: int = 7) -> List[Dict[str, Any]]:
        """Get memories from the last N days, optionally filtered by category."""
        since = (datetime.now() - timedelta(days=days)).isoformat()
        with sqlite3.connect(self._index_db_path) as db:
            db.row_factory = sqlite3.Row
            if category:
                rows = db.execute(
                    """
                    SELECT file_path, title, category, tags, created_at, summary
                    FROM memory_index
                    WHERE created_at >= ? AND category = ? AND archived = 0
                    ORDER BY created_at DESC
                    """,
                    (since, category),
                ).fetchall()
            else:
                rows = db.execute(
                    """
                    SELECT file_path, title, category, tags, created_at, summary
                    FROM memory_index
                    WHERE created_at >= ? AND archived = 0
                    ORDER BY created_at DESC
                    """,
                    (since,),
                ).fetchall()
        return [dict(r) for r in rows]

    def get_context_for_task(self, task_description: str, max_items: int = 5) -> str:
        """
        Progressive disclosure: load only what's relevant to the current task.

        Returns a compact context string with the most relevant memories.
        This keeps token usage low instead of dumping everything.
        """
        results = self.search(task_description, limit=max_items)
        if not results:
            return ""

        lines = ["## Relevant Memory Context\n"]
        for r in results:
            lines.append(f"### {r['title']} ({r['category']})")
            lines.append(f"*{r['created_at'][:10]}* — {r['summary']}")
            lines.append(f"[Full: {r['file_path']}]\n")

        return "\n".join(lines)

    def get_project_index(self) -> str:
        """Load the project index."""
        return (self.root / "memory" / "project_index.md").read_text()

    def update_project_index(self, content: str) -> None:
        """Overwrite the project index."""
        (self.root / "memory" / "project_index.md").write_text(content)

    # ─────────────────────────────────────────
    # Auto-Archiving
    # ─────────────────────────────────────────

    def run_archiving(self) -> Dict[str, int]:
        """
        Auto-archive old memories:
        - 30–90 days old → gzip compress in place
        - 90+ days old → move to archive/ folder

        Returns counts: {compressed, archived}
        """
        now = datetime.now()
        compress_before = now - timedelta(days=30)
        archive_before = now - timedelta(days=90)
        counts = {"compressed": 0, "archived": 0}

        memories_dir = self.root / "memory" / "memories"
        archive_dir = memories_dir / "archive"

        for md_file in memories_dir.rglob("*.md"):
            if "archive" in md_file.parts:
                continue

            mtime = datetime.fromtimestamp(md_file.stat().st_mtime)

            if mtime < archive_before:
                # Move to archive/ as gzip
                dest = archive_dir / (md_file.name + ".gz")
                with open(md_file, "rb") as f_in, gzip.open(dest, "wb") as f_out:
                    shutil.copyfileobj(f_in, f_out)
                md_file.unlink()
                self._mark_archived(str(md_file))
                counts["archived"] += 1

            elif mtime < compress_before:
                # Gzip in place
                gz_path = md_file.with_suffix(md_file.suffix + ".gz")
                if not gz_path.exists():
                    with open(md_file, "rb") as f_in, gzip.open(gz_path, "wb") as f_out:
                        shutil.copyfileobj(f_in, f_out)
                    md_file.unlink()
                    counts["compressed"] += 1

        logger.info(f"Archiving complete: {counts}")
        return counts

    # ─────────────────────────────────────────
    # Stats
    # ─────────────────────────────────────────

    def get_stats(self) -> Dict[str, Any]:
        """Get storage stats."""
        with sqlite3.connect(self._index_db_path) as db:
            total = db.execute("SELECT COUNT(*) FROM memory_index").fetchone()[0]
            archived = db.execute(
                "SELECT COUNT(*) FROM memory_index WHERE archived = 1"
            ).fetchone()[0]
            by_cat = db.execute(
                "SELECT category, COUNT(*) FROM memory_index GROUP BY category"
            ).fetchall()

        root_size = sum(f.stat().st_size for f in self.root.rglob("*") if f.is_file())
        return {
            "total_memories": total,
            "archived_memories": archived,
            "by_category": dict(by_cat),
            "total_size_mb": round(root_size / (1024 * 1024), 2),
            "root": str(self.root),
        }

    # ─────────────────────────────────────────
    # Internal
    # ─────────────────────────────────────────

    def _index_file(
        self,
        file_path: Path,
        title: str,
        category: str,
        tags: List[str],
        summary: str,
    ) -> None:
        now = datetime.now().isoformat()
        size = file_path.stat().st_size if file_path.exists() else 0
        tags_str = json.dumps(tags)
        with sqlite3.connect(self._index_db_path) as db:
            db.execute(
                """
                INSERT OR REPLACE INTO memory_index
                (file_path, category, title, tags, created_at, updated_at, size_bytes, summary)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (str(file_path), category, title, tags_str, now, now, size, summary),
            )
            # Keep FTS table in sync
            db.execute(
                "INSERT OR REPLACE INTO memory_fts(rowid, title, tags, summary) "
                "VALUES ((SELECT id FROM memory_index WHERE file_path = ?), ?, ?, ?)",
                (str(file_path), title, tags_str, summary),
            )
            db.commit()

    def _mark_archived(self, file_path: str) -> None:
        with sqlite3.connect(self._index_db_path) as db:
            db.execute(
                "UPDATE memory_index SET archived = 1 WHERE file_path = ?",
                (file_path,),
            )
            db.commit()
