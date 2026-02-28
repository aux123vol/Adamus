"""
Brain Orchestrator: Multi-Brain Routing System

Adamus is the persistent orchestrator.
Brains are interchangeable tools.

Available brains (auto-detected):
  1. Claude      — Anthropic API. Best reasoning. Level 1-2 data only.
  2. Ollama      — Local LLMs (Llama, Mistral, etc). Free. All data levels.
  3. LM Studio   — Local OpenAI-compatible server. Free. All data levels.
  4. DeepSeek    — Cost-effective API. Level 1-2 data.
  5. OpenAI      — GPT-4o fallback. Level 1-2 data.

Routing logic (from MULTI_BRAIN_AUTONOMOUS_FINAL.md):
  - Level 3-4 data  → local only (Ollama or LM Studio)
  - Complex task    → Claude (best reasoning)
  - Cost-sensitive  → DeepSeek or local
  - Budget exceeded → local
  - Autonomous/bg   → Ollama/LM Studio

From the doc:
  "Brains change, Adamus stays consistent."
"""

import json
import logging
import os
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Generator, List, Optional, Tuple

logger = logging.getLogger(__name__)


class Brain(Enum):
    OPENCODE  = "opencode"   # Free hosted models — default first
    CLAUDE    = "claude"     # Best reasoning — power fallback
    GROQ      = "groq"       # Fast + free tier (Llama on Groq hardware)
    GEMINI    = "gemini"     # Google Gemini — free tier available
    GROK      = "grok"       # xAI Grok
    MISTRAL   = "mistral"    # Mistral AI — cost-effective
    DEEPSEEK  = "deepseek"   # DeepSeek — very cheap
    OPENAI    = "openai"     # OpenAI GPT-4o
    OLLAMA    = "ollama"     # Local — all data levels
    LMSTUDIO  = "lmstudio"   # Local OpenAI-compat — all data levels


class TaskType(Enum):
    CHAT          = "chat"          # General conversation
    CODING        = "coding"        # Write/review code
    PLANNING      = "planning"      # Architecture, strategy
    SUMMARIZE     = "summarize"     # Quick summarization
    BACKGROUND    = "background"    # Autonomous background task
    SENSITIVE     = "sensitive"     # Level 3-4 data processing


@dataclass
class BrainConfig:
    name: str
    is_local: bool
    max_data_level: int      # 1-4; local brains = 4
    base_url: str
    api_key_env: str         # env var for API key (empty if local)
    default_model: str
    cost_per_1k: float       # USD; 0.0 for local
    strengths: List[str] = field(default_factory=list)
    available: bool = False


