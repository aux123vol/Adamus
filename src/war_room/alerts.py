"""
War Room Alert System

Monitors metrics against thresholds and generates alerts.

Severity Levels:
- CRITICAL: Immediate action required (red)
- WARNING: Monitor closely (yellow)
- INFO: Good to know (blue)

Alert Categories:
- survival: Cash, burn, runway
- pmf: Users, MRR, churn
- technical: Errors, uptime, security
- competitor: New features, funding
"""

import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Callable, Any
from enum import Enum

from .metrics import InternalMetrics, ExternalMetrics

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"  # Red - immediate action
    WARNING = "warning"    # Yellow - monitor closely
    INFO = "info"          # Blue - good to know


class AlertCategory(Enum):
    """Alert categories."""
    SURVIVAL = "survival"
    PMF = "pmf"
    TECHNICAL = "technical"
    COMPETITOR = "competitor"
    ADAMUS = "adamus"


@dataclass
class Alert:
    """A single alert."""
    id: str
    timestamp: str
    severity: AlertSeverity
    category: AlertCategory
    title: str
    message: str
    metric_name: str
    metric_value: Any
    threshold: Any
    resolved: bool = False
    resolved_at: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "severity": self.severity.value,
            "category": self.category.value,
            "title": self.title,
            "message": self.message,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "resolved": self.resolved,
            "resolved_at": self.resolved_at
        }


@dataclass
class AlertThreshold:
    """Threshold configuration for an alert."""
    metric_name: str
    category: AlertCategory
    severity: AlertSeverity
    operator: str  # 'lt', 'gt', 'eq', 'lte', 'gte'
    value: Any
    title: str
    message_template: str


