# Adamus Architecture
## The Complete System Architecture Reference

**This is the canonical architecture document for Adamus.**

---

## System Overview

```yaml
adamus:
  type: "Persistent AI CTO orchestrator"
  purpose: "Build Genre 10x faster while maintaining sovereignty"
  
  core_components:
    1_ai_coordinator: "Routes tasks between brains"
    2_war_room: "Real-time dashboard"
    3_business_ai: "Competitor + financial intelligence"
    4_cambi_ai: "Community + content intelligence"
    5_tech_ai: "Self-improving meta-layer (Adamus itself)"
    
  brains_used:
    claude_code: "Complex coding (8am-5pm, supervised)"
    openclaw: "Autonomous tasks (5pm-8am, 15 hours)"
    ollama: "Background/free tasks"
    
  memory:
    type: "Persistent SQLite → PostgreSQL"
    stores: "All docs, decisions, conversations"
    never_forgets: true
```

---

## Component Architecture

### 1. AI Coordinator
```python
# src/coordinator/ai_coordinator.py
class AICoordinator:
    """
    Heart of Adamus — routes every task to the right brain
    """
    brains: dict  # All available brains
    memory: AdamusMemory  # Complete memory
    scheduler: TaskScheduler  # Priority queue
    approvals: ApprovalSystem  # Augustus gate
```

### 2. War Room
```python
# src/war_room/dashboard.py
class WarRoom:
    """
    Real-time visibility into everything
    """
    panels:
        internal_vitals: "Genre metrics, Adamus status"
        external_radar: "Competitors, market signals"
        strategic_horizon: "Decisions pending"
    access: "http://localhost:5000"
    mobile: "Via Tailscale"
```

### 3. Business AI
```python
# src/business_ai/business_brain.py
class BusinessAI:
    """
    Monitors competition and finances
    """
    monitors: ["Sudowrite", "NovelCrafter", "Notion AI"]
    tracks: ["MRR", "burn", "runway"]
    searches: "Via SearxNG (zero telemetry)"
```

### 4. CAMBI AI
```python
# src/cambi_ai/cambi_brain.py
class CAMBIAI:
    """
    Community + Content Intelligence
    """
    monitors: ["Reddit", "HackerNews", "ProductHunt"]
    generates: "Blog posts, social content, newsletters"
    detects: "Trend signals for Genre"
```

### 5. Tech AI (Adamus Core)
```python
# src/tech_ai/self_improvement.py
class TechAI:
    """
    Adamus builds itself from architecture docs
    """
    reads_docs: "All 90+ architecture files"
    implements: "Missing capabilities during idle"
    tests: "Before every commit"
    prs: "Draft PRs for Augustus review"
```

---

## Data Flow

```
User Request
    → AI Coordinator
        → Load memory (all 90 docs)
        → Choose brain (Claude/OpenClaw/Ollama)
        → Generate comprehensive prompt
        → Execute task
        → Store result
        → Report to War Room
        → (If major) Request approval from Augustus
```

---

## File Structure

```
~/adamus/
├── src/
│   ├── coordinator/    # AI Coordinator, routing
│   ├── war_room/       # Dashboard, metrics
│   ├── business_ai/    # Competitor intelligence
│   ├── cambi_ai/       # Community intelligence
│   └── tech_ai/        # Self-improvement
├── docs/
│   └── architecture/   # All 90 docs
├── config/             # Keys, settings
├── tests/              # All tests
├── logs/               # All logs
└── .adamus/            # Memory database
```

---

## Security Layers (All 8 Active)

```yaml
1_zero_trust: "Trust no input, verify everything"
2_data_governance: "Classify and protect all data"
3_llm_optimization: "Efficient, safe model usage"
4_multi_method: "Multiple validation methods"
5_bias_detection: "Flag biased outputs"
6_prompt_injection_defense: "Block malicious prompts"
7_explainable_ai: "Audit all decisions"
8_vulnerability_management: "Continuous security scanning"
```

---

**Status**: CANONICAL REFERENCE — Do not contradict this document
