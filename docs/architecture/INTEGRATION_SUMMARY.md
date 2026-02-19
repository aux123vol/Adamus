# Integration Summary
## How All Adamus Components Connect

---

## The Connection Map

```
OpenClaw (Autonomous Brain)
    ↕ (via Gateway API)
AI Coordinator (Adamus Heart)
    ↕ (via function calls)
    ├── Business AI → SearxNG → Internet
    ├── CAMBI AI → Content Generation
    ├── Tech AI → Architecture Docs → GitHub
    └── War Room → Dashboard → Augustus
    ↕ (via SQLite)
Memory System (All 90 docs + decisions)
    ↕ (via GitHub)
Genre Repository (Product code)
```

---

## Data Flows

### Build Request Flow
```yaml
1_augustus_requests: "Build login page"
2_coordinator_receives: "Routes to Claude Code"
3_memory_loads: "All context, all docs"
4_claude_builds: "Login page with tests"
5_tests_run: "Automated test suite"
6_pr_created: "Draft PR for review"
7_war_room_updates: "New PR ready"
8_augustus_approves: "Merge to main"
9_memory_stores: "Decision logged"
```

### Autonomous Flow (5pm-8am)
```yaml
1_5pm_trigger: "Augustus goes offline"
2_coordinator_switches: "Routes to OpenClaw"
3_openclaw_reads: "All 90 architecture docs"
4_backlog_prioritized: "By MRR impact"
5_openclaw_implements: "1 feature per 2-3 hours"
6_tests_written: "Before every commit"
7_prs_created: "Draft, never merged"
8_heartbeats_sent: "Telegram every 2 hours"
9_8am_summary: "Full report to War Room"
```

---

## Integration Points

```yaml
internal_apis:
  coordinator_to_memory: "Read/write via Python"
  coordinator_to_brains: "HTTP + subprocess"
  war_room_to_all: "WebSocket for real-time"
  
external_apis:
  anthropic: "Claude API"
  github: "PR management"
  telegram: "Notifications"
  searxng: "Private search"
```

---

**Status**: COMPLETE — All integrations designed
