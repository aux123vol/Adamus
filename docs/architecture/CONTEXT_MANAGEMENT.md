# Context Management
## How Adamus Manages Context Across All Brains

---

## The Context Problem

```yaml
problem:
  brains_forget: "Claude Code, OpenClaw, Ollama are all stateless"
  every_call: "Fresh start with no memory"
  naive_approach: "Brain loses all context between sessions"
  
  result_without_solution:
    - "OpenClaw asks same clarifying questions repeatedly"
    - "Claude Code contradicts previous decisions"
    - "Inconsistent implementations across sessions"
```

## Adamus's Solution

```yaml
solution:
  adamus_remembers: "Persistent orchestrator with full memory"
  before_every_brain_call: "Load complete context"
  context_includes:
    - "All 90+ architecture docs"
    - "All past decisions"
    - "Current task state"
    - "Genre product state"
    - "Augustus preferences"
```

## Context Layers

```yaml
layer_1_architecture: "Static — the 90 docs (changes rarely)"
layer_2_decisions: "Semi-static — major decisions made"
layer_3_state: "Dynamic — current build status"
layer_4_task: "Task-specific — what we're doing now"
layer_5_conversation: "Session history"
```

## Context Window Management

```yaml
for_claude_200k_context:
  fits_all: "200K tokens fits most context"
  priority_if_too_large:
    1: "Current task context"
    2: "Critical architecture docs"
    3: "Recent decisions"
    4: "Older history (summarized)"
    
for_ollama_32k_context:
  priority:
    1: "Current task only"
    2: "Relevant doc sections"
    3: "Critical constraints"
```

**Status**: ACTIVE — Context loaded before every brain call
