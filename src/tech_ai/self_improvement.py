"""
Self-Improvement Meta-Layer: Adamus builds itself.

From SELF_IMPROVING_ADAMUS.md:
  "Every time Augustus gives a command, Adamus:
   1. Executes the command (build Genre feature)
   2. Detects what capability is needed but missing
   3. Adds that capability to build queue"

Priority formula:
  - Blocking Genre = 100 points
  - Security critical = 80 points
  - Augustus requested = 60 points
  - Quick win (<4 hours) = +20 points
"""

import heapq
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from src.tech_ai.capability_builder import (
    Capability,
    CapabilityBuilder,
    CAPABILITY_CATALOGUE,
)

logger = logging.getLogger(__name__)


# ── Keyword → capability mappings ──────────────────────────────────────────

_TASK_SIGNALS: Dict[str, List[str]] = {
    "deploy":    ["credential_vault", "vulnerability_scanner"],
    "save":      ["data_governance"],
    "database":  ["data_governance", "credential_vault"],
    "user":      ["data_governance", "input_filter"],
    "api":       ["credential_vault", "input_filter"],
    "email":     ["email_notifier"],
    "monitor":   ["cost_monitor", "explainability_logger"],
    "payment":   ["data_governance", "credential_vault", "input_filter"],
    "auth":      ["credential_vault", "input_filter"],
    "editor":    ["data_governance", "input_filter"],
    "ai":        ["bias_detector", "explainability_logger", "cost_monitor"],
    "build":     ["vulnerability_scanner"],
    "test":      ["vulnerability_scanner"],
    "content":   ["bias_detector", "input_filter"],
}


@dataclass
class ImprovementTask:
    """A prioritised self-improvement task."""
    priority: int
    capability: Capability
    reason: str

    def __lt__(self, other: "ImprovementTask") -> bool:
        # Higher priority = lower heap value (max-heap via negation)
        return self.priority > other.priority


class ImprovementPrioritizer:
    """
    Scores capabilities by importance.

    From the doc:
      Blocking Genre = 100
      Security critical = 80
      Augustus requested = 60
      Quick win (<4h) = +20
    """

    def calculate_priority(self, cap: Capability) -> int:
        score = 0
        reasons = []

        if cap.is_blocking_genre():
            score += 100
            reasons.append("blocks Genre")

        if cap.is_security_critical():
            score += 80
            reasons.append("security critical")

        if cap.requested:
            score += 60
            reasons.append("explicitly requested")

        if cap.effort_hours < 4:
            score += 20
            reasons.append("quick win")

        reason_str = ", ".join(reasons) if reasons else "standard"
        return score

    def reason_string(self, cap: Capability) -> str:
        parts = []
        if cap.is_blocking_genre():
            parts.append("blocks Genre shipping")
        if cap.is_security_critical():
            parts.append("security critical")
        if cap.requested:
            parts.append("Augustus requested")
        if cap.effort_hours < 4:
            parts.append(f"quick win ({cap.effort_hours}h)")
        return "; ".join(parts) if parts else "standard capability"

    def prioritize(self, caps: List[Capability]) -> List[ImprovementTask]:
        tasks = []
        for cap in caps:
            priority = self.calculate_priority(cap)
            reason = self.reason_string(cap)
            tasks.append(ImprovementTask(priority=priority, capability=cap, reason=reason))
        return sorted(tasks, key=lambda t: t.priority, reverse=True)


