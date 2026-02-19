"""
Content Generation

AI-powered content creation for:
- Blog posts
- Social media posts
- Video scripts
- Email newsletters

From NETWORKED_AI_TRINITY.md:
- AI SEO Swarms: 1000+ pages/week
- Auto clips, memes, trailers, explainers
- Coordinate with Business AI for distribution
"""

import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional, Any
from enum import Enum

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Types of content to generate."""
    BLOG_POST = "blog_post"
    SOCIAL_POST = "social_post"
    VIDEO_SCRIPT = "video_script"
    EMAIL = "email"
    LANDING_PAGE = "landing_page"
    AD_COPY = "ad_copy"


class ContentFormat(Enum):
    """Content format specifications."""
    SHORT = "short"  # < 280 chars (Twitter)
    MEDIUM = "medium"  # 500-1000 words
    LONG = "long"  # 1500+ words (SEO)
    THREAD = "thread"  # Multi-part (Twitter thread)


class ContentTone(Enum):
    """Tone of content."""
    PROFESSIONAL = "professional"
    CASUAL = "casual"
    INSPIRATIONAL = "inspirational"
    EDUCATIONAL = "educational"
    PROMOTIONAL = "promotional"


@dataclass
class ContentPiece:
    """A single piece of generated content."""
    id: str
    content_type: ContentType
    format: ContentFormat
    tone: ContentTone
    title: str
    body: str
    keywords: List[str]
    cta: Optional[str]  # Call to action
    generated_at: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["content_type"] = self.content_type.value
        result["format"] = self.format.value
        result["tone"] = self.tone.value
        return result


@dataclass
class ContentBrief:
    """Brief for content generation."""
    topic: str
    content_type: ContentType
    format: ContentFormat
    tone: ContentTone
    keywords: List[str]
    target_audience: str
    goal: str  # e.g., "drive signups", "educate", "engage"
    additional_context: str = ""

    def to_dict(self) -> Dict:
        result = asdict(self)
        result["content_type"] = self.content_type.value
        result["format"] = self.format.value
        result["tone"] = self.tone.value
        return result


class ContentGenerator:
    """
    AI Content Generation System.

    From NETWORKED_AI_TRINITY.md:
    - Generate 1000+ pages/week (SEO swarms)
    - Deploy across niches
    - Track which content drives signups
    - Coordinate with Business AI for distribution

    For MVP: Uses templates and mock generation.
    Production: Would integrate with Claude API.
    """

    # Content templates for MVP
    TEMPLATES = {
        ContentType.BLOG_POST: {
            ContentTone.EDUCATIONAL: """# {title}

{intro}

## Understanding {topic}

{body}

## Key Takeaways

{takeaways}

## Conclusion

{conclusion}

{cta}
""",
            ContentTone.PROMOTIONAL: """# {title}

{hook}

## Why {topic} Matters

{body}

## Start Today

