# PPAI Architecture Summary
## Privacy-Preserving AI Infrastructure for Adamus

**PPAI = Privacy-Preserving AI** — Adamus uses AI at full power without leaking sensitive data.

---

## The Problem

```yaml
standard_ai_risks:
  - api_logs: "Claude sees all your prompts"
  - training_data: "Your data may train future models"
  - competitor_exposure: "Strategy sent to third party"
  - user_data: "Genre user data in external AI"
```

---

## The PPAI Solution

```yaml
layer_1_data_sanitization:
  before_api_call:
    - strip_pii: "Remove names, emails, IDs"
    - anonymize_code: "Replace real class/var names"
    - redact_keys: "Never send API keys, passwords"
    - mock_data: "Use fake data for testing"

layer_2_local_first:
  sensitive_tasks: "Always use Ollama (never leaves machine)"
  sensitive_categories:
    - user_data: "Local only"
    - financial_data: "Local only"
    - strategy_docs: "Local only with permission"
    - api_keys: "Never in any prompt"

layer_3_prompt_hygiene:
  never_include:
    - real_user_emails
    - payment_information
    - authentication_tokens
    - competitive_strategies_in_detail
    
layer_4_audit_trail:
  logs_every_api_call: true
  logs_data_categories_sent: true
  alerts_if_sensitive_detected: true
```

---

## Data Classification

```yaml
public_safe_for_any_ai:
  - generic_code_patterns
  - architecture_designs
  - public_documentation
  
internal_local_only:
  - user_data
  - financial_records
  - api_keys
  - detailed_strategy
  
hybrid_sanitize_first:
  - code_with_real_variable_names
  - user_feedback_quotes
  - competitor_analysis
```

---

## Implementation

```python
# Every API call goes through:
class PPAIGateway:
    def before_send(self, prompt):
        prompt = self.strip_pii(prompt)
        prompt = self.redact_secrets(prompt)
        prompt = self.classify_sensitivity(prompt)
        
        if self.is_too_sensitive(prompt):
            return self.route_to_local(prompt)
        
        return self.send_to_claude(prompt)
```

---

**Status**: ACTIVE — Applied to all AI calls
