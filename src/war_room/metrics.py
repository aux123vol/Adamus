"""
War Room Metrics Collection

Collects all metrics for the War Room:
- Internal Vitals (survival, PMF, productivity)
- Adamus Health (capabilities, security, cost)
- External Radar (competitors - placeholder)

Updated every 5 minutes in real-time mode.
"""

import os
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class SurvivalMetrics:
    """Survival metrics - is the company alive?"""
    cash_balance: float = 0.0        # $ in bank
    burn_rate: float = 0.0           # $/month
    runway_months: int = 0           # Months until out of money

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class PMFMetrics:
    """Product-Market Fit metrics."""
    total_users: int = 0
    active_users: int = 0            # Used in last 7 days
    paying_users: int = 0
    mrr: float = 0.0                 # Monthly recurring revenue
    churn_rate: float = 0.0          # % users who left
    retention_rate: float = 0.0      # % users who stayed

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ProductivityMetrics:
    """Team/AI productivity metrics."""
    features_shipped_7d: int = 0     # Last 7 days
    velocity: float = 0.0            # Features/week
    bugs_open: int = 0
    deploy_count_7d: int = 0         # Deployments in 7 days

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class AdamusMetrics:
    """Adamus AI CTO health metrics."""
    capabilities_built: int = 0      # Out of 100 total
    capabilities_total: int = 100
    self_improvement_rate: float = 0.0  # Systems/week
    security_score: float = 0.0      # Out of 10
    cost_efficiency: float = 0.0     # % saved vs baseline
    documents_loaded: int = 0
    monthly_spend: float = 0.0       # $ spent this month
    budget_remaining: float = 0.0    # $ remaining
    brains_available: Dict[str, bool] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class InternalMetrics:
    """Complete internal vitals."""
    timestamp: str
    survival: SurvivalMetrics
    pmf: PMFMetrics
    productivity: ProductivityMetrics
    adamus: AdamusMetrics

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "survival": self.survival.to_dict(),
            "pmf": self.pmf.to_dict(),
            "productivity": self.productivity.to_dict(),
            "adamus": self.adamus.to_dict()
        }


@dataclass
class CompetitorSnapshot:
    """Snapshot of competitor activity."""
    name: str
    last_checked: str
    recent_features: List[str] = field(default_factory=list)
    pricing_tier: str = ""
    funding_status: str = ""
    threat_level: str = "low"  # low, medium, high

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ExternalMetrics:
    """External radar metrics."""
    timestamp: str
    competitors: List[CompetitorSnapshot] = field(default_factory=list)
    market_signals: List[str] = field(default_factory=list)
    threats: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "competitors": [c.to_dict() for c in self.competitors],
            "market_signals": self.market_signals,
            "threats": self.threats
        }


