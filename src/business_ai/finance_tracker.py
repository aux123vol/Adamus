"""
Finance Tracker

Tracks survival metrics:
- Monthly Recurring Revenue (MRR)
- Burn rate
- Runway (months until out of money)
- Cash balance

For MVP: Uses environment variables and mock data.
Production: Connects to Genre database and accounting system.
"""

import os
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class FinanceMetrics:
    """Current financial snapshot."""
    timestamp: str
    cash_balance: float
    mrr: float
    burn_rate: float
    runway_months: int
    growth_rate: float  # MRR growth % month-over-month
    paying_users: int
    arpu: float  # Average Revenue Per User

    def to_dict(self) -> Dict:
        return asdict(self)

    @property
    def is_healthy(self) -> bool:
        """Check if financial health is acceptable."""
        return self.runway_months >= 6 and self.burn_rate <= self.mrr

    @property
    def severity(self) -> str:
        """Return severity level for alerts."""
        if self.runway_months < 3:
            return "critical"
        elif self.runway_months < 6:
            return "warning"
        return "healthy"


@dataclass
class RevenueRecord:
    """Historical revenue data point."""
    date: str
    mrr: float
    new_mrr: float  # New subscriptions
    churned_mrr: float  # Lost subscriptions
    expansion_mrr: float  # Upgrades