BRAIN_CONFIGS: Dict[Brain, BrainConfig] = {
    Brain.OPENCODE: BrainConfig(
        name="OpenCode",
        is_local=False,
        max_data_level=2,
        base_url="",  # CLI subprocess — no HTTP endpoint
        api_key_env="",  # No key needed for free models
        default_model="opencode/trinity-large-preview-free",
        cost_per_1k=0.0,
        strengths=["coding", "general", "free", "open_source"],
    ),
    Brain.CLAUDE: BrainConfig(
        name="Claude",
        is_local=False,
        max_data_level=2,
        base_url="https://api.anthropic.com",
        api_key_env="ANTHROPIC_API_KEY",
        default_model="claude-sonnet-4-6",
        cost_per_1k=0.009,
        strengths=["complex_reasoning", "coding", "architecture", "planning"],
    ),
    Brain.OLLAMA: BrainConfig(
        name="Ollama",
        is_local=True,
        max_data_level=4,
        base_url=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
        api_key_env="",
        default_model="llama3.2",
        cost_per_1k=0.0,
        strengths=["sensitive_data", "background", "cost_free", "summarize"],
    ),
    Brain.LMSTUDIO: BrainConfig(
        name="LM Studio",
        is_local=True,
        max_data_level=4,
        base_url="http://localhost:1234/v1",
        api_key_env="",
        default_model="local-model",
        cost_per_1k=0.0,
        strengths=["sensitive_data", "background", "cost_free", "offline"],
    ),
    Brain.GROQ: BrainConfig(
        name="Groq",
        is_local=False,
        max_data_level=2,
        base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        default_model="llama-3.3-70b-versatile",
        cost_per_1k=0.0,  # Free tier available
        strengths=["fast", "free_tier", "coding", "chat"],
    ),
    Brain.GEMINI: BrainConfig(
        name="Gemini",
        is_local=False,
        max_data_level=2,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        api_key_env="GEMINI_API_KEY",
        default_model="gemini-2.0-flash",
        cost_per_1k=0.0,  # Free tier available
        strengths=["free_tier", "multimodal", "chat", "coding"],
    ),
    Brain.GROK: BrainConfig(
        name="Grok",
        is_local=False,
        max_data_level=2,
        base_url="https://api.x.ai/v1",
        api_key_env="GROK_API_KEY",
        default_model="grok-3-mini",
        cost_per_1k=0.0003,
        strengths=["reasoning", "chat", "coding"],
    ),
    Brain.MISTRAL: BrainConfig(
        name="Mistral",
        is_local=False,
        max_data_level=2,
        base_url="https://api.mistral.ai/v1",
        api_key_env="MISTRAL_API_KEY",
        default_model="mistral-small-latest",
        cost_per_1k=0.0002,
        strengths=["cost_effective", "coding", "european_data"],
    ),
    Brain.DEEPSEEK: BrainConfig(
        name="DeepSeek",
        is_local=False,
        max_data_level=2,
        base_url="https://api.deepseek.com/v1",
        api_key_env="DEEPSEEK_API_KEY",
        default_model="deepseek-chat",
        cost_per_1k=0.0002,
        strengths=["cost_effective", "coding", "chat"],
    ),
    Brain.OPENAI: BrainConfig(
        name="OpenAI",
        is_local=False,
        max_data_level=2,
        base_url="https://api.openai.com/v1",
        api_key_env="OPENAI_API_KEY",
        default_model="gpt-4o-mini",
        cost_per_1k=0.0003,
        strengths=["fallback", "chat", "coding"],
    ),
}


