"""
Prompt Injection Defense System

Protects against prompt injection attacks.
This is security layer 7 of 8.

Attack types defended:
- Direct injection ("ignore previous instructions")
- Indirect injection (malicious content in documents)
- Jailbreak attempts
- Role manipulation
- Data exfiltration attempts

This runs on EVERY prompt before it reaches any AI.
"""

import re
import logging
from dataclasses import dataclass
from typing import List, Tuple, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ThreatLevel(Enum):
    """Threat severity levels."""
    NONE = 0
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class ThreatDetection:
    """A detected threat."""
    pattern_name: str
    matched_text: str
    threat_level: ThreatLevel
    category: str
    recommendation: str


@dataclass
class DefenseResult:
    """Result of prompt defense analysis."""
    is_safe: bool
    threat_level: ThreatLevel
    threats_found: List[ThreatDetection]
    blocked: bool
    sanitized_prompt: Optional[str]
    audit_notes: List[str]


class PromptDefense:
    """
    Prompt Injection Defense System.

    Scans all incoming prompts for:
    - Injection patterns
    - Jailbreak attempts
    - Malicious instructions
    - Data exfiltration

    Part of Adamus's 8-layer security architecture.
    """

    # Direct injection patterns - attempts to override instructions
    DIRECT_INJECTION_PATTERNS = [
        (r'ignore\s+(all\s+)?(previous|prior|above)\s+(instructions?|commands?|rules?)',
         ThreatLevel.CRITICAL, "direct_injection"),
        (r'disregard\s+(all\s+)?(previous|prior|your)\s+(instructions?|programming)',
         ThreatLevel.CRITICAL, "direct_injection"),
        (r'forget\s+(everything|all|your)\s+(instructions?|rules?|training)',
         ThreatLevel.CRITICAL, "direct_injection"),
        (r'new\s+instructions?\s*[:\-]',
         ThreatLevel.HIGH, "instruction_override"),
        (r'system\s*prompt\s*[:\-]',
         ThreatLevel.CRITICAL, "system_prompt_injection"),
        (r'</?(system|user|assistant)>',
         ThreatLevel.CRITICAL, "role_manipulation"),
    ]

    # Jailbreak patterns - attempts to bypass safety
    JAILBREAK_PATTERNS = [
        (r'DAN\s*mode|do\s+anything\s+now',
         ThreatLevel.CRITICAL, "jailbreak"),
        (r'pretend\s+(you\s+are|to\s+be)\s+(a|an)\s+\w+\s+without',
         ThreatLevel.HIGH, "jailbreak"),
        (r'role\s*play\s+as\s+(a|an)\s+evil',
         ThreatLevel.HIGH, "jailbreak"),
        (r'you\s+are\s+now\s+(a|an)\s+\w+\s+that\s+can',
         ThreatLevel.MEDIUM, "role_change"),
        (r'act\s+as\s+if\s+you\s+(have\s+no|don\'t\s+have)\s+restrictions',
         ThreatLevel.CRITICAL, "jailbreak"),
    ]

    # Data exfiltration patterns - attempts to extract data
    EXFIL_PATTERNS = [
        (r'send\s+(all|the)?\s*(data|information|content)\s+to',
         ThreatLevel.CRITICAL, "data_exfil"),
        (r'output\s+(all|the)\s+(data|database|credentials)',
         ThreatLevel.CRITICAL, "data_exfil"),
        (r'print\s+(all|every)\s+(secret|password|key|credential)',
         ThreatLevel.CRITICAL, "data_exfil"),
        (r'show\s+me\s+(the\s+)?(api\s+)?keys?',
         ThreatLevel.HIGH, "credential_theft"),
        (r'what\s+(is|are)\s+(the|your)\s+(password|secret|key)',
         ThreatLevel.HIGH, "credential_theft"),
        (r'list\s+(all\s+)?(user|customer)\s+(data|information|emails?)',
         ThreatLevel.HIGH, "data_exfil"),
        (r'send\s+.*\s+to\s+\S+\.com',
         ThreatLevel.CRITICAL, "data_exfil"),
    ]

    # Malicious action patterns
    MALICIOUS_ACTION_PATTERNS = [
        (r'delete\s+(all|every)\s+(file|data|record)',
         ThreatLevel.CRITICAL, "destructive"),
        (r'drop\s+(database|table|collection)',
         ThreatLevel.CRITICAL, "destructive"),
        (r'rm\s+-rf\s+/',
         ThreatLevel.CRITICAL, "destructive"),
        (r'execute\s+(shell|system|bash)\s+command',
         ThreatLevel.HIGH, "code_execution"),
        (r'run\s+(as|with)\s+(admin|root|sudo)',
         ThreatLevel.HIGH, "privilege_escalation"),
    ]

    # Indirect injection markers - content from external sources
    INDIRECT_MARKERS = [
        (r'<\s*!--\s*injection',
         ThreatLevel.MEDIUM, "indirect_injection"),
        (r'\[hidden\s+instructions?\]',
         ThreatLevel.MEDIUM, "indirect_injection"),
        (r'<!-- begin hidden instructions -->',
         ThreatLevel.HIGH, "indirect_injection"),
    ]

    def __init__(self, strict_mode: bool = True):
        """
        Initialize the prompt defense system.

        Args:
            strict_mode: If True, block on any threat. If False, only block CRITICAL.
        """
        self.strict_mode = strict_mode
        self._compile_patterns()
        self._threat_count = 0
        self._blocked_count = 0

    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self._all_patterns = []

        pattern_groups = [
            self.DIRECT_INJECTION_PATTERNS,
            self.JAILBREAK_PATTERNS,
            self.EXFIL_PATTERNS,
            self.MALICIOUS_ACTION_PATTERNS,
            self.INDIRECT_MARKERS,
        ]

        for group in pattern_groups:
            for pattern, level, category in group:
                self._all_patterns.append((
                    re.compile(pattern, re.IGNORECASE),
                    level,
                    category,
                    pattern
                ))

    def analyze(self, prompt: str) -> DefenseResult:
        """
        Analyze a prompt for injection attacks.

        Args:
            prompt: The prompt to analyze

        Returns:
            DefenseResult with analysis
        """
        threats_found = []
        max_threat_level = ThreatLevel.NONE
        audit_notes = []

        # Scan for all patterns
        for compiled, level, category, pattern_str in self._all_patterns:
            matches = compiled.findall(prompt)
            if matches:
                for match in matches:
                    match_text = match if isinstance(match, str) else str(match)
                    threat = ThreatDetection(
                        pattern_name=pattern_str[:50],
                        matched_text=match_text[:100],
                        threat_level=level,
                        category=category,
                        recommendation=self._get_recommendation(category)
                    )
                    threats_found.append(threat)

                    if level.value > max_threat_level.value:
                        max_threat_level = level

                    self._threat_count += 1

        # Determine if blocked
        if self.strict_mode:
            blocked = max_threat_level.value >= ThreatLevel.MEDIUM.value
        else:
            blocked = max_threat_level.value >= ThreatLevel.CRITICAL.value

        if blocked:
            self._blocked_count += 1
            audit_notes.append(f"BLOCKED: {len(threats_found)} threats detected")
            logger.warning(
                f"Prompt BLOCKED: {len(threats_found)} threats, "
                f"max level {max_threat_level.name}"
            )
        elif threats_found:
            audit_notes.append(f"ALLOWED with {len(threats_found)} low-level threats")

        # Attempt sanitization if not critical
        sanitized_prompt = None
        if not blocked and threats_found:
            sanitized_prompt = self._attempt_sanitization(prompt, threats_found)

        return DefenseResult(
            is_safe=len(threats_found) == 0,
            threat_level=max_threat_level,
            threats_found=threats_found,
            blocked=blocked,
            sanitized_prompt=sanitized_prompt if not blocked else None,
            audit_notes=audit_notes
        )

    def _get_recommendation(self, category: str) -> str:
        """Get recommendation for a threat category."""
        recommendations = {
            "direct_injection": "Block immediately - direct instruction override attempt",
            "instruction_override": "Block - attempt to change AI behavior",
            "system_prompt_injection": "Block - system prompt manipulation",
            "role_manipulation": "Block - attempt to manipulate AI role",
            "jailbreak": "Block - jailbreak attempt detected",
            "role_change": "Review - suspicious role change request",
            "data_exfil": "Block - data exfiltration attempt",
            "credential_theft": "Block - credential access attempt",
            "destructive": "Block - destructive action requested",
            "code_execution": "Block - arbitrary code execution attempt",
            "privilege_escalation": "Block - privilege escalation attempt",
            "indirect_injection": "Review - possible hidden instructions",
        }
        return recommendations.get(category, "Review - unknown threat category")

    def _attempt_sanitization(
        self,
        prompt: str,
        threats: List[ThreatDetection]
    ) -> str:
        """
        Attempt to sanitize low-threat prompts.

        Only for LOW/MEDIUM threats that can be safely removed.
        """
        sanitized = prompt

        for threat in threats:
            if threat.threat_level in [ThreatLevel.LOW, ThreatLevel.MEDIUM]:
                # Remove the matched text
                sanitized = sanitized.replace(threat.matched_text, "[REMOVED]")

        return sanitized

    def quick_check(self, prompt: str) -> Tuple[bool, str]:
        """
        Quick safety check for a prompt.

        Args:
            prompt: The prompt to check

        Returns:
            (is_safe, reason)
        """
        result = self.analyze(prompt)

        if result.blocked:
            threat_summary = ", ".join([
                t.category for t in result.threats_found[:3]
            ])
            return False, f"Blocked: {threat_summary}"

        if not result.is_safe:
            return True, f"Allowed with warnings: {len(result.threats_found)} low threats"

        return True, "Safe"

    def get_stats(self) -> dict:
        """Get defense statistics."""
        return {
            "threats_detected": self._threat_count,
            "prompts_blocked": self._blocked_count,
            "strict_mode": self.strict_mode,
            "patterns_loaded": len(self._all_patterns)
        }

    def add_custom_pattern(
        self,
        pattern: str,
        threat_level: ThreatLevel,
        category: str
    ) -> None:
        """
        Add a custom threat pattern.

        Use this to add domain-specific patterns.
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        self._all_patterns.append((compiled, threat_level, category, pattern))
        logger.info(f"Added custom pattern: {pattern[:30]}... ({category})")
