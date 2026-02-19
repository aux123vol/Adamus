"""
Context Manager: Provides complete context to brains.

This is the KEY to Adamus never forgetting.
Before ANY brain interaction, ContextManager provides:
- ALL architecture documents
- ALL past decisions
- ALL relevant conversations
- ALL current state

Brains are stateless. ContextManager gives them Adamus's full memory.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .document_loader import DocumentLoader, Document
from .memory_db import MemoryDatabase

logger = logging.getLogger(__name__)


@dataclass
class TaskContext:
    """Complete context for a task."""
    task_description: str
    task_id: str
    timestamp: str

    # Architecture context
    relevant_documents: List[Document]
    all_documents_summary: str

    # Memory context
    past_decisions: List[Dict]
    recent_conversations: List[Dict]

    # Current state
    monthly_spend: float
    budget_remaining: float

    # Security context
    data_classification: int  # 1-4
    allowed_brains: List[str]


class ContextManager:
    """
    Manages complete context for brain interactions.

    Adamus NEVER forgets because ContextManager:
    1. Loads ALL documents before every task
    2. Retrieves ALL relevant memory
    3. Feeds complete context to brains
    4. Stores results back to memory

    The brain forgets after the task.
    ContextManager ensures Adamus remembers.
    """

    def __init__(
        self,
        docs_path: str = "~/adamus/docs/architecture",
        db_path: str = "~/.adamus/memory.db",
        monthly_budget: float = 200.0
    ):
        """
        Initialize the context manager.

        Args:
            docs_path: Path to architecture documents
            db_path: Path to memory database
            monthly_budget: Monthly budget cap in USD
        """
        self.doc_loader = DocumentLoader(docs_path)
        self.memory_db = MemoryDatabase(db_path)
        self.monthly_budget = monthly_budget
        self._initialized = False

    async def initialize(self) -> None:
        """Initialize document loader and memory database."""
        logger.info("Initializing Adamus context manager...")

        # Initialize database
        await self.memory_db.initialize()

        # Load ALL documents
        self.doc_loader.load_all_documents()

        # Verify critical documents
        critical_status = self.doc_loader.verify_critical_documents()
        missing = [doc for doc, loaded in critical_status.items() if not loaded]

        if missing:
            logger.warning(f"Missing critical documents: {missing}")

        doc_summary = self.doc_loader.get_summary()
        logger.info(
            f"Context manager initialized: "
            f"{doc_summary['total_documents']} documents loaded"
        )

        self._initialized = True

    async def get_task_context(
        self,
        task_description: str,
        task_id: str,
        data_classification: int = 2
    ) -> TaskContext:
        """
        Get complete context for a task.

        This is called BEFORE every brain interaction.
        The brain receives Adamus's full memory.

        Args:
            task_description: What the task needs to do
            task_id: Unique task identifier
            data_classification: Security level (1-4)

        Returns:
            Complete TaskContext with all necessary information
        """
        if not self._initialized:
            await self.initialize()

        # Refresh documents if needed (hourly)
        changed = self.doc_loader.check_for_changes()
        if changed:
            logger.info(f"Reloading {len(changed)} changed documents")
            self.doc_loader.load_all_documents()

        # Find relevant documents for this task
        relevant_docs = self._find_relevant_documents(task_description)

        # Load memory context
        memory_context = await self.memory_db.load_complete_context()

        # Calculate budget remaining
        monthly_spend = memory_context['monthly_spend']
        budget_remaining = self.monthly_budget - monthly_spend

        # Determine allowed brains based on data classification
        allowed_brains = self._get_allowed_brains(data_classification)

        return TaskContext(
            task_description=task_description,
            task_id=task_id,
            timestamp=datetime.now().isoformat(),
            relevant_documents=relevant_docs,
            all_documents_summary=self._create_docs_summary(),
            past_decisions=[
                {
                    'decision': d.decision,
                    'reasoning': d.reasoning,
                    'timestamp': d.timestamp
                }
                for d in memory_context['decisions'][:20]  # Recent 20
            ],
            recent_conversations=[
                {
                    'role': c.role,
                    'content': c.content[:500],  # Truncate for context
                    'timestamp': c.timestamp
                }
                for c in memory_context['recent_conversations'][:10]
            ],
            monthly_spend=monthly_spend,
            budget_remaining=budget_remaining,
            data_classification=data_classification,
            allowed_brains=allowed_brains
        )

    def _find_relevant_documents(
        self,
        task_description: str
    ) -> List[Document]:
        """
        Find documents relevant to the task.

        Uses keyword matching to identify most relevant docs.
        Always includes critical documents.
        """
        relevant = []
        task_lower = task_description.lower()

        # Keywords to document mapping
        keyword_docs = {
            'security': ['ZERO_TRUST_ARCHITECTURE.md', 'PROMPT_INJECTION_DEFENSE.md'],
            'memory': ['MASTER_CONTEXT_SYSTEM.md', 'MEMORY_ARCHITECTURE_FINAL.md'],
            'privacy': ['PPAI_ARCHITECTURE_SPEC.md', 'TELEMETRY_FREE_SEARCH.md'],
            'coordinator': ['NETWORKED_AI_TRINITY.md', 'COMPLETE_ARCHITECTURE.md'],
            'build': ['WEEK_0_BUILD_PLAN.md', 'IMPLEMENTATION_ROADMAP.md'],
            'protocol': ['MASTER_PROTOCOL.md'],
            'genre': ['GENRE_MVP_SPEC.md'],
            'bias': ['BIAS_DETECTION_FRAMEWORK.md'],
            'data': ['DATA_GOVERNANCE_FRAMEWORK.md'],
            'llm': ['LLM_OPTIMIZATION_FRAMEWORK.md'],
        }

        # Always include critical docs
        critical = ['MASTER_PROTOCOL.md', 'MASTER_CONTEXT_SYSTEM.md']
        for doc_name in critical:
            doc = self.doc_loader.get_document(doc_name)
            if doc:
                relevant.append(doc)

        # Add keyword-matched docs
        for keyword, doc_names in keyword_docs.items():
            if keyword in task_lower:
                for doc_name in doc_names:
                    doc = self.doc_loader.get_document(doc_name)
                    if doc and doc not in relevant:
                        relevant.append(doc)

        return relevant

    def _create_docs_summary(self) -> str:
        """Create a summary of all loaded documents."""
        summary = self.doc_loader.get_summary()
        lines = [
            f"Loaded {summary['total_documents']} architecture documents",
            f"Total size: {summary['total_size_kb']:.1f} KB",
            "",
            "Key documents:",
        ]

        for doc in summary['documents'][:10]:
            lines.append(f"  - {doc['name']}: {doc['title']}")

        return "\n".join(lines)

    def _get_allowed_brains(self, data_classification: int) -> List[str]:
        """
        Determine which brains can be used based on data classification.

        Level 1-2: Can use Claude (external)
        Level 3-4: Ollama only (local)
        """
        if data_classification <= 2:
            return ['claude', 'ollama']
        else:
            return ['ollama']  # Sensitive data - local only

    def generate_brain_prompt(self, context: TaskContext) -> str:
        """
        Generate a comprehensive prompt for the brain.

        This prompt contains Adamus's complete context,
        ensuring the brain has all necessary information.
        """
        docs_content = "\n\n".join([
            f"### {doc.name}\n{doc.content[:2000]}..."  # Truncate large docs
            for doc in context.relevant_documents[:5]
        ])

        decisions_text = "\n".join([
            f"- {d['timestamp']}: {d['decision']}"
            for d in context.past_decisions[:5]
        ])

        prompt = f"""
