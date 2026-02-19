# Operations Testing
## How to Test Adamus Systems

---

## Test Categories

```yaml
unit_tests:
  location: "tests/unit/"
  runs: "On every commit"
  command: "pytest tests/unit/"

integration_tests:
  location: "tests/integration/"
  runs: "Before PRs merge"
  command: "pytest tests/integration/"

security_tests:
  location: "tests/security/"
  runs: "Weekly + before any security change"
  command: "pytest tests/security/"

autonomous_tests:
  location: "tests/autonomous/"
  runs: "OpenClaw always runs these before committing"
  command: "pytest tests/"
```

## Critical Tests (Must Always Pass)

```python
# tests/test_critical.py

def test_adamus_loads_all_docs():
    """Adamus must have all 90+ docs"""
    adamus = Adamus()
    assert len(adamus.documents) >= 90

def test_security_systems_active():
    """All 8 security systems must be running"""
    security = SecurityWrapper()
    assert security.zero_trust.active
    assert security.prompt_defense.active
    assert security.data_governance.active
    # ... all 8

def test_schedule_correct():
    """Autonomous mode only during 5pm-8am"""
    scheduler = Scheduler()
    assert scheduler.autonomous_hours == "17:00-08:00"

def test_approvals_required():
    """Major changes always need approval"""
    approval = ApprovalSystem()
    assert approval.required_for("delete_files")
    assert approval.required_for("deploy_production")
    assert approval.required_for("spend_money")
```

## Test Coverage Requirements

```yaml
minimum_coverage: "80%"
critical_components: "95%"
security_code: "100%"
run_command: "pytest --cov=src tests/"
```

**Status**: ACTIVE — Tests run before every commit
