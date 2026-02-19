"""
Business AI Agent

Part of the Networked AI Trinity.
Handles survival metrics: MRR, burn, runway, competitor monitoring.

Connects to:
- War Room (reports metrics)
- AI Coordinator (receives/sends tasks)
- SearxNG (telemetry-free search)
"""

from .finance_tracker import FinanceTracker, FinanceMetrics
from .competitor_intel import CompetitorIntel, CompetitorProfile
from .business_agent import BusinessAI

__all__ = [
    'BusinessAI',
    'FinanceTracker',
    'FinanceMetrics',
    'CompetitorIntel',
    'CompetitorProfile'
]