class ImprovementBacklog:
    """
    Priority queue of capabilities to build.

    "Adamus maintains a prioritized backlog of capabilities to build.
     Every time Augustus makes a request, backlog updates.
     Adamus works on backlog during idle time."
    """

    def __init__(self):
        self._heap: List[ImprovementTask] = []
        self._seen: set = set()
        self._prioritizer = ImprovementPrioritizer()

    def add(self, cap: Capability) -> bool:
        """Add a capability if not already queued."""
        if cap.name in self._seen:
            return False
        self._seen.add(cap.name)
        task = ImprovementTask(
            priority=self._prioritizer.calculate_priority(cap),
            capability=cap,
            reason=self._prioritizer.reason_string(cap),
        )
        heapq.heappush(self._heap, task)
        logger.debug(f"Backlog: added '{cap.name}' (priority {task.priority})")
        return True

    def pop(self) -> Optional[ImprovementTask]:
        """Return highest-priority task."""
        if self._heap:
            return heapq.heappop(self._heap)
        return None

    def peek(self) -> Optional[ImprovementTask]:
        if self._heap:
            return self._heap[0]
        return None

    def size(self) -> int:
        return len(self._heap)

    def is_empty(self) -> bool:
        return len(self._heap) == 0

    def list_items(self) -> List[Dict]:
        return [
            {
                "name": t.capability.name,
                "priority": t.priority,
                "reason": t.reason,
                "effort_hours": t.capability.effort_hours,
            }
            for t in sorted(self._heap, key=lambda t: t.priority, reverse=True)
        ]

    def update_from_command(self, command: str) -> List[str]:
        """
        Detect capabilities needed by a command and add missing ones to backlog.
        Returns list of newly-added capability names.
        """
        added = []
        command_lower = command.lower()
        needed_names = set()

        for keyword, caps in _TASK_SIGNALS.items():
            if keyword in command_lower:
                needed_names.update(caps)

        # Look up full Capability objects from catalogue
        catalogue_map = {c.name: c for c in CAPABILITY_CATALOGUE}
        for name in needed_names:
            if name in catalogue_map:
                cap = catalogue_map[name]
                if self.add(cap):
                    added.append(name)
                    logger.info(f"Detected need for '{name}' from command: {command[:50]}")

        return added


class SelfImprovementOrchestrator:
    """
    The meta-layer: processes commands and improves Adamus in parallel.

    "Adamus builds itself while building Genre."
    """

    def __init__(self, builder: Optional[CapabilityBuilder] = None):
        self.backlog = ImprovementBacklog()
        self._builder = builder or CapabilityBuilder()
        self._improvement_log: List[Dict] = []

    def detect_missing_capabilities(self, task_description: str) -> List[Capability]:
        """
        Analyse a task description and return capabilities not yet built.
        """
        command_lower = task_description.lower()
        needed_names = set()

        for keyword, caps in _TASK_SIGNALS.items():
            if keyword in command_lower:
                needed_names.update(caps)

        missing = []
        for name in needed_names:
            if not self._builder.is_built(name):
                catalogue_map = {c.name: c for c in CAPABILITY_CATALOGUE}
                if name in catalogue_map:
                    missing.append(catalogue_map[name])

        return missing

    def process_command(self, command: str) -> Dict:
        """
        Process a command: detect gaps and update backlog.

        In full implementation, Genre feature building happens in parallel.
        For now: detect gaps + queue them.
        """
        added = self.backlog.update_from_command(command)
        missing = self.detect_missing_capabilities(command)

        result = {
            "command": command,
            "capabilities_detected": len(missing),
            "newly_queued": added,
            "backlog_size": self.backlog.size(),
            "message": (
                f"Detected {len(missing)} needed capabilities; "
                f"queued {len(added)} new items."
            ),
        }
        logger.info(f"process_command: {result['message']}")
        return result

    def work_on_backlog(self, max_items: int = 1) -> List[str]:
        """
        Build highest-priority items from backlog.

        "During idle time, work on highest-priority backlog items."
        Returns list of capability names successfully built.
        """
        built = []
        for _ in range(max_items):
            task = self.backlog.pop()
            if task is None:
                break

            cap = task.capability
            logger.info(f"Building capability: {cap.name} (priority {task.priority})")
            success = self._builder.build_capability(cap)

            if success:
                built.append(cap.name)
                self._improvement_log.append({
                    "capability": cap.name,
                    "version": cap.version,
                    "priority": task.priority,
                    "reason": task.reason,
                    "built_at": cap.built_at,
                })
                logger.info(f"Capability built: {cap.name} v{cap.version}")
            else:
                logger.warning(f"Failed to build: {cap.name}")

        return built

    def get_improvement_log(self) -> List[Dict]:
        return list(self._improvement_log)

    def get_backlog_summary(self) -> Dict:
        return {
            "backlog_size": self.backlog.size(),
            "items": self.backlog.list_items(),
        }
