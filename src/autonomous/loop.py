"""
Adamus Autonomous Event Loop.

Adamus runs 24/7 as a persistent AI orchestrator.  This module provides
the background asyncio loop that:

* Processes a persistent task queue via AICoordinator.
* Fires a heartbeat every 2 hours: logs status, runs the self-improvement
  backlog, and updates metrics.
* Persists state across restarts via ``~/.adamus/task_queue.json``.
* Never crashes — every code path is wrapped in try/except with logging.

Typical usage::

    loop = AutonomousLoop()
    loop.start()                         # spawns background thread
    loop.submit_task("build login API")  # enqueue from anywhere
    ...
    loop.stop()
"""

import asyncio
import json
import logging
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────

_ADAMUS_DIR = Path.home() / ".adamus"
_QUEUE_FILE = _ADAMUS_DIR / "task_queue.json"
_LOG_FILE = _ADAMUS_DIR / "loop.log"

# Heartbeat interval in seconds (2 hours)
HEARTBEAT_INTERVAL_SEC = 2 * 60 * 60

# How long (seconds) to wait between queue-poll cycles when the queue is empty
IDLE_POLL_INTERVAL_SEC = 10

# How long (seconds) to wait between queue-poll cycles when tasks are present
ACTIVE_POLL_INTERVAL_SEC = 2


# ── State enum ─────────────────────────────────────────────────────────────

class LoopState(Enum):
    STOPPED = auto()
    RUNNING = auto()
    PAUSED = auto()


# ── Task dataclass ─────────────────────────────────────────────────────────

@dataclass
class QueuedTask:
    """A task waiting to be processed by the autonomous loop."""
    description: str
    priority: int = 5          # 1 (highest) … 10 (lowest)
    submitted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    attempts: int = 0
    status: str = "pending"    # pending | processing | done | failed


# ── File-based logging handler ─────────────────────────────────────────────

