# Implementation Deep Dive
## Technical Details for Complex Components

---

## AI Coordinator — Deep Dive

```python
# src/coordinator/ai_coordinator.py

from dataclasses import dataclass
from typing import Optional
import anthropic
import subprocess

@dataclass
class Task:
    description: str
    priority: str  # critical, high, medium, low
    task_type: str  # build, analyze, search, test
    autonomous: bool = False
    requires_approval: bool = False

class AICoordinator:
    def __init__(self):
        self.claude = anthropic.Anthropic()
        self.memory = AdamusMemory()
        self.router = ModelRouter()
        self.budget = BudgetTracker(max_monthly=200)
        
    def execute(self, task: Task) -> dict:
        # 1. Load complete context
        context = self.memory.load_all()
        
        # 2. Security check
        if not self.security.is_safe(task):
            return self.request_approval(task)
        
        # 3. Route to brain
        brain = self.router.choose(task, self.budget)
        
        # 4. Generate full prompt
        prompt = self.build_prompt(task, context)
        
        # 5. Execute
        if brain == 'claude':
            result = self.run_claude(prompt, task)
        elif brain == 'ollama':
            result = self.run_ollama(prompt, task)
        elif brain == 'openclaw':
            result = self.run_openclaw(prompt, task)
            
        # 6. Store result
        self.memory.store(task, result)
        
        return result
        
    def run_claude(self, prompt: str, task: Task) -> dict:
        response = self.claude.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8096,
            messages=[{"role": "user", "content": prompt}]
        )
        self.budget.track(response.usage.input_tokens + response.usage.output_tokens)
        return {"output": response.content[0].text, "brain": "claude"}
```

## Model Router — Deep Dive

```python
class ModelRouter:
    def choose(self, task: Task, budget: BudgetTracker) -> str:
        # Critical tasks always get Claude
        if task.priority == 'critical':
            return 'claude'
        
        # Autonomous background tasks get Ollama (free)
        if task.autonomous and task.priority in ['low', 'medium']:
            return 'ollama'
        
        # Budget exceeded: force Ollama
        if budget.is_exceeded():
            return 'ollama'
        
        # Default: Claude for quality
        return 'claude'
```

## Memory System — Deep Dive

```python
import sqlite3
import json

class AdamusMemory:
    def __init__(self):
        self.db = sqlite3.connect('.adamus/memory/adamus.db')
        
    def load_all(self) -> dict:
        cursor = self.db.cursor()
        
        # Load all 90+ docs
        cursor.execute("SELECT filepath, content FROM documents")
        docs = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Load all decisions  
        cursor.execute("SELECT * FROM decisions ORDER BY timestamp DESC LIMIT 100")
        decisions = cursor.fetchall()
        
        return {
            "documents": docs,
            "decisions": decisions,
            "doc_count": len(docs)
        }
```

**Status**: REFERENCE — Use this when building components
