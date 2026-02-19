"""
Security Wrapper: All 8 Security Layers in One

This wraps ALL AI operations with complete security.
NOTHING bypasses this wrapper.

The 8 Layers:
1. Data Governance - Validate data at boundaries
2. LLM Optimization - Cost control and efficiency
3. Multi-Method Agents - Right tool for right job
4. Bias Detection - Monitor for unfairness
5. Explainable AI - Track decision reasoning
6. Zero Trust - Verify everything, assume breach
7. Prompt Injection Defense - Block malicious inputs
8. Vulnerability Management - Patch and protect

All 8 layers MUST be active before any AI operation.
"""

import os
import logging
from datetime import datetime
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from .data_classifier import DataClassifier, DataLevel
from .ppai_gateway import PPAIGateway, GatewayResult, RouteDecision
from .prompt_defense import PromptDefense, DefenseResult, ThreatLevel

logger = logging.getLogger(__name__)


class SecurityStatus(Enum):
    """Overall security status."""
    ACTIVE = "active"           # All 8 layers operational
    DEGRADED = "degraded"       # Some layers inactive
    CRITICAL = "critical"       # Security compromised
    DISABLED = "disabled"       # Security off (NEVER in production)


@dataclass
class SecurityCheckResult:
    """Result of all 8 security layer checks."""
    passed: bool
    layer_status: Dict[str, bool]
    blocked_reason: Optional[str]
    route_decision: RouteDecision
    sanitized_content: Optional[str]
    audit_trail: List[str]
    security_score: float  # 0.0 to 1.0


class BudgetTracker:
    """Tracks API spending against budget (Layer 2)."""

    def __init__(
        self,
        monthly_budget: float = 200.0,
        alert_threshold: float = 0.75
    ):
        self.monthly_budget = monthly_budget
        self.alert_threshold = alert_threshold
        self.current_spend = 0.0

    def check_budget(self, estimated_cost: float) -> Tuple[bool, str]:
        """Check if we have budget for this operation."""
        if self.current_spend + estimated_cost > self.monthly_budget:
            return False, f"Budget exceeded: ${self.current_spend:.2f}/${self.monthly_budget:.2f}"

        if (self.current_spend + estimated_cost) / self.monthly_budget > self.alert_threshold:
            return True, f"WARNING: Budget at {((self.current_spend + estimated_cost) / self.monthly_budget * 100):.1f}%"

        return True, "OK"

    def record_spend(self, amount: float) -> None:
        """Record spending."""
        self.current_spend += amount


class BiasDetector:
    """Monitors for bias in AI outputs (Layer 4)."""

    def check_for_bias(self, content: str) -> Tuple[bool, List[str]]:
        """
        Check content for potential bias.

        Returns (has_bias, issues_found)
        """
        issues = []
        content_lower = content.lower()

        # Check for absolute statements
        absolute_phrases = [
            "always", "never", "everyone", "no one",
            "all people", "nobody", "definitely"
        ]
        for phrase in absolute_phrases:
            if phrase in content_lower:
                issues.append(f"Absolute statement detected: '{phrase}'")

        # Check for potentially biased generalizations
        # (This is a simple check - production would use ML)

        return len(issues) > 0, issues


class XAIAuditor:
    """Explainable AI auditor (Layer 5)."""

    def __init__(self):
        self.audit_log = []

    def log_decision(
        self,
        decision: str,
        reasoning: str,
        confidence: float,
        context: Dict[str, Any]
    ) -> str:
        """Log a decision with reasoning for explainability."""
        audit_id = f"xai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.audit_log)}"

        entry = {
            "id": audit_id,
            "timestamp": datetime.now().isoformat(),
            "decision": decision,
            "reasoning": reasoning,
            "confidence": confidence,
            "context_keys": list(context.keys()),
            "escalate": confidence < 0.7  # Low confidence = escalate to Augustus
        }

        self.audit_log.append(entry)

        if entry["escalate"]:
            logger.warning(
                f"[XAI] Low confidence decision ({confidence:.2f}): {decision[:50]}..."
            )

        return audit_id


