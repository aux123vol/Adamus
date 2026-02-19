"""
Adamus War Room

Daily steering system for Genre.
Augustus's HUD showing:
- Internal Vitals (Genre + Adamus health)
- External Radar (competitors, threats)
- Strategic Horizon (unicorn/monopoly indices)

"Fighter jet cockpit - see everything at once"
"""

from .metrics import MetricsCollector, InternalMetrics, AdamusMetrics
from .alerts import AlertSystem, Alert, AlertSeverity
from .dashboard import create_app

__all__ = [
    'MetricsCollector',
    'InternalMetrics',
    'AdamusMetrics',
    'AlertSystem',
    'Alert',
    'AlertSeverity',
    'create_app'
]
