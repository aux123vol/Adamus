"""
Data Classification System

Classifies data into 4 security levels:
- Level 1 (PUBLIC): Safe for any AI
- Level 2 (INTERNAL): Sanitize before external AI
- Level 3 (CONFIDENTIAL): Local AI only (Ollama)
- Level 4 (SECRET): Never in any AI prompt

This determines which brain can process data.
"""

import re
import logging
from enum import IntEnum
from dataclasses import dataclass
from typing import List, Tuple, Set

logger = logging.getLogger(__name__)


class DataLevel(IntEnum):
    """Data classification levels."""
    PUBLIC = 1        # Safe for any AI
    INTERNAL = 2      # Sanitize before external
    CONFIDENTIAL = 3  # Local AI only
    SECRET = 4        # Never in AI prompts


@dataclass
class ClassificationResult:
    """Result of data classification."""
    level: DataLevel
    reasons: List[str]
    detected_patterns: List[str]
    sanitization_required: bool
    allowed_brains: List[str]


class DataClassifier:
    """
    Classifies data for security routing.

    Every piece of data must be classified before
    it can be sent to any AI brain.
    """

    # Level 4 patterns - NEVER send to AI
    SECRET_PATTERNS = [
        r'sk-ant-[a-zA-Z0-9-]+',              # Anthropic API keys
        r'sk-[a-zA-Z0-9]{48}',                # OpenAI API keys
        r'ghp_[a-zA-Z0-9]{36}',               # GitHub tokens
        r'aws_access_key_id\s*=\s*\S+',       # AWS keys
        r'aws_secret_access_key\s*=\s*\S+',
        r'password\s*[:=]\s*[\'"]?\S+[\'"]?', # Passwords
        r'secret\s*[:=]\s*[\'"]?\S+[\'"]?',
        r'token\s*[:=]\s*[\'"]?\S+[\'"]?',
        r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b',  # Credit cards
        r'\b\d{3}-\d{2}-\d{4}\b',             # SSN
    ]

    # Level 3 patterns - Local AI only
    CONFIDENTIAL_PATTERNS = [
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Emails
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',     # Phone numbers
        r'\$\d+[,\d]*\.?\d*\s*(?:MRR|ARR)',   # Revenue figures
        r'burn\s*rate\s*[:\s]\s*\$?\d+',       # Burn rate
        r'runway\s*[:\s]\s*\d+\s*months?',     # Runway
        r'(?:user|customer)\s*(?:id|ID)\s*[:\s]\s*\S+',  # User IDs
        r'(?:private|confidential|internal)',  # Confidential markers
    ]

    # Level 2 patterns - Need sanitization
    INTERNAL_PATTERNS = [
        r'Genre',                              # Product name (sanitize)
        r'Augustus',                           # Personal reference
        r'TODO:?\s*\S+',                       # TODO items
        r'FIXME:?\s*\S+',                      # Fix items
        r'\.env\b',                            # Env file references
        r'localhost:\d+',                      # Local URLs
    ]

    def __init__(self):
        """Initialize the data classifier."""
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        """Compile regex patterns for performance."""
        self._secret_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.SECRET_PATTERNS
        ]
        self._confidential_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.CONFIDENTIAL_PATTERNS
        ]
        self._internal_compiled = [
            re.compile(p, re.IGNORECASE) for p in self.INTERNAL_PATTERNS
        ]

    def classify(self, data: str) -> ClassificationResult:
        """
        Classify data into security levels.

        Args:
            data: The data to classify

        Returns:
            ClassificationResult with level and metadata
        """
        detected = []
        reasons = []

        # Check Level 4 (SECRET) - most restrictive first
        for pattern in self._secret_compiled:
            matches = pattern.findall(data)
            if matches:
                detected.extend(matches[:3])  # Limit logged matches
                reasons.append(f"Contains secret pattern: {pattern.pattern[:30]}...")

        if reasons:
            return ClassificationResult(
                level=DataLevel.SECRET,
                reasons=reasons,
                detected_patterns=detected,
                sanitization_required=True,
                allowed_brains=[]  # NO AI can process this
            )

        # Check Level 3 (CONFIDENTIAL)
        reasons = []
        for pattern in self._confidential_compiled:
            matches = pattern.findall(data)
            if matches:
                detected.extend(matches[:3])
                reasons.append(f"Contains confidential data: {pattern.pattern[:30]}...")

        if reasons:
            return ClassificationResult(
                level=DataLevel.CONFIDENTIAL,
                reasons=reasons,
                detected_patterns=detected,
                sanitization_required=False,
                allowed_brains=['ollama']  # Local only
            )

        # Check Level 2 (INTERNAL)
        reasons = []
        for pattern in self._internal_compiled:
            matches = pattern.findall(data)
            if matches:
                detected.extend(matches[:3])
                reasons.append(f"Contains internal reference: {pattern.pattern[:30]}...")

        if reasons:
            return ClassificationResult(
                level=DataLevel.INTERNAL,
                reasons=reasons,
                detected_patterns=detected,
                sanitization_required=True,
                allowed_brains=['claude', 'ollama']  # After sanitization
            )

        # Default: Level 1 (PUBLIC)
        return ClassificationResult(
            level=DataLevel.PUBLIC,
            reasons=["No sensitive patterns detected"],
            detected_patterns=[],
            sanitization_required=False,
            allowed_brains=['claude', 'ollama']
        )

    def get_level_name(self, level: DataLevel) -> str:
        """Get human-readable level name."""
        return {
            DataLevel.PUBLIC: "PUBLIC (Level 1)",
            DataLevel.INTERNAL: "INTERNAL (Level 2)",
            DataLevel.CONFIDENTIAL: "CONFIDENTIAL (Level 3)",
            DataLevel.SECRET: "SECRET (Level 4)"
        }.get(level, "UNKNOWN")

    def can_use_brain(
        self,
        level: DataLevel,
        brain: str
    ) -> bool:
        """Check if a brain can process data at this level."""
        allowed = {
            DataLevel.PUBLIC: {'claude', 'ollama'},
            DataLevel.INTERNAL: {'claude', 'ollama'},  # After sanitization
            DataLevel.CONFIDENTIAL: {'ollama'},
            DataLevel.SECRET: set()  # No AI
        }
        return brain.lower() in allowed.get(level, set())