{cta}
"""
        },
        ContentType.SOCIAL_POST: {
            ContentTone.CASUAL: "{hook}\n\n{point}\n\n{cta}",
            ContentTone.INSPIRATIONAL: "✨ {hook}\n\n{body}\n\n👉 {cta}"
        }
    }

    def __init__(
        self,
        claude_client=None,
        default_tone: ContentTone = ContentTone.EDUCATIONAL
    ):
        """
        Initialize content generator.

        Args:
            claude_client: Claude API client (optional for MVP)
            default_tone: Default content tone
        """
        self.claude_client = claude_client
        self.default_tone = default_tone

        # Content generation stats
        self._generated_count = 0
        self._generation_history: List[ContentPiece] = []

    async def generate_content(
        self,
        brief: ContentBrief
    ) -> ContentPiece:
        """
        Generate a single piece of content.

        Args:
            brief: Content brief with requirements

        Returns:
            Generated content piece
        """
        logger.info(f"Generating {brief.content_type.value}: {brief.topic}")

        # Generate content ID
        self._generated_count += 1
        content_id = f"content_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._generated_count}"

        # Generate content based on type
        if self.claude_client:
            # Production: Use Claude API
            body = await self._generate_with_claude(brief)
        else:
            # MVP: Use templates
            body = self._generate_from_template(brief)

        # Create title
        title = self._generate_title(brief)

        # Create CTA
        cta = self._generate_cta(brief)

        content = ContentPiece(
            id=content_id,
            content_type=brief.content_type,
            format=brief.format,
            tone=brief.tone,
            title=title,
            body=body,
            keywords=brief.keywords,
            cta=cta,
            generated_at=datetime.now().isoformat(),
            metadata={
                "topic": brief.topic,
                "target_audience": brief.target_audience,
                "goal": brief.goal
            }
        )

        self._generation_history.append(content)
        return content

    async def generate_content_cluster(
        self,
        topic: str,
        count: int = 10,
        types: Optional[List[ContentType]] = None
    ) -> List[ContentPiece]:
        """
        Generate a cluster of related content pieces.

        From NETWORKED_AI_TRINITY.md: Generate 50 content pieces per trend.

        Args:
            topic: Central topic
            count: Number of pieces to generate
            types: Content types to include

        Returns:
            List of generated content pieces
        """
        if types is None:
            types = [
                ContentType.BLOG_POST,
                ContentType.SOCIAL_POST,
                ContentType.EMAIL
            ]

        logger.info(f"Generating content cluster: {count} pieces on '{topic}'")

        pieces = []
        for i in range(count):
            content_type = types[i % len(types)]
            format_choice = (
                ContentFormat.LONG if content_type == ContentType.BLOG_POST
                else ContentFormat.SHORT
            )

            brief = ContentBrief(
                topic=f"{topic} - Angle {i + 1}",
                content_type=content_type,
                format=format_choice,
                tone=self.default_tone,
                keywords=[topic.lower(), "genre", "ai writing"],
                target_audience="creative writers",
                goal="drive signups"
            )

            content = await self.generate_content(brief)
            pieces.append(content)

        return pieces

    def _generate_from_template(self, brief: ContentBrief) -> str:
        """Generate content from templates (MVP approach)."""
        # Get template
        type_templates = self.TEMPLATES.get(brief.content_type, {})
        template = type_templates.get(
            brief.tone,
            type_templates.get(ContentTone.EDUCATIONAL, "{body}")
        )

        # Fill template with generated content
        content_parts = self._generate_content_parts(brief)

        try:
            return template.format(**content_parts)
        except KeyError:
            # Fallback to simple body
            return content_parts.get("body", f"Content about {brief.topic}")

    def _generate_content_parts(self, brief: ContentBrief) -> Dict[str, str]:
        """Generate content parts for template filling."""
        topic = brief.topic

        return {
            "title": self._generate_title(brief),
            "topic": topic,
            "hook": f"Discover the power of {topic}",
            "intro": f"In this article, we explore {topic} and how it can transform your creative workflow.",
            "body": f"""
{topic} is revolutionizing how creators work. With AI-powered tools like Genre,
you can streamline your creative process while maintaining your unique voice.

Here's what makes {topic} so powerful:

1. **Efficiency**: Complete tasks in half the time
2. **Quality**: AI assists without compromising creativity
3. **Consistency**: Maintain your style across all content

Genre helps you leverage {topic} effectively, giving you more time
to focus on what matters most: your creative vision.
""".strip(),
            "takeaways": f"""
- {topic} is changing the creative landscape
- AI tools can enhance (not replace) creativity
- Genre makes {topic} accessible to all creators
""".strip(),
            "conclusion": f"Ready to experience the power of {topic}? Start with Genre today.",
            "point": f"Here's one thing most people miss about {topic}...",
            "cta": self._generate_cta(brief)
        }

    def _generate_title(self, brief: ContentBrief) -> str:
        """Generate engaging title."""
        templates = {
            ContentType.BLOG_POST: [
                f"The Complete Guide to {brief.topic}",
                f"How {brief.topic} is Changing Creative Writing",
                f"5 Ways to Master {brief.topic} Today"
            ],
            ContentType.SOCIAL_POST: [
                f"✨ {brief.topic}",
                f"Unlock {brief.topic}"
            ],
            ContentType.EMAIL: [
                f"[Genre] {brief.topic}: What You Need to Know",
                f"Your {brief.topic} Journey Starts Here"
            ]
        }

        type_templates = templates.get(brief.content_type, [f"{brief.topic}"])
        return type_templates[self._generated_count % len(type_templates)]

    def _generate_cta(self, brief: ContentBrief) -> str:
        """Generate call to action based on goal."""
        ctas = {
            "drive signups": "Start your free trial at genre.app →",
            "educate": "Learn more about Genre →",
            "engage": "What's your experience? Share in the comments! 👇"
        }
        return ctas.get(brief.goal, "Try Genre today →")

    async def _generate_with_claude(self, brief: ContentBrief) -> str:
        """Generate content using Claude API (production)."""
        # Would call Claude API here
        # For MVP, fall back to template
        return self._generate_from_template(brief)

    def get_generation_stats(self) -> Dict[str, Any]:
        """Get content generation statistics."""
        type_counts = {}
        for content in self._generation_history:
            type_name = content.content_type.value
            type_counts[type_name] = type_counts.get(type_name, 0) + 1

        return {
            "total_generated": self._generated_count,
            "by_type": type_counts,
            "recent_topics": [
                c.metadata.get("topic", "")
                for c in self._generation_history[-10:]
            ]
        }

    def get_recent_content(self, count: int = 10) -> List[Dict]:
        """Get recently generated content."""
        return [c.to_dict() for c in self._generation_history[-count:]]
