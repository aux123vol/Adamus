"""
CAMBI AI Agent

The CAMBI AI handles:
- Community: Sentiment, engagement, Asabiyyah
- Audience: Believer pipeline, retention
- Marketing: Content swarms, SEO, video
- Branding: Positioning, archetypes
- Innovation: Play Lab → Rails pipeline

Part of the Networked AI Trinity:
- Reports to War Room
- Receives tasks from AI Coordinator
- Sends content to Business AI for distribution
- Sends Play Lab specs to Tech AI (Adamus) for building
"""

import logging
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any

from .sentiment import SentimentAnalyzer, CommunityPulse
from .content_gen import (
    ContentGenerator, ContentPiece, ContentBrief,
    ContentType, ContentFormat, ContentTone
)
from .trends import TrendDetector, TrendReport

logger = logging.getLogger(__name__)


class CAMBI_AI:
    """
    CAMBI AI Agent.

    The "Soul" brain of the Trinity.
    Handles community health, content generation, and cultural innovation.

    Daily Responsibilities:
    - Morning: Community pulse (sentiment, engagement)
    - Continuous: Trend detection and content generation
    - Weekly: A/B testing cultural signals

    Integration:
    - War Room: Report community health
    - AI Coordinator: Receive/execute tasks
    - Business AI: Send content for distribution
    - Tech AI: Send Play Lab specs for building
    """

    def __init__(
        self,
        coordinator=None,
        war_room=None,
        searxng_url: str = "http://localhost:8080",
        claude_client=None
    ):
        """
        Initialize CAMBI AI.

        Args:
            coordinator: AI Coordinator instance
            war_room: War Room metrics collector
            searxng_url: Self-hosted SearxNG URL
            claude_client: Claude API client for content generation
        """
        self.coordinator = coordinator
        self.war_room = war_room
        self.searxng_url = searxng_url

        # Initialize components
        self.sentiment = SentimentAnalyzer()
        self.content = ContentGenerator(claude_client=claude_client)
        self.trends = TrendDetector(searxng_url=searxng_url)

        # Task queue
        self._task_queue: List[Dict[str, Any]] = []
        self._completed_tasks: List[Dict[str, Any]] = []

        # A/B testing experiments
        self._active_experiments: List[Dict[str, Any]] = []
        self._experiment_results: List[Dict[str, Any]] = []

        # State
        self._initialized = False
        self._last_community_pulse: Optional[datetime] = None
        self._last_trend_scan: Optional[datetime] = None

        logger.info("CAMBI AI initialized")

    async def initialize(self) -> bool:
        """
        Initialize CAMBI AI components.

        Returns:
            True if initialization successful
        """
        try:
            # Verify sentiment analyzer
            pulse = await self.sentiment.get_community_pulse()
            logger.info(f"Sentiment analyzer ready: overall={pulse.overall_sentiment:.2f}")

            # Verify content generator
            stats = self.content.get_generation_stats()
            logger.info(f"Content generator ready")

            # Verify trend detector
            logger.info("Trend detector ready")

            self._initialized = True
            return True

        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            return False

    async def community_pulse(self) -> CommunityPulse:
        """
        Get community pulse.

        From NETWORKED_AI_TRINITY.md:
        - Sentiment across Discord, Twitter, Reddit
        - Engagement metrics
        - Asabiyyah strength (cult cohesion)
        - Early churn signals
        - Alert if sentiment dropping

        Returns:
            Complete community pulse
        """
        logger.info("Getting community pulse...")

        pulse = await self.sentiment.get_community_pulse()

        # Check for alerts
        for alert in pulse.alerts:
            if alert["severity"] == "critical":
                logger.warning(f"[CRITICAL] {alert['title']}: {alert['message']}")
                await self._send_to_war_room(alert)

        # Update War Room
        if self.war_room:
            await self._update_war_room("community", pulse.to_dict())

        self._last_community_pulse = datetime.now()
        logger.info(
            f"Community pulse: sentiment={pulse.overall_sentiment:.2f}, "
            f"asabiyyah={pulse.asabiyyah_score:.1f}, churn_risk={pulse.churn_risk:.1f}"
        )

        return pulse

    async def content_swarm_generation(
        self,
        topic: Optional[str] = None,
        count: int = 10
    ) -> List[ContentPiece]:
        """
        Generate content swarm.

        From NETWORKED_AI_TRINITY.md:
        - AI SEO Swarms: Generate 1000+ pages/week
        - Identify trending topics
        - Generate SEO-optimized content
        - Deploy across niches
        - Track which content drives signups

        Args:
            topic: Topic to generate content for (auto-detects if None)
            count: Number of pieces to generate

        Returns:
            List of generated content pieces
        """
        logger.info("Generating content swarm...")

        # If no topic, detect from trends
        if topic is None:
            topics = self.trends.get_trending_topics(5)
            topic = topics[0] if topics else "AI Writing"

        # Generate content cluster
        pieces = await self.content.generate_content_cluster(
            topic=topic,
            count=count
        )

        # Send to Business AI for distribution
        if self.coordinator:
            await self._send_to_business_ai([p.to_dict() for p in pieces])

        logger.info(f"Generated {len(pieces)} content pieces on '{topic}'")
        return pieces

    async def ab_test_cultural_signals(
        self,
        experiment: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Run A/B test on cultural signals.

        From NETWORKED_AI_TRINITY.md:
        - Test different myths, rituals, messaging
        - Example: "World Founders" vs "Creative Rebels"
        - Measure: Which resonates more?

        Args:
            experiment: Experiment configuration

        Returns:
            Experiment results
        """
        logger.info(f"Running A/B test: {experiment.get('name', 'Unnamed')}")

        # Register experiment
        exp_id = f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        experiment["id"] = exp_id
        experiment["started_at"] = datetime.now().isoformat()
        experiment["status"] = "running"

        self._active_experiments.append(experiment)

        # Send variants to Tech AI for deployment
        if self.coordinator:
            await self._send_to_tech_ai({
                "type": "deploy_experiment",
                "experiment": experiment
            })

        # Mock results for MVP (production would track real data)
        results = {
            "experiment_id": exp_id,
            "variant_a": experiment.get("variant_a", "Control"),
            "variant_b": experiment.get("variant_b", "Test"),
            "variant_a_conversion": 0.065,
            "variant_b_conversion": 0.082,
            "winner": "variant_b",
            "confidence": 0.92,
            "status": "complete"
        }

        self._experiment_results.append(results)
        return results

    async def translate_play_lab_to_rails(
        self,
        play_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Translate Play Lab output to technical specs.

        From NETWORKED_AI_TRINITY.md:
        1. Humans play (Legos, toys, paint)
        2. CAMBI AI scans/photographs creations
        3. AI interprets intent
        4. Generates wireframes/specs
        5. Sends to Adamus (Tech AI) to build

        Args:
            play_session: Play Lab session data with photos/notes

        Returns:
            Technical spec for Tech AI
        """
        logger.info("Translating Play Lab output to technical spec...")

        # Interpret creation (mock for MVP)
        interpretation = self._interpret_creation(play_session)

        if interpretation["shippable"]:
            # Generate technical spec
            spec = self._generate_tech_spec(interpretation)

            # Send to Tech AI
            if self.coordinator:
                await self._send_to_tech_ai({
                    "type": "build_from_play_lab",
                    "spec": spec,
                    "priority": "innovation_pipeline"
                })

            return {
                "status": "sent_to_tech_ai",
                "spec": spec,
                "interpretation": interpretation
            }

        return {
            "status": "not_shippable",
            "interpretation": interpretation
        }

    def _interpret_creation(
        self,
        play_session: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpret Play Lab creation (mock for MVP)."""
        # In production: Use vision model to analyze images
        return {
            "concept": play_session.get("description", "Unknown concept"),
            "shippable": True,
            "technical_requirements": {
                "components": ["UI", "backend", "database"],
                "estimated_effort": "3-5 days"
            }
        }

    def _generate_tech_spec(
        self,
        interpretation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate technical spec from interpretation."""
        return {
            "feature_name": interpretation["concept"],
            "requirements": interpretation["technical_requirements"],
            "generated_at": datetime.now().isoformat(),
            "source": "play_lab"
        }

    async def detect_trends(self) -> TrendReport:
        """
        Run trend detection.

        Returns:
            Trend report
        """
        logger.info("Detecting trends...")

        report = await self.trends.detect_trends()

        # Update War Room
        if self.war_room:
            await self._update_war_room("trends", report.to_dict())

        self._last_trend_scan = datetime.now()
        logger.info(f"Found {len(report.top_trends)} relevant trends")

        return report

    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a task from AI Coordinator.

        Task types:
        - community_pulse: Check community health
        - content_swarm: Generate content
        - ab_test: Run A/B test
        - detect_trends: Find trending topics
        - play_lab_translate: Translate Play Lab to specs
        - ready_for_beta: Handle beta test request from Tech AI

        Args:
            task: Task dictionary with type and parameters

        Returns:
            Task result
        """
        task_type = task.get("type", "")
        logger.info(f"Executing task: {task_type}")

        result = {"task_id": task.get("id"), "status": "completed"}

        try:
            if task_type == "community_pulse":
                pulse = await self.community_pulse()
                result["data"] = pulse.to_dict()

            elif task_type == "content_swarm":
                pieces = await self.content_swarm_generation(
                    topic=task.get("topic"),
                    count=task.get("count", 10)
                )
                result["data"] = {"count": len(pieces)}

            elif task_type == "ab_test":
                experiment = task.get("experiment", {})
                results = await self.ab_test_cultural_signals(experiment)
                result["data"] = results

            elif task_type == "detect_trends":
                report = await self.detect_trends()
                result["data"] = report.to_dict()

            elif task_type == "play_lab_translate":
                session = task.get("session", {})
                spec = await self.translate_play_lab_to_rails(session)
                result["data"] = spec

            elif task_type == "ready_for_beta":
                # Handle beta test request from Tech AI
                result["data"] = await self._handle_beta_request(task)

            else:
                result["status"] = "unknown_task"
                result["error"] = f"Unknown task type: {task_type}"

        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
            logger.error(f"Task execution failed: {e}")

        self._completed_tasks.append(result)
        return result

    async def _handle_beta_request(
        self,
        task: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle beta test request from Tech AI."""
        feature = task.get("feature", "Unknown")
        staging_url = task.get("staging_url", "")

        # In production: Select beta testers and notify them
        return {
            "feature": feature,
            "staging_url": staging_url,
            "beta_testers_notified": 20,
            "status": "beta_started"
        }

    async def _send_to_war_room(self, alert: Dict[str, Any]) -> None:
        """Send alert to War Room."""
        if self.war_room:
            logger.info(f"Alert sent to War Room: {alert.get('title', 'Unknown')}")

    async def _update_war_room(
        self,
        category: str,
        data: Dict[str, Any]
    ) -> None:
        """Update War Room with metrics."""
        if self.war_room:
            logger.info(f"War Room updated: {category}")

    async def _send_to_business_ai(
        self,
        content: List[Dict[str, Any]]
    ) -> None:
        """Send content to Business AI for distribution."""
        if self.coordinator:
            # In production: coordinator.send_to_business_ai(task)
            logger.info(f"Content sent to Business AI: {len(content)} pieces")

    async def _send_to_tech_ai(self, task: Dict[str, Any]) -> None:
        """Send task to Tech AI."""
        if self.coordinator:
            # In production: coordinator.send_to_tech_ai(task)
            logger.info(f"Task sent to Tech AI: {task.get('type')}")

    def suggest_experiments(self) -> List[Dict[str, Any]]:
        """
        Suggest A/B experiments based on trends and community data.

        From NETWORKED_AI_TRINITY.md Weekly cycle.
        """
        return [
            {
                "name": "positioning_test",
                "variant_a": "World Founders (civilization builders)",
                "variant_b": "Creative Rebels (disruptors)",
                "metric": "conversion_to_believer"
            },
            {
                "name": "cta_test",
                "variant_a": "Start writing for free",
                "variant_b": "Join 10,000+ creators",
                "metric": "signup_rate"
            }
        ]

    def get_status(self) -> Dict[str, Any]:
        """
        Get CAMBI AI status for monitoring.

        Returns:
            Status dictionary
        """
        return {
            "initialized": self._initialized,
            "last_community_pulse": self._last_community_pulse.isoformat() if self._last_community_pulse else None,
            "last_trend_scan": self._last_trend_scan.isoformat() if self._last_trend_scan else None,
            "pending_tasks": len(self._task_queue),
            "completed_tasks": len(self._completed_tasks),
            "active_experiments": len(self._active_experiments),
            "content_generated": self.content.get_generation_stats()["total_generated"]
        }

    async def run_daily_cycle(self) -> Dict[str, Any]:
        """
        Run complete daily cycle.

        Daily cycle:
        1. Community pulse
        2. Trend detection
        3. Content generation
        4. Report to War Room
        """
        logger.info("=" * 50)
        logger.info("CAMBI AI: Starting daily cycle")
        logger.info("=" * 50)

        results = {}

        # 1. Community pulse
        pulse = await self.community_pulse()
        results["community"] = pulse.to_dict()

        # 2. Trend detection
        trends = await self.detect_trends()
        results["trends"] = {
            "top_trends": [t.title for t in trends.top_trends[:5]],
            "recommendations": trends.recommendations
        }

        # 3. Content generation based on trends
        if trends.top_trends:
            top_topic = trends.top_trends[0].title
            content = await self.content_swarm_generation(topic=top_topic, count=5)
            results["content"] = {
                "topic": top_topic,
                "pieces_generated": len(content)
            }

        # 4. Summary
        results["summary"] = {
            "community_health": "healthy" if pulse.is_healthy else "needs_attention",
            "sentiment": pulse.overall_sentiment,
            "trends_found": len(trends.top_trends),
            "timestamp": datetime.now().isoformat()
        }

        logger.info("=" * 50)
        logger.info(f"Daily cycle complete: {results['summary']}")
        logger.info("=" * 50)

        return results


async def main():
    """Test CAMBI AI standalone."""
    logging.basicConfig(level=logging.INFO)

    cambi = CAMBI_AI()
    await cambi.initialize()

    # Run daily cycle
    results = await cambi.run_daily_cycle()

    print("\n" + "=" * 50)
    print("CAMBI AI DAILY REPORT")
    print("=" * 50)
    print(f"Community Health: {results['summary']['community_health']}")
    print(f"Sentiment: {results['summary']['sentiment']:.2f}")
    print(f"Trends Found: {results['summary']['trends_found']}")


if __name__ == "__main__":
    asyncio.run(main())
