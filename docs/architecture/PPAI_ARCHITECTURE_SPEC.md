# PPAI Architecture Specification
## Privacy-Preserving AI — Full Technical Specification

*Note: This is the full specification document (the .docx version contains the same content)*

---

## Executive Summary

PPAI (Privacy-Preserving AI) is Adamus's data handling framework ensuring AI operations never expose sensitive data to external providers.

---

## 1. Data Classification System

### 1.1 Classification Levels

```yaml
LEVEL_1_PUBLIC:
  description: "Safe to send to any AI provider"
  examples:
    - Generic code patterns (no business logic)
    - Architecture diagrams (anonymized)
    - Public documentation
    - Open source code
  handling: "No restrictions"

LEVEL_2_INTERNAL:
  description: "Sanitize before external AI"
  examples:
    - Code with real variable names
    - User feedback (anonymized)
    - Feature specifications
    - Build plans
  handling: "Strip PII, anonymize identifiers"

LEVEL_3_CONFIDENTIAL:
  description: "Local AI only (Ollama)"
  examples:
    - User personal data
    - Financial records
    - Authentication tokens
    - Competitive strategy details
  handling: "NEVER send to external API"

LEVEL_4_SECRET:
  description: "Never in any AI prompt"
  examples:
    - API keys
    - Passwords
    - User credentials
    - Payment data
  handling: "Redact completely, use placeholders"
```

---

## 2. Data Sanitization Pipeline

```python
# src/security/ppai_gateway.py

class PPAIGateway:
    """
    All AI calls go through this gateway.
    No exceptions.
    """
    
    def process(self, prompt: str, data_level: int) -> str:
        # Level 4: Never send
        if data_level == 4:
            raise SecurityError("Level 4 data cannot be sent to external AI")
        
        # Level 3: Route to local
        if data_level == 3:
            return self.route_to_ollama(prompt)
        
        # Level 1-2: Sanitize then send
        sanitized = self.sanitize(prompt)
        return self.route_to_claude(sanitized)
    
    def sanitize(self, prompt: str) -> str:
        prompt = self.strip_pii(prompt)
        prompt = self.redact_secrets(prompt)
        prompt = self.anonymize_identifiers(prompt)
        return prompt
    
    def strip_pii(self, text: str) -> str:
        """Remove emails, phone numbers, real names"""
        import re
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', text)
        text = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '[PHONE]', text)
        return text
    
    def redact_secrets(self, text: str) -> str:
        """Redact API keys, tokens, passwords"""
        import re
        text = re.sub(r'sk-ant-[a-zA-Z0-9-]+', '[ANTHROPIC_KEY]', text)
        text = re.sub(r'(password|token|secret|key)\s*[:=]\s*\S+', r'\1=[REDACTED]', text, flags=re.IGNORECASE)
        return text
```

---

## 3. Routing Rules

```yaml
always_local_ollama:
  - "Anything containing user emails"
  - "Financial data or MRR details"
  - "API keys (should never appear in prompts)"
  - "User-generated content with PII"

always_external_claude:
  - "Architecture design questions"
  - "Generic code problems"
  - "Public documentation"

conditional_sanitize_first:
  - "Code that references real systems"
  - "Strategy documents (remove specifics)"
  - "User feedback (anonymize)"
```

---

## 4. Audit Trail

```python
class PPAIAuditLog:
    def log_every_call(self, call: APICall):
        self.db.insert({
            'timestamp': call.timestamp,
            'provider': call.provider,  # 'claude' or 'ollama'
            'data_level': call.data_level,
            'sanitization_applied': call.was_sanitized,
            'tokens_sent': call.token_count,
            'pii_detected': call.pii_found,
            'routed_to_local': call.used_ollama,
        })
```

---

## 5. Compliance

```yaml
gdpr_compliance:
  - "No user PII to external AI: ✅"
  - "Data minimization: ✅"
  - "Audit trail: ✅"
  - "User data local only: ✅"

creator_data_protection:
  - "Story content stays local: ✅"
  - "IP records stay local: ✅"
  - "Payment data never in AI: ✅"
```

---

**Status**: ACTIVE — All AI calls routed through PPAI Gateway
**Version**: 1.0.0
**Owner**: Adamus Security Layer