class BrainOrchestrator:
    """
    Adamus routes tasks to the best available brain.

    Auto-detects which brains are online at startup.
    Falls back gracefully when brains go offline.
    """

    def __init__(self):
        self._load_env()
        self._available: Dict[Brain, BrainConfig] = {}
        self._probe_all()

    # ── Setup ─────────────────────────────────────────────────────────────────

    def _load_env(self) -> None:
        """Load .env file if present."""
        from pathlib import Path
        env = Path(__file__).resolve().parents[2] / ".env"
        if env.exists():
            for line in env.read_text().splitlines():
                if "=" in line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ.setdefault(k.strip(), v.strip())

    def _probe_all(self) -> None:
        """Detect which brains are available right now."""
        for brain, cfg in BRAIN_CONFIGS.items():
            cfg.available = self._probe(brain, cfg)
            if cfg.available:
                self._available[brain] = cfg
                logger.info(f"Brain online: {cfg.name} ({cfg.default_model})")
            else:
                logger.debug(f"Brain offline: {cfg.name}")

    def _probe(self, brain: Brain, cfg: BrainConfig) -> bool:
        """Check if a brain is reachable."""
        # OpenCode — check CLI is installed
        if brain == Brain.OPENCODE:
            import shutil
            return shutil.which("opencode") is not None

        # API-key-gated brains
        if cfg.api_key_env:
            key = os.environ.get(cfg.api_key_env, "")
            if not key or "YOUR-KEY" in key:
                return False

        # Local brains — check HTTP
        if brain == Brain.OLLAMA:
            return self._http_ok(f"{cfg.base_url}/api/tags")
        if brain == Brain.LMSTUDIO:
            return self._http_ok(f"{cfg.base_url}/models")

        # Remote brains — just check key presence
        return True

    def _http_ok(self, url: str, timeout: int = 2) -> bool:
        try:
            urllib.request.urlopen(url, timeout=timeout)
            return True
        except Exception:
            return False

    # ── Routing ───────────────────────────────────────────────────────────────

    def route(
        self,
        task_type: TaskType = TaskType.CHAT,
        data_level: int = 1,
        estimated_tokens: int = 1000,
        monthly_budget_remaining: float = 200.0,
        force: Optional[Brain] = None,
    ) -> Tuple[Brain, str]:
        """
        Select best brain for a task.

        Returns (Brain, reason_string).
        """
        if force is not None and force in self._available:
            cfg = BRAIN_CONFIGS[force]
            if data_level > cfg.max_data_level:
                raise ValueError(
                    f"{cfg.name} can't handle Level {data_level} data"
                )
            return force, f"Forced: {cfg.name}"

        # OpenCode first — free hosted models, no API key needed
        if data_level <= 2 and task_type != TaskType.SENSITIVE:
            if Brain.OPENCODE in self._available:
                return Brain.OPENCODE, "OpenCode first (free open-source models)"

        # Security: Level 3-4 → local only
        if data_level >= 3:
            for brain in (Brain.OLLAMA, Brain.LMSTUDIO):
                if brain in self._available:
                    return brain, f"Level {data_level} data → local ({BRAIN_CONFIGS[brain].name})"
            raise RuntimeError(
                f"Level {data_level} data requires a local brain "
                f"(start Ollama or LM Studio) but none available"
            )

        # Background / autonomous → prefer free local
        if task_type == TaskType.BACKGROUND:
            for brain in (Brain.OLLAMA, Brain.LMSTUDIO):
                if brain in self._available:
                    return brain, "Background task → free local brain"

        # Budget exceeded → local
        if Brain.CLAUDE in self._available:
            cost = (estimated_tokens / 1000) * BRAIN_CONFIGS[Brain.CLAUDE].cost_per_1k
            if cost > monthly_budget_remaining:
                for brain in (Brain.OLLAMA, Brain.LMSTUDIO, Brain.DEEPSEEK):
                    if brain in self._available:
                        return brain, f"Budget limit → {BRAIN_CONFIGS[brain].name}"

        # Complex tasks → Claude
        if task_type in (TaskType.CODING, TaskType.PLANNING):
            if Brain.CLAUDE in self._available:
                return Brain.CLAUDE, "Complex task → Claude (best reasoning)"

        # Preferred order: free first → power → cost-effective → fallback
        preference = [
            Brain.OPENCODE, Brain.GROQ, Brain.GEMINI,   # free tiers first
            Brain.CLAUDE, Brain.GROK,                    # power
            Brain.MISTRAL, Brain.DEEPSEEK,               # cost-effective
            Brain.OPENAI,                                 # paid fallback
            Brain.LMSTUDIO, Brain.OLLAMA,                # local last for general
        ]
        for brain in preference:
            if brain in self._available:
                return brain, f"Best available: {BRAIN_CONFIGS[brain].name}"

        raise RuntimeError("No brains available. Check API keys and local services.")

    # ── Execution ─────────────────────────────────────────────────────────────

    def stream(
        self,
        messages: List[Dict[str, str]],
        system: str = "",
        task_type: TaskType = TaskType.CHAT,
        data_level: int = 1,
        force: Optional[Brain] = None,
    ) -> Generator[str, None, None]:
        """
        Stream a response from the best available brain.

        Yields text chunks as they arrive.
        Also yields a special header chunk: '__brain__:<name>\n'
        so the UI can display which brain is responding.
        """
        brain, reason = self.route(task_type=task_type, data_level=data_level, force=force)
        cfg = BRAIN_CONFIGS[brain]
        logger.info(f"Routing to {cfg.name}: {reason}")

        # Tell the caller which brain we're using
        yield f"__brain__{cfg.name}\n"

        if brain == Brain.OPENCODE:
            yield from self._stream_opencode(messages, system, cfg)
        elif brain == Brain.CLAUDE:
            yield from self._stream_claude(messages, system, cfg)
        elif brain == Brain.OLLAMA:
            yield from self._stream_ollama(messages, system, cfg)
        elif brain in (
            Brain.LMSTUDIO, Brain.GROQ, Brain.GEMINI,
            Brain.GROK, Brain.MISTRAL, Brain.DEEPSEEK, Brain.OPENAI,
        ):
            yield from self._stream_openai_compat(messages, system, cfg)
        else:
            yield "No compatible streaming method for this brain."

    def _stream_opencode(self, messages, system, cfg):
        """Run opencode CLI non-interactively and yield the response."""
        import shutil
        import subprocess
        import re

        opencode_bin = shutil.which("opencode")
        if not opencode_bin:
            yield "⚠️ opencode CLI not found"
            return

        prompt = self._msgs_to_prompt(messages, system)
        try:
            result = subprocess.run(
                [opencode_bin, "run", "-m", cfg.default_model, prompt],
                capture_output=True,
                text=True,
                timeout=120,
            )
            output = result.stdout or ""
            # Strip ANSI escape codes
            ansi_escape = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
            output = ansi_escape.sub("", output).strip()
            if output:
                yield output
            elif result.stderr:
                err = ansi_escape.sub("", result.stderr).strip()
                yield f"⚠️ OpenCode: {err[:300]}"
            else:
                yield "⚠️ OpenCode returned empty response"
        except subprocess.TimeoutExpired:
            yield "⚠️ OpenCode timed out (120s)"
        except Exception as e:
            yield f"⚠️ OpenCode error: {e}"

    def _stream_claude(self, messages, system, cfg):
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=os.environ[cfg.api_key_env])
            with client.messages.stream(
                model=cfg.default_model,
                max_tokens=1024,
                system=system,
                messages=messages,
            ) as s:
                for chunk in s.text_stream:
                    yield chunk
        except Exception as e:
            yield f"\n⚠️ Claude error: {e}"

    def _stream_ollama(self, messages, system, cfg):
        try:
            # Ollama native API
            prompt = self._msgs_to_prompt(messages, system)
            data = json.dumps({
                "model": cfg.default_model,
                "prompt": prompt,
                "stream": True,
            }).encode()
            req = urllib.request.Request(
                f"{cfg.base_url}/api/generate",
                data=data,
                headers={"Content-Type": "application/json"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    if line:
                        obj = json.loads(line.decode())
                        yield obj.get("response", "")
                        if obj.get("done"):
                            break
        except Exception as e:
            yield f"\n⚠️ Ollama error: {e}"

    def _stream_openai_compat(self, messages, system, cfg):
        """Works for LM Studio, DeepSeek, OpenAI (all use OpenAI-compatible API)."""
        try:
            all_msgs = []
            if system:
                all_msgs.append({"role": "system", "content": system})
            all_msgs.extend(messages)

            data = json.dumps({
                "model": cfg.default_model,
                "messages": all_msgs,
                "stream": True,
            }).encode()

            headers = {"Content-Type": "application/json"}
            if cfg.api_key_env and cfg.api_key_env in os.environ:
                headers["Authorization"] = f"Bearer {os.environ[cfg.api_key_env]}"
            else:
                headers["Authorization"] = "Bearer lm-studio"  # LM Studio default

            req = urllib.request.Request(
                f"{cfg.base_url}/chat/completions",
                data=data,
                headers=headers,
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                for line in resp:
                    line = line.decode().strip()
                    if line.startswith("data: "):
                        line = line[6:]
                    if line == "[DONE]" or not line:
                        continue
                    try:
                        obj = json.loads(line)
                        delta = obj["choices"][0]["delta"].get("content", "")
                        if delta:
                            yield delta
                    except Exception:
                        continue
        except Exception as e:
            yield f"\n⚠️ {cfg.name} error: {e}"

    def _msgs_to_prompt(self, messages: List[Dict], system: str) -> str:
        """Convert messages list to a single prompt string (for Ollama)."""
        parts = []
        if system:
            parts.append(f"System: {system}\n")
        for m in messages:
            role = "User" if m["role"] == "user" else "Assistant"
            parts.append(f"{role}: {m['content']}")
        parts.append("Assistant:")
        return "\n\n".join(parts)

    # ── Status ────────────────────────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Return status of all brains."""
        self._probe_all()
        return {
            brain.value: {
                "name": cfg.name,
                "available": brain in self._available,
                "local": cfg.is_local,
                "model": cfg.default_model,
                "cost_per_1k": cfg.cost_per_1k,
                "max_data_level": cfg.max_data_level,
            }
            for brain, cfg in BRAIN_CONFIGS.items()
        }

    @property
    def available_brains(self) -> List[str]:
        return [BRAIN_CONFIGS[b].name for b in self._available]
