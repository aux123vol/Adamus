# Threat Model
## Known Threats to Adamus and Genre

---

## Threat Categories

### T1: Prompt Injection
```yaml
threat: "Malicious instructions embedded in data"
likelihood: "HIGH (OpenClaw processes external data)"
impact: "HIGH (could execute unintended actions)"
mitigation:
  - PROMPT_INJECTION_DEFENSE.md
  - Input sanitization on all external data
  - Sandboxed execution
```

### T2: Data Exfiltration
```yaml
threat: "AI leaks sensitive data externally"
likelihood: "MEDIUM"
impact: "HIGH (user data, API keys, strategy)"
mitigation:
  - PPAI_ARCHITECTURE_SUMMARY.md
  - Local-first for sensitive data
  - Outbound network restrictions
```

### T3: Runaway Agent
```yaml
threat: "OpenClaw runs out of control"
likelihood: "LOW (sandboxed)"
impact: "HIGH (could delete code or spend money)"
mitigation:
  - Docker sandbox
  - Approval system for major actions
  - Kill switch always available
```

### T4: API Key Compromise
```yaml
threat: "Anthropic API key stolen"
likelihood: "LOW (if .env protected)"
impact: "HIGH (billing, data access)"
mitigation:
  - Never commit .env
  - Rotate keys monthly
  - Budget alerts at $150
```

### T5: Dependency Attack
```yaml
threat: "Malicious npm/pip package"
likelihood: "LOW-MEDIUM"
impact: "HIGH"
mitigation:
  - Pin dependency versions
  - Audit new packages
  - Use well-known packages only
```

---

## Risk Matrix

```yaml
critical_mitigate_now:
  - T1_prompt_injection
  - T4_api_key_compromise

high_mitigate_week_0:
  - T2_data_exfiltration
  - T3_runaway_agent

medium_monitor:
  - T5_dependency_attack
```

**Status**: ACTIVE — All critical threats mitigated before launch
