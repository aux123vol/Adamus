"""
Tests for Business AI components.

The Business AI handles survival-critical operations:
- Finance tracking (MRR, burn, runway)
- Competitor intelligence
- Market signals and acquisition radar
"""

import pytest
from datetime import datetime


class TestFinanceTracker:
    """Tests for finance tracking."""

    def test_finance_metrics_dataclass(self):
        """Test FinanceMetrics dataclass."""
        from src.business_ai.finance_tracker import FinanceMetrics

        metrics = FinanceMetrics(
            timestamp=datetime.now().isoformat(),
            cash_balance=50000,
            mrr=5000,
            burn_rate=3000,
            runway_months=25,
            growth_rate=15.0,
            paying_users=50,
            arpu=100.0
        )

        assert metrics.cash_balance == 50000
        assert metrics.mrr == 5000
        assert metrics.is_healthy  # runway > 6
        assert metrics.severity == "healthy"

        d = metrics.to_dict()
        assert d["mrr"] == 5000

    def test_finance_metrics_warning_status(self):
        """Test FinanceMetrics with warning status."""
        from src.business_ai.finance_tracker import FinanceMetrics

        metrics = FinanceMetrics(
            timestamp=datetime.now().isoformat(),
            cash_balance=10000,
            mrr=1000,
            burn_rate=2500,
            runway_months=5,  # 5 months = warning
            growth_rate=5.0,
            paying_users=10,
            arpu=100.0
        )

        assert metrics.severity == "warning"
        assert not metrics.is_healthy

    def test_finance_metrics_critical_status(self):
        """Test FinanceMetrics with critical status."""
        from src.business_ai.finance_tracker import FinanceMetrics

        metrics = FinanceMetrics(
            timestamp=datetime.now().isoformat(),
            cash_balance=3000,
            mrr=0,
            burn_rate=1500,
            runway_months=2,  # 2 months = critical
            growth_rate=0,
            paying_users=0,
            arpu=0
        )

        assert metrics.severity == "critical"

    def test_finance_tracker_initialization(self):
        """Test FinanceTracker initialization."""
        from src.business_ai.finance_tracker import FinanceTracker

        tracker = FinanceTracker()

        # Should have default thresholds
        assert tracker.runway_critical == 3
        assert tracker.runway_warning == 6

    def test_get_current_metrics(self):
        """Test getting current financial metrics."""
        from src.business_ai.finance_tracker import FinanceTracker

        tracker = FinanceTracker()
        metrics = tracker.get_current_metrics()

        assert metrics.timestamp is not None
        assert metrics.cash_balance >= 0
        assert metrics.burn_rate >= 0
        assert metrics.runway_months >= 0

    def test_get_burn_analysis(self):
        """Test burn rate analysis."""
        from src.business_ai.finance_tracker import FinanceTracker

        tracker = FinanceTracker()
        analysis = tracker.get_burn_analysis()

        assert "total" in analysis
        assert "infrastructure" in analysis
        assert "ai_apis" in analysis

    def test_get_revenue_forecast(self):
        """Test revenue forecasting."""
        from src.business_ai.finance_tracker import FinanceTracker

        tracker = FinanceTracker()
        forecast = tracker.get_revenue_forecast(6)

        assert len(forecast) == 6
        for month in forecast:
            assert "month" in month
            assert "projected_mrr" in month

    def test_check_alerts(self):
        """Test alert checking."""
        from src.business_ai.finance_tracker import FinanceTracker

        tracker = FinanceTracker()
        alerts = tracker.check_alerts()

        # Alerts should be a list
        assert isinstance(alerts, list)

        # Each alert should have required fields
        for alert in alerts:
            assert "severity" in alert
            assert "category" in alert
            assert "title" in alert
            assert "message" in alert

    def test_get_survival_report(self):
        """Test comprehensive survival report."""
        from src.business_ai.finance_tracker import FinanceTracker

        tracker = FinanceTracker()
        report = tracker.get_survival_report()

        assert "timestamp" in report
        assert "current_metrics" in report
        assert "burn_breakdown" in report
        assert "forecast_6mo" in report
        assert "alerts" in report
        assert "status" in report
        assert "summary" in report


