"""
Day 9 Tests — Self-Improvement Agent + Genre Build Agent

Covers:
- SelfBuildAgent: importable, has run_cycle(), build_with_context(), get_status()
- SelfBuildAgent: run_cycle() returns CycleResult with expected fields
- SelfBuildAgent: failure history tracking works
- SelfBuildAgent: gap detection returns list of dicts with name/description
- GenreBuildAgent: importable, has run_cycle(), enqueue_feature(), get_queue_status()
- GenreBuildAgent: enqueue_feature() adds to queue, dedup works
- GenreBuildAgent: get_queue_status() returns expected shape
- GenreBuildAgent: build_feature() returns GenreBuildResult in stub mode
- AutonomousLoop: wired with _self_build_agent and _genre_build_agent attributes
"""

import json
import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path


# ── SelfBuildAgent ─────────────────────────────────────────────────────────────

class TestSelfBuildAgentImports:
    def test_importable(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        assert SelfBuildAgent is not None

    def test_cycle_result_importable(self):
        from src.autonomous.self_build_agent import CycleResult
        assert CycleResult is not None

    def test_failure_record_importable(self):
        from src.autonomous.self_build_agent import FailureRecord
        assert FailureRecord is not None


class TestSelfBuildAgentInit:
    def test_instantiates(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        agent = SelfBuildAgent()
        assert agent is not None

    def test_has_run_cycle(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        assert hasattr(SelfBuildAgent, "run_cycle")
        assert callable(SelfBuildAgent.run_cycle)

    def test_has_build_with_context(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        assert hasattr(SelfBuildAgent, "build_with_context")

    def test_has_get_status(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        assert hasattr(SelfBuildAgent, "get_status")

    def test_has_get_failure_history(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        assert hasattr(SelfBuildAgent, "get_failure_history")


class TestSelfBuildAgentRunCycle:
    """run_cycle() must return a valid CycleResult even when mocked."""

    def test_run_cycle_returns_cycle_result(self):
        from src.autonomous.self_build_agent import SelfBuildAgent, CycleResult
        agent = SelfBuildAgent()
        # Patch _detect_gaps to return empty so nothing is built
        with patch.object(agent, "_detect_gaps", return_value=[]):
            result = agent.run_cycle(max_capabilities=1)
        assert isinstance(result, CycleResult)

    def test_run_cycle_zero_on_empty_gaps(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        agent = SelfBuildAgent()
        with patch.object(agent, "_detect_gaps", return_value=[]):
            result = agent.run_cycle()
        assert result.capabilities_attempted == 0
        assert result.capabilities_built == 0
        assert result.capabilities_failed == 0
        assert result.details == []

    def test_run_cycle_respects_max_capabilities(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult
        agent = SelfBuildAgent()
        gaps = [
            {"name": "cap_a", "description": "desc a"},
            {"name": "cap_b", "description": "desc b"},
            {"name": "cap_c", "description": "desc c"},
        ]
        mock_result = BuildResult(success=True, capability_name="cap_a", attempts=1, file_path="x.py", test_output="ok")
        with patch.object(agent, "_detect_gaps", return_value=gaps), \
             patch.object(agent, "build_with_context", return_value=mock_result):
            result = agent.run_cycle(max_capabilities=2)
        assert result.capabilities_attempted == 2

    def test_run_cycle_counts_successes(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult
        agent = SelfBuildAgent()
        gaps = [{"name": "cap_x", "description": "some cap"}]
        mock_ok = BuildResult(success=True, capability_name="cap_x", attempts=1, file_path="x.py", test_output="ok")
        with patch.object(agent, "_detect_gaps", return_value=gaps), \
             patch.object(agent, "build_with_context", return_value=mock_ok):
            result = agent.run_cycle(max_capabilities=5)
        assert result.capabilities_built == 1
        assert result.capabilities_failed == 0

    def test_run_cycle_counts_failures(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult
        agent = SelfBuildAgent()
        gaps = [{"name": "cap_y", "description": "broken cap"}]
        mock_fail = BuildResult(success=False, capability_name="cap_y", attempts=3, file_path="y.py",
                                test_output="err", error="tests failed")
        with patch.object(agent, "_detect_gaps", return_value=gaps), \
             patch.object(agent, "build_with_context", return_value=mock_fail):
            result = agent.run_cycle(max_capabilities=5)
        assert result.capabilities_built == 0
        assert result.capabilities_failed == 1


class TestSelfBuildAgentFailureHistory:
    def test_failure_history_empty_initially(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        agent = SelfBuildAgent()
        assert agent.get_failure_history("nonexistent") == []

    def test_failure_recorded_on_failed_build(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult
        agent = SelfBuildAgent()
        gaps = [{"name": "bad_cap", "description": "will fail"}]
        mock_fail = BuildResult(success=False, capability_name="bad_cap", attempts=3,
                                file_path="b.py", test_output="boom", error="boom")
        with patch.object(agent, "_detect_gaps", return_value=gaps), \
             patch.object(agent, "build_with_context", return_value=mock_fail):
            agent.run_cycle()
        history = agent.get_failure_history("bad_cap")
        assert len(history) == 1
        assert history[0].attempt == 1

    def test_failure_history_cleared_on_success(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult
        agent = SelfBuildAgent()
        gaps = [{"name": "flip_cap", "description": "flip"}]
        fail = BuildResult(success=False, capability_name="flip_cap", attempts=3,
                           file_path="f.py", test_output="err", error="err")
        ok = BuildResult(success=True, capability_name="flip_cap", attempts=1,
                         file_path="f.py", test_output="ok")
        with patch.object(agent, "_detect_gaps", return_value=gaps), \
             patch.object(agent, "build_with_context", return_value=fail):
            agent.run_cycle()
        assert len(agent.get_failure_history("flip_cap")) == 1
        with patch.object(agent, "_detect_gaps", return_value=gaps), \
             patch.object(agent, "build_with_context", return_value=ok):
            agent.run_cycle()
        assert agent.get_failure_history("flip_cap") == []


class TestSelfBuildAgentStatus:
    def test_get_status_returns_dict(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        agent = SelfBuildAgent()
        status = agent.get_status()
        assert isinstance(status, dict)
        assert "capabilities_built" in status
        assert "capabilities_with_failures" in status
        assert "failure_history_size" in status


class TestSelfBuildAgentGapDetection:
    def test_detect_gaps_returns_list(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        agent = SelfBuildAgent()
        gaps = agent._detect_gaps()
        assert isinstance(gaps, list)

    def test_detect_gaps_items_have_name_and_description(self):
        from src.autonomous.self_build_agent import SelfBuildAgent
        agent = SelfBuildAgent()
        gaps = agent._detect_gaps()
        for gap in gaps:
            assert "name" in gap
            assert "description" in gap


# ── GenreBuildAgent ────────────────────────────────────────────────────────────

class TestGenreBuildAgentImports:
    def test_importable(self):
        from src.autonomous.genre_build_agent import GenreBuildAgent
        assert GenreBuildAgent is not None

    def test_genre_feature_spec_importable(self):
        from src.autonomous.genre_build_agent import GenreFeatureSpec
        assert GenreFeatureSpec is not None

    def test_genre_build_result_importable(self):
        from src.autonomous.genre_build_agent import GenreBuildResult
        assert GenreBuildResult is not None

    def test_genre_cycle_result_importable(self):
        from src.autonomous.genre_build_agent import GenreCycleResult
        assert GenreCycleResult is not None


class TestGenreBuildAgentInit:
    def test_instantiates_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from src.autonomous.genre_build_agent import GenreBuildAgent
        agent = GenreBuildAgent()
        assert agent is not None
        assert agent._client is None

    def test_has_run_cycle(self):
        from src.autonomous.genre_build_agent import GenreBuildAgent
        assert hasattr(GenreBuildAgent, "run_cycle")

    def test_has_enqueue_feature(self):
        from src.autonomous.genre_build_agent import GenreBuildAgent
        assert hasattr(GenreBuildAgent, "enqueue_feature")

    def test_has_build_feature(self):
        from src.autonomous.genre_build_agent import GenreBuildAgent
        assert hasattr(GenreBuildAgent, "build_feature")

    def test_has_get_queue_status(self):
        from src.autonomous.genre_build_agent import GenreBuildAgent
        assert hasattr(GenreBuildAgent, "get_queue_status")


class TestGenreBuildAgentQueue:
    """Queue operations — use an in-memory queue to avoid touching disk."""

    @pytest.fixture
    def agent(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        from src.autonomous.genre_build_agent import GenreBuildAgent
        a = GenreBuildAgent()
        # Point queue file at a temp location
        import src.autonomous.genre_build_agent as mod
        monkeypatch.setattr(mod, "GENRE_QUEUE_FILE", tmp_path / "queue.json")
        return a

    def test_enqueue_adds_item(self, agent):
        agent.enqueue_feature("lore_editor", "Edit lore entries")
        status = agent.get_queue_status()
        assert status["total"] >= 1
        assert status["pending"] >= 1

    def test_enqueue_deduplicates(self, agent):
        agent.enqueue_feature("dup_feature", "First add")
        agent.enqueue_feature("dup_feature", "Second add — should be ignored")
        status = agent.get_queue_status()
        # Only one entry for dup_feature
        queue = agent._load_queue()
        names = [item["name"] for item in queue]
        assert names.count("dup_feature") == 1

    def test_get_queue_status_shape(self, agent):
        status = agent.get_queue_status()
        assert "total" in status
        assert "by_status" in status
        assert "pending" in status
        assert "done" in status
        assert "failed" in status

    def test_run_cycle_empty_queue_returns_zero(self, agent):
        from src.autonomous.genre_build_agent import GenreCycleResult
        result = agent.run_cycle(max_features=3)
        assert isinstance(result, GenreCycleResult)
        assert result.features_attempted == 0


class TestGenreBuildAgentBuildFeature:
    """build_feature() in stub mode (no API key)."""

    @pytest.fixture
    def agent(self, monkeypatch, tmp_path):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        import src.autonomous.genre_build_agent as mod
        features_dir = tmp_path / "features"
        monkeypatch.setattr(mod, "GENRE_FEATURES_DIR", features_dir)
        monkeypatch.setattr(mod, "REPO_ROOT", tmp_path)
        from src.autonomous.genre_build_agent import GenreBuildAgent
        a = GenreBuildAgent()
        return a

    def test_build_feature_returns_result(self, agent, tmp_path):
        from src.autonomous.genre_build_agent import GenreFeatureSpec, GenreBuildResult
        spec = GenreFeatureSpec(name="saga_timeline", description="Show saga timeline")
        mock_test = MagicMock()
        mock_test.passed = True
        mock_test.output = "1 passed"
        with patch.object(agent._builder, "run_tests", return_value=mock_test), \
             patch.object(agent._git, "commit", return_value=True):
            result = agent.build_feature(spec)
        assert isinstance(result, GenreBuildResult)
        assert result.feature_name == "saga_timeline"

    def test_build_feature_stub_success(self, agent, tmp_path):
        from src.autonomous.genre_build_agent import GenreFeatureSpec
        spec = GenreFeatureSpec(name="bible_export", description="Export bible to PDF")
        mock_test = MagicMock()
        mock_test.passed = True
        mock_test.output = "ok"
        with patch.object(agent._builder, "run_tests", return_value=mock_test), \
             patch.object(agent._git, "commit", return_value=True):
            result = agent.build_feature(spec)
        assert result.success is True
        assert result.attempts >= 1

    def test_stub_code_is_importable_python(self, agent):
        from src.autonomous.genre_build_agent import GenreFeatureSpec
        spec = GenreFeatureSpec(name="lore_search", description="Search lore entries")
        code = agent._stub_feature(spec)
        # Must be valid Python
        compile(code, "<string>", "exec")

    def test_stub_code_contains_class(self, agent):
        from src.autonomous.genre_build_agent import GenreFeatureSpec
        spec = GenreFeatureSpec(name="saga_arc", description="Arc tracking")
        code = agent._stub_feature(spec)
        assert "class SagaArc" in code

    def test_build_feature_failed_tests_returns_failure(self, agent):
        from src.autonomous.genre_build_agent import GenreFeatureSpec
        spec = GenreFeatureSpec(name="broken_feat", description="Will fail")
        mock_test = MagicMock()
        mock_test.passed = False
        mock_test.output = "FAILED test_something"
        with patch.object(agent._builder, "run_tests", return_value=mock_test):
            result = agent.build_feature(spec)
        assert result.success is False
        assert result.attempts == 3


# ── AutonomousLoop Day 9 wiring ────────────────────────────────────────────────

class TestAutonomousLoopDay9Wiring:
    """loop.py must expose the Day 9 agent attributes."""

    def test_loop_has_self_build_agent_attr(self):
        from src.autonomous.loop import AutonomousLoop
        loop = AutonomousLoop(coordinator=None)
        assert hasattr(loop, "_self_build_agent")

    def test_loop_has_genre_build_agent_attr(self):
        from src.autonomous.loop import AutonomousLoop
        loop = AutonomousLoop(coordinator=None)
        assert hasattr(loop, "_genre_build_agent")

    def test_loop_agents_initially_none(self):
        from src.autonomous.loop import AutonomousLoop
        loop = AutonomousLoop(coordinator=None)
        # Before _init_components they should be None
        assert loop._self_build_agent is None
        assert loop._genre_build_agent is None


# ── API endpoints ──────────────────────────────────────────────────────────────

@pytest.fixture
def web_client():
    from src.ui.unified_app import create_app
    app = create_app()
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


class TestSelfBuildApiEndpoints:
    """GET/POST /api/self-build must exist and return expected JSON."""

    def test_get_self_build_status_returns_200(self, web_client):
        r = web_client.get("/api/self-build")
        assert r.status_code == 200

    def test_get_self_build_status_is_json(self, web_client):
        r = web_client.get("/api/self-build")
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_get_self_build_has_ok_field(self, web_client):
        r = web_client.get("/api/self-build")
        data = json.loads(r.data)
        assert "ok" in data

    def test_get_self_build_has_pending_gaps(self, web_client):
        r = web_client.get("/api/self-build")
        data = json.loads(r.data)
        if data.get("ok"):
            assert "pending_gaps" in data
            assert isinstance(data["pending_gaps"], int)

    def test_post_self_build_trigger_returns_200(self, web_client):
        import json as json_mod
        r = web_client.post(
            "/api/self-build",
            data=json_mod.dumps({"max_capabilities": 0}),
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_post_self_build_trigger_has_attempted(self, web_client):
        import json as json_mod
        r = web_client.post(
            "/api/self-build",
            data=json_mod.dumps({"max_capabilities": 0}),
            content_type="application/json",
        )
        data = json.loads(r.data)
        if data.get("ok"):
            assert "attempted" in data
            assert "built" in data
            assert "failed" in data


class TestGenreBuildApiEndpoints:
    """GET/POST /api/genre-build must exist and return expected JSON."""

    def test_get_genre_build_status_returns_200(self, web_client):
        r = web_client.get("/api/genre-build")
        assert r.status_code == 200

    def test_get_genre_build_status_is_json(self, web_client):
        r = web_client.get("/api/genre-build")
        data = json.loads(r.data)
        assert isinstance(data, dict)

    def test_get_genre_build_has_ok_field(self, web_client):
        r = web_client.get("/api/genre-build")
        data = json.loads(r.data)
        assert "ok" in data

    def test_get_genre_build_has_queue_fields(self, web_client):
        r = web_client.get("/api/genre-build")
        data = json.loads(r.data)
        if data.get("ok"):
            assert "total" in data
            assert "pending" in data

    def test_post_genre_build_empty_queue_returns_200(self, web_client):
        import json as json_mod
        r = web_client.post(
            "/api/genre-build",
            data=json_mod.dumps({"max_features": 0}),
            content_type="application/json",
        )
        assert r.status_code == 200

    def test_post_genre_build_returns_result_shape(self, web_client):
        import json as json_mod
        r = web_client.post(
            "/api/genre-build",
            data=json_mod.dumps({"max_features": 0}),
            content_type="application/json",
        )
        data = json.loads(r.data)
        if data.get("ok"):
            assert "attempted" in data
            assert "built" in data
            assert "queue" in data


# ── Integration test: full self-improvement loop ───────────────────────────────

class TestSelfImprovementIntegration:
    """
    Prove the full loop: detect gap → build capability → test → result.

    Uses real SelfBuildAgent but mocks the underlying SelfBuilder so no
    actual Claude API call or file write is made.
    """

    def test_full_loop_gap_to_built(self, tmp_path):
        """Gap detected → build_with_context called → CycleResult shows 1 built."""
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult

        agent = SelfBuildAgent()

        # Inject a single known gap
        fake_gap = [{"name": "integration_cap", "description": "Integration test cap"}]

        # SelfBuilder returns success on first attempt
        mock_build_result = BuildResult(
            success=True,
            capability_name="integration_cap",
            attempts=1,
            file_path=str(tmp_path / "integration_cap.py"),
            test_output="1 passed",
        )

        with patch.object(agent, "_detect_gaps", return_value=fake_gap), \
             patch.object(agent._builder, "build_capability", return_value=mock_build_result):
            cycle = agent.run_cycle(max_capabilities=5)

        assert cycle.capabilities_attempted == 1
        assert cycle.capabilities_built == 1
        assert cycle.capabilities_failed == 0
        assert cycle.details[0]["name"] == "integration_cap"
        assert cycle.details[0]["success"] is True

    def test_full_loop_failure_records_history(self, tmp_path):
        """Gap → build fails → failure history is recorded for next retry."""
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult

        agent = SelfBuildAgent()
        fake_gap = [{"name": "flaky_cap", "description": "Flaky capability"}]
        mock_fail = BuildResult(
            success=False,
            capability_name="flaky_cap",
            attempts=3,
            file_path=str(tmp_path / "flaky_cap.py"),
            test_output="FAILED: assertion error",
            error="tests failed after 3 attempts",
        )

        with patch.object(agent, "_detect_gaps", return_value=fake_gap), \
             patch.object(agent._builder, "build_capability", return_value=mock_fail):
            cycle = agent.run_cycle()

        assert cycle.capabilities_failed == 1
        history = agent.get_failure_history("flaky_cap")
        assert len(history) == 1
        assert "tests failed" in history[0].error_summary.lower()

    def test_full_loop_retry_passes_failure_context(self, tmp_path):
        """On second run, failure history must appear in the enriched description."""
        from src.autonomous.self_build_agent import SelfBuildAgent
        from src.autonomous.self_builder import BuildResult

        agent = SelfBuildAgent()
        fake_gap = [{"name": "retry_cap", "description": "Will retry"}]
        mock_fail = BuildResult(
            success=False, capability_name="retry_cap", attempts=3,
            file_path=str(tmp_path / "retry_cap.py"),
            test_output="boom", error="boom error",
        )

        # First run — record failure
        with patch.object(agent, "_detect_gaps", return_value=fake_gap), \
             patch.object(agent._builder, "build_capability", return_value=mock_fail):
            agent.run_cycle()

        # Second run — capture what description is passed to build_capability
        captured = {}
        original_build = agent._builder.build_capability

        def capture_build(name, desc):
            captured["description"] = desc
            return BuildResult(success=True, capability_name=name, attempts=1,
                               file_path="x.py", test_output="ok")

        with patch.object(agent, "_detect_gaps", return_value=fake_gap), \
             patch.object(agent._builder, "build_capability", side_effect=capture_build):
            agent.run_cycle()

        # The failure context must be injected into the description
        assert "Previous Failures" in captured.get("description", "") or \
               "boom error" in captured.get("description", "")