═══════════════════════════════════════════════════════════
ADAMUS CONTEXT INJECTION
═══════════════════════════════════════════════════════════

You are executing a task for Adamus, the AI CTO orchestrator.
You (the brain) are stateless and will forget after this task.
Adamus remembers everything - you are just a tool.

═══════════════════════════════════════════════════════════
CURRENT TASK
═══════════════════════════════════════════════════════════

Task ID: {context.task_id}
Description: {context.task_description}
Data Classification: Level {context.data_classification}
Allowed Brains: {', '.join(context.allowed_brains)}

═══════════════════════════════════════════════════════════
BUDGET STATUS
═══════════════════════════════════════════════════════════

Monthly Spend: ${context.monthly_spend:.2f}
Budget Remaining: ${context.budget_remaining:.2f}
Budget Cap: ${self.monthly_budget:.2f}

⚠️  If budget is low, prefer Ollama (free) over Claude.

═══════════════════════════════════════════════════════════
RELEVANT ARCHITECTURE
═══════════════════════════════════════════════════════════

{docs_content}

═══════════════════════════════════════════════════════════
RECENT DECISIONS
═══════════════════════════════════════════════════════════

{decisions_text}

═══════════════════════════════════════════════════════════
CONSTRAINTS
═══════════════════════════════════════════════════════════

1. Follow MASTER_PROTOCOL.md rules
2. All 8 security systems must be respected
3. Level 3-4 data → Ollama only
4. Tests required before any output
5. No secrets in code (use .env)
6. Maintain consistency with all context above

═══════════════════════════════════════════════════════════
EXECUTE TASK
═══════════════════════════════════════════════════════════

Now execute: {context.task_description}
"""
        return prompt

    async def store_task_result(
        self,
        context: TaskContext,
        result: str,
        success: bool,
        brain_used: str
    ) -> None:
        """
        Store task result in permanent memory.

        The brain forgets after this. Adamus remembers.
        """
        from .memory_db import TaskResult

        task_result = TaskResult(
            id=context.task_id,
            task_description=context.task_description,
            brain_used=brain_used,
            started_at=context.timestamp,
            completed_at=datetime.now().isoformat(),
            result=result,
            success=success,
            documents_referenced=[d.name for d in context.relevant_documents]
        )

        await self.memory_db.store_task_result(task_result)
        logger.info(f"Task {context.task_id} result stored in memory")
