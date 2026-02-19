# Product Spec
## Adamus v1.0 Full Product Specification

---

## What Adamus Is

```yaml
type: "Autonomous AI CTO system"
purpose: "Build Genre 10x faster than any human team"
owner: "Augustus"
built_by: "Itself (with initial help from Claude Code)"
```

---

## Core Capabilities

### 1. AI Coordinator
```yaml
function: "Central brain that routes all tasks"
inputs: ["Task description", "Priority", "Context"]
outputs: ["Completed implementation", "Test results", "PR"]
brains: ["Claude Code", "OpenClaw", "Ollama"]
```

### 2. War Room Dashboard
```yaml
function: "Real-time visibility into everything"
panels:
  internal: "Genre MRR, users, Adamus capabilities"
  external: "Competitors, trends, market"
  strategic: "Pending decisions, approvals"
access: "http://localhost:5000, mobile via Tailscale"
```

### 3. Business AI
```yaml
function: "Competitive and financial intelligence"
monitors: ["Sudowrite", "NovelCrafter", "Notion AI"]
tracks: ["MRR", "burn rate", "runway"]
search: "Via SearxNG (zero telemetry)"
reports: "Daily briefing in War Room"
```

### 4. CAMBI AI
```yaml
function: "Community and content intelligence"
monitors: ["Reddit r/writing", "HackerNews", "ProductHunt"]
generates: ["Blog posts", "Social content", "Newsletters"]
detects: "Trend signals relevant to Genre"
```

### 5. Tech AI (Self-Improvement)
```yaml
function: "Adamus builds and improves itself"
reads: "All 90+ architecture docs continuously"
implements: "Missing capabilities from backlog"
schedule: "5pm-8am autonomous (15 hours/night)"
creates: "Draft PRs for Augustus review"
```

---

## Technical Stack

```yaml
language: "Python 3.11+"
memory: "SQLite → PostgreSQL"
frontend: "Flask + React (War Room)"
ai_primary: "Claude via Anthropic API"
ai_autonomous: "OpenClaw"
ai_local: "Ollama"
search: "SearxNG"
vcs: "GitHub"
mobile: "Tailscale"
```

---

## Non-Functional Requirements

```yaml
performance:
  response_time: "< 500ms for routing"
  uptime: "> 99%"
  
security:
  all_8_systems: "Always active"
  zero_trust: "Never trust any input"
  
cost:
  target: "< $200/month Claude API"
  local_work: "$0 (Ollama)"
  
privacy:
  telemetry: "Zero"
  data: "Local first"
  search: "SearxNG"
```

---

**Status**: v0.1 IN BUILD — Week 0
