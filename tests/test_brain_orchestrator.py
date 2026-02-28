"""
Tests for the Multi-Brain Orchestrator.
"""
import os
import pytest
from unittest.mock import patch, MagicMock


class TestBrainConfigs:
    def test_all_brains_defined(self):
        from src.coordinator.brain_orchestrator import BRAIN_CONFIGS, Brain
        for b in Brain:
            assert b in BRAIN_CONFIGS

    def test_local_brains_have_no_cost(self):
        from src.coordinator.brain_orchestrator import BRAIN_CONFIGS, Brain
        for brain in (Brain.OLLAMA, Brain.LMSTUDIO):
            assert BRAIN_CONFIGS[brain].cost_per_1k == 0.0

    def test_local_brains_handle_all_data_levels(self):
        from src.coordinator.brain_orchestrator import BRAIN_CONFIGS, Brain
        for brain in (Brain.OLLAMA, Brain.LMSTUDIO):
            assert BRAIN_CONFIGS[brain].max_data_level == 4

    def test_remote_brains_limited_to_level_2(self):
        from src.coordinator.brain_orchestrator import BRAIN_CONFIGS, Brain
        for brain in (Brain.CLAUDE, Brain.DEEPSEEK, Brain.OPENAI):
            assert BRAIN_CONFIGS[brain].max_data_level <= 2

    def test_claude_is_not_local(self):
        from src.coordinator.brain_orchestrator import BRAIN_CONFIGS, Brain
        assert BRAIN_CONFIGS[Brain.CLAUDE].is_local is False


