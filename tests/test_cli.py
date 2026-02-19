"""
Tests for Adamus CLI interface.
"""

import json
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest

# Ensure src is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


class TestCLIParsing:
    """Test that CLI subcommands parse correctly."""

    def _run(self, argv):
        from src.ui.adamus_interface import main
        with patch("sys.argv", ["adamus"] + argv):
            return main

    def test_status_command_exists(self):
        import argparse
        from src.ui import adamus_interface as cli
        # Just ensure the module imports cleanly
        assert hasattr(cli, "cmd_status")

    def test_memory_command_exists(self):
        from src.ui import adamus_interface as cli
        assert hasattr(cli, "cmd_memory")

    def test_task_command_exists(self):
        from src.ui import adamus_interface as cli
        assert hasattr(cli, "cmd_task")

    def test_review_command_exists(self):
        from src.ui import adamus_interface as cli
        assert hasattr(cli, "cmd_review")

    def test_approve_command_exists(self):
        from src.ui import adamus_interface as cli
        assert hasattr(cli, "cmd_approve")

    def test_rollback_command_exists(self):
        from src.ui import adamus_interface as cli
        assert hasattr(cli, "cmd_rollback")


class TestStatus:
    def test_status_runs_without_crash(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_status
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        with patch("src.ui.adamus_interface.AdamusPersistentMemory",
                   return_value=AdamusPersistentMemory(root=tmp_path / "adamus")):
            cmd_status(None)

        captured = capsys.readouterr()
        assert "ADAMUS STATUS" in captured.out

    def test_status_shows_git_info(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_status
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        with patch("src.ui.adamus_interface.AdamusPersistentMemory",
                   return_value=AdamusPersistentMemory(root=tmp_path / "adamus")):
            cmd_status(None)

        captured = capsys.readouterr()
        assert "Git" in captured.out

    def test_status_shows_memory_info(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_status
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        with patch("src.ui.adamus_interface.AdamusPersistentMemory",
                   return_value=AdamusPersistentMemory(root=tmp_path / "adamus")):
            cmd_status(None)

        captured = capsys.readouterr()
        assert "Memory" in captured.out


class TestMemoryCommand:
    def test_memory_shows_recent_when_no_query(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_memory
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        mem = AdamusPersistentMemory(root=tmp_path / "adamus")
        mem.save_memory("Test item", "Content")

        args = MagicMock()
        args.query = []

        with patch("src.ui.adamus_interface.AdamusPersistentMemory", return_value=mem):
            cmd_memory(args)

        captured = capsys.readouterr()
        assert "Recent" in captured.out

    def test_memory_searches_with_query(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_memory
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        mem = AdamusPersistentMemory(root=tmp_path / "adamus")
        mem.save_memory("SQLite setup", "WAL mode")

        args = MagicMock()
        args.query = ["SQLite"]

        with patch("src.ui.adamus_interface.AdamusPersistentMemory", return_value=mem):
            cmd_memory(args)

        captured = capsys.readouterr()
        assert "SQLite" in captured.out

    def test_memory_handles_no_results(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_memory
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        mem = AdamusPersistentMemory(root=tmp_path / "adamus")
        args = MagicMock()
        args.query = ["zzznomatch"]

        with patch("src.ui.adamus_interface.AdamusPersistentMemory", return_value=mem):
            cmd_memory(args)

        captured = capsys.readouterr()
        assert "No memories" in captured.out


class TestTaskCommand:
    def test_task_saves_to_memory(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_task
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        mem = AdamusPersistentMemory(root=tmp_path / "adamus")
        args = MagicMock()
        args.description = ["Build", "login", "page"]

        with patch("src.ui.adamus_interface.AdamusPersistentMemory", return_value=mem):
            cmd_task(args)

        captured = capsys.readouterr()
        assert "Task assigned" in captured.out
        assert "Build login page" in captured.out

    def test_task_exits_on_empty_description(self):
        from src.ui.adamus_interface import cmd_task
        args = MagicMock()
        args.description = []

        with pytest.raises(SystemExit):
            cmd_task(args)


class TestReviewCommand:
    def test_review_runs_without_crash(self, capsys, tmp_path):
        from src.ui.adamus_interface import cmd_review
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory

        mem = AdamusPersistentMemory(root=tmp_path / "adamus")
        mem.save_decision("Use SQLite", "It's simple")

        with patch("src.ui.adamus_interface.AdamusPersistentMemory", return_value=mem):
            cmd_review(None)

        captured = capsys.readouterr()
        assert "REVIEW" in captured.out


class TestApproveCommand:
    def test_approve_updates_decision_file(self, tmp_path):
        from src.ui.adamus_interface import cmd_approve

        decision_file = tmp_path / "decision.md"
        decision_file.write_text(
            "# Decision\n**Augustus Approved**: False\nReasoning here."
        )

        args = MagicMock()
        args.path = str(decision_file)

        cmd_approve(args)

        content = decision_file.read_text()
        assert "Augustus Approved**: True" in content

    def test_approve_exits_on_missing_file(self):
        from src.ui.adamus_interface import cmd_approve
        args = MagicMock()
        args.path = "/nonexistent/path.md"

        with pytest.raises(SystemExit):
            cmd_approve(args)


class TestHelpers:
    def test_git_helper_returns_string(self):
        from src.ui.adamus_interface import _git
        result = _git("git --version")
        assert isinstance(result, str)

    def test_adamus_root_returns_path(self):
        from src.ui.adamus_interface import _adamus_root
        assert isinstance(_adamus_root(), Path)

    def test_repo_root_exists(self):
        from src.ui.adamus_interface import _repo_root
        assert _repo_root().exists()
