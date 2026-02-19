"""
Tests for CAMBI AI components.

CAMBI AI handles:
- Community: Sentiment, engagement, Asabiyyah
- Audience: Believer pipeline, retention
- Marketing: Content swarms, SEO, video
- Branding: Positioning, archetypes
- Innovation: Play Lab → Rails pipeline
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch


# ─────────────────────────────────────────────────────────────────────────────
# Sentiment Module
# ─────────────────────────────────────────────────────────────────────────────

class TestSentimentDataclasses:
    def test_sentiment_level_enum_values(self):
        from src.cambi_ai.sentiment import SentimentLevel
        assert SentimentLevel.VERY_NEGATIVE.value == "very_negative"
        assert SentimentLevel.POSITIVE.value == "positive"
        assert SentimentLevel.NEUTRAL.value == "neutral"

    def test_platform_enum_values(self):
        from src.cambi_ai.sentiment import Platform
        assert Platform.DISCORD.value == "discord"
        assert Platform.HACKER_NEWS.value == "hacker_news"

    def test_sentiment_data_to_dict(self):
        from src.cambi_ai.sentiment import SentimentData, Platform
        data = SentimentData(
            platform=Platform.DISCORD,
            content="Love this app!",
            sentiment_score=0.9,
            engagement=42,
            timestamp=datetime.now().isoformat()
        )
        d = data.to_dict()
        assert d["platform"] == "discord"
        assert d["sentiment_score"] == 0.9
        assert d["engagement"] == 42

    def test_community_pulse_is_healthy(self):
        from src.cambi_ai.sentiment import CommunityPulse, SentimentLevel, Platform, PlatformPulse
        pulse = CommunityPulse(
            timestamp=datetime.now().isoformat(),
            overall_sentiment=0.75,
            overall_level=SentimentLevel.POSITIVE,
            engagement_score=70.0,
            asabiyyah_score=80.0,
            churn_risk=10.0,
            platform_data={},
            alerts=[]
        )
        assert pulse.is_healthy is True

    def test_community_pulse_is_not_healthy_low_sentiment(self):
        from src.cambi_ai.sentiment import CommunityPulse, SentimentLevel
        pulse = CommunityPulse(
            timestamp=datetime.now().isoformat(),
            overall_sentiment=0.3,
            overall_level=SentimentLevel.NEGATIVE,
            engagement_score=20.0,
            asabiyyah_score=30.0,
            churn_risk=10.0,
            platform_data={},
            alerts=[]
        )
        assert pulse.is_healthy is False

    def test_community_pulse_is_not_healthy_high_churn(self):
        from src.cambi_ai.sentiment import CommunityPulse, SentimentLevel
        pulse = CommunityPulse(
            timestamp=datetime.now().isoformat(),
            overall_sentiment=0.8,
            overall_level=SentimentLevel.POSITIVE,
            engagement_score=70.0,
            asabiyyah_score=80.0,
            churn_risk=50.0,  # > 30 threshold
            platform_data={},
            alerts=[]
        )
        assert pulse.is_healthy is False

    def test_community_pulse_to_dict(self):
        from src.cambi_ai.sentiment import CommunityPulse, SentimentLevel
        pulse = CommunityPulse(
            timestamp=datetime.now().isoformat(),
            overall_sentiment=0.7,
            overall_level=SentimentLevel.POSITIVE,
            engagement_score=60.0,
            asabiyyah_score=70.0,
            churn_risk=15.0,
            platform_data={},
            alerts=[]
        )
        d = pulse.to_dict()
        assert d["overall_sentiment"] == 0.7
        assert d["overall_level"] == "positive"
        assert "platforms" in d


class TestSentimentAnalyzer:
    def test_initialization(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        assert analyzer.sentiment_warning_threshold == 0.5
        assert analyzer.churn_warning_threshold == 20

    def test_analyze_text_positive(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        score = analyzer.analyze_text("This is amazing and love it!")
        assert score > 0

    def test_analyze_text_negative(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        score = analyzer.analyze_text("This is terrible and broken and frustrating")
        assert score < 0

    def test_analyze_text_neutral(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        score = analyzer.analyze_text("The weather today is fine")
        assert -0.5 <= score <= 0.5

    @pytest.mark.asyncio
    async def test_get_community_pulse_returns_pulse(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer, CommunityPulse
        analyzer = SentimentAnalyzer()
        pulse = await analyzer.get_community_pulse()
        assert isinstance(pulse, CommunityPulse)
        assert -1.0 <= pulse.overall_sentiment <= 1.0
        assert 0 <= pulse.churn_risk <= 100
        assert 0 <= pulse.asabiyyah_score <= 100

    @pytest.mark.asyncio
    async def test_get_community_pulse_has_platform_data(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        pulse = await analyzer.get_community_pulse()
        assert len(pulse.platform_data) > 0

    @pytest.mark.asyncio
    async def test_get_community_pulse_has_timestamp(self):
        from src.cambi_ai.sentiment import SentimentAnalyzer
        analyzer = SentimentAnalyzer()
        pulse = await analyzer.get_community_pulse()
        assert pulse.timestamp is not None
        # Should be parseable ISO timestamp
        datetime.fromisoformat(pulse.timestamp)


# ─────────────────────────────────────────────────────────────────────────────
# Content Generation Module
# ─────────────────────────────────────────────────────────────────────────────

class TestContentDataclasses:
    def test_content_type_enum(self):
        from src.cambi_ai.content_gen import ContentType
        assert ContentType.BLOG_POST.value == "blog_post"
        assert ContentType.SOCIAL_POST.value == "social_post"

    def test_content_format_enum(self):
        from src.cambi_ai.content_gen import ContentFormat
        assert ContentFormat.SHORT.value == "short"
        assert ContentFormat.LONG.value == "long"

    def test_content_tone_enum(self):
        from src.cambi_ai.content_gen import ContentTone
        assert ContentTone.EDUCATIONAL.value == "educational"
        assert ContentTone.PROMOTIONAL.value == "promotional"

    def test_content_piece_to_dict(self):
        from src.cambi_ai.content_gen import ContentPiece, ContentType, ContentFormat, ContentTone
        piece = ContentPiece(
            id="test-1",
            content_type=ContentType.BLOG_POST,
            format=ContentFormat.MEDIUM,
            tone=ContentTone.EDUCATIONAL,
            title="Test Post",
            body="Body content here",
            keywords=["ai", "writing"],
            cta="Sign up now",
            generated_at=datetime.now().isoformat()
        )
        d = piece.to_dict()
        assert d["content_type"] == "blog_post"
        assert d["format"] == "medium"
        assert d["tone"] == "educational"
        assert d["title"] == "Test Post"

    def test_content_brief_to_dict(self):
        from src.cambi_ai.content_gen import ContentBrief, ContentType, ContentFormat, ContentTone
        brief = ContentBrief(
            topic="AI Writing",
            content_type=ContentType.SOCIAL_POST,
            format=ContentFormat.SHORT,
            tone=ContentTone.CASUAL,
            keywords=["ai"],
            target_audience="writers",
            goal="drive signups"
        )
        d = brief.to_dict()
        assert d["topic"] == "AI Writing"
        assert d["content_type"] == "social_post"


class TestContentGenerator:
    def test_initialization(self):
        from src.cambi_ai.content_gen import ContentGenerator, ContentTone
        gen = ContentGenerator()
        assert gen.default_tone == ContentTone.EDUCATIONAL
        assert gen._generated_count == 0

    @pytest.mark.asyncio
    async def test_generate_content_returns_piece(self):
        from src.cambi_ai.content_gen import (
            ContentGenerator, ContentBrief, ContentPiece,
            ContentType, ContentFormat, ContentTone
        )
        gen = ContentGenerator()
        brief = ContentBrief(
            topic="AI writing tools",
            content_type=ContentType.BLOG_POST,
            format=ContentFormat.MEDIUM,
            tone=ContentTone.EDUCATIONAL,
            keywords=["ai", "writing"],
            target_audience="writers",
            goal="educate"
        )
        piece = await gen.generate_content(brief)
        assert isinstance(piece, ContentPiece)
        assert piece.title
        assert piece.body
        assert piece.content_type == ContentType.BLOG_POST

    @pytest.mark.asyncio
    async def test_generate_content_increments_count(self):
        from src.cambi_ai.content_gen import (
            ContentGenerator, ContentBrief, ContentType, ContentFormat, ContentTone
        )
        gen = ContentGenerator()
        brief = ContentBrief(
            topic="Productivity",
            content_type=ContentType.SOCIAL_POST,
            format=ContentFormat.SHORT,
            tone=ContentTone.CASUAL,
            keywords=["productivity"],
            target_audience="professionals",
            goal="engage"
        )
        await gen.generate_content(brief)
        assert gen._generated_count == 1

    @pytest.mark.asyncio
    async def test_generate_content_cluster_returns_list(self):
        from src.cambi_ai.content_gen import ContentGenerator, ContentPiece
        gen = ContentGenerator()
        pieces = await gen.generate_content_cluster(topic="Note taking", count=3)
        assert isinstance(pieces, list)
        assert len(pieces) == 3
        assert all(isinstance(p, ContentPiece) for p in pieces)

    def test_get_generation_stats(self):
        from src.cambi_ai.content_gen import ContentGenerator
        gen = ContentGenerator()
        stats = gen.get_generation_stats()
        assert "total_generated" in stats
        assert "by_type" in stats

    def test_get_recent_content_empty(self):
        from src.cambi_ai.content_gen import ContentGenerator
        gen = ContentGenerator()
        recent = gen.get_recent_content(5)
        assert isinstance(recent, list)


# ─────────────────────────────────────────────────────────────────────────────
# Trend Detection Module
# ─────────────────────────────────────────────────────────────────────────────

class TestTrendDataclasses:
    def test_trend_source_enum(self):
        from src.cambi_ai.trends import TrendSource
        assert TrendSource.HACKER_NEWS.value == "hacker_news"
        assert TrendSource.PRODUCT_HUNT.value == "product_hunt"

    def test_trend_category_enum(self):
        from src.cambi_ai.trends import TrendCategory
        assert TrendCategory.AI_TOOLS.value == "ai_tools"
        assert TrendCategory.CREATIVE_WRITING.value == "creative_writing"

    def test_trend_signal_to_dict(self):
        from src.cambi_ai.trends import TrendSignal, TrendSource, TrendCategory
        signal = TrendSignal(
            id="sig-1",
            source=TrendSource.HACKER_NEWS,
            category=TrendCategory.AI_TOOLS,
            title="AI writing tool hits 1M users",
            url="https://hn.example.com/1",
            score=350,
            comments=120,
            detected_at=datetime.now().isoformat(),
            relevance_score=0.85
        )
        d = signal.to_dict()
        assert d["source"] == "hacker_news"
        assert d["category"] == "ai_tools"
        assert d["relevance_score"] == 0.85

    def test_trend_report_to_dict(self):
        from src.cambi_ai.trends import TrendReport, TrendSignal, TrendSource, TrendCategory
        report = TrendReport(
            timestamp=datetime.now().isoformat(),
            top_trends=[],
            by_category={},
            by_source={},
            opportunities=[],
            recommendations=["Focus on AI tools content"]
        )
        d = report.to_dict()
        assert "timestamp" in d
        assert "top_trends" in d
        assert "recommendations" in d


class TestTrendDetector:
    def test_initialization(self):
        from src.cambi_ai.trends import TrendDetector
        detector = TrendDetector()
        assert detector.searxng_url == "http://localhost:8080"
        assert detector._signal_counter == 0

    def test_custom_searxng_url(self):
        from src.cambi_ai.trends import TrendDetector
        detector = TrendDetector(searxng_url="http://search.local:9090")
        assert detector.searxng_url == "http://search.local:9090"

    @pytest.mark.asyncio
    async def test_detect_trends_returns_report(self):
        from src.cambi_ai.trends import TrendDetector, TrendReport
        detector = TrendDetector()
        report = await detector.detect_trends()
        assert isinstance(report, TrendReport)
        assert report.timestamp is not None

    @pytest.mark.asyncio
    async def test_detect_trends_has_recommendations(self):
        from src.cambi_ai.trends import TrendDetector
        detector = TrendDetector()
        report = await detector.detect_trends()
        assert isinstance(report.recommendations, list)

    @pytest.mark.asyncio
    async def test_detect_trends_stores_history(self):
        from src.cambi_ai.trends import TrendDetector
        detector = TrendDetector()
        await detector.detect_trends()
        assert len(detector._trend_history) == 1

    def test_get_trending_topics_returns_list(self):
        from src.cambi_ai.trends import TrendDetector
        detector = TrendDetector()
        topics = detector.get_trending_topics(5)
        assert isinstance(topics, list)

    def test_get_trend_report_empty_initially(self):
        from src.cambi_ai.trends import TrendDetector
        detector = TrendDetector()
        report = detector.get_trend_report()
        assert isinstance(report, dict)


# ─────────────────────────────────────────────────────────────────────────────
# CAMBI AI Agent
# ─────────────────────────────────────────────────────────────────────────────

class TestCAMBIAIInit:
    def test_initialization(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        assert cambi._initialized is False
        assert cambi.searxng_url == "http://localhost:8080"

    def test_components_initialized(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        from src.cambi_ai.sentiment import SentimentAnalyzer
        from src.cambi_ai.content_gen import ContentGenerator
        from src.cambi_ai.trends import TrendDetector
        cambi = CAMBI_AI()
        assert isinstance(cambi.sentiment, SentimentAnalyzer)
        assert isinstance(cambi.content, ContentGenerator)
        assert isinstance(cambi.trends, TrendDetector)

    def test_custom_searxng_url(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI(searxng_url="http://search.local:9090")
        assert cambi.searxng_url == "http://search.local:9090"
        assert cambi.trends.searxng_url == "http://search.local:9090"

    @pytest.mark.asyncio
    async def test_initialize_returns_true(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        result = await cambi.initialize()
        assert result is True
        assert cambi._initialized is True


class TestCAMBIAICommunityPulse:
    @pytest.mark.asyncio
    async def test_community_pulse_returns_pulse(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        from src.cambi_ai.sentiment import CommunityPulse
        cambi = CAMBI_AI()
        pulse = await cambi.community_pulse()
        assert isinstance(pulse, CommunityPulse)

    @pytest.mark.asyncio
    async def test_community_pulse_updates_timestamp(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        assert cambi._last_community_pulse is None
        await cambi.community_pulse()
        assert cambi._last_community_pulse is not None

    @pytest.mark.asyncio
    async def test_community_pulse_no_war_room_no_crash(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI(war_room=None)
        pulse = await cambi.community_pulse()
        assert pulse is not None


class TestCAMBIAIContentSwarm:
    @pytest.mark.asyncio
    async def test_content_swarm_returns_list(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        from src.cambi_ai.content_gen import ContentPiece
        cambi = CAMBI_AI()
        pieces = await cambi.content_swarm_generation(topic="AI tools", count=3)
        assert isinstance(pieces, list)
        assert len(pieces) == 3
        assert all(isinstance(p, ContentPiece) for p in pieces)

    @pytest.mark.asyncio
    async def test_content_swarm_auto_detects_topic(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        # No topic — should auto-detect from trends
        pieces = await cambi.content_swarm_generation(topic=None, count=2)
        assert len(pieces) == 2

    @pytest.mark.asyncio
    async def test_content_swarm_no_coordinator_no_crash(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI(coordinator=None)
        pieces = await cambi.content_swarm_generation(topic="Writing", count=2)
        assert pieces is not None


class TestCAMBIAIABTesting:
    @pytest.mark.asyncio
    async def test_ab_test_returns_results(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        experiment = {
            "name": "Messaging test",
            "variant_a": "World Founders",
            "variant_b": "Creative Rebels"
        }
        results = await cambi.ab_test_cultural_signals(experiment)
        assert "experiment_id" in results
        assert "winner" in results
        assert "confidence" in results

    @pytest.mark.asyncio
    async def test_ab_test_records_experiment(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        await cambi.ab_test_cultural_signals({"name": "Test"})
        assert len(cambi._active_experiments) == 1

    @pytest.mark.asyncio
    async def test_ab_test_stores_results(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        await cambi.ab_test_cultural_signals({"name": "Test"})
        assert len(cambi._experiment_results) == 1


class TestCAMBIAIPlayLab:
    @pytest.mark.asyncio
    async def test_translate_play_lab_returns_spec(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        play_session = {
            "description": "Built a tower with blocks representing user flow",
            "photos": [],
            "notes": "Three blocks = three steps in onboarding"
        }
        spec = await cambi.translate_play_lab_to_rails(play_session)
        assert isinstance(spec, dict)
        assert "type" in spec or "features" in spec or "spec" in spec

    @pytest.mark.asyncio
    async def test_translate_play_lab_no_coordinator_no_crash(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI(coordinator=None)
        spec = await cambi.translate_play_lab_to_rails({"description": "test"})
        assert spec is not None


class TestCAMBIAIStatus:
    def test_get_status_returns_dict(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        status = cambi.get_status()
        assert isinstance(status, dict)

    def test_get_status_has_required_keys(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        status = cambi.get_status()
        assert "initialized" in status

    def test_suggest_experiments_returns_list(self):
        from src.cambi_ai.cambi_agent import CAMBI_AI
        cambi = CAMBI_AI()
        experiments = cambi.suggest_experiments()
        assert isinstance(experiments, list)
