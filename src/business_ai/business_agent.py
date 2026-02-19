"""
Business AI Agent

The Business AI handles survival-critical operations:
- Finance tracking (MRR, burn, runway)
- Competitor intelligence
- Market signals and trends
- Acquisition radar

Part of the Networked AI Trinity:
- Reports to War Room
- Receives tasks from AI Coordinator
- Sends clone requests to Tech AI (Adamus)
- Receives content distribution from CAMBI AI
"""

import os
import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable

from .finance_tracker import FinanceTracker, FinanceMetrics
from .competitor_intel import CompetitorIntel, CloneOpportunity, ThreatLevel

logger = logging.getLogger(__name__)


class BusinessAI:
    """
    Business AI Agent.

    The "Finance + Intel" brain of the Trinity.
    Keeps Genre alive by monitoring survival metrics
    and competitor landscape.

    Daily Responsibilities:
    - Morning: Finance pulse (MRR, burn, runway)
    - Continuous: Competitor monitoring
    - Weekly: Trend analysis and forecasting

    Integration:
    - War Room: Report all metrics
    - AI Coordinator: Receive/execute tasks
    - Tech AI: Send clone requests
    """

    def __init__(
        self,
        coordinator=None,
        war_room=None,
        searxng_url: str = "http://localhost:8080"
    ):
        """
        Initialize Business AI.

        Args:
            coordinator: AI Coordinator instance
            war_room: War Room metrics collector
            searxng_url: Self-hosted SearxNG URL
        """
        self.coordinator = coordinator
        self.war_room = war_room
        self.searxng_url = searxng_url

        # Initialize components
        self.finance = FinanceTracker()
        self.intel = CompetitorIntel(searxng_url=searxng_url)

        # Task queue
        self._task_queue: List[Dict[str, Any]] = []
        self._completed_tasks: List[Dict[str, Any]] = []

        # State
        self._initialized = False
        self._last_daily_pulse: Optional[datetime] = None
        self._last_competitor_scan: Optional[datetime] = None

        logger.info("Business AI initialized")

    async def initialize(self) -> bool:
        """
        Initialize Business AI components.

        Returns:
            True if initialization successful
        """
        try:
            # Verify finance tracker
            metrics = self.finance.get_current_metrics()
            logger.info(f"Finance tracker ready: MRR=${metrics.mrr}")

            # Verify competitor intel
            profiles = self.intel.get_competitor_profiles()
            logger.info(f"Monitoring {len(profiles)} competitors")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def daily_finance_pulse(self) -> Dict[str, Any]:
        """
        Run daily finance pulse.

        From NETWORKED_AI_TRINITY.md:
        - Track: Burn rate vs revenue
        - Runway projection
        - Cash reserves health
        - Revenue growth trajectory
        - Alert if runway < 6 months

        Returns:
            Complete survival report
        """
        logger.info("Running daily finance pulse...")

        # Get survival report
        report = self.finance.get_survival_report()

        # Check for alerts
        alerts = report.get("alerts", [])
        for alert in alerts:
            if alert["severity"] == "critical":
                logger.warning(f"[CRITICAL ALERT] {alert['title']}: {alert['message']}")
                await self._send_to_war_room(alert)

        # Report to War Room
        if self.war_room:
            await self._update_war_room("finance", report)

        self._last_daily_pulse = datetime.now()
        logger.info(f"Finance pulse complete: {report['status']}")

        return report

    async def competitor_intelligence(self) -> Dict[str, Any]:
        """
        Run competitor intelligence scan.

        From NETWORKED_AI_TRINITY.md:
        - Monitor competitors: Feature launches, pricing, team changes, funding
        - Uses SECURE SEARCH ONLY (SearxNG - telemetry-free)
        - Identify clone opportunities
        - Coordinate with Tech AI for cloning

        Returns:
            Complete intel report
        """
        logger.info("Running competitor intelligence scan...")

        # Run monitoring
        intel = await self.intel.monitor_all()

        # Process clone opportunities
        clone_queue = intel.get("clone_opportunities", [])
        for opportunity in clone_queue:
            logger.info(
                f"Clone opportunity: {opportunity['feature_name']} "
                f"from {opportunity['competitor']}"
            )

            # Send to Tech AI (Adamus) for cloning
            if self.coordinator:
                await self._send_clone_request(opportunity)

        # Update War Room
        if self.war_room:
            await self._update_war_room("competitors", intel)

        self._last_competitor_scan = datetime.now()
        logger.info(f"Intel scan complete: {len(clone_queue)} opportunities found")

        return intel

    async def acquisition_radar(self) -> Dict[str, Any]:
        """
        Scan for acquisition targets.

        From NETWORKED_AI_TRINITY.md:
        - Failed competitors with good tech
        - Complementary products
        - Talent teams

        Returns:
            Acquisition targets report
        """
        logger.info("Running acquisition radar...")

        # Mock implementation (production: full market scan)
        targets = []

        # Check for struggling competitors
        for profile in self.intel.competitors:
            # Hypothetical: check for distress signals
            if profile.funding_status.lower() in ["unknown", "struggling"]:
                targets.append({
                    "name": profile.name,
                    "type": "competitor",
                    "reason": "Potential distress",
                    "score": 6.0
                })

        # Filter high-score targets
        high_value = [t for t in targets if t.get("score", 0) > 7.5]
        for target in high_value:
            logger.info(f"High-value acquisition target: {target['name']}")
            if self.war_room:
                await self._send_to_war_room({
                    "severity": "info",
                    "category": "acquisition",
                    "title": f"Acquisition Target: {target['name']}",
                    "message": target.get("reason", "")
                })

        return {
            "timestamp": datetime.now().isoformat(),
            "targets": targets,
            "high_value_count": len(high_value)
        }

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task from AI Coordinator.

        Task types:
        - finance_pulse: Run daily finance check
        - competitor_scan: Run competitor intelligence
        - acquisition_radar: Scan for acquisition targets
        - distribute_content: Handle content distribution (from CAMBI AI)
        - track_experiment: Track A/B test results

        Args:
            task: Task dictionary with type and parameters

        Returns:
            Task result
        """
        task_type = task.get("type", "")
        logger.info(f"Executing task: {task_type}")

        result = {"task_id": task.get("id"), "status": "completed"}

        try:
            if task_type == "finance_pulse":
                result["data"] = await self.daily_finance_pulse()

            elif task_type == "competitor_scan":
                result["data"] = await self.competitor_intelligence()

            elif task_type == "acquisition_radar":
                result["data"] = await self.acquisition_radar()

            elif task_type == "distribute_content":
                # Content distribution request from CAMBI AI
                content = task.get("content", [])
                result["data"] = await self._distribute_content(content)

            elif task_type == "track_experiment":
                # Track A/B test results
                experiment = task.get("experiment", {})
                result["data"] = await self._track_experiment(experiment)

            else:
                result["status"] = "unknown_task"
                result["error"] = f"Unknown task type: {task_type}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Task execution failed: {e}")

        self._completed_tasks.append(result)
        return result

    async def _distribute_content(
        self,
        content: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Handle content distribution (from CAMBI AI).

        Tracks which content drives signups and revenue.
        """
        # Mock distribution tracking
        distributed = []
        for item in content:
            distributed.append({
                "content_id": item.get("id", "unknown"),
                "title": item.get("title", ""),
                "status": "distributed",
                "tracking_url": f"https://genre.app/track/{item.get('id', 'x')}"
            })

        return {
            "distributed_count": len(distributed),
            "items": distributed
        }

    async def _track_experiment(
        self,
        experiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Track A/B test results.

        Part of weekly testing cycle with CAMBI AI.
        """
        # Mock experiment tracking
        return {
            "experiment_id": experiment.get("id", "unknown"),
            "variant_a_conversion": 0.065,  # 6.5%
            "variant_b_conversion": 0.087,  # 8.7%
            "winner": "variant_b",
            "confidence": 0.95,
            "recommendation": "Lock variant_b into rails"
        }

    async def _send_clone_request(
        self,
        opportunity: Dict[str, Any]
    ) -> None:
        """
        Send clone request to Tech AI (Adamus).

        Args:
            opportunity: Clone opportunity details
        """
        if self.coordinator:
            task = {
                "type": "clone_feature",
                "feature": opportunity.get("feature_name"),
                "competitor": opportunity.get("competitor"),
                "priority": opportunity.get("priority", "medium"),
                "source": "business_ai"
            }
            # In production: coordinator.send_to_tech_ai(task)
            logger.info(f"Clone request sent to Tech AI: {task}")

    async def _send_to_war_room(self, alert: Dict[str, Any]) -> None:
        """Send alert to War Room."""
        if self.war_room:
            # In production: war_room.add_alert(alert)
            logger.info(f"Alert sent to War Room: {alert.get('title', 'Unknown')}")

    async def _update_war_room(
        self,
        category: str,
        data: Dict[str, Any]
    ) -> None:
        """Update War Room with metrics."""
        if self.war_room:
            # In production: war_room.update(category, data)
            logger.info(f"War Room updated: {category}")

    def get_status(self) -> Dict[str, Any]:
        """
        Get Business AI status for monitoring.

        Returns:
            Status dictionary
        """
        metrics = self.finance.get_current_metrics()

        return {
            "initialized": self._initialized,
            "last_finance_pulse": self._last_daily_pulse.isoformat() if self._last_daily_pulse else None,
            "last_competitor_scan": self._last_competitor_scan.isoformat() if self._last_competitor_scan else None,
            "pending_tasks": len(self._task_queue),
            "completed_tasks": len(self._completed_tasks),
            "clone_queue_size": len(self.intel.get_clone_queue()),
            "financial_status": metrics.severity,
            "mrr": metrics.mrr,
            "runway_months": metrics.runway_months
        }

    async def run_daily_cycle(self) -> Dict[str, Any]:
        """
        Run complete daily cycle.

        Daily cycle from NETWORKED_AI_TRINITY.md:
        1. Finance pulse
        2. Competitor intelligence
        3. Report to War Room
        """
        logger.info("=" * 50)
        logger.info("BUSINESS AI: Starting daily cycle")
        logger.info("=" * 50)

        results = {}

        # 1. Finance pulse
        results["finance"] = await self.daily_finance_pulse()

        # 2. Competitor intelligence
        results["intel"] = await self.competitor_intelligence()

        # 3. Summary
        results["summary"] = {
            "financial_status": results["finance"]["status"],
            "clone_opportunities": len(results["intel"].get("clone_opportunities", [])),
            "timestamp": datetime.now().isoformat()
        }

        logger.info("=" * 50)
        logger.info(f"Daily cycle complete: {results['summary']}")
        logger.info("=" * 50)

        return results


async def main():
    """Test Business AI standalone."""
    logging.basicConfig(level=logging.INFO)

    business_ai = BusinessAI()
    await business_ai.initialize()

    # Run daily cycle
    results = await business_ai.run_daily_cycle()

    print("\n" + "=" * 50)
    print("BUSINESS AI DAILY REPORT")
    print("=" * 50)
    print(f"Financial Status: {results['summary']['financial_status']}")
    print(f"Clone Opportunities: {results['summary']['clone_opportunities']}")
    print(f"Timestamp: {results['summary']['timestamp']}")


if __name__ == "__main__":
    asyncio.run(main())
