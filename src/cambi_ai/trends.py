"""
Trend Detection

Monitors trends across platforms:
- HackerNews
- ProductHunt
- Reddit (creative subs)
- Industry news

From NETWORKED_AI_TRINITY.md:
- Identify trending topics in creative space
- Detect what content resonates
- Feed trends to content generation
- Use TELEMETRY-FREE search (SearxNG)
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class TrendSource(Enum):
    """Sources for trend detection."""
    HACKER_NEWS = "hacker_news"
    PRODUCT_HUNT = "product_hunt"
    REDDIT = "reddit"
    TWITTER = "twitter"
    SEARXNG = "searxng"


class TrendCategory(Enum):
    """Categories of trends."""
    AI_TOOLS = "ai_tools"
    CREATIVE_WRITING = "creative_writing"
    PRODUCTIVITY = "productivity"
    MARKETING = "marketing"
    TECHNOLOGY = "technology"
    STARTUP = "startup"


@dataclass
class TrendSignal:
    """A single trend signal."""
    id: str
    source: TrendSource
    category: TrendCategory
    title: str
    url: str
    score: int  # Upvotes, points, etc.
    comments: int
    detected_at: str
    relevance_score: float  # 0-1, how relevant to Genre

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["source"] = self.source.value
        result["category"] = self.category.value
        return result


@dataclass
class TrendReport:
    """Complete trend analysis report."""
    timestamp: str
    top_trends: List[TrendSignal]
    by_category: Dict[str, List[TrendSignal]]
    by_source: Dict[str, List[TrendSignal]]
    opportunities: List[Dict[str, str]]
    recommendations: List[str]

    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "top_trends": [t.to_dict() for t in self.top_trends],
            "by_category": {
                k: [t.to_dict() for t in v]
                for k, v in self.by_category.items()
            },
            "by_source": {
                k: [t.to_dict() for t in v]
                for k, v in self.by_source.items()
            },
            "opportunities": self.opportunities,
            "recommendations": self.recommendations
        }


class TrendDetector:
    """
    Trend Detection System.

    Monitors external sources for trends relevant to Genre.
    All sources are TELEMETRY-FREE (direct scraping, RSS, public APIs).

    From TELEMETRY_FREE_SEARCH.md:
    - HackerNews API (public, no tracking)
    - ProductHunt (public RSS)
    - Direct website scraping

    NO Google, Bing, or other tracking search engines.
    """

    # Keywords relevant to Genre
    RELEVANT_KEYWORDS = [
        "ai writing", "creative writing", "note taking",
        "knowledge management", "second brain", "productivity",
        "writing tools", "ai assistant", "content creation",
        "notion", "obsidian", "roam", "writing app"
    ]

    def __init__(
        self,
        searxng_url: str = "http://localhost:8080"
    ):
        """
        Initialize trend detector.

        Args:
            searxng_url: Self-hosted SearxNG URL for search
        """
        self.searxng_url = searxng_url

        # Trend history
        self._trend_history: List[TrendReport] = []
        self._signal_counter = 0

    async def detect_trends(self) -> TrendReport:
        """
        Run full trend detection cycle.

        Returns:
            Complete trend report
        """
        timestamp = datetime.now().isoformat()
        all_signals = []

        # Collect from each source
        for source in TrendSource:
            try:
                signals = await self._scan_source(source)
                all_signals.extend(signals)
            except Exception as e:
                logger.error(f"Error scanning {source.value}: {e}")

        # Filter for relevance
        relevant_signals = [
            s for s in all_signals if s.relevance_score > 0.3
        ]

        # Sort by combined score (popularity + relevance)
        relevant_signals.sort(
            key=lambda x: (x.score * x.relevance_score),
            reverse=True
        )

        # Organize by category and source
        by_category = self._group_by_category(relevant_signals)
        by_source = self._group_by_source(relevant_signals)

        # Identify opportunities
        opportunities = self._identify_opportunities(relevant_signals)

        # Generate recommendations
        recommendations = self._generate_recommendations(
            relevant_signals, opportunities
        )

        report = TrendReport(
            timestamp=timestamp,
            top_trends=relevant_signals[:20],
            by_category=by_category,
            by_source=by_source,
            opportunities=opportunities,
            recommendations=recommendations
        )

        self._trend_history.append(report)
        logger.info(f"Trend detection complete: {len(relevant_signals)} relevant signals")

        return report

    async def _scan_source(self, source: TrendSource) -> List[TrendSignal]:
        """
        Scan a single source for trends.

        For MVP: Returns mock data.
        Production: Would call actual APIs/scrape.
        """
        # Mock data for each source
        mock_data = {
            TrendSource.HACKER_NEWS: [
                {
                    "title": "Show HN: AI Writing Assistant with Memory",
                    "url": "https://news.ycombinator.com/item?id=12345",
                    "score": 256,
                    "comments": 89,
                    "category": TrendCategory.AI_TOOLS
                },
                {
                    "title": "The Future of Knowledge Management",
                    "url": "https://news.ycombinator.com/item?id=12346",
                    "score": 189,
                    "comments": 67,
                    "category": TrendCategory.PRODUCTIVITY
                },
                {
                    "title": "Why I Switched from Notion to Obsidian",
                    "url": "https://news.ycombinator.com/item?id=12347",
                    "score": 312,
                    "comments": 145,
                    "category": TrendCategory.PRODUCTIVITY
                }
            ],
            TrendSource.PRODUCT_HUNT: [
                {
                    "title": "AI Content Studio - Create Blog Posts in Minutes",
                    "url": "https://producthunt.com/posts/ai-content-studio",
                    "score": 456,
                    "comments": 78,
                    "category": TrendCategory.AI_TOOLS
                },
                {
                    "title": "Writer's Block Solver - AI Writing Prompts",
                    "url": "https://producthunt.com/posts/writers-block-solver",
                    "score": 234,
                    "comments": 45,
                    "category": TrendCategory.CREATIVE_WRITING
                }
            ],
            TrendSource.REDDIT: [
                {
                    "title": "[Discussion] Best AI tools for creative writing in 2026",
                    "url": "https://reddit.com/r/writing/comments/abc123",
                    "score": 567,
                    "comments": 234,
                    "category": TrendCategory.CREATIVE_WRITING
                }
            ],
            TrendSource.TWITTER: [
                {
                    "title": "Thread: AI is changing how we write (viral)",
                    "url": "https://twitter.com/user/status/123",
                    "score": 12500,
                    "comments": 890,
                    "category": TrendCategory.AI_TOOLS
                }
            ],
            TrendSource.SEARXNG: [
                {
                    "title": "New Report: AI Writing Tools Market Growing 45% YoY",
                    "url": "https://techcrunch.com/ai-writing-tools-report",
                    "score": 100,
                    "comments": 0,
                    "category": TrendCategory.MARKETING
                }
            ]
        }

        signals = []
        for item in mock_data.get(source, []):
            self._signal_counter += 1
            signal_id = f"trend_{source.value}_{self._signal_counter}"

            # Calculate relevance
            relevance = self._calculate_relevance(item["title"])

            signals.append(TrendSignal(
                id=signal_id,
                source=source,
                category=item["category"],
                title=item["title"],
                url=item["url"],
                score=item["score"],
                comments=item["comments"],
                detected_at=datetime.now().isoformat(),
                relevance_score=relevance
            ))

        return signals

    def _calculate_relevance(self, text: str) -> float:
        """
        Calculate relevance score based on keywords.

        Args:
            text: Text to analyze

        Returns:
            Relevance score 0-1
        """
        text_lower = text.lower()
        matches = sum(
            1 for keyword in self.RELEVANT_KEYWORDS
            if keyword in text_lower
        )

        # More matches = higher relevance
        return min(1.0, matches * 0.25)

    def _group_by_category(
        self,
        signals: List[TrendSignal]
    ) -> Dict[str, List[TrendSignal]]:
        """Group signals by category."""
        result: Dict[str, List[TrendSignal]] = {}
        for signal in signals:
            cat = signal.category.value
            if cat not in result:
                result[cat] = []
            result[cat].append(signal)
        return result

    def _group_by_source(
        self,
        signals: List[TrendSignal]
    ) -> Dict[str, List[TrendSignal]]:
        """Group signals by source."""
        result: Dict[str, List[TrendSignal]] = {}
        for signal in signals:
            src = signal.source.value
            if src not in result:
                result[src] = []
            result[src].append(signal)
        return result

    def _identify_opportunities(
        self,
        signals: List[TrendSignal]
    ) -> List[Dict[str, str]]:
        """
        Identify content/feature opportunities from trends.

        Returns list of opportunities to pursue.
        """
        opportunities = []

        # Look for high-engagement trends in relevant categories
        for signal in signals[:10]:  # Top 10 trends
            if signal.relevance_score > 0.5:
                opportunity = {
                    "type": "content",
                    "trend": signal.title,
                    "source": signal.source.value,
                    "action": f"Create content cluster around: {signal.title}",
                    "urgency": "high" if signal.score > 500 else "medium"
                }
                opportunities.append(opportunity)

        # Look for competitor mentions
        competitor_keywords = ["notion", "obsidian", "mem", "reflect"]
        for signal in signals:
            title_lower = signal.title.lower()
            for comp in competitor_keywords:
                if comp in title_lower:
                    opportunities.append({
                        "type": "competitive",
                        "trend": signal.title,
                        "competitor": comp,
                        "action": f"Monitor discussion about {comp}",
                        "urgency": "medium"
                    })
                    break

        return opportunities[:10]  # Return top 10

    def _generate_recommendations(
        self,
        signals: List[TrendSignal],
        opportunities: List[Dict[str, str]]
    ) -> List[str]:
        """Generate actionable recommendations."""
        recommendations = []

        # Top trends recommendation
        if signals:
            top = signals[0]
            recommendations.append(
                f"Hot topic: '{top.title}' with {top.score} points. "
                f"Create content cluster around this theme."
            )

        # Category recommendations
        categories = self._group_by_category(signals)
        if TrendCategory.AI_TOOLS.value in categories:
            recommendations.append(
                "AI tools trending - emphasize Genre's AI capabilities in content."
            )

        if TrendCategory.CREATIVE_WRITING.value in categories:
            recommendations.append(
                "Creative writing discussions active - share Genre use cases."
            )

        # Opportunity recommendations
        high_urgency = [o for o in opportunities if o.get("urgency") == "high"]
        if high_urgency:
            recommendations.append(
                f"High-urgency opportunity: {high_urgency[0]['action']}"
            )

        return recommendations

    async def scan_hacker_news(self) -> List[TrendSignal]:
        """
        Scan HackerNews specifically.

        From TELEMETRY_FREE_SEARCH.md:
        HackerNews API is completely public, no tracking.
        """
        return await self._scan_source(TrendSource.HACKER_NEWS)

    async def scan_product_hunt(self) -> List[TrendSignal]:
        """
        Scan ProductHunt specifically.

        Uses public RSS feed - no tracking.
        """
        return await self._scan_source(TrendSource.PRODUCT_HUNT)

    def get_trend_report(self) -> Dict[str, Any]:
        """Get most recent trend report for War Room."""
        if self._trend_history:
            return self._trend_history[-1].to_dict()
        return {"error": "No trend data available"}

    def get_trending_topics(self, count: int = 5) -> List[str]:
        """Get list of trending topics for content generation."""
        if not self._trend_history:
            return []

        latest = self._trend_history[-1]
        return [t.title for t in latest.top_trends[:count]]