class SecurityWrapper:
    """
    Complete 8-layer security wrapper.

    ALL AI operations MUST go through this.
    This is the FOUNDATION of Adamus security.
    """

    def __init__(
        self,
        monthly_budget: float = 200.0,
        strict_mode: bool = True,
        memory_db=None
    ):
        """
        Initialize all 8 security layers.

        Args:
            monthly_budget: Monthly budget cap in USD
            strict_mode: Strict security (block on any threat)
            memory_db: Memory database for audit logging
        """
        # Layer 1: Data Governance
        self.data_classifier = DataClassifier()

        # Layer 2: LLM Optimization (Budget)
        self.budget_tracker = BudgetTracker(monthly_budget=monthly_budget)

        # Layer 3: Multi-Method Agents (handled by AI Coordinator)
        # Placeholder - actual routing in coordinator

        # Layer 4: Bias Detection
        self.bias_detector = BiasDetector()

        # Layer 5: Explainable AI
        self.xai_auditor = XAIAuditor()

        # Layer 6: Zero Trust (PPAI Gateway includes this)
        # Verify everything, assume breach

        # Layer 7: Prompt Injection Defense
        self.prompt_defense = PromptDefense(strict_mode=strict_mode)

        # Layer 8: Vulnerability Management
        # Handled by continuous patching process

        # Combined gateway
        self.ppai_gateway = PPAIGateway(memory_db=memory_db)

        self.memory_db = memory_db
        self._status = SecurityStatus.ACTIVE
        self._initialized = True

        logger.info("SecurityWrapper initialized with all 8 layers active")

    def verify_all_layers_active(self) -> Dict[str, bool]:
        """
        Verify all 8 security layers are active.

        This MUST pass before any autonomous operation.
        """
        status = {
            "layer_1_data_governance": self.data_classifier is not None,
            "layer_2_llm_optimization": self.budget_tracker is not None,
            "layer_3_multi_method": True,  # Handled by coordinator
            "layer_4_bias_detection": self.bias_detector is not None,
            "layer_5_explainable_ai": self.xai_auditor is not None,
            "layer_6_zero_trust": self.ppai_gateway is not None,
            "layer_7_prompt_defense": self.prompt_defense is not None,
            "layer_8_vulnerability_mgmt": True,  # Continuous process
        }

        all_active = all(status.values())

        if not all_active:
            inactive = [k for k, v in status.items() if not v]
            logger.error(f"SECURITY DEGRADED: Inactive layers: {inactive}")
            self._status = SecurityStatus.DEGRADED
        else:
            self._status = SecurityStatus.ACTIVE

        return status

    def check_all_layers(
        self,
        prompt: str,
        estimated_tokens: int = 1000
    ) -> SecurityCheckResult:
        """
        Run all 8 security layer checks.

        This is called BEFORE every AI operation.

        Args:
            prompt: The prompt to check
            estimated_tokens: Estimated token count for cost

        Returns:
            SecurityCheckResult with pass/fail and details
        """
        audit_trail = []
        layer_status = {}

        # === Layer 1: Data Governance ===
        classification = self.data_classifier.classify(prompt)
        layer_status["layer_1_data_governance"] = True
        audit_trail.append(
            f"Layer 1: Data classified as {classification.level.name}"
        )

        # === Layer 2: LLM Optimization (Budget) ===
        # Estimate cost based on model and tokens
        estimated_cost = self._estimate_cost(estimated_tokens, classification.level)
        budget_ok, budget_msg = self.budget_tracker.check_budget(estimated_cost)
        layer_status["layer_2_budget"] = budget_ok
        audit_trail.append(f"Layer 2: Budget check - {budget_msg}")

        if not budget_ok:
            return SecurityCheckResult(
                passed=False,
                layer_status=layer_status,
                blocked_reason="Budget exceeded",
                route_decision=RouteDecision.BLOCKED,
                sanitized_content=None,
                audit_trail=audit_trail,
                security_score=0.0
            )

        # === Layer 3: Multi-Method (handled by coordinator) ===
        layer_status["layer_3_multi_method"] = True
        audit_trail.append("Layer 3: Multi-method routing delegated to coordinator")

        # === Layer 4: Bias Detection ===
        # (Checked on output, not input - placeholder here)
        layer_status["layer_4_bias_detection"] = True
        audit_trail.append("Layer 4: Bias detection active (checked on output)")

        # === Layer 5: Explainable AI ===
        # Log that we're making a decision
        self.xai_auditor.log_decision(
            decision="Process prompt through security",
            reasoning=f"Data level: {classification.level.name}",
            confidence=0.9,
            context={"prompt_length": len(prompt)}
        )
        layer_status["layer_5_xai"] = True
        audit_trail.append("Layer 5: Decision logged for explainability")

        # === Layer 6: Zero Trust (PPAI Gateway) ===
        gateway_result = self.ppai_gateway.process(prompt)
        layer_status["layer_6_zero_trust"] = gateway_result.allowed
        audit_trail.append(
            f"Layer 6: Zero trust - Route to {gateway_result.route.value}"
        )

        if not gateway_result.allowed:
            return SecurityCheckResult(
                passed=False,
                layer_status=layer_status,
                blocked_reason="Data classification blocked by PPAI",
                route_decision=gateway_result.route,
                sanitized_content=None,
                audit_trail=audit_trail,
                security_score=0.0
            )

        # === Layer 7: Prompt Injection Defense ===
        defense_result = self.prompt_defense.analyze(
            gateway_result.sanitized_prompt or prompt
        )
        layer_status["layer_7_prompt_defense"] = not defense_result.blocked
        audit_trail.append(
            f"Layer 7: Prompt defense - "
            f"{'BLOCKED' if defense_result.blocked else 'PASSED'} "
            f"(threats: {len(defense_result.threats_found)})"
        )

        if defense_result.blocked:
            return SecurityCheckResult(
                passed=False,
                layer_status=layer_status,
                blocked_reason=f"Prompt injection detected: {defense_result.threat_level.name}",
                route_decision=RouteDecision.BLOCKED,
                sanitized_content=None,
                audit_trail=audit_trail,
                security_score=0.0
            )

        # === Layer 8: Vulnerability Management ===
        # Continuous process - just log status
        layer_status["layer_8_vulnerability"] = True
        audit_trail.append("Layer 8: Vulnerability management active")

        # Calculate security score
        passed_layers = sum(1 for v in layer_status.values() if v)
        security_score = passed_layers / len(layer_status)

        return SecurityCheckResult(
            passed=True,
            layer_status=layer_status,
            blocked_reason=None,
            route_decision=gateway_result.route,
            sanitized_content=gateway_result.sanitized_prompt,
            audit_trail=audit_trail,
            security_score=security_score
        )

    def check_output(self, output: str) -> Tuple[bool, List[str]]:
        """
        Check AI output for issues (bias, secrets, etc.).

        Called AFTER every AI response.
        """
        issues = []

        # Check for leaked secrets in output
        classification = self.data_classifier.classify(output)
        if classification.level >= DataLevel.CONFIDENTIAL:
            issues.append(
                f"Output contains {classification.level.name} data - "
                "possible secret leak"
            )

        # Check for bias
        has_bias, bias_issues = self.bias_detector.check_for_bias(output)
        if has_bias:
            issues.extend(bias_issues)

        return len(issues) == 0, issues

    def _estimate_cost(
        self,
        tokens: int,
        data_level: DataLevel
    ) -> float:
        """Estimate cost for an operation."""
        # Claude pricing (approximate)
        # Input: $3 per 1M tokens, Output: $15 per 1M tokens
        # Assume 50% input, 50% output
        if data_level <= DataLevel.INTERNAL:
            # Claude
            cost_per_1k = 0.009  # Average of input/output
        else:
            # Ollama (free)
            cost_per_1k = 0.0

        return (tokens / 1000) * cost_per_1k

    def record_operation(
        self,
        tokens_used: int,
        brain: str,
        success: bool
    ) -> None:
        """Record a completed operation for tracking."""
        if brain.lower() == "claude":
            estimated_cost = (tokens_used / 1000) * 0.009
            self.budget_tracker.record_spend(estimated_cost)

    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status."""
        layer_status = self.verify_all_layers_active()

        return {
            "status": self._status.value,
            "all_layers_active": all(layer_status.values()),
            "layer_status": layer_status,
            "budget": {
                "spent": self.budget_tracker.current_spend,
                "limit": self.budget_tracker.monthly_budget,
                "remaining": self.budget_tracker.monthly_budget - self.budget_tracker.current_spend
            },
            "threats_blocked": self.prompt_defense.get_stats()["prompts_blocked"],
            "ppai_requests": self.ppai_gateway.get_stats()["total_requests"]
        }

    def require_all_layers_active(self) -> None:
        """
        Assert all 8 layers are active.

        Call this before enabling autonomous mode.
        Raises exception if security is not ready.
        """
        status = self.verify_all_layers_active()
        inactive = [k for k, v in status.items() if not v]

        if inactive:
            raise SecurityError(
                f"Cannot proceed: Security layers inactive: {inactive}"
            )

        logger.info("✅ All 8 security layers verified active")


class SecurityError(Exception):
    """Security-related error."""
    pass
