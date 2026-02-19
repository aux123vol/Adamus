"""
Memory Database: Persistent storage for Adamus.

Adamus NEVER forgets because everything is stored here:
- All decisions made
- All conversations
- All task results
- All context

Brains forget after each use. Adamus remembers forever.
"""

import os
import json
import logging
import aiosqlite
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class Decision:
    """A recorded decision."""
    id: str
    timestamp: str
    context: str
    decision: str
    reasoning: str
    source_brain: str  # Which brain made this decision
    augustus_approved: bool


@dataclass
class Conversation:
    """A conversation segment."""
    id: str
    timestamp: str
    brain: str
    role: str  # 'human' or 'assistant'
    content: str
    task_id: Optional[str]


@dataclass
class TaskResult:
    """Result of a completed task."""
    id: str
    task_description: str
    brain_used: str
    started_at: str
    completed_at: str
    result: str
    success: bool
    documents_referenced: List[str]


class MemoryDatabase:
    """
    Persistent SQLite database for Adamus memory.

    This is the foundation of Adamus's persistent identity.
    While brains (Claude, Ollama) forget after each session,
    Adamus stores everything here permanently.
    """

    def __init__(self, db_path: str = "~/.adamus/memory.db"):
        """
        Initialize the memory database.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path).expanduser()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize database schema."""
        async with aiosqlite.connect(self.db_path) as db:
            # Decisions table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS decisions (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    context TEXT,
                    decision TEXT NOT NULL,
                    reasoning TEXT,
                    source_brain TEXT,
                    augustus_approved INTEGER DEFAULT 0
                )
            """)

            # Conversations table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id TEXT PRIMARY KEY,
                    timestamp TEXT NOT NULL,
                    brain TEXT,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    task_id TEXT
                )
            """)

            # Task results table
            await db.execute("""
                CREATE TABLE IF NOT EXISTS task_results (
                    id TEXT PRIMARY KEY,
                    task_description TEXT NOT NULL,
                    brain_used TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,
                    success INTEGER,
                    documents_referenced TEXT
                )
            """)

            # Document hashes (for change detection)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS document_hashes (
                    path TEXT PRIMARY KEY,
                    hash TEXT NOT NULL,
                    last_checked TEXT NOT NULL
                )
            """)

            # Budget tracking
            await db.execute("""
                CREATE TABLE IF NOT EXISTS budget_tracking (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    brain TEXT NOT NULL,
                    tokens_in INTEGER DEFAULT 0,
                    tokens_out INTEGER DEFAULT 0,
                    estimated_cost_usd REAL DEFAULT 0.0
                )
            """)

            # Security events (audit log)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    details TEXT,
                    blocked INTEGER DEFAULT 0
                )
            """)

            # Create indexes for performance
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_decisions_timestamp "
                "ON decisions(timestamp)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_conversations_task "
                "ON conversations(task_id)"
            )
            await db.execute(
                "CREATE INDEX IF NOT EXISTS idx_budget_timestamp "
                "ON budget_tracking(timestamp)"
            )

            await db.commit()
            self._initialized = True

        logger.info(f"Memory database initialized at {self.db_path}")

    async def store_decision(self, decision: Decision) -> None:
        """Store a decision in permanent memory."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT OR REPLACE INTO decisions
                (id, timestamp, context, decision, reasoning, source_brain, augustus_approved)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    decision.id,
                    decision.timestamp,
                    decision.context,
                    decision.decision,
                    decision.reasoning,
                    decision.source_brain,
                    1 if decision.augustus_approved else 0
                )
            )
            await db.commit()

    async def get_all_decisions(self) -> List[Decision]:
        """Retrieve all decisions from memory."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM decisions ORDER BY timestamp DESC"
            ) as cursor:
                rows = await cursor.fetchall()
                return [
                    Decision(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        context=row['context'],
                        decision=row['decision'],
                        reasoning=row['reasoning'],
                        source_brain=row['source_brain'],
                        augustus_approved=bool(row['augustus_approved'])
                    )
                    for row in rows
                ]

    async def store_conversation(self, conv: Conversation) -> None:
        """Store a conversation segment."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO conversations
                (id, timestamp, brain, role, content, task_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    conv.id,
                    conv.timestamp,
                    conv.brain,
                    conv.role,
                    conv.content,
                    conv.task_id
                )
            )
            await db.commit()

    async def get_conversations(
        self,
        task_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Conversation]:
        """Retrieve conversations, optionally filtered by task."""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            if task_id:
                query = """
                    SELECT * FROM conversations
                    WHERE task_id = ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = (task_id, limit)
            else:
                query = """
                    SELECT * FROM conversations
                    ORDER BY timestamp DESC
                    LIMIT ?
                """
                params = (limit,)

            async with db.execute(query, params) as cursor:
                rows = await cursor.fetchall()
                return [
                    Conversation(
                        id=row['id'],
                        timestamp=row['timestamp'],
                        brain=row['brain'],
                        role=row['role'],
                        content=row['content'],
                        task_id=row['task_id']
                    )
                    for row in rows
                ]

    async def store_task_result(self, result: TaskResult) -> None:
        """Store a task result."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO task_results
                (id, task_description, brain_used, started_at, completed_at,
                 result, success, documents_referenced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    result.id,
                    result.task_description,
                    result.brain_used,
                    result.started_at,
                    result.completed_at,
                    result.result,
                    1 if result.success else 0,
                    json.dumps(result.documents_referenced)
                )
            )
            await db.commit()

    async def track_budget(
        self,
        brain: str,
        tokens_in: int,
        tokens_out: int,
        cost_usd: float
    ) -> None:
        """Track API usage for budget enforcement."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO budget_tracking
                (timestamp, brain, tokens_in, tokens_out, estimated_cost_usd)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    brain,
                    tokens_in,
                    tokens_out,
                    cost_usd
                )
            )
            await db.commit()

    async def get_monthly_spend(self) -> float:
        """Get total spend for current month."""
        async with aiosqlite.connect(self.db_path) as db:
            first_of_month = datetime.now().replace(
                day=1, hour=0, minute=0, second=0, microsecond=0
            ).isoformat()

            async with db.execute(
                """
                SELECT SUM(estimated_cost_usd) as total
                FROM budget_tracking
                WHERE timestamp >= ?
                """,
                (first_of_month,)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0.0

    async def log_security_event(
        self,
        event_type: str,
        severity: str,
        details: str,
        blocked: bool = False
    ) -> None:
        """Log a security event to the immutable audit log."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO security_events
                (timestamp, event_type, severity, details, blocked)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now().isoformat(),
                    event_type,
                    severity,
                    details,
                    1 if blocked else 0
                )
            )
            await db.commit()

    async def get_memory_stats(self) -> Dict[str, Any]:
        """Get statistics about stored memory."""
        async with aiosqlite.connect(self.db_path) as db:
            stats = {}

            # Count decisions
            async with db.execute("SELECT COUNT(*) FROM decisions") as cursor:
                row = await cursor.fetchone()
                stats['total_decisions'] = row[0]

            # Count conversations
            async with db.execute("SELECT COUNT(*) FROM conversations") as cursor:
                row = await cursor.fetchone()
                stats['total_conversations'] = row[0]

            # Count tasks
            async with db.execute("SELECT COUNT(*) FROM task_results") as cursor:
                row = await cursor.fetchone()
                stats['total_tasks'] = row[0]

            # Monthly spend
            stats['monthly_spend_usd'] = await self.get_monthly_spend()

            # Security events
            async with db.execute(
                "SELECT COUNT(*) FROM security_events WHERE blocked = 1"
            ) as cursor:
                row = await cursor.fetchone()
                stats['threats_blocked'] = row[0]

            # Database file size
            stats['db_size_mb'] = self.db_path.stat().st_size / (1024 * 1024)

            return stats

    async def load_complete_context(self) -> Dict[str, Any]:
        """
        Load COMPLETE context before any brain interaction.

        This is called BEFORE every task to ensure the brain
        has access to all of Adamus's memory.
        """
        return {
            'decisions': await self.get_all_decisions(),
            'recent_conversations': await self.get_conversations(limit=50),
            'monthly_spend': await self.get_monthly_spend(),
            'stats': await self.get_memory_stats()
        }