class MetricsCollector:
    """
    Collects all War Room metrics.

    This is the data layer for the War Room dashboard.
    Integrates with Adamus components to get real metrics.
    """

    def __init__(
        self,
        coordinator=None,
        memory_db=None,
        genre_db_path: Optional[str] = None
    ):
        """
        Initialize metrics collector.

        Args:
            coordinator: AI Coordinator instance (for Adamus metrics)
            memory_db: Memory database (for historical data)
            genre_db_path: Path to Genre database (for user/revenue metrics)
        """
        self.coordinator = coordinator
        self.memory_db = memory_db
        self.genre_db_path = genre_db_path

        # Cache for metrics
        self._last_internal: Optional[InternalMetrics] = None
        self._last_external: Optional[ExternalMetrics] = None
        self._last_update: Optional[datetime] = None

        # Competitors to track
        self.competitors = ["Notion", "Mem", "Reflect", "Obsidian"]

    async def collect_all(self) -> Dict[str, Any]:
        """
        Collect all metrics for War Room.

        Returns complete snapshot of:
        - Internal vitals
        - External radar
        - Timestamps
        """
        internal = await self.collect_internal()
        external = await self.collect_external()

        self._last_update = datetime.now()

        return {
            "internal": internal.to_dict(),
            "external": external.to_dict(),
            "collected_at": self._last_update.isoformat()
        }

    async def collect_internal(self) -> InternalMetrics:
        """Collect internal vitals."""
        timestamp = datetime.now().isoformat()

        # Collect each category
        survival = await self._collect_survival()
        pmf = await self._collect_pmf()
        productivity = await self._collect_productivity()
        adamus = await self._collect_adamus()

        metrics = InternalMetrics(
            timestamp=timestamp,
            survival=survival,
            pmf=pmf,
            productivity=productivity,
            adamus=adamus
        )

        self._last_internal = metrics
        return metrics

    async def _collect_survival(self) -> SurvivalMetrics:
        """
        Collect survival metrics.

        In production, this would connect to:
        - Bank API for cash balance
        - Accounting system for burn rate
        """
        # For MVP, use placeholder/manual values
        # These would be set via War Room config or API

        cash = float(os.getenv("GENRE_CASH_BALANCE", "5000"))
        burn = float(os.getenv("GENRE_BURN_RATE", "500"))

        runway = int(cash / burn) if burn > 0 else 99

        return SurvivalMetrics(
            cash_balance=cash,
            burn_rate=burn,
            runway_months=runway
        )

    async def _collect_pmf(self) -> PMFMetrics:
        """
        Collect PMF metrics.

        In production, this would query Genre's database.
        """
        # Placeholder values - would come from Genre DB
        return PMFMetrics(
            total_users=int(os.getenv("GENRE_TOTAL_USERS", "0")),
            active_users=int(os.getenv("GENRE_ACTIVE_USERS", "0")),
            paying_users=int(os.getenv("GENRE_PAYING_USERS", "0")),
            mrr=float(os.getenv("GENRE_MRR", "0")),
            churn_rate=float(os.getenv("GENRE_CHURN_RATE", "0")),
            retention_rate=float(os.getenv("GENRE_RETENTION_RATE", "100"))
        )

    async def _collect_productivity(self) -> ProductivityMetrics:
        """
        Collect productivity metrics.

        In production, this would query:
        - GitHub for commits/deploys
        - Issue tracker for bugs
        - Task system for velocity
        """
        return ProductivityMetrics(
            features_shipped_7d=int(os.getenv("GENRE_FEATURES_7D", "0")),
            velocity=float(os.getenv("GENRE_VELOCITY", "0")),
            bugs_open=int(os.getenv("GENRE_BUGS_OPEN", "0")),
            deploy_count_7d=int(os.getenv("GENRE_DEPLOYS_7D", "0"))
        )

    async def _collect_adamus(self) -> AdamusMetrics:
        """
        Collect Adamus health metrics.

        This pulls real data from the coordinator.
        """
        metrics = AdamusMetrics()

        if self.coordinator and hasattr(self.coordinator, '_initialized') and self.coordinator._initialized:
            try:
                status = await self.coordinator.get_status()

                # Documents loaded
                docs = status.get("documents", {})
                metrics.documents_loaded = docs.get("total_documents", 0)

                # Security
                security = status.get("security", {})
                layer_status = security.get("layer_status", {})
                active_layers = sum(1 for v in layer_status.values() if v)
                metrics.security_score = (active_layers / 8) * 10  # Out of 10

                # Budget
                budget = security.get("budget", {})
                metrics.monthly_spend = budget.get("spent", 0)
                metrics.budget_remaining = budget.get("remaining", 200)

                # Brains
                brains = status.get("brains", {})
                metrics.brains_available = {
                    name: info.get("available", False)
                    for name, info in brains.items()
                }

                # Capabilities (placeholder - would track actual systems built)
                metrics.capabilities_built = 8  # Day 1 foundation

            except Exception as e:
                logger.error(f"Error collecting Adamus metrics: {e}")

        return metrics

    async def collect_external(self) -> ExternalMetrics:
        """
        Collect external radar metrics.

        In production, this would:
        - Scrape competitor websites
        - Monitor news feeds
        - Track social media
        """
        timestamp = datetime.now().isoformat()

        # Placeholder competitor data
        competitors = [
            CompetitorSnapshot(
                name="Notion",
                last_checked=timestamp,
                recent_features=["AI writing", "Collaborative editing"],
                pricing_tier="$10-20/user/month",
                funding_status="Series C ($2B valuation)",
                threat_level="high"
            ),
            CompetitorSnapshot(
                name="Mem",
                last_checked=timestamp,
                recent_features=["AI memory", "Smart search"],
                pricing_tier="$10-15/user/month",
                funding_status="Series A ($60M raised)",
                threat_level="medium"
            ),
            CompetitorSnapshot(
                name="Obsidian",
                last_checked=timestamp,
                recent_features=["Local-first", "Plugin ecosystem"],
                pricing_tier="Free / $8 sync",
                funding_status="Bootstrapped",
                threat_level="medium"
            )
        ]

        metrics = ExternalMetrics(
            timestamp=timestamp,
            competitors=competitors,
            market_signals=[
                "AI writing tools growing 40% YoY",
                "Creator economy expanding"
            ],
            threats=[
                "Large tech companies entering space",
                "Open source alternatives emerging"
            ]
        )

        self._last_external = metrics
        return metrics

    def get_cached_metrics(self) -> Optional[Dict[str, Any]]:
        """Get last collected metrics without re-fetching."""
        if not self._last_internal or not self._last_external:
            return None

        return {
            "internal": self._last_internal.to_dict(),
            "external": self._last_external.to_dict(),
            "collected_at": self._last_update.isoformat() if self._last_update else None
        }

    def needs_refresh(self, max_age_seconds: int = 300) -> bool:
        """Check if metrics need refresh (default: 5 minutes)."""
        if not self._last_update:
            return True

        age = (datetime.now() - self._last_update).total_seconds()
        return age > max_age_seconds
