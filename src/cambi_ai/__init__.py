"""
CAMBI AI Agent

Part of the Networked AI Trinity.
Handles community, audience, marketing, branding, and innovation.

Connects to:
- War Room (reports community health)
- AI Coordinator (receives/sends tasks)
- Business AI (content distribution)
- Tech AI (Play Lab → Rails pipeline)
"""

from .sentiment import SentimentAnalyzer, CommunityPulse
from .content_gen import ContentGenerator, ContentPiece
from .trends import TrendDetector, TrendSignal
from .cambi_agent import CAMBI_AI

__all__ = [
    'CAMBI_AI',
    'SentimentAnalyzer',
    'CommunityPulse',
    'ContentGenerator',
    'ContentPiece',
    'TrendDetector',
    'TrendSignal'
]
