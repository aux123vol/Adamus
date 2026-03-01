#!/usr/bin/env python3
"""
Adamus Main Entry Point

Starts:
  1. AI Coordinator (loads all docs, activates all 8 security layers)
  2. Autonomous Loop (24/7 task processing + self-improvement)
  3. Unified Web UI (chat, docs browser, war room — port 8888)

Usage:
    python -m src.main          # full stack
    python -m src.main --cli    # CLI mode only
    python -m src.main --ui     # web UI only
"""

import os
import sys
import signal
import asyncio
import logging
import argparse
import threading
from pathlib import Path
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.coordinator.ai_coordinator import AICoordinator


def setup_logging() -> None:
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_path = os.getenv("LOG_PATH", "./logs")
    Path(log_path).mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f"{log_path}/adamus.log"),
        ],
    )


def start_web_ui(host: str = "0.0.0.0", port: int = 8888) -> threading.Thread:
    """Start the unified web UI in a background thread."""
    def _run():
        try:
            from src.ui.unified_app import create_app
            app = create_app()
            app.run(host=host, port=port, debug=False, use_reloader=False)
        except Exception as e:
            logging.getLogger("adamus.ui").error(f"Web UI failed: {e}")

    t = threading.Thread(target=_run, daemon=True, name="adamus-ui")
    t.start()
    return t


def start_autonomous_loop(coordinator: AICoordinator) -> object:
    """Start the autonomous loop."""
    try:
        from src.autonomous.loop import AutonomousLoop
        loop = AutonomousLoop(coordinator=coordinator)
        loop.start()
        return loop
    except Exception as e:
        logging.getLogger("adamus.loop").error(f"Autonomous loop failed to start: {e}")
        return None


async def main(args: argparse.Namespace) -> None:
    load_dotenv()
    setup_logging()
    logger = logging.getLogger("adamus")

    logger.info("=" * 60)
    logger.info("ADAMUS - AI CTO Orchestrator v0.1")
    logger.info("=" * 60)

    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning("ANTHROPIC_API_KEY not set — Claude brain unavailable")

    docs_path  = os.getenv("ADAMUS_DOCS_PATH",  os.path.expanduser("~/adamus/docs/architecture"))
    db_path    = os.getenv("ADAMUS_DB_PATH",     os.path.expanduser("~/.adamus/memory.db"))
    monthly_budget = float(os.getenv("MONTHLY_BUDGET_USD", "200.0"))

    # ── Start web UI immediately (no coordinator needed) ──────────────────
    ui_thread = None
    if not args.cli_only:
        ui_port = int(os.getenv("ADAMUS_UI_PORT", "8888"))
        ui_thread = start_web_ui(port=ui_port)
        logger.info(f"Web UI starting on http://0.0.0.0:{ui_port}")

    # ── Initialize coordinator ────────────────────────────────────────────
    coordinator = AICoordinator(
        docs_path=docs_path,
        db_path=db_path,
        monthly_budget=monthly_budget,
        strict_security=True,
    )

    try:
        init_status = await coordinator.initialize()

        docs_n    = init_status.get("documents_loaded", "?")
        sec_ok    = init_status.get("security_active", False)
        brains    = init_status.get("brains", {})
        claude_ok = brains.get("claude", {}).get("available", False)
        ollama_ok = brains.get("ollama", {}).get("available", False)

        logger.info(f"Docs loaded  : {docs_n}")
        logger.info(f"Security     : {'✅ all 8 layers' if sec_ok else '⚠️  degraded'}")
        logger.info(f"Claude       : {'✅' if claude_ok else '❌'}")
        logger.info(f"Ollama       : {'✅' if ollama_ok else '❌'}")
        logger.info("=" * 60)
        logger.info("ADAMUS READY")
        logger.info("=" * 60)

    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        raise

    # ── Start autonomous loop ─────────────────────────────────────────────
    auto_loop = None
    if not args.cli_only:
        auto_loop = start_autonomous_loop(coordinator)
        if auto_loop:
            logger.info("Autonomous loop started (heartbeat every 2 hours)")

    # ── Keep alive ────────────────────────────────────────────────────────
    if args.cli_only:
        # Interactive CLI mode
        from src.ui.adamus_interface import AdamusInterface
        interface = AdamusInterface(coordinator)
        await interface.run()
    else:
        logger.info("Adamus running. Web UI: http://localhost:8888")
        logger.info("Press Ctrl+C to stop.")
        try:
            while True:
                await asyncio.sleep(60)
        except (KeyboardInterrupt, SystemExit):
            logger.info("Shutting down Adamus...")
            if auto_loop:
                auto_loop.stop()


def run() -> None:
    parser = argparse.ArgumentParser(description="Adamus AI CTO Orchestrator")
    parser.add_argument("--cli",  dest="cli_only",  action="store_true", help="CLI mode only")
    parser.add_argument("--ui",   dest="ui_only",   action="store_true", help="Web UI only (no coordinator)")
    args = parser.parse_args()

    if args.ui_only:
        # Just spin up the web UI
        load_dotenv()
        setup_logging()
        from src.ui.unified_app import create_app
        port = int(os.getenv("ADAMUS_UI_PORT", "8888"))
        create_app().run(host="0.0.0.0", port=port, debug=False)
        return

    asyncio.run(main(args))


if __name__ == "__main__":
    run()
