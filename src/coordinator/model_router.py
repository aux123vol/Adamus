"""
Model Router: Routes tasks to the right AI brain.

Brain Selection Logic:
- Claude (external): Complex reasoning, coding, Level 1-2 data
- Ollama (local): Sensitive data (Level 3-4), free background tasks

This is a CRITICAL security component.
Wrong routing = data leak.
"""

import os
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, Optional, List, Tuple

logger = logging.getLogger(__name__)


class Brain(Enum):
    """Available AI brains."""
    OPENCODE = "opencode"  # Free hosted models (opencode.ai) - default first
    CLAUDE = "claude"      # External API - best reasoning (power fallback)
    OLLAMA = "ollama"      # Local - free, private


@dataclass
class BrainCapabilities:
    """Capabilities of each brain."""
    name: str
    is_local: bool
    max_data_level: int  # Highest data level it can process
    strengths: List[str]
    cost_per_1k_tokens: float
    context_window: int


class ModelRouter:
    """
    Routes tasks to the appropriate AI brain.

    Decision factors:
    1. Data sensitivity (Level 1-4)
    2. Task complexity
    3. Budget constraints
    4. Required capabilities
    """

    # Brain specifications
    BRAINS = {
        Brain.OPENCODE: BrainCapabilities(
            name="OpenCode",
            is_local=False,
            max_data_level=2,
            strengths=[
                "coding", "general", "free", "open_source",
                "background_work", "simple_tasks"
            ],
            cost_per_1k_tokens=0.0,  # Free hosted models
            context_window=32000
        ),
        Brain.CLAUDE: BrainCapabilities(
            name="Claude",
            is_local=False,
            max_data_level=2,  # Level 1-2 only (after sanitization)
            strengths=[
                "complex_reasoning", "coding", "architecture",
                "debugging", "documentation", "planning"
            ],
            cost_per_1k_tokens=0.009,  # Average of input/output
            context_window=200000
        ),
        Brain.OLLAMA: BrainCapabilities(
            name="Ollama",
            is_local=True,
            max_data_level=4,  # Can handle all levels (local)
            strengths=[
                "simple_tasks", "background_work", "sensitive_data",
                "cost_sensitive", "summarization"
            ],
            cost_per_1k_tokens=0.0,  # Free (local)
            context_window=32000
        )
    }

    def __init__(
        self,
        budget_remaining: float = 200.0,
        prefer_local: bool = False
    ):
        """
        Initialize the model router.

        Args:
            budget_remaining: Remaining monthly budget
            prefer_local: Prefer Ollama when possible
        """
        self.budget_remaining = budget_remaining
        self.prefer_local = prefer_local
        self._opencode_available = self._check_opencode()
        self._claude_available = self._check_claude()
        self._ollama_available = self._check_ollama()

    def _check_claude(self) -> bool:
        """Check if Claude API is available."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.warning("ANTHROPIC_API_KEY not set - Claude unavailable")
            return False
        return True

    def _check_ollama(self) -> bool:
        """Check if Ollama is running locally."""
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        try:
            import urllib.request
            urllib.request.urlopen(f"{ollama_host}/api/tags", timeout=2)
            return True
        except Exception:
            logger.warning(f"Ollama not available at {ollama_host}")
            return False

    def select_brain(
        self,
        data_level: int,
        task_type: str,
        estimated_tokens: int = 1000,
        force_brain: Optional[Brain] = None
    ) -> Tuple[Brain, str]:
        """
        Select the best brain for a task.

        Args:
            data_level: Data sensitivity level (1-4)
            task_type: Type of task (e.g., "coding", "summarization")
            estimated_tokens: Estimated token count
            force_brain: Force a specific brain (if allowed by security)

        Returns:
            (selected_brain, reason)
        """
        # Security override: Level 3-4 MUST use local
        if data_level >= 3:
            if not self._ollama_available:
                raise SecurityError(
                    f"Level {data_level} data requires Ollama but it's not available"
                )
            return Brain.OLLAMA, f"Level {data_level} data requires local processing"

        # Level 4: Never send to any AI
        if data_level == 4:
            raise SecurityError("Level 4 SECRET data cannot be sent to any AI")

        # Force brain (if security allows)
        if force_brain:
            brain_caps = self.BRAINS[force_brain]
            if data_level > brain_caps.max_data_level:
                raise SecurityError(
                    f"Cannot use {force_brain.value} for Level {data_level} data"
                )
            return force_brain, "Forced by request"

        # Prefer local mode
        if self.prefer_local and self._ollama_available:
            return Brain.OLLAMA, "Prefer local mode enabled"

        # Budget check for Claude
        estimated_cost = (estimated_tokens / 1000) * self.BRAINS[Brain.CLAUDE].cost_per_1k_tokens
        if estimated_cost > self.budget_remaining:
            if self._ollama_available:
                return Brain.OLLAMA, "Budget constraint - using free local model"
            raise BudgetError(
                f"Insufficient budget: need ${estimated_cost:.2f}, "
                f"have ${self.budget_remaining:.2f}"
            )

        # Task-based selection
        claude_caps = self.BRAINS[Brain.CLAUDE]
        ollama_caps = self.BRAINS[Brain.OLLAMA]

        # Complex tasks prefer Claude
        complex_tasks = ["coding", "architecture", "debugging", "complex_reasoning"]
        if task_type.lower() in complex_tasks:
            if self._claude_available:
                return Brain.CLAUDE, f"Complex task ({task_type}) - using Claude"
            elif self._ollama_available:
                return Brain.OLLAMA, f"Claude unavailable, falling back to Ollama"
            raise NoAvailableBrainError("No AI brain available")

        # Simple tasks can use either
        simple_tasks = ["summarization", "simple_tasks", "background_work"]
        if task_type.lower() in simple_tasks:
            if self._ollama_available:
                return Brain.OLLAMA, f"Simple task ({task_type}) - using free local model"
            if self._claude_available:
                return Brain.CLAUDE, f"Ollama unavailable, using Claude"
            raise NoAvailableBrainError("No AI brain available")

        # Default: Use Claude if available and budget allows
        if self._claude_available:
            return Brain.CLAUDE, "Default selection - using Claude"
        if self._ollama_available:
            return Brain.OLLAMA, "Default selection - Claude unavailable, using Ollama"

        raise NoAvailableBrainError("No AI brain available")

    def get_brain_status(self) -> Dict[str, Dict]:
        """Get status of all brains."""
        return {
            "claude": {
                "available": self._claude_available,
                "capabilities": self.BRAINS[Brain.CLAUDE].strengths,
                "cost": f"${self.BRAINS[Brain.CLAUDE].cost_per_1k_tokens}/1k tokens",
                "max_data_level": self.BRAINS[Brain.CLAUDE].max_data_level
            },
            "ollama": {
                "available": self._ollama_available,
                "capabilities": self.BRAINS[Brain.OLLAMA].strengths,
                "cost": "Free (local)",
                "max_data_level": self.BRAINS[Brain.OLLAMA].max_data_level
            }
        }

    def update_budget(self, remaining: float) -> None:
        """Update remaining budget."""
        self.budget_remaining = remaining
        logger.info(f"Budget updated: ${remaining:.2f} remaining")


class SecurityError(Exception):
    """Security constraint violated."""
    pass


class BudgetError(Exception):
    """Budget constraint violated."""
    pass


class NoAvailableBrainError(Exception):
    """No AI brain is available."""
    pass
