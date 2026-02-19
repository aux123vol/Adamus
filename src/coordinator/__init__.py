"""
Adamus Coordinator

The AI Coordinator orchestrates:
- Business AI (finance, competition)
- CAMBI AI (community, content)
- Tech AI (Adamus core - infrastructure)

Routes tasks to the right brain (Claude, Ollama).
All coordinated through this central orchestrator.
"""

from .ai_coordinator import AICoordinator
from .model_router import ModelRouter
from .task_router import TaskRouter

__all__ = ['AICoordinator', 'ModelRouter', 'TaskRouter']
