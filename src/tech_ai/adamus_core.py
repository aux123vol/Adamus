"""
Adamus Core: Tech AI — the self-improving builder.

From SELF_IMPROVING_ADAMUS.md:
  "Adamus is the persistent orchestrator.
   Brains are interchangeable tools.
   Brains change, Adamus stays consistent."

AdamusCore:
  1. Receives commands from Augustus
  2. Detects missing capabilities (self-improvement loop)
  3. Scaffolds Genre features (genre builder)
  4. Reports status to War Room
  5. Runs improvement cycles autonomously
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from src.tech_ai.capability_builder import Capability, CapabilityBuilder, CAPABILITY_CATALOGUE
from src.tech_ai.genre_builder import GenreBuilder, GenreFeature
from src.tech_ai.self_improvement import SelfImprovementOrchestrator

logger = logging.getLogger(__name__)

_START_TIME = datetime.utcnow()


class AdamusCore:
    """
    Adamus Tech AI core.

    The meta-system that builds Genre AND improves itself simultaneously.

    Usage:
        core = AdamusCore()
        result = core.process("Build Lore v2 editor")
        # → detects needed capabilities, queues them
        # → scaffolds Genre feature scaffold

        core.run_improvement_cycle()
        # → builds highest-priority capability from backlog
    """

    VERSION = "0.1.0"

    def __init__(self, base_path: Optional[Path] = None):
        self._base = base_path or Path(".")
        self._builder = CapabilityBuilder(base_path=self._base)
        self._genre = GenreBuilder(base_path=self._base)
        self._orchestrator = SelfImprovementOrchestrator(builder=self._builder)
        self._command_log: List[Dict] = []
        logger.info(f"AdamusCore v{self.VERSION} initialized — Brains change, Adamus stays consistent.")

    # ── Primary interface ─────────────────────────────────────────────────────

    def process(self, command: str, scaffold_genre: bool = False) -> Dict:
        """
        Process a command from Augustus.

        Parallel execution (per architecture doc):
          Thread 1: Genre feature building (scaffold if requested)
          Thread 2: Self-improvement — detect + queue missing capabilities

        Args:
            command:       Natural language command
            scaffold_genre: If True, find and scaffold matching Genre feature

        Returns:
            dict with genre_result, self_improvement_result, backlog_size
        """
        logger.info(f"Processing command: {command[:80]}")

        # Thread 2: Self-improvement — always runs
        improvement_result = self._orchestrator.process_command(command)

        # Thread 1: Genre feature — optional scaffold
        genre_result = None
        if scaffold_genre:
            genre_result = self._scaffold_matching_feature(command)

        result = {
            "command": command[:100],
            "timestamp": datetime.utcnow().isoformat(),
            "self_improvement": improvement_result,
            "genre_feature": genre_result,
            "backlog_size": self._orchestrator.backlog.size(),
        }

        self._command_log.append(result)
        return result

    def run_improvement_cycle(self, max_items: int = 1) -> Dict:
        """
        Build capabilities from the backlog.

        "During idle time (no active Augustus commands),
         work on highest-priority backlog items."
        """
        built = self._orchestrator.work_on_backlog(max_items=max_items)
        return {
            "built": built,
            "count": len(built),
            "backlog_remaining": self._orchestrator.backlog.size(),
            "timestamp": datetime.utcnow().isoformat(),
        }

    def scaffold_genre_feature(self, feature: GenreFeature) -> Dict:
        """Scaffold a Genre product feature."""
        return self._genre.scaffold_feature(feature)

    # ── Status & reporting ────────────────────────────────────────────────────

    def status(self) -> Dict:
        """Full status report — for War Room display."""
        uptime = (datetime.utcnow() - _START_TIME).seconds
        inventory = self._builder.get_inventory()
        backlog = self._orchestrator.get_backlog_summary()
        pending_genre = self._genre.list_pending_features()

        return {
            "version": self.VERSION,
            "uptime_seconds": uptime,
            "capabilities": {
                "built": inventory,
                "built_count": len(inventory),
                "total_known": len(CAPABILITY_CATALOGUE),
                "coverage_pct": round(len(inventory) / len(CAPABILITY_CATALOGUE) * 100, 1),
            },
            "backlog": backlog,
            "genre": {
                "pending_features": len(pending_genre),
                "scaffolded": self._genre.get_scaffolded(),
            },
            "commands_processed": len(self._command_log),
            "improvement_log": self._orchestrator.get_improvement_log(),
        }

    def get_capabilities(self) -> List[str]:
        """List all built capabilities."""
        return self._builder.get_inventory()

    def get_improvement_backlog(self) -> List[Dict]:
        """Describe the improvement backlog."""
        return self._orchestrator.get_backlog_summary()["items"]

    def get_genre_roadmap(self, product: Optional[str] = None) -> List[Dict]:
        """Return Genre product roadmap."""
        return self._genre.get_roadmap(product=product)

    # ── Private ───────────────────────────────────────────────────────────────

    def _scaffold_matching_feature(self, command: str) -> Optional[Dict]:
        """Try to find and scaffold a Genre feature matching the command."""
        command_lower = command.lower()
        from src.tech_ai.genre_builder import GENRE_ROADMAP

        for feature in GENRE_ROADMAP:
            if (feature.name.replace("_", " ") in command_lower or
                    feature.product in command_lower and feature.status == "pending"):
                return self._genre.scaffold_feature(feature)

        return None
