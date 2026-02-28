"""
PPAI Gateway: Privacy-Preserving AI Gateway

ALL AI calls go through this gateway. No exceptions.

Data Classification:
- Level 1 (PUBLIC): Safe for any AI
- Level 2 (INTERNAL): Sanitize before external AI
- Level 3 (CONFIDENTIAL): Local AI only (Ollama)
- Level 4 (SECRET): Never in any AI prompt

This is NON-NEGOTIABLE security.
"""

import re
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from .data_classifier import DataClassifier, DataLevel, ClassificationResult

logger = logging.getLogger(__name__)


class RouteDecision(Enum):
    """Where to route the AI call."""
    EXTERNAL = "external"      # External API (Level 1-2 after sanitization)
    LOCAL = "local"            # Local AI only (Level 3) — Ollama / LM Studio
    BLOCKED = "blocked"        # Cannot process (Level 4)


# Brains that run locally — safe for Level 3-4 data
LOCAL_BRAINS = {"ollama", "lmstudio", "local"}


@dataclass
class SanitizationResult:
    """Result of sanitizing data."""
    original_length: int
    sanitized_length: int
    sanitized_content: str
    replacements_made: int
    pii_found: int
    secrets_found: int


@dataclass
class GatewayResult:
    """Result of PPAI gateway processing."""
    allowed: bool
    route: RouteDecision
    sanitized_prompt: Optional[str]
    classification: ClassificationResult
    audit_id: str
    warnings: list


