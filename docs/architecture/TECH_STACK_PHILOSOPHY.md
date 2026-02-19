# Tech Stack Philosophy
## How Adamus and Genre Choose Technologies

**Core Philosophy**: Choose boring technology for infrastructure, cutting-edge only where it creates moats.

---

## The Decision Framework

```yaml
use_boring_tech_for:
  - databases: "PostgreSQL, SQLite — proven, reliable"
  - authentication: "Standard JWT, OAuth — don't reinvent"
  - hosting: "Standard cloud — no exotic providers"
  - version_control: "Git/GitHub — non-negotiable"

use_cutting_edge_for:
  - ai_features: "Latest models — this IS the moat"
  - ip_tracking: "Novel Lore system — competitive advantage"
  - autonomous_building: "OpenClaw + Adamus — 10x velocity"
```

---

## Genre's Tech Stack

```yaml
frontend:
  framework: "React/Next.js"
  styling: "Tailwind CSS"
  state: "Zustand or Context"
  why: "Hire-able, battle-tested, fast to build"

backend:
  language: "Python (FastAPI) or Node.js"
  database: "PostgreSQL (main) + Redis (cache)"
  auth: "Clerk or Auth0"
  why: "Mature ecosystems, Adamus knows them well"

ai_layer:
  primary: "Claude API (Anthropic)"
  secondary: "Ollama (local)"
  future: "Your own model"
  why: "Best quality now, sovereignty later"

infrastructure:
  hosting: "DigitalOcean or Railway (simple)"
  cdn: "Cloudflare"
  search: "SearxNG (self-hosted, private)"
  why: "Simple, cost-effective, sovereign"

payments:
  processor: "Stripe"
  why: "Standard, reliable, creators know it"

version_control:
  platform: "GitHub"
  strategy: "Everything in Git, always"
  why: "Non-negotiable foundation"
```

---

## Adamus's Tech Stack

```yaml
orchestration: "Python 3.11+"
memory: "SQLite (local) → PostgreSQL (scale)"
brains:
  - claude_code: "Complex coding"
  - openclaw: "Autonomous tasks"
  - ollama: "Background work"
messaging: "Telegram (OpenClaw interface)"
monitoring: "Custom War Room (Flask + React)"
search: "SearxNG"
mobile: "Tailscale"
```

---

## Anti-Patterns

```yaml
never:
  - over_engineer: "If it works at 10 users, ship it"
  - premature_scale: "Optimize when you have the problem"
  - exotic_tech: "If Adamus can't maintain it, don't use it"
  - vendor_lock: "Always have an exit path"
  - no_tests: "OpenClaw always writes tests"
```

---

## Evolution Path

```yaml
week_0_8:
  focus: "Working, not perfect"
  stack: "Minimal viable"
  
month_3_6:
  focus: "Scale to 1000 users"
  stack: "Add monitoring, optimize queries"
  
year_1:
  focus: "Enterprise-ready"
  stack: "Full observability, DR, compliance"
```

---

**Status**: ACTIVE — Stack defined and locked for Week 0