def _setup_file_logger() -> None:
    """Attach a FileHandler to the root logger that writes to ~/.adamus/loop.log."""
    try:
        _ADAMUS_DIR.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(str(_LOG_FILE), encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        fh.setFormatter(fmt)
        # Avoid adding duplicate handlers across multiple instantiations
        root = logging.getLogger()
        if not any(isinstance(h, logging.FileHandler) and h.baseFilename == fh.baseFilename
                   for h in root.handlers):
            root.addHandler(fh)
    except Exception as exc:
        logger.warning("Could not set up file logger: %s", exc)


# ── AutonomousLoop ─────────────────────────────────────────────────────────

class AutonomousLoop:
    """
    24/7 autonomous event loop for Adamus.

    The loop runs in a dedicated background thread with its own asyncio
    event loop so it does not interfere with other async code.

    Public interface:
    - :meth:`start`  — begin processing.
    - :meth:`stop`   — graceful shutdown.
    - :meth:`pause`  — temporarily halt task processing (heartbeat continues).
    - :meth:`resume` — re-enable task processing.
    - :meth:`submit_task` — enqueue a new task from any thread.
    """

    def __init__(self, coordinator=None) -> None:
        _setup_file_logger()

        self._state: LoopState = LoopState.STOPPED
        self._task_queue: List[QueuedTask] = []
        self._queue_lock = threading.Lock()

        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Metrics
        self._tasks_processed: int = 0
        self._tasks_failed: int = 0
        self._start_time: Optional[datetime] = None
        self._last_heartbeat: Optional[datetime] = None

        # Lazy-initialised heavy components (keep __init__ fast)
        self._coordinator = coordinator
        self._self_improvement: Optional[Any] = None
        self._self_builder = None
        self._self_build_agent = None   # Day 9: context-aware self-improvement
        self._genre_build_agent = None  # Day 9: Genre feature builder

        self._load_queue()
        logger.info("AutonomousLoop created")

    # ------------------------------------------------------------------ #
    # Public control API                                                   #
    # ------------------------------------------------------------------ #

    @property
    def state(self) -> str:
        """Return the current loop state as a lowercase string."""
        return self._state.name.lower()

    def start(self) -> None:
        """
        Start the autonomous loop in a background daemon thread.

        Safe to call only once; subsequent calls are no-ops if already running.
        """
        if self._state == LoopState.RUNNING:
            logger.warning("start() called but loop is already running")
            return

        self._stop_event.clear()
        self._state = LoopState.RUNNING
        self._start_time = datetime.utcnow()

        self._thread = threading.Thread(
            target=self._run_loop,
            name="adamus-autonomous-loop",
            daemon=True,
        )
        self._thread.start()
        logger.info("AutonomousLoop started (thread: %s)", self._thread.name)

    def stop(self) -> None:
        """
        Signal the loop to stop and wait for the background thread to finish.

        Blocks for up to 5 seconds; times out gracefully.
        """
        logger.info("AutonomousLoop stop requested")
        self._state = LoopState.STOPPED
        self._stop_event.set()

        if self._loop and self._loop.is_running():
            self._loop.call_soon_threadsafe(self._loop.stop)

        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                logger.warning("Background thread did not exit within 5 s")

        self._save_queue()
        logger.info("AutonomousLoop stopped")

    def pause(self) -> None:
        """Pause task processing (heartbeat continues running)."""
        if self._state == LoopState.RUNNING:
            self._state = LoopState.PAUSED
            logger.info("AutonomousLoop paused")

    def resume(self) -> None:
        """Resume task processing after a pause."""
        if self._state == LoopState.PAUSED:
            self._state = LoopState.RUNNING
            logger.info("AutonomousLoop resumed")

    def submit_task(self, description: str, priority: int = 5) -> None:
        """
        Enqueue a new task for the autonomous loop.

        Thread-safe; can be called from any thread.

        Args:
            description: Human-readable description of the task.
            priority:    Integer 1–10, where 1 is highest priority.
                         Defaults to 5 (medium).
        """
        priority = max(1, min(10, priority))
        task = QueuedTask(description=description, priority=priority)
        with self._queue_lock:
            self._task_queue.append(task)
            # Keep queue sorted: highest priority first (lowest int)
            self._task_queue.sort(key=lambda t: t.priority)
        self._save_queue()
        logger.info("Task submitted (priority %d): %s", priority, description[:80])

    def get_metrics(self) -> Dict:
        """Return a snapshot of runtime metrics."""
        uptime = (
            str(datetime.utcnow() - self._start_time)
            if self._start_time
            else "not started"
        )
        with self._queue_lock:
            queue_len = len([t for t in self._task_queue if t.status == "pending"])
        return {
            "state": self._state.name.lower(),
            "uptime": uptime,
            "uptime_seconds": (
                (datetime.utcnow() - self._start_time).total_seconds()
                if self._start_time
                else 0
            ),
            "tasks_processed": self._tasks_processed,
            "tasks_failed": self._tasks_failed,
            "queue_pending": queue_len,
            "queue_size": queue_len,
            "last_heartbeat": (
                self._last_heartbeat.isoformat() if self._last_heartbeat else None
            ),
        }

    # ------------------------------------------------------------------ #
    # Background thread entry point                                        #
    # ------------------------------------------------------------------ #

    def _run_loop(self) -> None:
        """Entry point for the background daemon thread."""
        try:
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(self._async_main())
        except Exception as exc:
            logger.error("AutonomousLoop background thread crashed: %s", exc, exc_info=True)
        finally:
            try:
                if self._loop and not self._loop.is_closed():
                    self._loop.close()
            except Exception:
                pass
            logger.info("Background loop thread exited")

    # ------------------------------------------------------------------ #
    # Async main orchestrator                                              #
    # ------------------------------------------------------------------ #

    async def _async_main(self) -> None:
        """
        Async main function: runs task processing and heartbeat concurrently.
        """
        try:
            await self._init_components()
        except Exception as exc:
            logger.error("Component initialisation failed: %s", exc, exc_info=True)
            # Continue without coordinator — heartbeat will still work

        # Schedule heartbeat and task processor as concurrent tasks
        heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        processor_task = asyncio.create_task(self._task_processor_loop())

        try:
            await asyncio.gather(heartbeat_task, processor_task)
        except asyncio.CancelledError:
            logger.info("Async tasks cancelled — shutting down")
        except Exception as exc:
            logger.error("_async_main error: %s", exc, exc_info=True)

    # ------------------------------------------------------------------ #
    # Initialisation                                                       #
    # ------------------------------------------------------------------ #

    async def _init_components(self) -> None:
        """
        Lazily initialise the heavy coordinator and self-improvement objects.

        Errors are logged but do not abort the loop.
        """
        if self._coordinator is None:
            try:
                from src.coordinator.ai_coordinator import AICoordinator
                self._coordinator = AICoordinator()
                await self._coordinator.initialize()
                logger.info("AICoordinator initialised")
            except Exception as exc:
                logger.warning("Could not initialise AICoordinator: %s", exc)
                self._coordinator = None

        try:
            from src.tech_ai.self_improvement import SelfImprovementOrchestrator
            self._self_improvement = SelfImprovementOrchestrator()
            logger.info("SelfImprovementOrchestrator initialised")
        except Exception as exc:
            logger.warning("Could not initialise SelfImprovementOrchestrator: %s", exc)
            self._self_improvement = None

        try:
            from src.autonomous.self_builder import SelfBuilder  # noqa: F401
            self._self_builder = SelfBuilder()
            logger.info("SelfBuilder initialised")
        except Exception as exc:
            logger.warning("Could not initialise SelfBuilder: %s", exc)
            self._self_builder = None

    # ------------------------------------------------------------------ #
    # Heartbeat loop                                                       #
    # ------------------------------------------------------------------ #

    async def _heartbeat_loop(self) -> None:
        """Fire a heartbeat every HEARTBEAT_INTERVAL_SEC seconds."""
        # Fire immediately on start, then every 2 hours
        while not self._stop_event.is_set():
            try:
                await self._heartbeat()
            except Exception as exc:
                logger.error("Heartbeat error: %s", exc, exc_info=True)

            # Sleep in small increments so we can react to stop quickly
            elapsed = 0
            while elapsed < HEARTBEAT_INTERVAL_SEC and not self._stop_event.is_set():
                await asyncio.sleep(min(30, HEARTBEAT_INTERVAL_SEC - elapsed))
                elapsed += 30

    async def _heartbeat(self) -> None:
        """
        Periodic heartbeat handler (every 2 hours).

        1. Logs system status.
        2. Runs up to 3 items from the self-improvement backlog.
        3. Updates metrics snapshot.
        """
        self._last_heartbeat = datetime.utcnow()
        metrics = self.get_metrics()
        logger.info(
            "HEARTBEAT | state=%s uptime=%s processed=%d failed=%d queue=%d",
            metrics["state"],
            metrics["uptime"],
            metrics["tasks_processed"],
            metrics["tasks_failed"],
            metrics["queue_pending"],
        )

        # Run self-improvement backlog
        if self._self_improvement is not None:
            try:
                built = self._self_improvement.work_on_backlog(max_items=3)
                if built:
                    logger.info("Self-improvement: built %s", built)
                else:
                    logger.debug("Self-improvement: backlog empty or nothing built")
            except Exception as exc:
                logger.error("Self-improvement backlog error: %s", exc)

        # Log coordinator status
        if self._coordinator is not None:
            try:
                status = await self._coordinator.get_status()
                logger.info(
                    "Coordinator status: docs=%s security=%s",
                    status.get("documents", {}).get("total_documents", "?"),
                    status.get("security", {}).get("all_layers_active", "?"),
                )
            except Exception as exc:
                logger.warning("Could not get coordinator status: %s", exc)

    # ------------------------------------------------------------------ #
    # Task processor loop                                                  #
    # ------------------------------------------------------------------ #

    async def _task_processor_loop(self) -> None:
        """Continuously drain the pending task queue."""
        while not self._stop_event.is_set():
            try:
                if self._state == LoopState.PAUSED:
                    await asyncio.sleep(IDLE_POLL_INTERVAL_SEC)
                    continue

                task = self._pop_pending_task()
                if task is None:
                    await asyncio.sleep(IDLE_POLL_INTERVAL_SEC)
                    continue

                await self._process_task(task)
                await asyncio.sleep(ACTIVE_POLL_INTERVAL_SEC)

            except asyncio.CancelledError:
                break
            except Exception as exc:
                logger.error("Task processor loop error: %s", exc, exc_info=True)
                await asyncio.sleep(IDLE_POLL_INTERVAL_SEC)

    async def _process_task(self, task: QueuedTask) -> None:
        """
        Execute a single queued task via AICoordinator.

        Updates the task's status in place and persists the queue.

        Args:
            task: The QueuedTask to execute.
        """
        task.status = "processing"
        task.attempts += 1
        self._save_queue()

        logger.info("Processing task: %s", task.description[:80])

        try:
            if self._coordinator is not None:
                from src.coordinator.task_router import TaskPriority
                # Map numeric priority to TaskPriority enum
                tp = TaskPriority.HIGH if task.priority <= 3 else (
                    TaskPriority.MEDIUM if task.priority <= 6 else TaskPriority.LOW
                )
                result = await self._coordinator.execute_task(
                    description=task.description,
                    priority=tp,
                )
                if result.success:
                    task.status = "done"
                    self._tasks_processed += 1
                    logger.info("Task done: %s", task.description[:60])
                else:
                    task.status = "failed"
                    self._tasks_failed += 1
                    logger.warning("Task failed: %s | %s", task.description[:60], result.result[:120])
            else:
                # Coordinator unavailable — mark as failed but log for retry
                logger.warning(
                    "Coordinator unavailable; task deferred: %s",
                    task.description[:80],
                )
                task.status = "failed"
                self._tasks_failed += 1

            # Signal self-improvement of the command
            if self._self_improvement is not None:
                try:
                    self._self_improvement.process_command(task.description)
                except Exception as exc:
                    logger.debug("self_improvement.process_command error: %s", exc)

        except Exception as exc:
            task.status = "failed"
            self._tasks_failed += 1
            logger.error("Unhandled error processing task '%s': %s", task.description[:60], exc, exc_info=True)
        finally:
            self._save_queue()

    # ------------------------------------------------------------------ #
    # Queue persistence                                                    #
    # ------------------------------------------------------------------ #

    def _pop_pending_task(self) -> Optional[QueuedTask]:
        """Return and remove the highest-priority pending task, or None."""
        with self._queue_lock:
            for task in self._task_queue:
                if task.status == "pending":
                    return task
        return None

    def _save_queue(self) -> None:
        """Persist the task queue to ~/.adamus/task_queue.json."""
        try:
            _ADAMUS_DIR.mkdir(parents=True, exist_ok=True)
            with self._queue_lock:
                data = [asdict(t) for t in self._task_queue]
            _QUEUE_FILE.write_text(
                json.dumps(data, indent=2, default=str),
                encoding="utf-8",
            )
        except Exception as exc:
            logger.error("Could not save task queue: %s", exc)

    def _load_queue(self) -> None:
        """Restore the task queue from ~/.adamus/task_queue.json if it exists."""
        try:
            if not _QUEUE_FILE.exists():
                return
            raw = json.loads(_QUEUE_FILE.read_text(encoding="utf-8"))
            with self._queue_lock:
                self._task_queue = [
                    QueuedTask(
                        description=item.get("description", ""),
                        priority=item.get("priority", 5),
                        submitted_at=item.get("submitted_at", datetime.utcnow().isoformat()),
                        attempts=item.get("attempts", 0),
                        # Reset in-flight tasks to pending so they are retried
                        status="pending" if item.get("status") == "processing" else item.get("status", "pending"),
                    )
                    for item in raw
                ]
                # Re-sort after load
                self._task_queue.sort(key=lambda t: t.priority)
            pending = sum(1 for t in self._task_queue if t.status == "pending")
            logger.info("Loaded %d tasks from queue file (%d pending)", len(self._task_queue), pending)
        except Exception as exc:
            logger.error("Could not load task queue: %s", exc)
            self._task_queue = []
