# Logging Infrastructure
## Adamus Comprehensive Logging System

---

## Log Categories

```yaml
categories:
  ai_calls: "Every prompt sent to every brain"
  decisions: "Every routing/approval decision"
  builds: "Every file created/modified"
  security: "Every security event"
  performance: "Response times, costs"
  errors: "All errors with stack traces"
  user_actions: "Augustus approvals/rejections"
```

## Log Format

```json
{
  "timestamp": "2026-02-17T08:00:00Z",
  "level": "INFO",
  "component": "ai_coordinator",
  "brain_used": "claude_code",
  "task_type": "build_feature",
  "tokens_used": 1250,
  "cost_usd": 0.0125,
  "success": true,
  "duration_ms": 3200,
  "security_flags": []
}
```

## Storage

```yaml
location: "~/adamus/logs/"
rotation: "Daily, keep 30 days"
format: "JSON (machine readable)"
war_room: "Real-time streaming"
alerts: "Errors → Telegram immediately"
```

**Status**: ACTIVE from Day 1