class AlertSystem:
    """
    War Room Alert System.

    Monitors all metrics and generates alerts when thresholds crossed.
    Supports:
    - Configurable thresholds
    - Multiple severity levels
    - Alert history
    - Resolution tracking
    """

    # Default thresholds based on WAR_ROOM_SPEC.md
    DEFAULT_THRESHOLDS = [
        # CRITICAL - Survival
        AlertThreshold(
            metric_name="survival.cash_balance",
            category=AlertCategory.SURVIVAL,
            severity=AlertSeverity.CRITICAL,
            operator="lt",
            value=10000,
            title="Cash Below Critical Level",
            message_template="Cash balance ${value} is below ${threshold} threshold"
        ),
        AlertThreshold(
            metric_name="survival.runway_months",
            category=AlertCategory.SURVIVAL,
            severity=AlertSeverity.CRITICAL,
            operator="lt",
            value=3,
            title="Runway Critical",
            message_template="Only {value} months runway remaining (threshold: {threshold})"
        ),

        # WARNING - Survival
        AlertThreshold(
            metric_name="survival.runway_months",
            category=AlertCategory.SURVIVAL,
            severity=AlertSeverity.WARNING,
            operator="lt",
            value=6,
            title="Runway Low",
            message_template="Runway at {value} months - below 6 month warning threshold"
        ),

        # CRITICAL - PMF
        AlertThreshold(
            metric_name="pmf.churn_rate",
            category=AlertCategory.PMF,
            severity=AlertSeverity.CRITICAL,
            operator="gt",
            value=20,
            title="Churn Spike",
            message_template="Churn rate {value}% exceeds critical threshold of {threshold}%"
        ),

        # WARNING - PMF
        AlertThreshold(
            metric_name="pmf.churn_rate",
            category=AlertCategory.PMF,
            severity=AlertSeverity.WARNING,
            operator="gt",
            value=10,
            title="Churn High",
            message_template="Churn rate {value}% exceeds warning threshold of {threshold}%"
        ),

        # CRITICAL - Adamus
        AlertThreshold(
            metric_name="adamus.security_score",
            category=AlertCategory.ADAMUS,
            severity=AlertSeverity.CRITICAL,
            operator="lt",
            value=5,
            title="Security Score Critical",
            message_template="Security score {value}/10 below critical threshold {threshold}/10"
        ),
        AlertThreshold(
            metric_name="adamus.budget_remaining",
            category=AlertCategory.ADAMUS,
            severity=AlertSeverity.CRITICAL,
            operator="lt",
            value=20,
            title="Budget Nearly Exhausted",
            message_template="Only ${value} budget remaining this month"
        ),

        # WARNING - Adamus
        AlertThreshold(
            metric_name="adamus.budget_remaining",
            category=AlertCategory.ADAMUS,
            severity=AlertSeverity.WARNING,
            operator="lt",
            value=50,
            title="Budget Running Low",
            message_template="Budget at ${value} - approaching monthly limit"
        ),

        # INFO - Growth
        AlertThreshold(
            metric_name="pmf.mrr",
            category=AlertCategory.PMF,
            severity=AlertSeverity.INFO,
            operator="gte",
            value=1000,
            title="MRR Milestone",
            message_template="🎉 MRR reached ${value}!"
        ),
    ]

    def __init__(self, thresholds: Optional[List[AlertThreshold]] = None):
        """
        Initialize the alert system.

        Args:
            thresholds: Custom thresholds (uses defaults if not provided)
        """
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._alert_counter = 0

    def check_metrics(self, metrics: InternalMetrics) -> List[Alert]:
        """
        Check all metrics against thresholds.

        Args:
            metrics: Current internal metrics

        Returns:
            List of new alerts generated
        """
        new_alerts = []
        metrics_dict = metrics.to_dict()

        for threshold in self.thresholds:
            # Get metric value using dot notation
            value = self._get_nested_value(metrics_dict, threshold.metric_name)

            if value is None:
                continue

            # Check if threshold crossed
            if self._check_threshold(value, threshold.operator, threshold.value):
                alert = self._create_alert(threshold, value)

                # Check if this alert already exists (avoid duplicates)
                alert_key = f"{threshold.metric_name}_{threshold.severity.value}"

                if alert_key not in self.active_alerts:
                    self.active_alerts[alert_key] = alert
                    self.alert_history.append(alert)
                    new_alerts.append(alert)

                    logger.warning(
                        f"[ALERT] {alert.severity.value.upper()}: {alert.title} - {alert.message}"
                    )
            else:
                # Threshold no longer crossed - resolve alert
                alert_key = f"{threshold.metric_name}_{threshold.severity.value}"
                if alert_key in self.active_alerts:
                    self._resolve_alert(alert_key)

        return new_alerts

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value using dot notation (e.g., 'survival.cash_balance')."""
        keys = path.split('.')
        value = data

        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None

        return value

    def _check_threshold(self, value: Any, operator: str, threshold: Any) -> bool:
        """Check if value crosses threshold."""
        try:
            if operator == "lt":
                return value < threshold
            elif operator == "lte":
                return value <= threshold
            elif operator == "gt":
                return value > threshold
            elif operator == "gte":
                return value >= threshold
            elif operator == "eq":
                return value == threshold
            else:
                return False
        except (TypeError, ValueError):
            return False

    def _create_alert(self, threshold: AlertThreshold, value: Any) -> Alert:
        """Create an alert from threshold and value."""
        self._alert_counter += 1
        alert_id = f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._alert_counter}"

        message = threshold.message_template.format(
            value=value,
            threshold=threshold.value
        )

        return Alert(
            id=alert_id,
            timestamp=datetime.now().isoformat(),
            severity=threshold.severity,
            category=threshold.category,
            title=threshold.title,
            message=message,
            metric_name=threshold.metric_name,
            metric_value=value,
            threshold=threshold.value
        )

    def _resolve_alert(self, alert_key: str) -> None:
        """Mark an alert as resolved."""
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.resolved = True
            alert.resolved_at = datetime.now().isoformat()
            del self.active_alerts[alert_key]

            logger.info(f"[ALERT RESOLVED] {alert.title}")

    def get_active_alerts(self) -> List[Alert]:
        """Get all currently active alerts."""
        return list(self.active_alerts.values())

    def get_alerts_by_severity(self, severity: AlertSeverity) -> List[Alert]:
        """Get active alerts filtered by severity."""
        return [a for a in self.active_alerts.values() if a.severity == severity]

    def get_critical_alerts(self) -> List[Alert]:
        """Get all critical alerts."""
        return self.get_alerts_by_severity(AlertSeverity.CRITICAL)

    def get_alert_summary(self) -> Dict[str, Any]:
        """Get summary of current alert status."""
        active = self.get_active_alerts()

        return {
            "total_active": len(active),
            "critical": len([a for a in active if a.severity == AlertSeverity.CRITICAL]),
            "warning": len([a for a in active if a.severity == AlertSeverity.WARNING]),
            "info": len([a for a in active if a.severity == AlertSeverity.INFO]),
            "by_category": {
                cat.value: len([a for a in active if a.category == cat])
                for cat in AlertCategory
            },
            "alerts": [a.to_dict() for a in active]
        }

    def add_threshold(self, threshold: AlertThreshold) -> None:
        """Add a custom threshold."""
        self.thresholds.append(threshold)

    def clear_all_alerts(self) -> None:
        """Clear all active alerts (use with caution)."""
        for alert in self.active_alerts.values():
            alert.resolved = True
            alert.resolved_at = datetime.now().isoformat()

        self.active_alerts.clear()
        logger.info("All alerts cleared")
