# Claude
## Working with Claude Code Effectively

### The Correct Install Command
```bash
# WRONG (common mistake)
npm install -g @anthropic/claude-code

# RIGHT
npm install -g @anthropic-ai/claude-code
```

### Role in Adamus
- Primary supervised brain (8am-5pm when you work)
- Best for: Complex architecture, debugging, novel problems
- Not for: Repetitive tasks (OpenClaw), background work (Ollama)

### Starting a Session
```bash
cd ~/adamus
claude
```

### First Prompt Template
```
Read these files first:
- docs/architecture/MASTER_PROTOCOL.md
- docs/architecture/NETWORKED_AI_TRINITY.md
- docs/architecture/WEEK_0_BUILD_PLAN.md

Today: Day [X] of Week 0
Task: [Specific task]
Requirements: Python 3.11+, tests required, PR-ready
Let's build.
```

### Best Practices
- Give full context (reference architecture docs)
- Always ask for tests
- Iterate fast (draft first, refine)
- Use for complex work only

### Cost
- Target: Less than $200/month total
- Alert at $150
- Use Ollama for background tasks

**Status**: ACTIVE — Primary brain for supervised sessions
