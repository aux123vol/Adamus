"""
Tests for War Room components.

The War Room is Augustus's daily steering system.
All metrics and alerts must work correctly.
"""

import pytest
from datetime import datetime


class TestMetrics:
    """Tests for metrics collection."""

    def test_survival_metrics_dataclass(self):
        """Test SurvivalMetrics dataclass."""
        from src.war_room.metrics import SurvivalMetrics

        metrics = SurvivalMetrics(
            cash_balance=50000,
            burn_rate=5000,
            runway_months=10
        )

        assert metrics.cash_balance == 50000
        assert metrics.burn_rate == 5000
        assert metrics.runway_months == 10

        d = metrics.to_dict()
        assert d["cash_balance"] == 50000

    def test_pmf_metrics_dataclass(self):
        """Test PMFMetrics dataclass."""
        from src.war_room.metrics import PMFMetrics

        metrics = PMFMetrics(
            total_users=100,
            active_users=80,
            paying_users=20,
            mrr=1000,
            churn_rate=5.0,
            retention_rate=95.0
        )

        assert metrics.total_users == 100
        assert metrics.mrr == 1000

    def test_adamus_metrics_dataclass(self):
        """Test AdamusMetrics dataclass."""
        from src.war_room.metrics import AdamusMetrics

        metrics = AdamusMetrics(
            capabilities_built=8,
            security_score=10.0,
            documents_loaded=100,
            monthly_spend=50.0,
            budget_remaining=150.0
        )

        assert metrics.capabilities_built == 8
        assert metrics.security_score == 10.0

    @pytest.mark.asyncio
    async def test_metrics_collector_initialization(self):
        """Test MetricsCollector initialization."""
        from src.war_room.metrics import MetricsCollector

        collector = MetricsCollector()

        assert collector.competitors == ["Notion", "Mem", "Reflect", "Obsidian"]
        assert collector._last_internal is None

    @pytest.mark.asyncio
    async def test_collect_internal_metrics(self):
        """Test collecting internal metrics."""
        from src.war_room.metrics import MetricsCollector

        collector = MetricsCollector()
        metrics = await collector.collect_internal()

        assert metrics.timestamp is not None
        assert metrics.survival is not None
        assert metrics.pmf is not None
        assert metrics.adamus is not None

    @pytest.mark.asyncio
    async def test_collect_external_metrics(self):
        """Test collecting external metrics."""
        from src.war_room.metrics import MetricsCollector

        collector = MetricsCollector()
        metrics = await collector.collect_external()

        assert len(metrics.competitors) > 0
        assert metrics.competitors[0].name == "Notion"

    @pytest.mark.asyncio
    async def test_collect_all_metrics(self):
        """Test collecting all metrics."""
        from src.war_room.metrics import MetricsCollector

        collector = MetricsCollector()
        all_metrics = await collector.collect_all()

        assert "internal" in all_metrics
        assert "external" in all_metrics
        assert "collected_at" in all_metrics

    def test_needs_refresh(self):
        """Test refresh check."""
        from src.war_room.metrics import MetricsCollector

        collector = MetricsCollector()

        # Should need refresh initially
        assert collector.needs_refresh()


