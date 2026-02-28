"""
AI Coordinator: The Central Orchestrator

This is the HEART of Adamus.

The AI Coordinator:
1. Loads ALL documents before every task
2. Routes tasks to the right agent (Business/CAMBI/Tech)
3. Selects the right brain (Claude/Ollama)
4. Enforces all 8 security layers
5. Stores results in permanent memory
6. Never forgets (brains forget, Adamus remembers)

This implements the Networked AI Trinity architecture.
"""

import os
import uuid
import logging
from datetime import datetime
from typing import Dict, Optional, Any, Tuple, List
from dataclasses import dataclass

from ..memory import DocumentLoader, MemoryDatabase, ContextManager
from ..security import SecurityWrapper, PPAIGateway
from .model_router import ModelRouter, Brain, SecurityError, BudgetError
from .task_router import TaskRouter, Agent, Task, TaskPriority

logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """Result of executing a task."""
    task_id: str
    success: bool
    result: str
    brain_used: str
    tokens_used: int
    cost_usd: float
    execution_time_ms: int
    documents_referenced: list
    security_audit: dict


class AICoordinator:
    """
    Central AI Coordinator.

    Implements the full Networked AI Trinity architecture:
    - Coordinates Business AI, CAMBI AI, Tech AI
    - Routes to appropriate brains (Claude, Ollama)
    - Enforces all 8 security layers
    - Maintains persistent memory

    This is the core of Adamus.
    """

    def __init__(
        self,
        docs_path: str = "~/adamus/docs/architecture",
        db_path: str = "~/.adamus/memory.db",
        monthly_budget: float = 200.0,
        strict_security: bool = True
    ):
        """
        Initialize the AI Coordinator.

        Args:
            docs_path: Path to architecture documents
            db_path: Path to memory database
            monthly_budget: Monthly budget cap in USD
            strict_security: Enable strict security mode
        """
        self.docs_path = docs_path
        self.db_path = db_path
        self.monthly_budget = monthly_budget

        # Core components
        self.context_manager: Optional[ContextManager] = None
        self.security_wrapper: Optional[SecurityWrapper] = None
        self.model_router: Optional[ModelRouter] = None
        self.task_router: Optional[TaskRouter] = None

        self._initialized = False
        self._strict_security = strict_security

        logger.info("AI Coordinator created (not yet initialized)")

    async def initialize(self) -> Dict[str, Any]:
        """
        Initialize all Adamus components.

        This MUST be called before any operations.
        Loads ALL documents and activates all 8 security layers.
        """
        logger.info("=" * 60)
        logger.info("INITIALIZING ADAMUS AI COORDINATOR")
        logger.info("=" * 60)

        init_status = {}

        # 1. Initialize Context Manager (Memory System)
        logger.info("1. Initializing Context Manager...")
        self.context_manager = ContextManager(
            docs_path=self.docs_path,
            db_path=self.db_path,
            monthly_budget=self.monthly_budget
        )
        await self.context_manager.initialize()

        doc_summary = self.context_manager.doc_loader.get_summary()
        init_status["documents_loaded"] = doc_summary["total_documents"]
        logger.info(f"   ✅ Loaded {doc_summary['total_documents']} documents")

        # Verify critical documents
        critical_status = self.context_manager.doc_loader.verify_critical_documents()
        missing = [d for d, v in critical_status.items() if not v]
        if missing:
            logger.warning(f"   ⚠️ Missing critical documents: {missing}")
        init_status["critical_docs_status"] = critical_status

        # 2. Initialize Security Wrapper (All 8 Layers)
        logger.info("2. Initializing Security Wrapper...")
        self.security_wrapper = SecurityWrapper(
            monthly_budget=self.monthly_budget,
            strict_mode=self._strict_security,
            memory_db=self.context_manager.memory_db
        )

        # Verify all 8 layers
        security_status = self.security_wrapper.verify_all_layers_active()
        all_secure = all(security_status.values())
        init_status["security_layers"] = security_status
        init_status["security_active"] = all_secure

        if all_secure:
            logger.info("   ✅ All 8 security layers active")
        else:
            inactive = [k for k, v in security_status.items() if not v]
            logger.error(f"   ❌ SECURITY DEGRADED: {inactive}")
            if self._strict_security:
                raise SecurityError(f"Cannot initialize: Security layers inactive: {inactive}")

        # 3. Initialize Model Router
        logger.info("3. Initializing Model Router...")
        self.model_router = ModelRouter(
            budget_remaining=self.monthly_budget,
            prefer_local=False
        )
        brain_status = self.model_router.get_brain_status()
        init_status["brains"] = brain_status

        if brain_status["claude"]["available"]:
            logger.info("   ✅ Claude (external) available")
        else:
            logger.warning("   ⚠️ Claude unavailable - check ANTHROPIC_API_KEY")

        if brain_status["ollama"]["available"]:
            logger.info("   ✅ Ollama (local) available")
        else:
            logger.warning("   ⚠️ Ollama unavailable - local AI disabled")

        # 4. Initialize Task Router
        logger.info("4. Initializing Task Router...")
        self.task_router = TaskRouter()
        init_status["task_router"] = "active"
        logger.info("   ✅ Task Router initialized")

        # Mark as initialized
        self._initialized = True
        init_status["status"] = "ready"
        init_status["timestamp"] = datetime.now().isoformat()

        logger.info("=" * 60)
        logger.info("ADAMUS AI COORDINATOR READY")
        logger.info(f"  Documents: {doc_summary['total_documents']}")
        logger.info(f"  Security: {'✅ All 8 layers' if all_secure else '⚠️ Degraded'}")
        logger.info(f"  Brains: Claude={'✅' if brain_status['claude']['available'] else '❌'}, "
                   f"Ollama={'✅' if brain_status['ollama']['available'] else '❌'}")
        logger.info("=" * 60)

        return init_status

    async def execute_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        data_level: int = 2,
        force_brain: Optional[str] = None,
        force_agent: Optional[Agent] = None
    ) -> ExecutionResult:
        """
        Execute a task through the full Adamus pipeline.

        This is the main entry point for all AI operations.

        Pipeline:
        1. Load complete context (ALL documents)
        2. Route to appropriate agent
        3. Run all 8 security checks
        4. Select and route to brain
        5. Execute with full context
        6. Check output
        7. Store result in memory
        8. Return result

        Args:
            description: Task description
            priority: Task priority
            data_level: Data sensitivity level (1-4)
            force_brain: Force specific brain ('claude' or 'ollama')
            force_agent: Force specific agent

        Returns:
            ExecutionResult with full details
        """
        if not self._initialized:
            raise RuntimeError("AI Coordinator not initialized. Call initialize() first.")

        start_time = datetime.now()
        task_id = f"exec_{start_time.strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"

        logger.info(f"[{task_id}] Starting task: {description[:50]}...")

        try:
            # 1. Get complete context (ALL documents + memory)
            context = await self.context_manager.get_task_context(
                task_description=description,
                task_id=task_id,
                data_classification=data_level
            )
            logger.info(f"[{task_id}] Context loaded: {len(context.relevant_documents)} relevant docs")

            # 2. Route to agent
            task = self.task_router.route_task(
                description=description,
                priority=priority,
                data_level=data_level,
                force_agent=force_agent
            )
            logger.info(f"[{task_id}] Routed to agent: {task.agent.value}")

            # 3. Generate prompt with full context
            full_prompt = self.context_manager.generate_brain_prompt(context)

            # 4. Run all 8 security checks
            security_result = self.security_wrapper.check_all_layers(
                prompt=full_prompt,
                estimated_tokens=len(full_prompt) // 4
            )

            if not security_result.passed:
                logger.warning(f"[{task_id}] BLOCKED by security: {security_result.blocked_reason}")
                return ExecutionResult(
                    task_id=task_id,
                    success=False,
                    result=f"Blocked by security: {security_result.blocked_reason}",
                    brain_used="none",
                    tokens_used=0,
                    cost_usd=0.0,
                    execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                    documents_referenced=[d.name for d in context.relevant_documents],
                    security_audit={
                        "passed": False,
                        "reason": security_result.blocked_reason,
                        "audit_trail": security_result.audit_trail
                    }
                )

            logger.info(f"[{task_id}] Security passed (score: {security_result.security_score:.2f})")

            # 5. Select brain
            if force_brain:
                brain = Brain.CLAUDE if force_brain.lower() == 'claude' else Brain.OLLAMA
                route_reason = "Forced"
            else:
                brain, route_reason = self.model_router.select_brain(
                    data_level=data_level,
                    task_type=self._classify_task_type(description),
                    estimated_tokens=len(full_prompt) // 4
                )

            logger.info(f"[{task_id}] Selected brain: {brain.value} ({route_reason})")

            # 6. Execute with brain (placeholder - actual API calls would go here)
            # In production, this would call Claude API or Ollama
            result = await self._execute_with_brain(
                brain=brain,
                prompt=security_result.sanitized_content or full_prompt,
                task_id=task_id
            )

            # 7. Check output
            output_ok, output_issues = self.security_wrapper.check_output(result["content"])
            if not output_ok:
                logger.warning(f"[{task_id}] Output issues detected: {output_issues}")
                result["content"] += f"\n\n[WARNING: Output issues: {output_issues}]"

            # 8. Store in memory
            await self.context_manager.store_task_result(
                context=context,
                result=result["content"],
                success=True,
                brain_used=brain.value
            )

            # 9. Record spending
            self.security_wrapper.record_operation(
                tokens_used=result["tokens"],
                brain=brain.value,
                success=True
            )

            execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

            logger.info(f"[{task_id}] Completed in {execution_time}ms")

            return ExecutionResult(
                task_id=task_id,
                success=True,
                result=result["content"],
                brain_used=brain.value,
                tokens_used=result["tokens"],
                cost_usd=result["cost"],
                execution_time_ms=execution_time,
                documents_referenced=[d.name for d in context.relevant_documents],
                security_audit={
                    "passed": True,
                    "score": security_result.security_score,
                    "audit_trail": security_result.audit_trail
                }
            )

        except Exception as e:
            logger.error(f"[{task_id}] Error: {e}")
            return ExecutionResult(
                task_id=task_id,
                success=False,
                result=f"Error: {str(e)}",
                brain_used="none",
                tokens_used=0,
                cost_usd=0.0,
                execution_time_ms=int((datetime.now() - start_time).total_seconds() * 1000),
                documents_referenced=[],
                security_audit={"error": str(e)}
            )

    async def _execute_with_brain(
        self,
        brain: Brain,
        prompt: str,
        task_id: str
    ) -> Dict[str, Any]:
        """
        Execute prompt with selected brain via BrainOrchestrator.

        Collects all streamed chunks into a single response.
        """
        from .brain_orchestrator import BrainOrchestrator, TaskType
        from .brain_orchestrator import Brain as OrcBrain

        orchestrator = BrainOrchestrator()

        # Map Brain enum to OrcBrain enum
        brain_map = {
            Brain.OPENCODE: OrcBrain.OPENCODE,
            Brain.CLAUDE: OrcBrain.CLAUDE,
            Brain.OLLAMA: OrcBrain.OLLAMA,
        }
        force_brain = brain_map.get(brain)

        messages = [{"role": "user", "content": prompt}]
        system = (
            "You are Adamus, an AI CTO. Execute the task precisely. "
            "Be direct and thorough. Return complete, actionable output."
        )

        chunks = []
        try:
            for chunk in orchestrator.stream(
                messages=messages,
                system=system,
                task_type=TaskType.CODING,
                data_level=1,
                force=force_brain,
            ):
                if not chunk.startswith("__brain__"):
                    chunks.append(chunk)
        except Exception as e:
            logger.error(f"[{task_id}] Brain execution error: {e}")
            return {
                "content": f"Brain execution failed: {e}",
                "tokens": 0,
                "cost": 0.0,
            }

        content = "".join(chunks)
        tokens = len(content) // 4
        cost = (tokens / 1000) * (0.009 if brain == Brain.CLAUDE else 0.0)

        return {"content": content, "tokens": tokens, "cost": cost}

    def _classify_task_type(self, description: str) -> str:
        """Classify task type for brain selection."""
        desc_lower = description.lower()

        if any(kw in desc_lower for kw in ["code", "implement", "build", "debug"]):
            return "coding"
        if any(kw in desc_lower for kw in ["architecture", "design", "plan"]):
            return "architecture"
        if any(kw in desc_lower for kw in ["summarize", "analyze"]):
            return "summarization"

        return "general"

    async def get_status(self) -> Dict[str, Any]:
        """Get current coordinator status."""
        if not self._initialized:
            return {"status": "not_initialized"}

        return {
            "status": "ready",
            "documents": self.context_manager.doc_loader.get_summary(),
            "security": self.security_wrapper.get_security_status(),
            "brains": self.model_router.get_brain_status(),
            "tasks": self.task_router.get_queue_status(),
            "budget_remaining": self.monthly_budget - self.security_wrapper.budget_tracker.current_spend
        }

    async def verify_ready_for_autonomous(self) -> Tuple[bool, List[str]]:
        """
        Verify system is ready for autonomous mode (OpenClaw).

        All 8 security layers MUST be active.
        """
        issues = []

        if not self._initialized:
            issues.append("Coordinator not initialized")

        # Check security
        self.security_wrapper.require_all_layers_active()

        # Check at least one brain available
        brain_status = self.model_router.get_brain_status()
        if not any(b["available"] for b in brain_status.values()):
            issues.append("No AI brains available")

        # Check documents loaded
        doc_count = len(self.context_manager.doc_loader.documents)
        if doc_count < 100:  # Should be 107+
            issues.append(f"Only {doc_count} documents loaded (expected 107+)")

        return len(issues) == 0, issues
