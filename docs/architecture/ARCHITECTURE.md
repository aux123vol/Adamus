# Architecture
## Adamus System Architecture — One Page Overview

---

## What Adamus Is

Adamus is a **persistent AI CTO orchestrator** that uses interchangeable AI models (brains) as tools to build Genre 10x faster than any human team.

---

## The Three Laws

```
1. Adamus NEVER forgets (loads all 90+ docs before every task)
2. Brains are TOOLS (Claude, OpenClaw, Ollama are interchangeable)
3. Augustus APPROVES major changes (autonomous ≠ unchecked)
```

---

## System Map

```
AUGUSTUS
  ↕ (approvals, reviews)
ADAMUS CORE
  ├── Memory (SQLite — all 90 docs, all decisions)
  ├── AI Coordinator (routes tasks to right brain)
  ├── War Room (real-time dashboard :5000)
  ├── Security (8 systems — always active)
  │
  ├── BRAINS
  │   ├── Claude Code (8am-5pm, supervised)
  │   ├── OpenClaw (5pm-8am, autonomous)
  │   └── Ollama (free background tasks)
  │
  ├── INTELLIGENCE
  │   ├── Business AI (competitors + finance)
  │   └── CAMBI AI (community + content)
  │
  └── INFRASTRUCTURE
      ├── SearxNG (private search)
      ├── Tailscale (mobile access)
      └── GitHub (everything in version control)
```

---

## Files

```
~/adamus/
├── src/coordinator/    → AI Coordinator, routing, memory
├── src/war_room/       → Dashboard
├── src/business_ai/    → Competitor + financial intelligence  
├── src/cambi_ai/       → Community + content intelligence
├── src/tech_ai/        → Self-improvement engine
├── docs/architecture/  → All 90+ documents (loaded always)
├── tests/              → All tests (required before commit)
├── logs/               → All logs (audit trail)
└── .adamus/memory/     → SQLite database (persistent memory)
```

---

## Schedule

```
8am-5pm:  Augustus works → Adamus uses Claude Code (supervised)
5pm-2am:  Augustus at job → Adamus uses OpenClaw (autonomous)
2am-8am:  Augustus sleeps → Adamus uses OpenClaw (continues)
```

**One doc rule**: When in doubt, re-read MASTER_PROTOCOL.md

**Status**: CANONICAL OVERVIEW — Start here if lost
