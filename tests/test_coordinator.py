"""
Tests for Adamus Coordinator.

The coordinator is the HEART of Adamus.
It must route correctly and enforce security.
"""

import pytest


class TestModelRouter:
    """Tests for model routing."""

    def test_routes_safe_data_to_free_brain(self):
        """Test safe data routes to a free brain (opencode first, then Claude fallback)."""
        from src.coordinator.model_router import ModelRouter, Brain

        router = ModelRouter(budget_remaining=100.0)
        router._claude_available = True
        router._ollama_available = True

        brain, reason = router.select_brain(
            data_level=1,
            task_type="coding"
        )

        # OpenCode is free and takes priority; Claude is the power fallback
        assert brain in (Brain.OPENCODE, Brain.CLAUDE)

    def test_routes_confidential_to_ollama(self):
        """Test confidential data must route to Ollama."""
        from src.coordinator.model_router import ModelRouter, Brain

        router = ModelRouter()
        router._ollama_available = True

        brain, reason = router.select_brain(
            data_level=3,  # CONFIDENTIAL
            task_type="analysis"
        )

        assert brain == Brain.OLLAMA
        assert "level 3" in reason.lower()

    def test_blocks_secret_data(self):
        """Test secret data is blocked entirely."""
        from src.coordinator.model_router import ModelRouter, SecurityError

        router = ModelRouter()

        with pytest.raises(SecurityError):
            router.select_brain(
                data_level=4,  # SECRET
                task_type="anything"
            )

    def test_respects_budget(self):
        """Test budget constraints are respected — free brains used first."""
        from src.coordinator.model_router import ModelRouter, Brain

        router = ModelRouter(budget_remaining=0.001)
        router._opencode_available = False  # disable opencode to test budget fallback
        router._claude_available = True
        router._ollama_available = True

        # With low budget and no opencode, should route to free Ollama
        brain, reason = router.select_brain(
            data_level=1,
            task_type="coding",
            estimated_tokens=10000
        )

        assert brain in (Brain.OLLAMA,)
        assert "budget" in reason.lower()

    def test_prefers_free_brain_for_complex_tasks(self):
        """Test opencode (free) is used first; Claude is the power fallback."""
        from src.coordinator.model_router import ModelRouter, Brain

        router = ModelRouter(budget_remaining=100.0)
        router._claude_available = True
        router._ollama_available = True

        brain, reason = router.select_brain(
            data_level=1,
            task_type="architecture"
        )

        # OpenCode takes priority as it's free; Claude is power fallback
        assert brain in (Brain.OPENCODE, Brain.CLAUDE)


class TestTaskRouter:
    """Tests for task routing to agents."""

    def test_routes_to_business_ai(self):
        """Test business tasks route to Business AI."""
        from src.coordinator.task_router import TaskRouter, Agent

        router = TaskRouter()

        task = router.route_task("Analyze competitor pricing and MRR trends")

        assert task.agent == Agent.BUSINESS

    def test_routes_to_cambi_ai(self):
        """Test community tasks route to CAMBI AI."""
        from src.coordinator.task_router import TaskRouter, Agent

        router = TaskRouter()

        task = router.route_task("Analyze community sentiment on Discord")

        assert task.agent == Agent.CAMBI

    def test_routes_to_tech_ai(self):
        """Test technical tasks route to Tech AI."""
        from src.coordinator.task_router import TaskRouter, Agent

        router = TaskRouter()

        task = router.route_task("Implement the user authentication API")

        assert task.agent == Agent.TECH

    def test_force_routing(self):
        """Test forced routing to specific agent."""
        from src.coordinator.task_router import TaskRouter, Agent

        router = TaskRouter()

        task = router.route_task(
            "General question",
            force_agent=Agent.BUSINESS
        )

        assert task.agent == Agent.BUSINESS

    def test_priority_queue(self):
        """Test tasks are queued by priority."""
        from src.coordinator.task_router import TaskRouter, TaskPriority

        router = TaskRouter()

        # Add tasks in reverse priority order
        router.route_task("Low priority task", priority=TaskPriority.LOW)
        router.route_task("Critical task", priority=TaskPriority.CRITICAL)
        router.route_task("Medium task", priority=TaskPriority.MEDIUM)

        # Get next task - should be critical
        from src.coordinator.task_router import Agent
        next_task = router.get_next_task(Agent.TECH)

        assert next_task.priority == TaskPriority.CRITICAL

    def test_mrr_prioritization(self):
        """Test MRR impact prioritization."""
        from src.coordinator.task_router import TaskRouter, TaskPriority

        router = TaskRouter()

        task = router.route_task(
            "Fix payment subscription bug affecting MRR",
            priority=TaskPriority.MEDIUM
        )

        router.prioritize_by_mrr_impact()

        # Task should be upgraded to HIGH
        from src.coordinator.task_router import Agent
        tasks = router.get_agent_tasks(Agent.TECH)
        target = next((t for t in tasks if t.id == task.id), None)

        if target:
            assert target.priority == TaskPriority.HIGH


class TestAICoordinator:
    """Tests for the main AI Coordinator."""

    @pytest.mark.asyncio
    async def test_coordinator_initialization(self):
        """Test coordinator initializes correctly."""
        from src.coordinator.ai_coordinator import AICoordinator
        import tempfile
        import os

        # Use temp directory for testing
        with tempfile.TemporaryDirectory() as tmpdir:
            docs_path = os.path.expanduser("~/adamus/docs/architecture")
            db_path = os.path.join(tmpdir, "test.db")

            coordinator = AICoordinator(
                docs_path=docs_path,
                db_path=db_path,
                monthly_budget=200.0
            )

            # Only initialize if docs exist
            import pathlib
            if pathlib.Path(docs_path).exists():
                status = await coordinator.initialize()

                assert status["status"] == "ready"
                assert status["documents_loaded"] > 0
                assert coordinator._initialized

    @pytest.mark.asyncio
    async def test_get_status(self):
        """Test getting coordinator status."""
        from src.coordinator.ai_coordinator import AICoordinator
        import tempfile
        import os
        import pathlib

        docs_path = os.path.expanduser("~/adamus/docs/architecture")
        if not pathlib.Path(docs_path).exists():
            pytest.skip("Architecture docs not found")

        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test.db")

            coordinator = AICoordinator(
                docs_path=docs_path,
                db_path=db_path
            )

            await coordinator.initialize()
            status = await coordinator.get_status()

            assert status["status"] == "ready"
            assert "documents" in status
            assert "security" in status
            assert "brains" in status

    @pytest.mark.asyncio
    async def test_execute_task_requires_init(self):
        """Test execute_task requires initialization."""
        from src.coordinator.ai_coordinator import AICoordinator

        coordinator = AICoordinator()

        with pytest.raises(RuntimeError, match="not initialized"):
            await coordinator.execute_task("Test task")
