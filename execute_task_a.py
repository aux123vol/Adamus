#!/usr/bin/env python3
"""
Execute Task A - Focused Execution
"""

import asyncio
import logging
import os
import sys
import signal

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.coordinator.ai_coordinator import AICoordinator
from src.coordinator.task_router import TaskPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def execute_task_a():
    """Execute Task A using the AICoordinator."""
    logger.info("Executing Task A...")

    # Initialize coordinator
    coordinator = AICoordinator(
        docs_path=os.getenv("ADAMUS_DOCS_PATH", "~/adamus/docs/architecture"),
        db_path=os.getenv("ADAMUS_DB_PATH", "~/.adamus/memory.db"),
        monthly_budget=float(os.getenv("MONTHLY_BUDGET_USD", "200.0")),
        strict_security=True,
    )

    try:
        # Initialize coordinator
        await coordinator.initialize()

        # Execute Task A with minimal context
        result = await coordinator.execute_task(
            description="Task A - Execute Task A as requested",
            priority=TaskPriority.MEDIUM,
            data_level=2,
        )

        logger.info("Task A completed:")
        logger.info(f"Success: {result.success}")
        logger.info(f"Brain used: {result.brain_used}")
        logger.info(f"Cost: ${result.cost_usd:.4f}")
        logger.info(f"Result: {result.result[:200]}...")

        return result

    except Exception as e:
        logger.error(f"Task A execution failed: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(execute_task_a())
