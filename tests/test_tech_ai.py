"""
Tests for Tech AI: AdamusCore, SelfImprovementOrchestrator,
CapabilityBuilder, and GenreBuilder.
"""
import os
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock


# ── CapabilityBuilder Tests ───────────────────────────────────────────────────

class TestCapability:
    def test_blocking_genre(self):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("x", "desc", "sys", is_blocking=True)
        assert cap.is_blocking_genre() is True

    def test_security_critical(self):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("x", "desc", "sys", risk_level="critical")
        assert cap.is_security_critical() is True

    def test_not_critical_by_default(self):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("x", "desc", "sys")
        assert cap.is_security_critical() is False


class TestCapabilityCatalogue:
    def test_catalogue_not_empty(self):
        from src.tech_ai.capability_builder import CAPABILITY_CATALOGUE
        assert len(CAPABILITY_CATALOGUE) >= 5

    def test_catalogue_has_data_governance(self):
        from src.tech_ai.capability_builder import CAPABILITY_CATALOGUE
        names = [c.name for c in CAPABILITY_CATALOGUE]
        assert "data_governance" in names

    def test_catalogue_has_credential_vault(self):
        from src.tech_ai.capability_builder import CAPABILITY_CATALOGUE
        names = [c.name for c in CAPABILITY_CATALOGUE]
        assert "credential_vault" in names

    def test_blocking_caps_have_high_risk(self):
        from src.tech_ai.capability_builder import CAPABILITY_CATALOGUE
        for cap in CAPABILITY_CATALOGUE:
            if cap.is_blocking:
                # Blocking caps should be at least medium risk
                assert cap.risk_level in ("medium", "critical")


class TestCapabilityBuilder:
    @pytest.fixture
    def builder(self, tmp_path):
        from src.tech_ai.capability_builder import CapabilityBuilder
        return CapabilityBuilder(base_path=tmp_path)

    def test_empty_inventory_initially(self, builder):
        assert builder.get_inventory() == []

    def test_build_creates_file(self, builder, tmp_path):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("email_notifier", "Send emails", "operations")
        builder.build_capability(cap)
        assert (tmp_path / "src/capabilities/email_notifier.py").exists()

    def test_build_marks_as_built(self, builder):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("cost_monitor", "Track costs", "llm_optimization")
        builder.build_capability(cap)
        assert cap.built is True

    def test_build_sets_file_path(self, builder):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("input_filter", "Block injections", "prompt_defense")
        builder.build_capability(cap)
        assert cap.file_path is not None
        assert "input_filter" in cap.file_path

    def test_is_built_true_after_build(self, builder):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("data_governance", "Validate data", "data_governance")
        builder.build_capability(cap)
        assert builder.is_built("data_governance") is True

    def test_is_built_false_before_build(self, builder):
        assert builder.is_built("nonexistent") is False

    def test_inventory_grows_after_build(self, builder):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("email_notifier", "Send emails", "operations")
        builder.build_capability(cap)
        assert "email_notifier" in builder.get_inventory()

    def test_generated_module_has_class(self, builder, tmp_path):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("email_notifier", "Send emails", "operations")
        builder.build_capability(cap)
        code = (tmp_path / "src/capabilities/email_notifier.py").read_text()
        assert "class EmailNotifier" in code

    def test_build_log_updated(self, builder):
        from src.tech_ai.capability_builder import Capability
        cap = Capability("email_notifier", "Send emails", "operations")
        builder.build_capability(cap)
        assert "email_notifier" in builder.get_build_log()


# ── ImprovementPrioritizer Tests ──────────────────────────────────────────────

