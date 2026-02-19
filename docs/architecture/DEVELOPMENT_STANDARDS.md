# Development Standards
## Adamus Code Quality Requirements

---

## Language Standards

```yaml
python:
  version: "3.11+"
  style: "Black formatter"
  typing: "Type hints required"
  docstrings: "All public functions"
  
javascript:
  version: "ES2022+"
  style: "Prettier"
  typing: "TypeScript preferred"
```

## Testing Requirements

```yaml
mandatory:
  - unit_tests: "All new functions"
  - integration_tests: "All new APIs"
  - coverage_target: ">80%"
  
openclaw_rule:
  - never_commit_without_tests: true
  - tests_must_pass: true
  - test_file_naming: "test_[feature].py"
```

## Security Standards

```yaml
never_commit:
  - api_keys: "Use env vars"
  - passwords: "Use secrets manager"
  - user_data: "Never in code"
  - pii: "Always redacted in logs"
```

## PR Standards

```yaml
pr_required_fields:
  - what_changed: "Summary of changes"
  - why_changed: "Business reason"
  - tests_added: "List test files"
  - security_impact: "Any security considerations"
  
openclaw_prs:
  - always_draft: true
  - wait_for_augustus: true
  - never_auto_merge: true
```

**Status**: ENFORCED — Adamus checks all PRs against these standards