class TestBrainOrchestrator:
    @pytest.fixture
    def orch_no_brains(self):
        """Orchestrator with no brains available."""
        from src.coordinator.brain_orchestrator import BrainOrchestrator
        with patch.object(BrainOrchestrator, '_probe', return_value=False):
            o = BrainOrchestrator()
        return o

    @pytest.fixture
    def orch_claude_only(self):
        """Orchestrator with only Claude available."""
        from src.coordinator.brain_orchestrator import BrainOrchestrator, Brain
        def fake_probe(self_inner, brain, cfg):
            return brain == Brain.CLAUDE
        with patch.object(BrainOrchestrator, '_probe', fake_probe):
            with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-test123"}):
                o = BrainOrchestrator()
        return o

    @pytest.fixture
    def orch_local_only(self):
        """Orchestrator with only Ollama available."""
        from src.coordinator.brain_orchestrator import BrainOrchestrator, Brain
        def fake_probe(self_inner, brain, cfg):
            return brain == Brain.OLLAMA
        with patch.object(BrainOrchestrator, '_probe', fake_probe):
            o = BrainOrchestrator()
        return o

    @pytest.fixture
    def orch_all(self):
        """Orchestrator with all brains available."""
        from src.coordinator.brain_orchestrator import BrainOrchestrator
        with patch.object(BrainOrchestrator, '_probe', return_value=True):
            with patch.dict(os.environ, {
                "ANTHROPIC_API_KEY": "sk-ant-test",
                "DEEPSEEK_API_KEY": "ds-test",
                "OPENAI_API_KEY": "sk-test",
            }):
                o = BrainOrchestrator()
        return o

    # ── Route tests ──────────────────────────────────────────────────────────

    def test_no_brains_raises(self, orch_no_brains):
        from src.coordinator.brain_orchestrator import TaskType
        with pytest.raises(RuntimeError, match="No brains"):
            orch_no_brains.route()

    def test_level_3_data_requires_local(self, orch_local_only):
        from src.coordinator.brain_orchestrator import TaskType, Brain
        brain, reason = orch_local_only.route(data_level=3)
        assert brain == Brain.OLLAMA
        assert "local" in reason.lower()

    def test_level_3_no_local_raises(self, orch_claude_only):
        with pytest.raises(RuntimeError, match="local brain"):
            orch_claude_only.route(data_level=3)

    def test_chat_routes_to_claude_when_only_claude_available(self, orch_claude_only):
        from src.coordinator.brain_orchestrator import TaskType, Brain
        brain, reason = orch_claude_only.route(task_type=TaskType.CHAT)
        assert brain == Brain.CLAUDE

    def test_coding_prefers_free_brain(self, orch_all):
        """OpenCode (free) takes priority; Claude is power fallback."""
        from src.coordinator.brain_orchestrator import TaskType, Brain
        brain, reason = orch_all.route(task_type=TaskType.CODING)
        assert brain in (Brain.OPENCODE, Brain.CLAUDE)

    def test_background_prefers_free_brain(self, orch_all):
        """Background tasks use a free brain (opencode or local Ollama)."""
        from src.coordinator.brain_orchestrator import TaskType, Brain, BRAIN_CONFIGS
        brain, reason = orch_all.route(task_type=TaskType.BACKGROUND)
        assert BRAIN_CONFIGS[brain].cost_per_1k == 0.0

    def test_force_brain_respected(self, orch_all):
        from src.coordinator.brain_orchestrator import TaskType, Brain
        brain, reason = orch_all.route(force=Brain.OLLAMA)
        assert brain == Brain.OLLAMA
        assert "Forced" in reason

    def test_force_wrong_data_level_raises(self, orch_all):
        from src.coordinator.brain_orchestrator import Brain
        with pytest.raises(ValueError):
            orch_all.route(data_level=3, force=Brain.CLAUDE)

    # ── Status tests ─────────────────────────────────────────────────────────

    def test_get_status_returns_all_brains(self, orch_no_brains):
        status = orch_no_brains.get_status()
        from src.coordinator.brain_orchestrator import Brain
        for b in Brain:
            assert b.value in status

    def test_get_status_has_required_fields(self, orch_claude_only):
        status = orch_claude_only.get_status()
        first = next(iter(status.values()))
        assert "name" in first
        assert "available" in first
        assert "local" in first
        assert "cost_per_1k" in first

    def test_available_brains_list(self, orch_claude_only):
        assert len(orch_claude_only.available_brains) >= 1
        assert "Claude" in orch_claude_only.available_brains

    def test_no_available_brains_when_none(self, orch_no_brains):
        assert orch_no_brains.available_brains == []

    # ── Probe tests ──────────────────────────────────────────────────────────

    def test_claude_needs_api_key(self):
        from src.coordinator.brain_orchestrator import BrainOrchestrator, Brain, BRAIN_CONFIGS
        o = BrainOrchestrator.__new__(BrainOrchestrator)
        o._available = {}
        cfg = BRAIN_CONFIGS[Brain.CLAUDE]
        with patch.dict(os.environ, {}, clear=True):
            result = o._probe(Brain.CLAUDE, cfg)
        assert result is False

    def test_claude_available_with_key(self):
        from src.coordinator.brain_orchestrator import BrainOrchestrator, Brain, BRAIN_CONFIGS
        o = BrainOrchestrator.__new__(BrainOrchestrator)
        o._available = {}
        cfg = BRAIN_CONFIGS[Brain.CLAUDE]
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-ant-real"}):
            result = o._probe(Brain.CLAUDE, cfg)
        assert result is True

    # ── Streaming tests ──────────────────────────────────────────────────────

    def test_stream_yields_brain_header(self, orch_claude_only):
        chunks = []
        def fake_stream_claude(self_inner, messages, system, cfg):
            yield "Hello world"
        with patch('src.coordinator.brain_orchestrator.BrainOrchestrator._stream_claude', fake_stream_claude):
            for chunk in orch_claude_only.stream([{"role":"user","content":"hi"}]):
                chunks.append(chunk)
        assert any(c.startswith("__brain__") for c in chunks)
        assert any("Hello" in c for c in chunks)

    def test_stream_no_brains_raises(self, orch_no_brains):
        with pytest.raises(RuntimeError):
            list(orch_no_brains.stream([{"role":"user","content":"hi"}]))


# ── Helper ────────────────────────────────────────────────────────────────────

def BRAIN_CONFIGS_is_local(brain):
    from src.coordinator.brain_orchestrator import BRAIN_CONFIGS
    return BRAIN_CONFIGS[brain].is_local


class TestTaskType:
    def test_all_task_types_exist(self):
        from src.coordinator.brain_orchestrator import TaskType
        expected = {"chat","coding","planning","summarize","background","sensitive"}
        actual = {t.value for t in TaskType}
        assert expected == actual
