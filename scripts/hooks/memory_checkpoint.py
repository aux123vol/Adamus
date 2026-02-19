#!/usr/bin/env python3
"""
Memory checkpoint hook — runs at Stop event.

Reads the Claude session summary from stdin (JSON) and saves
a memory entry to Adamus persistent memory so context survives
across sessions.
"""

import json
import sys
import os
from datetime import datetime
from pathlib import Path

# Add adamus src to path
ADAMUS = Path("/home/johan/adamus")
sys.path.insert(0, str(ADAMUS))

try:
    from src.memory.adamus_persistent_memory import AdamusPersistentMemory

    # Read hook input from stdin
    hook_input = {}
    try:
        raw = sys.stdin.read()
        if raw.strip():
            hook_input = json.loads(raw)
    except Exception:
        pass

    # Extract useful info from the hook event
    session_id = hook_input.get("session_id", "unknown")
    transcript = hook_input.get("transcript", [])

    # Build a compact summary from last few messages
    summary_lines = []
    for msg in transcript[-6:]:  # last 3 turns
        role = msg.get("role", "")
        content = msg.get("content", "")
        if isinstance(content, str) and content.strip():
            summary_lines.append(f"**{role}**: {content[:200]}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict) and block.get("type") == "text":
                    text = block.get("text", "")[:200]
                    summary_lines.append(f"**{role}**: {text}")
                    break

    if not summary_lines:
        sys.exit(0)

    content = "\n\n".join(summary_lines)
    mem = AdamusPersistentMemory()
    mem.save_memory(
        title=f"Session checkpoint {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        content=content,
        category="conversation",
        tags=["checkpoint", "auto", session_id[:8]],
    )

except Exception as e:
    # Never crash Claude Code due to hook errors
    print(f"[memory_checkpoint] Warning: {e}", file=sys.stderr)
    sys.exit(0)
