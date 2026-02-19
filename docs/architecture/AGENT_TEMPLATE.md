# Agent Template
## Reusable Template for New Adamus Skills/Agents

---

## Skill Template Format (OpenClaw Compatible)

```markdown
---
name: [Skill Name]
description: [What this skill does]
author: Augustus
version: 1.0.0
adamus_component: [coordinator/business_ai/cambi_ai/tech_ai]
---

## Objective
[Clear statement of what this skill accomplishes]

## Trigger
[What causes this skill to run]

## Process
1. [Step 1]
2. [Step 2]
3. [Step 3]

## Security Constraints
- NEVER delete files without approval
- NEVER modify .env or credentials
- ALWAYS run tests before committing
- ALWAYS create draft PRs (never push to main)

## Success Criteria
- [Measurable outcome 1]
- [Measurable outcome 2]

## Error Handling
- If blocked: Create GitHub issue, continue to next task
- If uncertain: Flag for Augustus review
- If error: Log, alert via Telegram, stop
```

---

## Python Agent Template

```python
class AdamusAgent:
    def __init__(self, name: str):
        self.name = name
        self.memory = AdamusMemory()
        self.security = SecurityWrapper()
        self.logger = Logger(name)
        
    def execute(self, task: dict) -> dict:
        self.logger.start(task)
        
        # Security check
        if not self.security.is_safe(task):
            return self.request_approval(task)
        
        # Load context
        context = self.memory.load_relevant(task)
        
        # Execute
        result = self._execute(task, context)
        
        # Store
        self.memory.store(task, result)
        self.logger.complete(result)
        
        return result
        
    def _execute(self, task: dict, context: dict) -> dict:
        raise NotImplementedError("Implement in subclass")
```

**Status**: USE THIS for every new agent