class FinanceTracker:
    """
    Track all financial metrics for Business AI.

    Sources (MVP):
    - Environment variables for manual override
    - Historical mock data

    Sources (Production):
    - Stripe API for MRR/subscriptions
    - Bank API for cash balance
    - Genre database for user metrics
    """

    def __init__(
        self,
        genre_db_path: Optional[str] = None,
        stripe_client=None
    ):
        """
        Initialize finance tracker.

        Args:
            genre_db_path: Path to Genre database (optional)
            stripe_client: Stripe client for payment data (optional)
        """
        self.genre_db_path = genre_db_path
        self.stripe_client = stripe_client

        # Historical data (mock for MVP)
        self._revenue_history: List[RevenueRecord] = []
        self._load_historical_data()

        # Thresholds for alerts
        self.runway_critical = 3  # months
        self.runway_warning = 6  # months
        self.burn_threshold = 1.5  # burn rate shouldn't exceed 1.5x MRR

    def _load_historical_data(self) -> None:
        """Load historical revenue data (mock for MVP)."""
        # Generate 6 months of mock historical data
        today = datetime.now()

        base_mrr = 0  # Starting from $0
        for i in range(6, 0, -1):
            date = (today - timedelta(days=30 * i)).strftime("%Y-%m-%d")
            # Simulate growth from $0 to current MRR
            growth_factor = (6 - i) / 6
            mrr = base_mrr + (float(os.getenv("GENRE_MRR", "0")) * growth_factor)

            self._revenue_history.append(RevenueRecord(
                date=date,
                mrr=mrr,
                new_mrr=mrr * 0.2,
                churned_mrr=mrr * 0.05,
                expansion_mrr=mrr * 0.1
            ))

    def get_current_metrics(self) -> FinanceMetrics:
        """
        Get current financial metrics.

        Returns:
            FinanceMetrics with current snapshot
        """
        # Get values from environment (manual override) or defaults
        cash_balance = float(os.getenv("GENRE_CASH_BALANCE", "5000"))
        mrr = float(os.getenv("GENRE_MRR", "0"))
        burn_rate = float(os.getenv("GENRE_BURN_RATE", "500"))
        paying_users = int(os.getenv("GENRE_PAYING_USERS", "0"))

        # Calculate derived metrics
        runway = self._calculate_runway(cash_balance, mrr, burn_rate)
        growth_rate = self._calculate_growth_rate()
        arpu = mrr / paying_users if paying_users > 0 else 0

        metrics = FinanceMetrics(
            timestamp=datetime.now().isoformat(),
            cash_balance=cash_balance,
            mrr=mrr,
            burn_rate=burn_rate,
            runway_months=runway,
            growth_rate=growth_rate,
            paying_users=paying_users,
            arpu=arpu
        )

        logger.info(
            f"Finance pulse: MRR=${mrr}, Burn=${burn_rate}, "
            f"Runway={runway}mo, Status={metrics.severity}"
        )

        return metrics

    def _calculate_runway(
        self,
        cash: float,
        mrr: float,
        burn: float
    ) -> int:
        """
        Calculate runway in months.

        Formula: cash / (burn - mrr)
        If burn < mrr, runway is effectively infinite (99)
        """
        net_burn = burn - mrr

        if net_burn <= 0:
            # Cash positive or break-even
            return 99

        runway = int(cash / net_burn)
        return min(runway, 99)  # Cap at 99

    def _calculate_growth_rate(self) -> float:
        """
        Calculate MRR growth rate (month-over-month).

        Returns:
            Growth rate as percentage
        """
        if len(self._revenue_history) < 2:
            return 0.0

        current = self._revenue_history[-1].mrr
        previous = self._revenue_history[-2].mrr

        if previous == 0:
            return 100.0 if current > 0 else 0.0

        return ((current - previous) / previous) * 100

    def get_burn_analysis(self) -> Dict[str, Any]:
        """
        Analyze burn rate breakdown.

        Returns:
            Dict with burn rate categories
        """
        # In production, this would pull from accounting system
        total_burn = float(os.getenv("GENRE_BURN_RATE", "500"))

        # Mock breakdown (would come from real accounting)
        breakdown = {
            "total": total_burn,
            "infrastructure": total_burn * 0.15,  # Cloud, hosting
            "ai_apis": total_burn * 0.10,  # Claude, Ollama compute
            "tools": total_burn * 0.05,  # Dev tools, SaaS
            "other": total_burn * 0.70  # Living expenses (solo founder)
        }

        return breakdown

    def get_revenue_forecast(self, months: int = 6) -> List[Dict[str, Any]]:
        """
        Forecast revenue for next N months.

        Args:
            months: Number of months to forecast

        Returns:
            List of monthly forecasts
        """
        current_mrr = float(os.getenv("GENRE_MRR", "0"))
        growth_rate = self._calculate_growth_rate()

        # Conservative: assume half the current growth rate
        forecast_growth = growth_rate / 2 if growth_rate > 0 else 5.0

        forecasts = []
        projected_mrr = current_mrr

        for i in range(1, months + 1):
            projected_mrr = projected_mrr * (1 + forecast_growth / 100)
            month_date = (datetime.now() + timedelta(days=30 * i)).strftime("%Y-%m")

            forecasts.append({
                "month": month_date,
                "projected_mrr": round(projected_mrr, 2),
                "growth_assumption": f"{forecast_growth:.1f}%"
            })

        return forecasts

    def check_alerts(self) -> List[Dict[str, Any]]:
        """
        Check for financial alerts.

        Returns:
            List of alert conditions
        """
        metrics = self.get_current_metrics()
        alerts = []

        # Runway alerts
        if metrics.runway_months < self.runway_critical:
            alerts.append({
                "severity": "critical",
                "category": "survival",
                "title": "Runway Critical",
                "message": f"Only {metrics.runway_months} months runway remaining",
                "action": "Reduce burn or raise funds immediately"
            })
        elif metrics.runway_months < self.runway_warning:
            alerts.append({
                "severity": "warning",
                "category": "survival",
                "title": "Runway Low",
                "message": f"Runway at {metrics.runway_months} months",
                "action": "Plan fundraising or cost reduction"
            })

        # Burn rate alerts
        if metrics.burn_rate > metrics.mrr * self.burn_threshold:
            alerts.append({
                "severity": "warning",
                "category": "survival",
                "title": "High Burn Rate",
                "message": f"Burn ${metrics.burn_rate}/mo exceeds {self.burn_threshold}x MRR",
                "action": "Review and reduce expenses"
            })

        # Cash balance alerts
        if metrics.cash_balance < metrics.burn_rate * 3:
            alerts.append({
                "severity": "critical",
                "category": "survival",
                "title": "Cash Balance Critical",
                "message": f"Cash ${metrics.cash_balance} is less than 3 months burn",
                "action": "Urgent: Raise funds or cut costs"
            })

        return alerts

    def get_survival_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive survival report.

        Returns:
            Dict with all survival metrics and analysis
        """
        metrics = self.get_current_metrics()
        burn_analysis = self.get_burn_analysis()
        forecast = self.get_revenue_forecast(6)
        alerts = self.check_alerts()

        return {
            "timestamp": datetime.now().isoformat(),
            "current_metrics": metrics.to_dict(),
            "burn_breakdown": burn_analysis,
            "forecast_6mo": forecast,
            "alerts": alerts,
            "status": metrics.severity,
            "summary": self._generate_summary(metrics)
        }

    def _generate_summary(self, metrics: FinanceMetrics) -> str:
        """Generate human-readable summary."""
        if metrics.severity == "critical":
            return (
                f"CRITICAL: Only {metrics.runway_months} months runway. "
                f"MRR ${metrics.mrr}/mo vs burn ${metrics.burn_rate}/mo. "
                "Immediate action required."
            )
        elif metrics.severity == "warning":
            return (
                f"WARNING: {metrics.runway_months} months runway. "
                f"MRR ${metrics.mrr}/mo growing at {metrics.growth_rate:.1f}%/mo. "
                "Monitor closely."
            )
        else:
            return (
                f"HEALTHY: {metrics.runway_months}+ months runway. "
                f"MRR ${metrics.mrr}/mo with {metrics.paying_users} paying users. "
                "Continue building."
            )