class PPAIGateway:
    """
    Privacy-Preserving AI Gateway.

    ALL AI calls MUST go through this gateway.
    It ensures:
    1. Data is classified correctly
    2. Sensitive data never leaves the system
    3. External AI only sees sanitized data
    4. Everything is audited

    This is a CRITICAL security component.
    """

    def __init__(self, memory_db=None):
        """
        Initialize the PPAI gateway.

        Args:
            memory_db: Memory database for audit logging
        """
        self.classifier = DataClassifier()
        self.memory_db = memory_db
        self._audit_counter = 0

    def process(
        self,
        prompt: str,
        force_local: bool = False
    ) -> GatewayResult:
        """
        Process a prompt through the PPAI gateway.

        This is the ONLY way to send data to AI.

        Args:
            prompt: The prompt to process
            force_local: Force routing to Ollama

        Returns:
            GatewayResult with routing decision and sanitized content
        """
        self._audit_counter += 1
        audit_id = f"ppai_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._audit_counter}"

        # 1. Classify the data
        classification = self.classifier.classify(prompt)

        logger.info(
            f"[{audit_id}] Data classified as {classification.level.name}: "
            f"{', '.join(classification.reasons[:2])}"
        )

        # 2. Determine routing
        if force_local:
            route = RouteDecision.OLLAMA
        elif classification.level == DataLevel.SECRET:
            # Level 4: BLOCK - cannot send to ANY AI
            logger.warning(f"[{audit_id}] BLOCKED: Level 4 SECRET data detected")
            return GatewayResult(
                allowed=False,
                route=RouteDecision.BLOCKED,
                sanitized_prompt=None,
                classification=classification,
                audit_id=audit_id,
                warnings=["Contains Level 4 SECRET data - cannot process"]
            )
        elif classification.level == DataLevel.CONFIDENTIAL:
            # Level 3: Local only
            route = RouteDecision.LOCAL
        else:
            # Level 1-2: External AI allowed after sanitization
            route = RouteDecision.EXTERNAL

        # 3. Sanitize if needed
        sanitized_prompt = prompt
        warnings = []

        if classification.sanitization_required or route == RouteDecision.EXTERNAL:
            sanitization = self.sanitize(prompt)
            sanitized_prompt = sanitization.sanitized_content

            if sanitization.pii_found > 0:
                warnings.append(f"Removed {sanitization.pii_found} PII instances")
            if sanitization.secrets_found > 0:
                warnings.append(f"Redacted {sanitization.secrets_found} secrets")

            logger.info(
                f"[{audit_id}] Sanitized: {sanitization.replacements_made} replacements"
            )

        # 4. Final safety check on sanitized content
        if route == RouteDecision.EXTERNAL:
            final_check = self.classifier.classify(sanitized_prompt)
            if final_check.level > DataLevel.INTERNAL:
                logger.warning(
                    f"[{audit_id}] Post-sanitization check failed, "
                    f"routing to local brain instead"
                )
                route = RouteDecision.LOCAL
                warnings.append("Fallback to local: sanitization incomplete")

        # 5. Audit log
        self._log_audit(audit_id, classification, route, warnings)

        return GatewayResult(
            allowed=True,
            route=route,
            sanitized_prompt=sanitized_prompt,
            classification=classification,
            audit_id=audit_id,
            warnings=warnings
        )

    def sanitize(self, text: str) -> SanitizationResult:
        """
        Sanitize text by removing/redacting sensitive content.

        Args:
            text: Text to sanitize

        Returns:
            SanitizationResult with sanitized content
        """
        original_length = len(text)
        sanitized = text
        replacements = 0
        pii_found = 0
        secrets_found = 0

        # --- Remove PII ---

        # Emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, sanitized)
        pii_found += len(matches)
        sanitized = re.sub(email_pattern, '[EMAIL_REDACTED]', sanitized)
        replacements += len(matches)

        # Phone numbers
        phone_pattern = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
        matches = re.findall(phone_pattern, sanitized)
        pii_found += len(matches)
        sanitized = re.sub(phone_pattern, '[PHONE_REDACTED]', sanitized)
        replacements += len(matches)

        # SSN
        ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
        matches = re.findall(ssn_pattern, sanitized)
        pii_found += len(matches)
        sanitized = re.sub(ssn_pattern, '[SSN_REDACTED]', sanitized)
        replacements += len(matches)

        # Credit cards
        cc_pattern = r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'
        matches = re.findall(cc_pattern, sanitized)
        pii_found += len(matches)
        sanitized = re.sub(cc_pattern, '[CC_REDACTED]', sanitized)
        replacements += len(matches)

        # --- Redact Secrets ---

        # Anthropic API keys
        ant_pattern = r'sk-ant-[a-zA-Z0-9-]+'
        matches = re.findall(ant_pattern, sanitized)
        secrets_found += len(matches)
        sanitized = re.sub(ant_pattern, '[ANTHROPIC_KEY]', sanitized)
        replacements += len(matches)

        # OpenAI API keys
        oai_pattern = r'sk-[a-zA-Z0-9]{48}'
        matches = re.findall(oai_pattern, sanitized)
        secrets_found += len(matches)
        sanitized = re.sub(oai_pattern, '[OPENAI_KEY]', sanitized)
        replacements += len(matches)

        # GitHub tokens
        gh_pattern = r'ghp_[a-zA-Z0-9]{36}'
        matches = re.findall(gh_pattern, sanitized)
        secrets_found += len(matches)
        sanitized = re.sub(gh_pattern, '[GITHUB_TOKEN]', sanitized)
        replacements += len(matches)

        # Generic secrets (password=, token=, secret=, key=)
        secret_pattern = r'(password|token|secret|api_key|apikey|auth)\s*[:=]\s*[\'"]?([^\s\'"]+)[\'"]?'
        matches = re.findall(secret_pattern, sanitized, re.IGNORECASE)
        secrets_found += len(matches)
        sanitized = re.sub(
            secret_pattern,
            r'\1=[REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )
        replacements += len(matches)

        # Groq API keys
        groq_pattern = r'gsk_[a-zA-Z0-9]{52}'
        matches = re.findall(groq_pattern, sanitized)
        secrets_found += len(matches)
        sanitized = re.sub(groq_pattern, '[GROQ_KEY]', sanitized)
        replacements += len(matches)

        # Gemini / Google API keys
        gemini_pattern = r'AIza[a-zA-Z0-9_-]{35}'
        matches = re.findall(gemini_pattern, sanitized)
        secrets_found += len(matches)
        sanitized = re.sub(gemini_pattern, '[GEMINI_KEY]', sanitized)
        replacements += len(matches)

        # xAI / Grok API keys
        xai_pattern = r'xai-[a-zA-Z0-9]{32,}'
        matches = re.findall(xai_pattern, sanitized)
        secrets_found += len(matches)
        sanitized = re.sub(xai_pattern, '[GROK_KEY]', sanitized)
        replacements += len(matches)

        # Mistral API keys
        mistral_pattern = r'[a-zA-Z0-9]{32}(?=[^a-zA-Z0-9]|$)'
        # (too broad — use generic secret pattern instead, handled below)

        # AWS keys
        aws_pattern = r'(aws_access_key_id|aws_secret_access_key)\s*=\s*\S+'
        matches = re.findall(aws_pattern, sanitized, re.IGNORECASE)
        secrets_found += len(matches)
        sanitized = re.sub(
            aws_pattern,
            r'\1=[AWS_REDACTED]',
            sanitized,
            flags=re.IGNORECASE
        )
        replacements += len(matches)

        # --- Anonymize Internal References ---

        # Replace real URLs with generic ones
        url_pattern = r'https?://(?!example\.com)[^\s<>"\']+\.[^\s<>"\']+'
        sanitized = re.sub(url_pattern, '[URL_REDACTED]', sanitized)

        # Replace IP addresses
        ip_pattern = r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b'
        sanitized = re.sub(ip_pattern, '[IP_REDACTED]', sanitized)

        # Step 3: anonymize identifiers
        sanitized = self.anonymize_identifiers(sanitized)

        return SanitizationResult(
            original_length=original_length,
            sanitized_length=len(sanitized),
            sanitized_content=sanitized,
            replacements_made=replacements,
            pii_found=pii_found,
            secrets_found=secrets_found
        )

    def anonymize_identifiers(self, text: str) -> str:
        """
        Anonymize business-specific identifiers before sending to external AI.

        Replaces product names, internal system names, and personal references
        with generic placeholders so external AI never learns Adamus's internals.
        """
        replacements = [
            (r'\bGenre\b',    '[PRODUCT]'),
            (r'\bAdamus\b',   '[SYSTEM]'),
            (r'\bAugustus\b', '[USER]'),
            # Internal DB / file paths
            (r'~/\.adamus/[^\s]*', '[INTERNAL_PATH]'),
            (r'/home/[a-zA-Z0-9_]+/', '[HOME_PATH]/'),
            # Internal port references
            (r'\blocalhost:\d{4,5}\b', 'localhost:[PORT]'),
        ]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
        return text

    def before_send(self, prompt: str) -> str:
        """
        Full pre-send pipeline as specified in PPAI_ARCHITECTURE_SUMMARY.md.

        Call this before sending any prompt to an external AI.
        Returns sanitized prompt, or raises SecurityError if too sensitive.
        """
        # Classify ORIGINAL prompt first (catches secrets before sanitization hides them)
        result = self.process(prompt)

        if not result.allowed:
            raise SecurityError("PPAI blocked: prompt contains Level 4 SECRET data")

        if result.route == RouteDecision.LOCAL:
            raise SecurityError(
                "PPAI requires local routing — use Ollama/LM Studio for this data"
            )

        return result.sanitized_prompt or prompt

    def _log_audit(
        self,
        audit_id: str,
        classification: ClassificationResult,
        route: RouteDecision,
        warnings: list
    ) -> None:
        """Log to audit trail — writes to DB if available, always logs."""
        logger.info(
            f"[PPAI AUDIT] {audit_id}: "
            f"Level={classification.level.name}, "
            f"Route={route.value}, "
            f"Warnings={len(warnings)}"
        )

        if self.memory_db:
            try:
                PPAIAuditLog(self.memory_db).log_call(
                    audit_id=audit_id,
                    data_level=classification.level.value,
                    route=route.value,
                    pii_detected=len(classification.detected_patterns),
                    warnings=warnings,
                )
            except Exception as exc:
                logger.warning(f"PPAI audit DB write failed: {exc}")

    def validate_before_send(
        self,
        prompt: str,
        target_brain: str
    ) -> Tuple[bool, str]:
        """
        Final validation before sending to AI.

        This is the LAST line of defense.

        Args:
            prompt: The prompt to validate
            target_brain: 'claude' or 'ollama'

        Returns:
            (is_valid, error_message)
        """
        classification = self.classifier.classify(prompt)

        # Level 4: Never allowed
        if classification.level == DataLevel.SECRET:
            return False, "Level 4 SECRET data cannot be sent to any AI"

        # Level 3: Local brains only
        if classification.level == DataLevel.CONFIDENTIAL:
            if target_brain.lower() not in LOCAL_BRAINS:
                return False, f"Level 3 CONFIDENTIAL data can only go to local brains {LOCAL_BRAINS}, got: {target_brain}"

        # Check for residual secrets (belt and suspenders)
        secret_patterns = [
            r'sk-ant-',
            r'sk-[a-zA-Z0-9]{48}',
            r'ghp_[a-zA-Z0-9]{36}',
            r'gsk_[a-zA-Z0-9]{52}',
            r'AIza[a-zA-Z0-9_-]{35}',
            r'xai-[a-zA-Z0-9]{32}',
            r'password\s*=\s*[^\s]',
        ]

        for pattern in secret_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                return False, f"Residual secret pattern detected: {pattern[:20]}..."

        return True, ""

    def get_stats(self) -> Dict:
        """Get gateway statistics."""
        return {
            "total_requests": self._audit_counter,
            "status": "active"
        }


class SecurityError(Exception):
    """Raised when PPAI blocks a request."""
    pass


class PPAIAuditLog:
    """
    Audit trail for all AI calls — as specified in PPAI_ARCHITECTURE_SPEC.md §4.

    Logs every call to SQLite so Augustus can review what data
    was sent to which provider.
    """

    TABLE_SQL = """
        CREATE TABLE IF NOT EXISTS ppai_audit (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT    NOT NULL,
            audit_id    TEXT    NOT NULL,
            data_level  INTEGER NOT NULL,
            route       TEXT    NOT NULL,
            pii_detected INTEGER DEFAULT 0,
            sanitization_applied INTEGER DEFAULT 1,
            routed_to_local INTEGER DEFAULT 0,
            warnings    TEXT    DEFAULT '',
            tokens_sent INTEGER DEFAULT 0
        )
    """

    def __init__(self, memory_db):
        self.db = memory_db
        self._ensure_table()

    def _ensure_table(self) -> None:
        try:
            conn = self.db._get_connection() if hasattr(self.db, '_get_connection') else None
            if conn:
                conn.execute(self.TABLE_SQL)
                conn.commit()
        except Exception as exc:
            logger.debug(f"PPAIAuditLog table setup: {exc}")

    def log_call(
        self,
        audit_id: str,
        data_level: int,
        route: str,
        pii_detected: int = 0,
        warnings: list = None,
        tokens_sent: int = 0,
    ) -> None:
        """Log every AI call to the audit DB."""
        try:
            conn = self.db._get_connection() if hasattr(self.db, '_get_connection') else None
            if conn:
                conn.execute(
                    """INSERT INTO ppai_audit
                       (timestamp, audit_id, data_level, route, pii_detected,
                        sanitization_applied, routed_to_local, warnings, tokens_sent)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        datetime.now().isoformat(),
                        audit_id,
                        data_level,
                        route,
                        pii_detected,
                        1,
                        1 if route == "local" else 0,
                        "; ".join(warnings or []),
                        tokens_sent,
                    )
                )
                conn.commit()
        except Exception as exc:
            logger.warning(f"PPAIAuditLog write failed: {exc}")
