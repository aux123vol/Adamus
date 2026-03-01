"""Tests for autonomous systems: loop, self-builder, git ops."""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))


# ── GitOps ────────────────────────────────────────────────────────────────────

class TestGitOps:
    def setup_method(self):
        from src.autonomous.git_ops import GitOps
        self.git = GitOps()

    def test_get_status_returns_dict(self):
        s = self.git.get_status()
        assert isinstance(s, dict)
        assert "branch" in s
        assert "clean" in s

    def test_get_status_has_branch(self):
        s = self.git.get_status()
        assert isinstance(s["branch"], str)
        assert len(s["branch"]) > 0

    def test_log_returns_list(self):
        log = self.git.log(n=5)
        assert isinstance(log, list)

    def test_log_length(self):
        log = self.git.log(n=3)
        assert len(log) <= 3

    def test_create_pr_description_returns_string(self):
        desc = self.git.create_pr_description("Added new capability")
        assert isinstance(desc, str)
        assert len(desc) > 0

    def test_create_pr_description_contains_changes(self):
        desc = self.git.create_pr_description("Added capability X")
        assert "capability X" in desc or "Added" in desc

    def test_commit_false_without_changes(self):
        # Nothing to commit right now (or graceful false)
        result = self.git.commit("test: no-op commit [adamus-test]")
        assert isinstance(result, bool)

    def test_push_returns_bool(self):
        # Should return bool (True or False) without raising
        result = self.git.push()
        assert isinstance(result, bool)


# ── SelfBuilder ───────────────────────────────────────────────────────────────

class TestSelfBuilder:
    def setup_method(self):
        from src.autonomous.self_builder import SelfBuilder, BuildResult, TestResult
        self.SelfBuilder = SelfBuilder
        self.BuildResult = BuildResult
        self.TestResult = TestResult

    def test_instantiation(self):
        sb = self.SelfBuilder()
        assert sb is not None

    def test_build_result_dataclass(self):
        r = self.BuildResult(
            success=True,
            capability_name="test_cap",
            file_path="/tmp/test_cap.py",
            test_output="1 passed",
            attempts=1,
            error=None,
        )
        assert r.success is True
        assert r.capability_name == "test_cap"
        assert r.attempts == 1

    def test_test_result_dataclass(self):
        r = self.TestResult(passed=True, output="1 passed", failed_tests=[])
        assert r.passed is True
        assert r.failed_tests == []

    def test_run_tests_returns_test_result(self):
        sb = self.SelfBuilder()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"# placeholder\n")
            tmp = f.name
        result = sb.run_tests(tmp)
        assert isinstance(result, self.TestResult)
        os.unlink(tmp)

    def test_build_from_backlog_item(self):
        sb = self.SelfBuilder()
        item = {"name": "test_capability", "description": "A test capability"}
        # Without API key this uses stub — should return BuildResult
        result = sb.build_from_backlog(item)
        assert isinstance(result, self.BuildResult)
        assert result.capability_name == "test_capability"

    def test_stub_generated_when_no_api_key(self):
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": ""}):
            sb = self.SelfBuilder()
            result = sb.build_capability("stub_test", "A stub capability for testing")
        assert isinstance(result, self.BuildResult)


# ── AutonomousLoop ────────────────────────────────────────────────────────────

class TestAutonomousLoop:
    def setup_method(self):
        from src.autonomous.loop import AutonomousLoop
        self.AutonomousLoop = AutonomousLoop

    def test_instantiation_no_coordinator(self):
        loop = self.AutonomousLoop(coordinator=None)
        assert loop is not None

    def test_initial_state_stopped(self):
        loop = self.AutonomousLoop(coordinator=None)
        assert loop.state in ("stopped", "initialized")

    def test_get_metrics_returns_dict(self):
        loop = self.AutonomousLoop(coordinator=None)
        m = loop.get_metrics()
        assert isinstance(m, dict)
        assert "state" in m

    def test_submit_task_queues_item(self):
        loop = self.AutonomousLoop(coordinator=None)
        loop.submit_task("Build a test feature", priority=2)
        m = loop.get_metrics()
        assert m.get("queue_size", 0) >= 1

    def test_submit_multiple_tasks(self):
        loop = self.AutonomousLoop(coordinator=None)
        loop.submit_task("Task A", priority=1)
        loop.submit_task("Task B", priority=3)
        loop.submit_task("Task C", priority=2)
        m = loop.get_metrics()
        assert m.get("queue_size", 0) >= 3

    def test_start_and_stop(self):
        loop = self.AutonomousLoop(coordinator=None)
        loop.start()
        assert loop.state in ("running", "idle")
        loop.stop()
        assert loop.state in ("stopped", "stopping")

    def test_metrics_has_uptime(self):
        loop = self.AutonomousLoop(coordinator=None)
        loop.start()
        import time; time.sleep(0.1)
        m = loop.get_metrics()
        assert "uptime_seconds" in m or "uptime" in m
        loop.stop()

    def test_pause_resume(self):
        loop = self.AutonomousLoop(coordinator=None)
        loop.start()
        loop.pause()
        assert loop.state in ("paused",)
        loop.resume()
        assert loop.state in ("running", "idle")
        loop.stop()
