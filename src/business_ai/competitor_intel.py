"""
Competitor Intelligence

Monitors competitors for:
- New feature launches (clone opportunities)
- Pricing changes
- Funding rounds
- Team changes

Uses TELEMETRY-FREE sources:
- SearxNG (self-hosted search)
- Direct web scraping
- RSS feeds
- Public APIs

NEVER uses Google, Brave, or DDG directly (telemetry).
"""

import os
import logging
import asyncio
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Competitor threat level."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class CompetitorProfile:
    """Competitor profile and monitoring data."""
    name: str
    website: str
    threat_level: ThreatLevel = ThreatLevel.MEDIUM
    last_checked: Optional[str] = None
    recent_features: List[str] = field(default_factory=list)
    pricing_info: Dict[str, Any] = field(default_factory=dict)
    funding_status: str = "unknown"
    employee_count: Optional[int] = None
    notes: str = ""

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["threat_level"] = self.threat_level.value
        return result


@dataclass
class CloneOpportunity:
    """A feature worth cloning from competitor."""
    competitor: str
    feature_name: str
    detected_date: str
    priority: str  # high, medium, low
    description: str
    estimated_effort: str  # days
    strategic_value: str

    def to_dict(self) -> Dict:
        return asdict(self)


class CompetitorIntel:
    """
    Competitor Intelligence System.

    Monitors competitors using telemetry-free sources:
    - SearxNG for web search
    - Direct scraping for specific pages
    - RSS feeds for updates
    - HackerNews/ProductHunt for launches

    Reports to War Room and AI Coordinator.
    """

    # Default competitors (from NETWORKED_AI_TRINITY.md)
    DEFAULT_COMPETITORS = [
        CompetitorProfile(
            name="Notion",
            website="https://www.notion.so",
            threat_level=ThreatLevel.HIGH,
            pricing_info={"tier": "$10-20/user/month"},
            funding_status="Series C ($2B valuation)",
            recent_features=["AI writing", "Collaborative editing"]
        ),
        CompetitorProfile(
            name="Mem",
            website="https://get.mem.ai",
            threat_level=ThreatLevel.MEDIUM,
            pricing_info={"tier": "$10-15/user/month"},
            funding_status="Series A ($60M raised)",
            recent_features=["AI memory", "Smart search"]
        ),
        CompetitorProfile(
            name="Reflect",
            website="https://reflect.app",
            threat_level=ThreatLevel.MEDIUM,
            pricing_info={"tier": "$10/month"},
            funding_status="Seed",
            recent_features=["Backlinks", "Daily notes"]
        ),
        CompetitorProfile(
            name="Obsidian",
            website="https://obsidian.md",
            threat_level=ThreatLevel.MEDIUM,
            pricing_info={"tier": "Free / $8 sync"},
            funding_status="Bootstrapped",
            recent_features=["Local-first", "Plugin ecosystem"]
        )
    ]

    def __init__(
        self,
        searxng_url: str = "http://localhost:8080",
        competitors: Optional[List[CompetitorProfile]] = None
    ):
        """
        Initialize competitor intelligence.

        Args:
            searxng_url: URL to self-hosted SearxNG instance
            competitors: List of competitors to monitor
        """
        self.searxng_url = searxng_url
        self.competitors = competitors or self.DEFAULT_COMPETITORS.copy()

        # Clone opportunities queue
        self.clone_queue: List[CloneOpportunity] = []

        # Intel history
        self._intel_history: List[Dict[str, Any]] = []

        # Feature keywords to watch
        self.watch_keywords = [
            "new feature", "launch", "update", "pricing",
            "ai", "collaboration", "integration", "api"
        ]

    async def monitor_all(self) -> Dict[str, Any]:
        """
        Run full competitor monitoring cycle.

        Returns:
            Complete intel report
        """
        timestamp = datetime.now().isoformat()
        results = {}

        for competitor in self.competitors:
            try:
                intel = await self._monitor_competitor(competitor)
                results[competitor.name] = intel
                competitor.last_checked = timestamp
            except Exception as e:
                logger.error(f"Error monitoring {competitor.name}: {e}")
                results[competitor.name] = {"error": str(e)}

        # Identify clone opportunities
        opportunities = self._identify_clone_opportunities(results)

        report = {
            "timestamp": timestamp,
            "competitors": results,
            "clone_opportunities": [o.to_dict() for o in opportunities],
            "threat_summary": self._generate_threat_summary()
        }

        self._intel_history.append(report)
        return report

    async def _monitor_competitor(
        self,
        competitor: CompetitorProfile
    ) -> Dict[str, Any]:
        """
        Monitor a single competitor.

        Uses telemetry-free methods:
        1. Direct website scraping (changelog, blog, pricing)
        2. SearxNG search for news
        3. RSS feeds if available
        """
        intel = {
            "name": competitor.name,
            "website": competitor.website,
            "checked_at": datetime.now().isoformat()
        }

        # Method 1: Direct page monitoring (mock for MVP)
        # In production: requests + BeautifulSoup
        intel["direct_check"] = await self._check_direct_pages(competitor)

        # Method 2: SearxNG search (mock for MVP)
        # In production: query self-hosted SearxNG
        intel["search_results"] = await self._search_competitor(competitor)

        # Method 3: RSS/News feeds (mock for MVP)
        intel["news"] = await self._check_news_feeds(competitor)

        # Analyze for changes
        intel["changes_detected"] = self._detect_changes(competitor, intel)

        return intel

    async def _check_direct_pages(
        self,
        competitor: CompetitorProfile
    ) -> Dict[str, Any]:
        """
        Check competitor's key pages directly.

        Pages to monitor:
        - Changelog/releases
        - Blog
        - Pricing page
        - Feature page
        """
        # URLs to check (production would actually scrape these)
        target_pages = {
            "changelog": f"{competitor.website}/changelog",
            "blog": f"{competitor.website}/blog",
            "pricing": f"{competitor.website}/pricing"
        }

        results = {}
        for page_type, url in target_pages.items():
            # Mock response (production: actual HTTP request)
            results[page_type] = {
                "url": url,
                "status": "mock_success",
                "last_modified": datetime.now().isoformat()
            }

        return results

    async def _search_competitor(
        self,
        competitor: CompetitorProfile
    ) -> List[Dict[str, str]]:
        """
        Search for competitor news via SearxNG.

        Telemetry-free: Uses self-hosted SearxNG instance.
        """
        # Mock search results (production: query SearxNG API)
        # SearxNG API: GET /search?q=query&format=json

        query = f"{competitor.name} new features {datetime.now().year}"

        # Mock results - production would call SearxNG
        mock_results = [
            {
                "title": f"{competitor.name} launches new AI features",
                "url": f"https://techcrunch.com/{competitor.name.lower()}-ai",
                "snippet": f"{competitor.name} announced new AI-powered features today...",
                "source": "TechCrunch"
            },
            {
                "title": f"{competitor.name} product update",
                "url": f"{competitor.website}/blog/update",
                "snippet": "We're excited to announce several new features...",
                "source": competitor.website
            }
        ]

        return mock_results

    async def _check_news_feeds(
        self,
        competitor: CompetitorProfile
    ) -> List[Dict[str, str]]:
        """
        Check RSS/news feeds for competitor mentions.

        Sources (telemetry-free):
        - HackerNews API (public)
        - ProductHunt RSS
        - TechCrunch RSS
        """
        # Mock news feed results
        # Production: feedparser + requests

        mock_news = [
            {
                "title": f"Discussion: {competitor.name} vs alternatives",
                "url": "https://news.ycombinator.com/item?id=12345",
                "source": "HackerNews",
                "date": datetime.now().isoformat()
            }
        ]

        return mock_news

    def _detect_changes(
        self,
        competitor: CompetitorProfile,
        intel: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Detect significant changes from competitor.

        Returns list of detected changes.
        """
        changes = []

        # In production: compare with previous intel
        # For MVP: flag mock changes

        # Check search results for keywords
        for result in intel.get("search_results", []):
            title = result.get("title", "").lower()
            for keyword in self.watch_keywords:
                if keyword in title:
                    changes.append({
                        "type": "news",
                        "keyword": keyword,
                        "title": result["title"],
                        "url": result["url"]
                    })
                    break

        return changes

    def _identify_clone_opportunities(
        self,
        intel_results: Dict[str, Any]
    ) -> List[CloneOpportunity]:
        """
        Identify features worth cloning.

        Criteria:
        - New feature announcement
        - High engagement/buzz
        - Fits Genre's roadmap
        - Technically feasible
        """
        opportunities = []

        for competitor_name, intel in intel_results.items():
            if isinstance(intel, dict) and "error" not in intel:
                changes = intel.get("changes_detected", [])

                for change in changes:
                    if "new feature" in change.get("keyword", ""):
                        opportunity = CloneOpportunity(
                            competitor=competitor_name,
                            feature_name=change["title"][:50],
                            detected_date=datetime.now().isoformat(),
                            priority="high" if "ai" in change["title"].lower() else "medium",
                            description=f"Clone opportunity from {competitor_name}",
                            estimated_effort="1-3 days",
                            strategic_value="Competitive parity"
                        )
                        opportunities.append(opportunity)

        self.clone_queue.extend(opportunities)
        return opportunities

    def _generate_threat_summary(self) -> Dict[str, Any]:
        """Generate overall threat assessment."""
        high_threats = [c for c in self.competitors if c.threat_level == ThreatLevel.HIGH]
        medium_threats = [c for c in self.competitors if c.threat_level == ThreatLevel.MEDIUM]

        return {
            "high_threats": [c.name for c in high_threats],
            "medium_threats": [c.name for c in medium_threats],
            "clone_queue_size": len(self.clone_queue),
            "recommendation": self._generate_recommendation()
        }

    def _generate_recommendation(self) -> str:
        """Generate strategic recommendation."""
        if self.clone_queue:
            top = self.clone_queue[0]
            return f"Priority: Clone {top.feature_name} from {top.competitor}"
        return "Continue monitoring. No immediate clone opportunities."

    def get_competitor_profiles(self) -> List[Dict[str, Any]]:
        """Get all competitor profiles."""
        return [c.to_dict() for c in self.competitors]

    def get_clone_queue(self) -> List[Dict[str, Any]]:
        """Get current clone opportunity queue."""
        return [c.to_dict() for c in self.clone_queue]

    def update_threat_level(
        self,
        competitor_name: str,
        level: ThreatLevel
    ) -> bool:
        """
        Update a competitor's threat level.

        Args:
            competitor_name: Name of competitor
            level: New threat level

        Returns:
            True if updated, False if competitor not found
        """
        for competitor in self.competitors:
            if competitor.name.lower() == competitor_name.lower():
                competitor.threat_level = level
                logger.info(f"Updated {competitor_name} threat level to {level.value}")
                return True
        return False

    def add_competitor(self, profile: CompetitorProfile) -> None:
        """Add a new competitor to monitor."""
        self.competitors.append(profile)
        logger.info(f"Added competitor: {profile.name}")

    def get_intel_report(self) -> Dict[str, Any]:
        """
        Get comprehensive intel report for War Room.

        Returns:
            Complete competitor intelligence report
        """
        return {
            "timestamp": datetime.now().isoformat(),
            "competitors": self.get_competitor_profiles(),
            "clone_queue": self.get_clone_queue(),
            "threat_summary": self._generate_threat_summary(),
            "recent_intel": self._intel_history[-5:] if self._intel_history else []
        }
