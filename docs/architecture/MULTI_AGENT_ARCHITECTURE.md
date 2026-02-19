# Multi Agent Architecture
## How Multiple AI Agents Coordinate in Adamus

---

## The Agent Ecosystem

```
ADAMUS ORCHESTRATOR
        │
        ├── Business AI Agent
        │     └── Competitor monitoring, financial tracking
        │
        ├── CAMBI AI Agent  
        │     └── Community trends, content generation
        │
        ├── Tech AI Agent (Adamus itself)
        │     └── Self-improvement, architecture
        │
        └── Task Agents (spawned as needed)
              └── One-off specialized tasks
```

---

## Agent Communication Protocol

```yaml
agent_to_orchestrator:
  method: "Python function calls"
  format: "Structured dict with result + confidence"
  async: "Yes — agents run in parallel"

orchestrator_to_agent:
  method: "Task object with full context"
  includes: "All 90 docs + relevant history"
  timeout: "5 minutes per task"
```

---

## Agent Lifecycle

```yaml
spawn:
  trigger: "Task assigned by coordinator"
  loads: "Context from memory system"
  
execute:
  reads: "Relevant architecture docs"
  implements: "Task from spec"
  tests: "Before completing"
  
report:
  returns: "Result + confidence + side_effects"
  stores: "In Adamus memory"
  
terminate:
  after: "Task complete"
  cleans: "Temp files, not permanent state"
```

---

## Agent Isolation

```yaml
each_agent:
  memory: "Shared via Adamus memory system"
  files: "Isolated workspace"
  network: "Only approved endpoints"
  compute: "Resource limited"
  
prevents:
  - "Agent A interfering with Agent B"
  - "Runaway resource usage"
  - "Cross-contamination of tasks"
```

---

## Coordination Patterns

```yaml
sequential:
  when: "Task B depends on Task A"
  example: "Build feature → write tests → create PR"

parallel:
  when: "Independent tasks"
  example: "Business AI monitors while CAMBI generates content"

pipeline:
  when: "Output of A feeds B feeds C"
  example: "Search → Analyze → Report → Action"
```

---

**Status**: ACTIVE — Multi-agent from Day 1