class TestCompetitorIntel:
    """Tests for competitor intelligence."""

    def test_competitor_profile_dataclass(self):
        """Test CompetitorProfile dataclass."""
        from src.business_ai.competitor_intel import CompetitorProfile, ThreatLevel

        profile = CompetitorProfile(
            name="TestComp",
            website="https://testcomp.com",
            threat_level=ThreatLevel.HIGH
        )

        assert profile.name == "TestComp"
        assert profile.threat_level == ThreatLevel.HIGH

        d = profile.to_dict()
        assert d["threat_level"] == "high"

    def test_clone_opportunity_dataclass(self):
        """Test CloneOpportunity dataclass."""
        from src.business_ai.competitor_intel import CloneOpportunity

        opportunity = CloneOpportunity(
            competitor="Notion",
            feature_name="AI Writing Assistant",
            detected_date=datetime.now().isoformat(),
            priority="high",
            description="Clone Notion's new AI writing feature",
            estimated_effort="3 days",
            strategic_value="Competitive parity"
        )

        assert opportunity.competitor == "Notion"
        assert opportunity.priority == "high"

        d = opportunity.to_dict()
        assert d["feature_name"] == "AI Writing Assistant"

    def test_competitor_intel_initialization(self):
        """Test CompetitorIntel initialization."""
        from src.business_ai.competitor_intel import CompetitorIntel

        intel = CompetitorIntel()

        # Should have default competitors
        assert len(intel.competitors) == 4
        assert intel.competitors[0].name == "Notion"

    def test_competitor_intel_custom_competitors(self):
        """Test CompetitorIntel with custom competitors."""
        from src.business_ai.competitor_intel import CompetitorIntel, CompetitorProfile

        custom = [
            CompetitorProfile(name="Custom1", website="https://custom1.com"),
            CompetitorProfile(name="Custom2", website="https://custom2.com")
        ]

        intel = CompetitorIntel(competitors=custom)
        assert len(intel.competitors) == 2
        assert intel.competitors[0].name == "Custom1"

    @pytest.mark.asyncio
    async def test_monitor_all(self):
        """Test full competitor monitoring cycle."""
        from src.business_ai.competitor_intel import CompetitorIntel

        intel = CompetitorIntel()
        results = await intel.monitor_all()

        assert "timestamp" in results
        assert "competitors" in results
        assert "clone_opportunities" in results
        assert "threat_summary" in results

    def test_get_competitor_profiles(self):
        """Test getting competitor profiles."""
        from src.business_ai.competitor_intel import CompetitorIntel

        intel = CompetitorIntel()
        profiles = intel.get_competitor_profiles()

        assert len(profiles) == 4
        for profile in profiles:
            assert "name" in profile
            assert "website" in profile
            assert "threat_level" in profile

    def test_update_threat_level(self):
        """Test updating competitor threat level."""
        from src.business_ai.competitor_intel import CompetitorIntel, ThreatLevel

        intel = CompetitorIntel()

        # Update Notion to critical
        result = intel.update_threat_level("Notion", ThreatLevel.CRITICAL)
        assert result is True

        # Verify update
        for comp in intel.competitors:
            if comp.name == "Notion":
                assert comp.threat_level == ThreatLevel.CRITICAL

        # Try non-existent competitor
        result = intel.update_threat_level("NonExistent", ThreatLevel.LOW)
        assert result is False

    def test_add_competitor(self):
        """Test adding new competitor."""
        from src.business_ai.competitor_intel import CompetitorIntel, CompetitorProfile

        intel = CompetitorIntel()
        initial_count = len(intel.competitors)

        new_comp = CompetitorProfile(
            name="NewCompetitor",
            website="https://newcomp.com"
        )
        intel.add_competitor(new_comp)

        assert len(intel.competitors) == initial_count + 1
        assert intel.competitors[-1].name == "NewCompetitor"

    def test_get_intel_report(self):
        """Test getting comprehensive intel report."""
        from src.business_ai.competitor_intel import CompetitorIntel

        intel = CompetitorIntel()
        report = intel.get_intel_report()

        assert "timestamp" in report
        assert "competitors" in report
        assert "clone_queue" in report
        assert "threat_summary" in report