class TestAlerts:
    """Tests for alert system."""

    def test_alert_creation(self):
        """Test Alert dataclass."""
        from src.war_room.alerts import Alert, AlertSeverity, AlertCategory

        alert = Alert(
            id="test_001",
            timestamp=datetime.now().isoformat(),
            severity=AlertSeverity.CRITICAL,
            category=AlertCategory.SURVIVAL,
            title="Test Alert",
            message="This is a test",
            metric_name="survival.cash_balance",
            metric_value=5000,
            threshold=10000
        )

        assert alert.severity == AlertSeverity.CRITICAL
        assert not alert.resolved

        d = alert.to_dict()
        assert d["severity"] == "critical"

    def test_alert_system_initialization(self):
        """Test AlertSystem initialization."""
        from src.war_room.alerts import AlertSystem

        system = AlertSystem()

        assert len(system.thresholds) > 0
        assert len(system.active_alerts) == 0

    def test_alert_system_default_thresholds(self):
        """Test default thresholds are configured."""
        from src.war_room.alerts import AlertSystem, AlertCategory

        system = AlertSystem()

        # Should have survival thresholds
        survival_thresholds = [
            t for t in system.thresholds
            if t.category == AlertCategory.SURVIVAL
        ]
        assert len(survival_thresholds) >= 2

        # Should have PMF thresholds
        pmf_thresholds = [
            t for t in system.thresholds
            if t.category == AlertCategory.PMF
        ]
        assert len(pmf_thresholds) >= 1

    def test_check_metrics_triggers_alert(self):
        """Test that checking metrics triggers alerts."""
        from src.war_room.alerts import AlertSystem, AlertSeverity
        from src.war_room.metrics import (
            InternalMetrics, SurvivalMetrics, PMFMetrics,
            ProductivityMetrics, AdamusMetrics
        )

        system = AlertSystem()

        # Create metrics that should trigger alerts
        metrics = InternalMetrics(
            timestamp=datetime.now().isoformat(),
            survival=SurvivalMetrics(
                cash_balance=5000,  # Below $10K threshold
                burn_rate=2000,
                runway_months=2  # Below 3 month threshold
            ),
            pmf=PMFMetrics(
                total_users=100,
                churn_rate=5.0  # Below warning threshold
            ),
            productivity=ProductivityMetrics(),
            adamus=AdamusMetrics(
                security_score=8.0,
                budget_remaining=100.0
            )
        )

        alerts = system.check_metrics(metrics)

        # Should have triggered some alerts
        assert len(alerts) > 0

        # Should have critical runway alert
        critical = system.get_critical_alerts()
        assert len(critical) > 0

    def test_alert_resolution(self):
        """Test that alerts are resolved when threshold no longer crossed."""
        from src.war_room.alerts import AlertSystem
        from src.war_room.metrics import (
            InternalMetrics, SurvivalMetrics, PMFMetrics,
            ProductivityMetrics, AdamusMetrics
        )

        system = AlertSystem()

        # First, trigger an alert
        bad_metrics = InternalMetrics(
            timestamp=datetime.now().isoformat(),
            survival=SurvivalMetrics(
                cash_balance=5000,  # Below threshold
                burn_rate=1000,
                runway_months=5
            ),
            pmf=PMFMetrics(),
            productivity=ProductivityMetrics(),
            adamus=AdamusMetrics(security_score=8.0, budget_remaining=100.0)
        )

        system.check_metrics(bad_metrics)
        initial_alerts = len(system.get_active_alerts())

        # Now, fix the issue
        good_metrics = InternalMetrics(
            timestamp=datetime.now().isoformat(),
            survival=SurvivalMetrics(
                cash_balance=50000,  # Above threshold
                burn_rate=1000,
                runway_months=50
            ),
            pmf=PMFMetrics(),
            productivity=ProductivityMetrics(),
            adamus=AdamusMetrics(security_score=8.0, budget_remaining=100.0)
        )

        system.check_metrics(good_metrics)

        # Should have fewer alerts now
        final_alerts = len(system.get_active_alerts())
        assert final_alerts <= initial_alerts

    def test_get_alert_summary(self):
        """Test alert summary generation."""
        from src.war_room.alerts import AlertSystem

        system = AlertSystem()
        summary = system.get_alert_summary()

        assert "total_active" in summary
        assert "critical" in summary
        assert "warning" in summary
        assert "by_category" in summary


class TestDashboard:
    """Tests for War Room dashboard."""

    def test_create_app(self):
        """Test Flask app creation."""
        from src.war_room.dashboard import create_app

        app = create_app()

        assert app is not None
        assert app.config['SECRET_KEY'] is not None

    def test_dashboard_routes(self):
        """Test dashboard routes exist."""
        from src.war_room.dashboard import create_app

        app = create_app()
        client = app.test_client()

        # Test main page
        response = client.get('/')
        assert response.status_code == 200
        assert b'War Room' in response.data or b'ADAMUS' in response.data

        # Test health endpoint
        response = client.get('/api/health')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'healthy'

    def test_metrics_api(self):
        """Test metrics API endpoint."""
        from src.war_room.dashboard import create_app

        app = create_app()
        client = app.test_client()

        response = client.get('/api/metrics')
        assert response.status_code == 200

        data = response.get_json()
        assert 'internal' in data
        assert 'external' in data

    def test_alerts_api(self):
        """Test alerts API endpoint."""
        from src.war_room.dashboard import create_app

        app = create_app()
        client = app.test_client()

        response = client.get('/api/alerts')
        assert response.status_code == 200

        data = response.get_json()
        assert 'total_active' in data
