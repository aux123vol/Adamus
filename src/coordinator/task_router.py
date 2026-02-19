"""
Task Router: Routes tasks between AI agents.

The Trinity:
- Business AI: Finance, competition, acquisitions
- CAMBI AI: Community, content, cultural signals
- Tech AI (Adamus): Infrastructure, code, self-improvement

Tasks are routed to the right agent based on:
- Task domain
- Required capabilities
- Current priorities
"""

import logging
from enum import Enum
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class Agent(Enum):
    """The AI Trinity agents."""
    BUSINESS = "business_ai"  # Finance, competition
    CAMBI = "cambi_ai"        # Community, content
    TECH = "tech_ai"          # Infrastructure, code (Adamus core)
    COORDINATOR = "coordinator"  # Cross-agent tasks


class TaskPriority(Enum):
    """Task priority levels."""
    CRITICAL = 1    # Security, urgent bugs
    HIGH = 2        # MRR-impacting
    MEDIUM = 3      # Standard work
    LOW = 4         # Nice-to-have
    BACKGROUND = 5  # Fill-in work


@dataclass
class Task:
    """A task to be routed."""
    id: str
    description: str
    agent: Agent
    priority: TaskPriority
    data_level: int  # 1-4
    created_at: str
    deadline: Optional[str] = None
    dependencies: List[str] = None
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.metadata is None:
            self.metadata = {}


class TaskRouter:
    """
    Routes tasks to appropriate AI agents.

    Implements the Networked AI Trinity architecture:
    - Business AI handles business domain
    - CAMBI AI handles community/content domain
    - Tech AI (Adamus) handles technical domain
    - Coordinator handles cross-domain tasks
    """

    # Keywords that map to agents
    AGENT_KEYWORDS = {
        Agent.BUSINESS: [
            "finance", "mrr", "revenue", "budget", "competitor",
            "acquisition", "funding", "burn", "runway", "pricing",
            "legal", "compliance", "cost"
        ],
        Agent.CAMBI: [
            "community", "content", "sentiment", "engagement",
            "marketing", "social", "culture", "ritual", "brand",
            "seo", "video", "creative", "believer"
        ],
        Agent.TECH: [
            "code", "build", "implement", "deploy", "test",
            "architecture", "infrastructure", "security", "api",
            "database", "feature", "bug", "performance"
        ]
    }

    def __init__(self):
        """Initialize the task router."""
        self._task_queue: Dict[Agent, List[Task]] = {
            Agent.BUSINESS: [],
            Agent.CAMBI: [],
            Agent.TECH: [],
            Agent.COORDINATOR: []
        }
        self._completed: List[Task] = []
        self._task_counter = 0

    def route_task(
        self,
        description: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        data_level: int = 2,
        force_agent: Optional[Agent] = None,
        deadline: Optional[str] = None,
        metadata: Optional[Dict] = None
    ) -> Task:
        """
        Route a task to the appropriate agent.

        Args:
            description: Task description
            priority: Task priority
            data_level: Data sensitivity level
            force_agent: Force routing to specific agent
            deadline: Optional deadline
            metadata: Additional task metadata

        Returns:
            Created Task object
        """
        self._task_counter += 1
        task_id = f"task_{datetime.now().strftime('%Y%m%d')}_{self._task_counter:04d}"

        # Determine agent
        if force_agent:
            agent = force_agent
            route_reason = "Forced routing"
        else:
            agent, route_reason = self._determine_agent(description)

        task = Task(
            id=task_id,
            description=description,
            agent=agent,
            priority=priority,
            data_level=data_level,
            created_at=datetime.now().isoformat(),
            deadline=deadline,
            metadata=metadata or {}
        )

        task.metadata["route_reason"] = route_reason

        # Add to queue
        self._task_queue[agent].append(task)

        # Sort by priority
        self._task_queue[agent].sort(key=lambda t: t.priority.value)

        logger.info(
            f"Task {task_id} routed to {agent.value}: "
            f"{description[:50]}... ({route_reason})"
        )

        return task

    def _determine_agent(self, description: str) -> tuple[Agent, str]:
        """Determine the best agent for a task."""
        description_lower = description.lower()

        scores = {agent: 0 for agent in Agent if agent != Agent.COORDINATOR}

        for agent, keywords in self.AGENT_KEYWORDS.items():
            for keyword in keywords:
                if keyword in description_lower:
                    scores[agent] += 1

        # Check for cross-domain tasks
        agents_with_hits = [a for a, s in scores.items() if s > 0]
        if len(agents_with_hits) > 1:
            # Multiple domains involved - coordinate
            max_score = max(scores.values())
            if max_score < 3:  # No clear winner
                return Agent.COORDINATOR, "Cross-domain task"

        # Return highest scoring agent
        best_agent = max(scores, key=scores.get)
        if scores[best_agent] == 0:
            # No keywords matched - default to Tech
            return Agent.TECH, "Default routing (no keywords matched)"

        return best_agent, f"Keyword match (score: {scores[best_agent]})"

    def get_next_task(self, agent: Agent) -> Optional[Task]:
        """Get the next highest-priority task for an agent."""
        if not self._task_queue[agent]:
            return None

        # Get highest priority (lowest value)
        task = self._task_queue[agent].pop(0)
        return task

    def complete_task(self, task: Task, result: str) -> None:
        """Mark a task as completed."""
        task.metadata["completed_at"] = datetime.now().isoformat()
        task.metadata["result"] = result[:500]  # Truncate for storage
        self._completed.append(task)

        logger.info(f"Task {task.id} completed by {task.agent.value}")

    def get_queue_status(self) -> Dict[str, Dict]:
        """Get status of all queues."""
        status = {}
        for agent in Agent:
            tasks = self._task_queue.get(agent, [])
            status[agent.value] = {
                "pending": len(tasks),
                "priorities": {
                    p.name: len([t for t in tasks if t.priority == p])
                    for p in TaskPriority
                }
            }

        status["completed_total"] = len(self._completed)
        return status

    def get_agent_tasks(
        self,
        agent: Agent,
        include_completed: bool = False
    ) -> List[Task]:
        """Get all tasks for an agent."""
        pending = self._task_queue[agent].copy()

        if include_completed:
            completed = [t for t in self._completed if t.agent == agent]
            return pending + completed

        return pending

    def prioritize_by_mrr_impact(self) -> None:
        """
        Re-prioritize all tasks by MRR impact.

        This follows the MASTER_PROTOCOL rule:
        "All work ranked by MRR impact"
        """
        for agent in Agent:
            for task in self._task_queue[agent]:
                mrr_keywords = [
                    "revenue", "mrr", "payment", "subscription",
                    "customer", "conversion", "churn", "retention"
                ]

                task_lower = task.description.lower()
                mrr_hits = sum(1 for kw in mrr_keywords if kw in task_lower)

                if mrr_hits >= 2:
                    task.priority = TaskPriority.HIGH
                    task.metadata["mrr_prioritized"] = True

            # Re-sort
            self._task_queue[agent].sort(key=lambda t: t.priority.value)
