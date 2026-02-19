# Multi-Method Agentic AI Architecture for Adamus
## From Video 3: Use Right Tool for Right Job

**CRITICAL**: "LLMs are wonderful but they need to be not the only tool in your toolbox. You need to combine them with workflow to manage state, and decisions and business rules for consistency."

**Why**: LLMs CANNOT handle stateful processes, consistent logic, or explainable decisions alone.

---

## Nine Agent Types for Adamus

### 1. Chat Agent (LLM) - Interface
```python
# Understand Augustus's natural language
"Deploy Lore" → ExecutionIntent(action="deploy", target="lore")
"Should we build X?" → AnalysisIntent(type="strategic")
```

### 2. Orchestration Agent (LLM) - Router
```python
# Look up registry, route to specialist agents
registry = {
    "policy_questions": PolicyAgent(),
    "execution_tasks": WorkflowAgent(),
    "strategic_analysis": DecisionAgent()
}
```

### 3. Policy Agent (LLM + RAG) - Documentation
```python
# Answer questions from docs
vector_db.search("deployment policy") → retrieve docs → LLM summarizes
```

### 4. Workflow Agent (NOT LLM!) - State Management
```python
# BPMN workflow engine for multi-step processes
# CRITICAL: Must remember state if Augustus interrupts
# Example: Deployment workflow
#   1. Run tests
#   2. Build Docker (Augustus leaves, comes back later)
#   3. Resume: Push to registry
#   4. Deploy to prod
```

### 5. Decision Agent (NOT LLM!) - Business Rules
```python
# Deterministic, explainable decisions
# Example: GO LEAN evaluator
if pmf_achieved == False and feature_request == True:
    return DENY("Focus on PMF first")
    
# Must be 100% consistent - same input → same output
```

### 6. Data Agent (System) - Database Access
```python
# Access PostgreSQL, Redis, APIs
# Provide data to other agents
```

### 7. Ingestion Agent (LLM) - Document Processing
```python
# LLMs EXCEL at extracting from messy documents
# Augustus uploads handwritten spec → structured JSON
```

### 8. Companion Agent (LLM) - Augustus Assistant
```python
# Quick answers while Augustus works
# Access all data, query all agents
# "What's our current MRR?" → instant answer
```

### 9. Explainer Agent (LLM) - Human Translation
```python
# Convert technical logs to English
decision_log = {"rule_fired": "R-341", "condition": "pmf==false"}
→ "Denied because you haven't reached PMF yet"
```

---

## Why This Architecture

```yaml
llm_for:
  - natural_language: "Chat, Policy, Companion, Explainer agents"
  - summarization: "Policy agent converts docs → English"
  - extraction: "Ingestion agent handles messy docs"

NOT_llm_for:
  - state_management: "Workflow agent remembers multi-step"
  - consistency: "Decision agent same logic every time"
  - explainability: "Decision agent explicit rule trace"
```

---

## Integration with Adamus

Existing multi-agent = different models (Claude, Codex, Ollama)
New multi-method = different AGENT TYPES per model

**Result**: Claude handles chat + policy + explainer, Local model handles workflow + decisions

---

## Implementation (Week 1-8)

Week 1-2: Chat + Orchestration + Policy agents
Week 3-4: Workflow + Decision agents  
Week 5-6: Ingestion + Explainer + Data agents
Week 7-8: Integration testing with Augustus

**Key**: Use LLMs where they excel, deterministic systems for consistency.
