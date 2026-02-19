# OpenClaw Security Fixes
## Hardening OpenClaw for Safe Autonomous Operation

### The Known Vulnerabilities (Per Research)
```yaml
vulnerability_1_broad_permissions:
  issue: 'OpenClaw requires broad system access'
  fix: 'Docker sandbox — isolate from host'
  implementation: 'Run OpenClaw in container with limited mounts'

vulnerability_2_prompt_injection:
  issue: 'Malicious instructions in data files'
  fix: 'Input sanitization before any file is processed'
  implementation: 'Scan all inputs with PromptInjectionDefense'

vulnerability_3_skill_repository:
  issue: 'Third-party skills can be malicious'
  fix: 'Allowlist only verified skills'
  implementation: 'No ClawHub auto-install — manual only'

vulnerability_4_data_exfiltration:
  issue: 'Agent could leak sensitive data'
  fix: 'Outbound network restrictions'
  implementation: 'Block all outbound except approved endpoints'
```

### Fixes Applied
```bash
# 1. Run in Docker
docker run --rm -v ~/adamus/src:/workspace --network none openclaw

# 2. File access only to allowed paths
allowed_paths:
  - ~/adamus/src/
  - ~/adamus/docs/
  - ~/adamus/tests/
  deny_all_else: true

# 3. No auto-skill installation
clawHub:
  enabled: false
  manual_only: true
```

**Status**: APPLIED before OpenClaw goes live