"""
Sentiment Analysis and Community Pulse

Monitors community health across platforms:
- Discord sentiment
- Twitter mentions
- Reddit discussions
- User feedback

From NETWORKED_AI_TRINITY.md:
- Sentiment across Discord, Twitter, Reddit
- Engagement metrics
- Asabiyyah strength (cult cohesion)
- Early churn signals
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class SentimentLevel(Enum):
    """Community sentiment levels."""
    VERY_NEGATIVE = "very_negative"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"
    POSITIVE = "positive"
    VERY_POSITIVE = "very_positive"


class Platform(Enum):
    """Monitored platforms."""
    DISCORD = "discord"
    TWITTER = "twitter"
    REDDIT = "reddit"
    PRODUCT_HUNT = "product_hunt"
    HACKER_NEWS = "hacker_news"


@dataclass
class SentimentData:
    """Sentiment data for a single message/post."""
    platform: Platform
    content: str
    sentiment_score: float  # -1.0 to 1.0
    engagement: int  # likes, upvotes, reactions
    timestamp: str
    author_id: Optional[str] = None

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["platform"] = self.platform.value
        return result


@dataclass
class PlatformPulse:
    """Aggregate sentiment for a platform."""
    platform: Platform
    sentiment_score: float
    sentiment_level: SentimentLevel
    message_count: int
    engagement_total: int
    top_topics: List[str]
    churn_signals: List[str]
    timestamp: str

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["platform"] = self.platform.value
        result["sentiment_level"] = self.sentiment_level.value
        return result


@dataclass
class CommunityPulse:
    """
    Complete community health snapshot.

    This is what gets reported to War Room.
    """
    timestamp: str
    overall_sentiment: float
    overall_level: SentimentLevel
    engagement_score: float  # 0-100
    asabiyyah_score: float  # Cult cohesion 0-100
    churn_risk: float  # 0-100
    platform_data: Dict[str, PlatformPulse]
    alerts: List[Dict[str, str]]

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "overall_sentiment": self.overall_sentiment,
            "overall_level": self.overall_level.value,
            "engagement_score": self.engagement_score,
            "asabiyyah_score": self.asabiyyah_score,
            "churn_risk": self.churn_risk,
            "platforms": {k: v.to_dict() for k, v in self.platform_data.items()},
            "alerts": self.alerts
        }

    @property
    def is_healthy(self) -> bool:
        """Check if community health is acceptable."""
        return self.overall_sentiment >= 0.5 and self.churn_risk < 30


class SentimentAnalyzer:
    """
    Analyze sentiment across community platforms.

    For MVP: Uses mock data and simple keyword-based sentiment.
    Production: Would integrate with Discord API, Twitter API, etc.
    """

    # Simple keyword-based sentiment (MVP approach)
    POSITIVE_KEYWORDS = [
        "love", "amazing", "great", "awesome", "excellent",
        "helpful", "thanks", "perfect", "brilliant", "fantastic"
    ]

    NEGATIVE_KEYWORDS = [
        "hate", "terrible", "awful", "broken", "bug",
        "crash", "slow", "disappointed", "frustrated", "annoying"
    ]

    CHURN_KEYWORDS = [
        "cancel", "unsubscribe", "leaving", "switching",
        "alternative", "competitor", "refund", "waste"
    ]

    def __init__(
        self,
        discord_token: Optional[str] = None,
        twitter_token: Optional[str] = None
    ):
        """
        Initialize sentiment analyzer.

        Args:
            discord_token: Discord bot token (optional for MVP)
            twitter_token: Twitter API token (optional for MVP)
        """
        self.discord_token = discord_token
        self.twitter_token = twitter_token

        # Thresholds for alerts
        self.sentiment_warning_threshold = 0.5
        self.sentiment_critical_threshold = 0.3
        self.churn_warning_threshold = 20
        self.churn_critical_threshold = 40

    async def get_community_pulse(self) -> CommunityPulse:
        """
        Get complete community health pulse.

        Returns:
            CommunityPulse with all platform data
        """
        timestamp = datetime.now().isoformat()

        # Collect data from each platform
        platform_data = {}
        for platform in Platform:
            pulse = await self._analyze_platform(platform)
            platform_data[platform.value] = pulse

        # Calculate overall metrics
        overall_sentiment = self._calculate_overall_sentiment(platform_data)
        overall_level = self._sentiment_to_level(overall_sentiment)
        engagement = self._calculate_engagement_score(platform_data)
        asabiyyah = self._calculate_asabiyyah(platform_data)
        churn_risk = self._calculate_churn_risk(platform_data)

        # Generate alerts
        alerts = self._generate_alerts(
            overall_sentiment, engagement, churn_risk
        )

        pulse = CommunityPulse(
            timestamp=timestamp,
            overall_sentiment=overall_sentiment,
            overall_level=overall_level,
            engagement_score=engagement,
            asabiyyah_score=asabiyyah,
            churn_risk=churn_risk,
            platform_data=platform_data,
            alerts=alerts
        )

        logger.info(
            f"Community pulse: sentiment={overall_sentiment:.2f}, "
            f"engagement={engagement:.1f}, churn_risk={churn_risk:.1f}"
        )

        return pulse

    async def _analyze_platform(self, platform: Platform) -> PlatformPulse:
        """
        Analyze sentiment for a single platform.

        For MVP: Returns mock data.
        Production: Would call actual platform APIs.
        """
        # Mock data generation
        messages = await self._get_platform_messages(platform)

        if not messages:
            # Return neutral data if no messages
            return PlatformPulse(
                platform=platform,
                sentiment_score=0.5,
                sentiment_level=SentimentLevel.NEUTRAL,
                message_count=0,
                engagement_total=0,
                top_topics=[],
                churn_signals=[],
                timestamp=datetime.now().isoformat()
            )

        # Calculate sentiment
        total_sentiment = sum(m.sentiment_score for m in messages)
        avg_sentiment = (total_sentiment / len(messages) + 1) / 2  # Normalize to 0-1

        # Calculate engagement
        total_engagement = sum(m.engagement for m in messages)

        # Detect topics and churn signals
        topics = self._extract_topics(messages)
        churn_signals = self._detect_churn_signals(messages)

        return PlatformPulse(
            platform=platform,
            sentiment_score=avg_sentiment,
            sentiment_level=self._sentiment_to_level(avg_sentiment),
            message_count=len(messages),
            engagement_total=total_engagement,
            top_topics=topics[:5],
            churn_signals=churn_signals,
            timestamp=datetime.now().isoformat()
        )

    async def _get_platform_messages(
        self,
        platform: Platform
    ) -> List[SentimentData]:
        """
        Get messages from a platform.

        For MVP: Returns mock data.
        Production: Would call actual platform APIs.
        """
        # Mock messages for each platform
        mock_messages = {
            Platform.DISCORD: [
                ("Love the new AI feature!", 0.9, 15),
                ("Having some issues with sync", -0.3, 5),
                ("This is exactly what I needed", 0.8, 12),
                ("Great update!", 0.7, 8),
            ],
            Platform.TWITTER: [
                ("Just discovered @Genre - amazing writing tool", 0.8, 45),
                ("Genre is the future of creative writing", 0.7, 32),
            ],
            Platform.REDDIT: [
                ("Has anyone tried Genre? Worth the price?", 0.1, 23),
                ("Genre vs Notion - my comparison", 0.4, 56),
            ],
            Platform.PRODUCT_HUNT: [
                ("This solves a real problem for writers", 0.8, 89),
                ("Interesting concept, but needs work", 0.3, 34),
            ],
            Platform.HACKER_NEWS: [
                ("Show HN: Genre - AI writing assistant", 0.5, 124),
            ]
        }

        messages = []
        for content, sentiment, engagement in mock_messages.get(platform, []):
            messages.append(SentimentData(
                platform=platform,
                content=content,
                sentiment_score=sentiment,
                engagement=engagement,
                timestamp=datetime.now().isoformat()
            ))

        return messages

    def analyze_text(self, text: str) -> float:
        """
        Analyze sentiment of a single text.

        Simple keyword-based approach for MVP.

        Args:
            text: Text to analyze

        Returns:
            Sentiment score from -1.0 to 1.0
        """
        text_lower = text.lower()

        positive_count = sum(
            1 for word in self.POSITIVE_KEYWORDS if word in text_lower
        )
        negative_count = sum(
            1 for word in self.NEGATIVE_KEYWORDS if word in text_lower
        )

        if positive_count + negative_count == 0:
            return 0.0

        score = (positive_count - negative_count) / (positive_count + negative_count)
        return max(-1.0, min(1.0, score))

    def _sentiment_to_level(self, score: float) -> SentimentLevel:
        """Convert sentiment score to level."""
        if score < 0.2:
            return SentimentLevel.VERY_NEGATIVE
        elif score < 0.4:
            return SentimentLevel.NEGATIVE
        elif score < 0.6:
            return SentimentLevel.NEUTRAL
        elif score < 0.8:
            return SentimentLevel.POSITIVE
        else:
            return SentimentLevel.VERY_POSITIVE

    def _calculate_overall_sentiment(
        self,
        platform_data: Dict[str, PlatformPulse]
    ) -> float:
        """Calculate weighted overall sentiment."""
        if not platform_data:
            return 0.5

        # Weight by message count
        total_weight = sum(p.message_count for p in platform_data.values())
        if total_weight == 0:
            return 0.5

        weighted_sum = sum(
            p.sentiment_score * p.message_count
            for p in platform_data.values()
        )

        return weighted_sum / total_weight

    def _calculate_engagement_score(
        self,
        platform_data: Dict[str, PlatformPulse]
    ) -> float:
        """Calculate engagement score (0-100)."""
        total_engagement = sum(p.engagement_total for p in platform_data.values())
        total_messages = sum(p.message_count for p in platform_data.values())

        if total_messages == 0:
            return 0.0

        # Engagement per message, normalized to 0-100
        avg_engagement = total_engagement / total_messages
        return min(100.0, avg_engagement * 2)

    def _calculate_asabiyyah(
        self,
        platform_data: Dict[str, PlatformPulse]
    ) -> float:
        """
        Calculate Asabiyyah (cult cohesion) score.

        From NETWORKED_AI_TRINITY.md: Measure of community loyalty.
        """
        # For MVP: Based on positive sentiment + engagement
        sentiment_factor = self._calculate_overall_sentiment(platform_data)
        engagement_factor = self._calculate_engagement_score(platform_data) / 100

        # Asabiyyah = sentiment * engagement * 100
        return (sentiment_factor * 0.6 + engagement_factor * 0.4) * 100

    def _calculate_churn_risk(
        self,
        platform_data: Dict[str, PlatformPulse]
    ) -> float:
        """Calculate churn risk score (0-100)."""
        total_churn_signals = sum(
            len(p.churn_signals) for p in platform_data.values()
        )
        total_messages = sum(p.message_count for p in platform_data.values())

        if total_messages == 0:
            return 0.0

        # Base risk on churn signal ratio and negative sentiment
        churn_signal_ratio = total_churn_signals / max(total_messages, 1)
        sentiment = self._calculate_overall_sentiment(platform_data)

        # Higher risk if sentiment is low
        sentiment_risk = (1 - sentiment) * 50

        # Risk from explicit churn signals
        signal_risk = churn_signal_ratio * 100

        return min(100.0, sentiment_risk + signal_risk)

    def _extract_topics(self, messages: List[SentimentData]) -> List[str]:
        """Extract top topics from messages."""
        # Simple word frequency for MVP
        word_counts: Dict[str, int] = {}

        for msg in messages:
            words = msg.content.lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    word_counts[word] = word_counts.get(word, 0) + 1

        # Sort by frequency
        sorted_words = sorted(
            word_counts.items(), key=lambda x: x[1], reverse=True
        )

        return [word for word, count in sorted_words[:10]]

    def _detect_churn_signals(self, messages: List[SentimentData]) -> List[str]:
        """Detect churn signals in messages."""
        signals = []

        for msg in messages:
            text_lower = msg.content.lower()
            for keyword in self.CHURN_KEYWORDS:
                if keyword in text_lower:
                    signals.append(f"Churn signal: '{keyword}' mentioned")
                    break

        return signals

    def _generate_alerts(
        self,
        sentiment: float,
        engagement: float,
        churn_risk: float
    ) -> List[Dict[str, str]]:
        """Generate alerts based on metrics."""
        alerts = []

        if sentiment < self.sentiment_critical_threshold:
            alerts.append({
                "severity": "critical",
                "category": "community",
                "title": "Community Sentiment Critical",
                "message": f"Sentiment at {sentiment:.2f} - immediate attention needed"
            })
        elif sentiment < self.sentiment_warning_threshold:
            alerts.append({
                "severity": "warning",
                "category": "community",
                "title": "Community Sentiment Declining",
                "message": f"Sentiment at {sentiment:.2f} - monitor closely"
            })

        if churn_risk > self.churn_critical_threshold:
            alerts.append({
                "severity": "critical",
                "category": "churn",
                "title": "High Churn Risk",
                "message": f"Churn risk at {churn_risk:.1f}% - retention focus needed"
            })
        elif churn_risk > self.churn_warning_threshold:
            alerts.append({
                "severity": "warning",
                "category": "churn",
                "title": "Elevated Churn Risk",
                "message": f"Churn risk at {churn_risk:.1f}%"
            })

        return alerts