class TestBusinessAI:
    """Tests for main Business AI agent."""

    def test_business_ai_initialization(self):
        """Test BusinessAI initialization."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()

        assert agent.finance is not None
        assert agent.intel is not None
        assert agent._initialized is False

    @pytest.mark.asyncio
    async def test_business_ai_initialize(self):
        """Test BusinessAI full initialization."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        result = await agent.initialize()

        assert result is True
        assert agent._initialized is True

    @pytest.mark.asyncio
    async def test_daily_finance_pulse(self):
        """Test daily finance pulse."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        report = await agent.daily_finance_pulse()

        assert "timestamp" in report
        assert "current_metrics" in report
        assert "status" in report
        assert agent._last_daily_pulse is not None

    @pytest.mark.asyncio
    async def test_competitor_intelligence(self):
        """Test competitor intelligence scan."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        intel = await agent.competitor_intelligence()

        assert "timestamp" in intel
        assert "competitors" in intel
        assert "clone_opportunities" in intel
        assert agent._last_competitor_scan is not None

    @pytest.mark.asyncio
    async def test_acquisition_radar(self):
        """Test acquisition radar."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        results = await agent.acquisition_radar()

        assert "timestamp" in results
        assert "targets" in results
        assert "high_value_count" in results

    @pytest.mark.asyncio
    async def test_execute_task_finance(self):
        """Test executing finance pulse task."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        task = {"id": "task_001", "type": "finance_pulse"}
        result = await agent.execute_task(task)

        assert result["status"] == "completed"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_execute_task_competitor_scan(self):
        """Test executing competitor scan task."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        task = {"id": "task_002", "type": "competitor_scan"}
        result = await agent.execute_task(task)

        assert result["status"] == "completed"
        assert "data" in result

    @pytest.mark.asyncio
    async def test_execute_task_unknown(self):
        """Test executing unknown task type."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        task = {"id": "task_003", "type": "unknown_task_type"}
        result = await agent.execute_task(task)

        assert result["status"] == "unknown_task"
        assert "error" in result

    @pytest.mark.asyncio
    async def test_execute_task_distribute_content(self):
        """Test content distribution task (from CAMBI AI)."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        task = {
            "id": "task_004",
            "type": "distribute_content",
            "content": [
                {"id": "blog_001", "title": "AI Writing Guide"},
                {"id": "blog_002", "title": "Productivity Tips"}
            ]
        }
        result = await agent.execute_task(task)

        assert result["status"] == "completed"
        assert result["data"]["distributed_count"] == 2

    @pytest.mark.asyncio
    async def test_execute_task_track_experiment(self):
        """Test A/B experiment tracking task."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        task = {
            "id": "task_005",
            "type": "track_experiment",
            "experiment": {"id": "exp_001", "name": "Onboarding Test"}
        }
        result = await agent.execute_task(task)

        assert result["status"] == "completed"
        assert "winner" in result["data"]

    def test_get_status(self):
        """Test getting Business AI status."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        status = agent.get_status()

        assert "initialized" in status
        assert "pending_tasks" in status
        assert "completed_tasks" in status
        assert "financial_status" in status
        assert "mrr" in status
        assert "runway_months" in status

    @pytest.mark.asyncio
    async def test_run_daily_cycle(self):
        """Test complete daily cycle."""
        from src.business_ai.business_agent import BusinessAI

        agent = BusinessAI()
        await agent.initialize()

        results = await agent.run_daily_cycle()

        assert "finance" in results
        assert "intel" in results
        assert "summary" in results
        assert "financial_status" in results["summary"]
        assert "clone_opportunities" in results["summary"]


class TestIntegration:
    """Integration tests for Business AI with other components."""

    @pytest.mark.asyncio
    async def test_business_ai_reports_to_war_room(self):
        """Test Business AI reporting to War Room."""
        from src.business_ai.business_agent import BusinessAI
        from src.war_room.metrics import MetricsCollector

        # Create War Room collector
        war_room = MetricsCollector()

        # Create Business AI with War Room
        agent = BusinessAI(war_room=war_room)
        await agent.initialize()

        # Run finance pulse (should report to War Room)
        report = await agent.daily_finance_pulse()

        # Verify report was generated
        assert report["status"] in ["healthy", "warning", "critical"]

    @pytest.mark.asyncio
    async def test_business_ai_full_cycle_with_war_room(self):
        """Test full Business AI cycle with War Room integration."""
        from src.business_ai.business_agent import BusinessAI
        from src.war_room.metrics import MetricsCollector
        from src.war_room.alerts import AlertSystem

        # Create War Room components
        war_room = MetricsCollector()
        alerts = AlertSystem()

        # Create Business AI
        agent = BusinessAI(war_room=war_room)
        await agent.initialize()

        # Run daily cycle
        results = await agent.run_daily_cycle()

        # Check for alerts based on finance status
        if results["summary"]["financial_status"] == "critical":
            # Should have generated alerts
            finance_alerts = agent.finance.check_alerts()
            assert len(finance_alerts) > 0