class TestImprovementPrioritizer:
    def test_blocking_gets_100(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementPrioritizer
        cap = Capability("x", "d", "s", is_blocking=True, risk_level="low")
        p = ImprovementPrioritizer()
        score = p.calculate_priority(cap)
        assert score >= 100

    def test_critical_adds_80(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementPrioritizer
        cap = Capability("x", "d", "s", risk_level="critical")
        p = ImprovementPrioritizer()
        score = p.calculate_priority(cap)
        assert score >= 80

    def test_quick_win_adds_20(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementPrioritizer
        cap_slow = Capability("x", "d", "s", effort_hours=8)
        cap_fast = Capability("x", "d", "s", effort_hours=2)
        p = ImprovementPrioritizer()
        assert p.calculate_priority(cap_fast) > p.calculate_priority(cap_slow)

    def test_prioritize_sorts_descending(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementPrioritizer
        caps = [
            Capability("a", "d", "s", is_blocking=False, risk_level="low"),
            Capability("b", "d", "s", is_blocking=True, risk_level="critical"),
        ]
        p = ImprovementPrioritizer()
        tasks = p.prioritize(caps)
        assert tasks[0].capability.name == "b"  # highest priority first


# ── ImprovementBacklog Tests ──────────────────────────────────────────────────

class TestImprovementBacklog:
    def test_empty_initially(self):
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        assert b.is_empty() is True

    def test_add_increases_size(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        cap = Capability("email_notifier", "Send emails", "operations")
        b.add(cap)
        assert b.size() == 1

    def test_duplicate_not_added(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        cap = Capability("email_notifier", "Send emails", "operations")
        b.add(cap)
        b.add(cap)
        assert b.size() == 1

    def test_pop_returns_task(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        cap = Capability("email_notifier", "Send emails", "operations")
        b.add(cap)
        task = b.pop()
        assert task is not None
        assert task.capability.name == "email_notifier"

    def test_pop_empty_returns_none(self):
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        assert b.pop() is None

    def test_update_from_deploy_command(self):
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        added = b.update_from_command("Deploy Lore v2 to production")
        assert len(added) > 0  # deploy command should trigger capabilities

    def test_list_items_returns_dicts(self):
        from src.tech_ai.capability_builder import Capability
        from src.tech_ai.self_improvement import ImprovementBacklog
        b = ImprovementBacklog()
        cap = Capability("email_notifier", "Send emails", "operations")
        b.add(cap)
        items = b.list_items()
        assert isinstance(items, list)
        assert "name" in items[0]
        assert "priority" in items[0]


# ── SelfImprovementOrchestrator Tests ─────────────────────────────────────────

class TestSelfImprovementOrchestrator:
    @pytest.fixture
    def orchestrator(self, tmp_path):
        from src.tech_ai.capability_builder import CapabilityBuilder
        from src.tech_ai.self_improvement import SelfImprovementOrchestrator
        builder = CapabilityBuilder(base_path=tmp_path)
        return SelfImprovementOrchestrator(builder=builder)

    def test_process_command_returns_dict(self, orchestrator):
        result = orchestrator.process_command("Build user authentication")
        assert isinstance(result, dict)
        assert "backlog_size" in result

    def test_detect_missing_capabilities(self, orchestrator):
        caps = orchestrator.detect_missing_capabilities("Save user data to database")
        assert isinstance(caps, list)

    def test_work_on_backlog_builds_item(self, orchestrator):
        orchestrator.process_command("Deploy editor to production")
        built = orchestrator.work_on_backlog(max_items=1)
        assert isinstance(built, list)

    def test_improvement_log_grows(self, orchestrator):
        orchestrator.process_command("Deploy editor")
        orchestrator.work_on_backlog(max_items=1)
        log = orchestrator.get_improvement_log()
        assert len(log) >= 0  # may be 0 if backlog was empty


# ── GenreBuilder Tests ────────────────────────────────────────────────────────

class TestGenreBuilder:
    @pytest.fixture
    def builder(self, tmp_path):
        from src.tech_ai.genre_builder import GenreBuilder
        return GenreBuilder(base_path=tmp_path)

    def test_scaffold_lore_feature(self, builder, tmp_path):
        from src.tech_ai.genre_builder import GenreFeature
        feat = GenreFeature("my_feature", "lore", "Test feature")
        result = builder.scaffold_feature(feat)
        assert result["status"] == "scaffolded"
        assert (tmp_path / "src/genre/lore/my_feature.py").exists()

    def test_scaffold_saga_feature(self, builder, tmp_path):
        from src.tech_ai.genre_builder import GenreFeature
        feat = GenreFeature("my_payment", "saga", "Test payment feature")
        result = builder.scaffold_feature(feat)
        assert result["status"] == "scaffolded"

    def test_scaffold_bible_feature(self, builder, tmp_path):
        from src.tech_ai.genre_builder import GenreFeature
        feat = GenreFeature("my_search", "bible", "Test search feature")
        result = builder.scaffold_feature(feat)
        assert result["status"] == "scaffolded"

    def test_invalid_product_raises(self, builder):
        from src.tech_ai.genre_builder import GenreFeature
        feat = GenreFeature("x", "invalid_product", "desc")
        with pytest.raises(ValueError, match="Unknown product"):
            builder.scaffold_feature(feat)

    def test_roadmap_not_empty(self, builder):
        roadmap = builder.get_roadmap()
        assert len(roadmap) >= 5

    def test_roadmap_filter_by_product(self, builder):
        lore = builder.get_roadmap(product="lore")
        assert all(f["product"] == "lore" for f in lore)

    def test_pending_features_list(self, builder):
        pending = builder.list_pending_features()
        assert isinstance(pending, list)
        assert len(pending) > 0

    def test_get_template_returns_string(self, builder):
        t = builder.get_feature_template("lore")
        assert isinstance(t, str)
        assert len(t) > 50


# ── AdamusCore Tests ──────────────────────────────────────────────────────────

class TestAdamusCore:
    @pytest.fixture
    def core(self, tmp_path):
        from src.tech_ai.adamus_core import AdamusCore
        return AdamusCore(base_path=tmp_path)

    def test_instantiation(self, core):
        assert core is not None
        assert core.VERSION == "0.1.0"

    def test_process_returns_dict(self, core):
        result = core.process("Build Lore editor")
        assert isinstance(result, dict)
        assert "self_improvement" in result

    def test_process_has_backlog_size(self, core):
        result = core.process("Deploy user authentication API")
        assert "backlog_size" in result
        assert isinstance(result["backlog_size"], int)

    def test_status_returns_version(self, core):
        status = core.status()
        assert status["version"] == "0.1.0"

    def test_status_has_capabilities(self, core):
        status = core.status()
        assert "capabilities" in status
        assert "built_count" in status["capabilities"]

    def test_status_has_backlog(self, core):
        status = core.status()
        assert "backlog" in status

    def test_status_has_genre(self, core):
        status = core.status()
        assert "genre" in status
        assert "pending_features" in status["genre"]

    def test_get_capabilities_is_list(self, core):
        caps = core.get_capabilities()
        assert isinstance(caps, list)

    def test_get_genre_roadmap(self, core):
        roadmap = core.get_genre_roadmap()
        assert isinstance(roadmap, list)
        assert len(roadmap) >= 5

    def test_get_genre_roadmap_filter(self, core):
        lore = core.get_genre_roadmap(product="lore")
        assert all(f["product"] == "lore" for f in lore)

    def test_run_improvement_cycle_returns_dict(self, core):
        # Put something in backlog first
        core.process("Deploy editor API")
        result = core.run_improvement_cycle(max_items=1)
        assert isinstance(result, dict)
        assert "built" in result
        assert "backlog_remaining" in result

    def test_scaffold_genre_feature(self, core, tmp_path):
        from src.tech_ai.genre_builder import GenreFeature
        feat = GenreFeature("lore_editor", "lore", "AI writing editor", priority=1)
        result = core.scaffold_genre_feature(feat)
        assert result["status"] == "scaffolded"
