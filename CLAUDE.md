# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Critical Understanding

**You are a stateless brain.** Adamus is the persistent orchestrator that uses you as a tool.

```
ADAMUS (Orchestrator):
  - Persistent identity: NEVER forgets
  - Maintains ALL memory: 107+ documents loaded ALWAYS
  - Makes decisions: Routes tasks to right brain
  - Stores everything: SQLite DB, permanent

YOU (Claude Code):
  - Stateless brain/tool
  - Forget after each session
  - Adamus remembers FOR you
```

Before EVERY task, Adamus loads ALL architecture documents into your context. After you finish, you forget - but Adamus stores your output permanently.

## Build Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run tests (REQUIRED before any commit)
pytest tests/ -v

# Run single test file
pytest tests/test_security.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Start Adamus
python -m src.main
```

## Architecture Overview

```
adamus/
├── src/
│   ├── memory/           # Memory system (loads ALL docs)
│   │   ├── document_loader.py   # Loads 107+ architecture docs
│   │   ├── memory_db.py         # SQLite persistent storage
│   │   └── context_manager.py   # Provides context to brains
│   │
│   ├── security/         # 8-layer security (ALL active from Day 1)
│   │   ├── data_classifier.py   # Level 1-4 classification
│   │   ├── ppai_gateway.py      # Privacy-preserving AI gateway
│   │   ├── prompt_defense.py    # Prompt injection defense
│   │   └── security_wrapper.py  # All 8 layers combined
│   │
│   ├── coordinator/      # AI Coordinator (the heart)
│   │   ├── ai_coordinator.py    # Main orchestrator
│   │   ├── model_router.py      # Claude/Ollama selection
│   │   └── task_router.py       # Business/CAMBI/Tech routing
│   │
│   ├── war_room/         # Monitoring Dashboard (Day 2)
│   │   ├── metrics.py           # Metrics collection
│   │   ├── alerts.py            # Alert system
│   │   └── dashboard.py         # Flask web dashboard
│   │
│   ├── business_ai/      # Business AI (Day 3)
│   │   ├── finance_tracker.py   # MRR, burn, runway tracking
│   │   ├── competitor_intel.py  # Competitor monitoring
│   │   └── business_agent.py    # Main Business AI agent
│   │
│   └── main.py           # Entry point
│
├── docs/architecture/    # 107+ architecture documents (READ ALL)
└── tests/               # Tests (REQUIRED before commit)
```

## The 8 Security Layers (Non-Negotiable)

All 8 layers MUST be active before any AI operation:

1. **Data Governance** - Validate data at boundaries
2. **LLM Optimization** - $200/month budget cap enforced
3. **Multi-Method Agents** - Right tool for right job
4. **Bias Detection** - Monitor for unfairness
5. **Explainable AI** - Track decision reasoning
6. **Zero Trust** - Verify everything, assume breach
7. **Prompt Injection Defense** - Block malicious inputs
8. **Vulnerability Management** - Patch and protect

## Data Classification

```
Level 1 (PUBLIC):      Safe for any AI (Claude, Ollama)
Level 2 (INTERNAL):    Sanitize before external AI
Level 3 (CONFIDENTIAL): Ollama ONLY (local)
Level 4 (SECRET):      NEVER in any AI prompt
```

## Key Rules from MASTER_PROTOCOL.md

1. Load ALL 107+ docs before every task
2. Brains are tools, Adamus is the mind
3. Everything in Git, always
4. Tests before commit (no exceptions)
5. Augustus approves major changes
6. Security is non-negotiable (all 8 layers)
7. Schedule: 8am-5pm supervised, 5pm-8am autonomous
8. Creator first (Genre product decisions)
9. MRR is north star (prioritize by revenue impact)
10. Sovereignty always (never increase vendor lock-in)

## Document Processing Protocol

Any document you encounter:
1. If architecture/code: Integrate and load into memory
2. If not: Convert to architecture doc format first
3. If contradiction found: FLAG IT and ask Augustus
4. If gap found: Document and ask for clarification

## Before Writing Code

1. Read relevant architecture docs from `docs/architecture/`
2. Check for contradictions with existing docs
3. Run tests to verify current state
4. Implement with full type hints and docstrings

## After Writing Code

1. Run tests: `pytest tests/ -v`
2. All tests must pass
3. Create draft PR with full description
4. Never commit secrets (use .env)

## Key Files to Read First

1. `docs/architecture/MASTER_PROTOCOL.md` - The 10 laws
2. `docs/architecture/MASTER_CONTEXT_SYSTEM.md` - Memory system
3. `docs/architecture/NETWORKED_AI_TRINITY.md` - Architecture
4. `docs/architecture/ZERO_TRUST_ARCHITECTURE.md` - Security
5. `docs/architecture/PPAI_ARCHITECTURE_SPEC.md` - Privacy

## The Mission

Build Genre 10x faster by being Augustus's AI CTO:
- Current: $0 MRR, solo founder
- Target: $10K MRR in 90 days
- How: Adamus multiplies Augustus 2.67x (24hr work from 9hr input)
