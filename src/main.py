#!/usr/bin/env python3
"""
Adamus Main Entry Point

This is the main entry point for Adamus, the AI CTO orchestrator.

Adamus:
- Loads ALL 107+ architecture documents
- Activates all 8 security layers
- Routes tasks to the right brain (Claude/Ollama)
- Never forgets (brains forget, Adamus remembers)

Usage:
    python -m src.main

Or:
    python src/main.py
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coordinator.ai_coordinator import AICoordinator


def setup_logging() -> None:
    """Configure logging for Adamus."""
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_path = os.getenv("LOG_PATH", "./logs")

    Path(log_path).mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"{log_path}/adamus.log")
        ]
    )


async def main() -> None:
    """Main entry point for Adamus."""
    # Load environment variables
    load_dotenv()

    # Setup logging
    setup_logging()
    logger = logging.getLogger("adamus")

    logger.info("=" * 60)
    logger.info("ADAMUS - AI CTO Orchestrator")
    logger.info("=" * 60)

    # Check required environment variables
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning(
            "ANTHROPIC_API_KEY not set. Claude brain will be unavailable. "
            "Set it in .env or environment."
        )

    # Initialize coordinator
    docs_path = os.getenv(
        "ADAMUS_DOCS_PATH",
        os.path.expanduser("~/adamus/docs/architecture")
    )
    db_path = os.getenv(
        "ADAMUS_DB_PATH",
        os.path.expanduser("~/.adamus/memory.db")
    )
    monthly_budget = float(os.getenv("MONTHLY_BUDGET_USD", "200.0"))

    logger.info(f"Documents path: {docs_path}")
    logger.info(f"Database path: {db_path}")
    logger.info(f"Monthly budget: ${monthly_budget:.2f}")

    coordinator = AICoordinator(
        docs_path=docs_path,
        db_path=db_path,
        monthly_budget=monthly_budget,
        strict_security=True
    )

    # Initialize
    try:
        init_status = await coordinator.initialize()

        logger.info("\n" + "=" * 60)
        logger.info("INITIALIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"Documents loaded: {init_status.get('documents_loaded', 'unknown')}")
        logger.info(f"Security active: {init_status.get('security_active', False)}")

        # Print brain status
        brains = init_status.get("brains", {})
        logger.info(f"Claude available: {brains.get('claude', {}).get('available', False)}")
        logger.info(f"Ollama available: {brains.get('ollama', {}).get('available', False)}")

        # Get full status
        status = await coordinator.get_status()
        logger.info(f"\nBudget remaining: ${status.get('budget_remaining', 0):.2f}")

        logger.info("\n" + "=" * 60)
        logger.info("ADAMUS READY")
        logger.info("=" * 60)
        logger.info("\nAdamus is now ready to accept tasks.")
        logger.info("In production, this would start the task processing loop.")
        logger.info("For now, use the coordinator directly in your code:")
        logger.info("\n  result = await coordinator.execute_task('Your task here')")

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise


def run() -> None:
    """Synchronous entry point."""
    asyncio.run(main())


if __name__ == "__main__":
    run()
