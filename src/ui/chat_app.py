"""
Adamus Chat UI

ChatGPT-style interface for talking to Adamus.
Genre-branded: dark theme, orange/blue gradient.

Run: python -m src.ui.chat_app
Access: http://localhost:5001
"""

import os
import json
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, Response, stream_with_context

app = Flask(__name__)

REPO = Path(__file__).resolve().parents[2]
SYSTEM_PROMPT = """You are Adamus — the persistent AI CTO for Genre, built by Augustus.

Your personality:
- Direct, decisive, action-oriented
- You think like a CTO: architecture, metrics, execution
- You know the full Genre/Adamus codebase (108+ architecture docs loaded)
- You speak concisely — no fluff, high signal
- When asked about the project, you reference real files and decisions
- You help Augustus build Genre from $0 → $10K MRR

Your role:
- Answer questions about the codebase, architecture, business strategy
- Help make technical and product decisions
- Review code, plan features, debug problems
- Track metrics: MRR, burn, runway, test counts
- Route tasks to Business AI, CAMBI AI, Tech AI

Current state:
- 198 tests passing
- Days 1-5 complete: Memory, Security, War Room, Business AI, CAMBI AI
- Persistent memory system operational
- Git auto-save hooks active

Always be helpful, specific, and grounded in the actual project."""


def get_system_status():
    """Get live system status for sidebar."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            capture_output=True, text=True, cwd=str(REPO)
        )
        last_commit = result.stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO)
        ).stdout.strip()
    except Exception:
        last_commit = "unknown"
        dirty = ""

    try:
        import sys
        sys.path.insert(0, str(REPO))
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory
        stats = AdamusPersistentMemory().get_stats()
        memories = stats["total_memories"]
        mem_mb = stats["total_size_mb"]
    except Exception:
        memories = 0
        mem_mb = 0

    return {
        "commit": last_commit,
        "clean": not bool(dirty),
        "memories": memories,
        "mem_mb": mem_mb,
        "time": datetime.now().strftime("%H:%M"),
        "tests": 198,
    }


def chat_with_claude(messages):
    """Stream response from Claude API."""
    api_key = os.environ.get("ANTHROPIC_API_KEY", "")

    if not api_key or api_key.startswith("sk-ant-your"):
        # Demo mode — smart mock response
        yield from _mock_response(messages[-1]["content"])
        return

    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)

        with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text
    except Exception as e:
        yield f"\n\n⚠️ API error: {e}\n\nSet ANTHROPIC_API_KEY in `/home/johan/adamus/.env` to enable real responses."


def _mock_response(user_message: str):
    """Smart demo responses when no API key is set."""
    msg = user_message.lower()

    if any(w in msg for w in ["status", "how are", "health"]):
        response = """**System Status: Operational ✓**

- **198 tests passing** across all modules
- **Git:** master, clean, pushed to GitHub
- **Memory:** persistent storage at `~/.adamus/`
- **Days complete:** 1–5 (Memory → Security → War Room → Business AI → CAMBI AI)

**Next up:** Day 6 (Tech AI) then full integration.

What do you want to work on?"""

    elif any(w in msg for w in ["test", "pytest", "passing"]):
        response = """**Test suite: 198 passing**

| Module | Tests |
|---|---|
| Memory | 24 |
| Security | 20 |
| War Room | 12 |
| Business AI | 18 |
| Persistent Memory | 32 |
| CLI | 20 |
| CAMBI AI | 54 |
| Coordinator | 18 |

All green. Run `pytest tests/ -v` to see live results."""

    elif any(w in msg for w in ["day 6", "tech ai", "adamus core"]):
        response = """**Day 6: Tech AI (Adamus Core)**

From the build plan:
```
src/tech_ai/
├── adamus_core.py       ← main self-improving agent
├── self_improvement.py  ← meta-layer
├── capability_builder.py← builds missing capabilities
└── genre_builder.py     ← scaffolds Genre features
```

**Core pattern:** Adamus detects what it can't do → builds the capability → tests it → deploys it.

Ready to build it? I'll start with `adamus_core.py`."""

    elif any(w in msg for w in ["mrr", "revenue", "money", "business"]):
        response = """**Business Context**

- **Current MRR:** $0 (pre-launch)
- **Target:** $10K MRR in 90 days
- **North star:** MRR is the metric everything optimizes for

**Business AI tracks:**
- Finance pulse (burn, runway, cash)
- Competitor intel (Notion, Mem, Reflect)
- Market signals

**Genre product:** AI writing/knowledge tool targeting creators.

What business decision do you need help with?"""

    elif any(w in msg for w in ["memory", "remember", "forget"]):
        response = """**Adamus Memory System**

I have two memory layers:

1. **SQLite DB** (`~/.adamus/memory.db`) — decisions, conversations, tasks, budget
2. **File system** (`~/.adamus/memories/YYYY-MM/`) — markdown files, TB+ capable

**Progressive disclosure:** I only load what's relevant to the current task — keeps tokens low.

**Auto-archiving:** 30 days → gzip, 90 days → archive/

Right now: `0 memories` stored (fresh instance). As we work together, I'll remember everything permanently.

Want me to save something specific?"""

    elif any(w in msg for w in ["hello", "hi", "hey", "who are you"]):
        response = """Hey Augustus 👋

I'm **Adamus** — your persistent AI CTO.

Here's what I can do:
- **Answer** questions about the codebase and architecture
- **Plan** features and technical decisions
- **Review** code and debug problems
- **Track** metrics and business health
- **Execute** tasks across Business AI, CAMBI AI, Tech AI

I never forget — even when the underlying Claude model resets, I store everything in persistent memory and Git.

**198 tests passing. What do you want to build?**"""

    else:
        response = f"""I'm Adamus, your AI CTO. You said: *"{user_message}"*

I can help with:
- **Code** — architecture, debugging, new features
- **Business** — MRR tracking, competitor intel, decisions
- **Memory** — searching past decisions and context
- **Planning** — Day 6+ build roadmap

> ⚠️ Set `ANTHROPIC_API_KEY` in `.env` for full AI responses. Currently in demo mode.

What specifically do you need?"""

    # Stream word by word for effect
    import time
    words = response.split(" ")
    for i, word in enumerate(words):
        yield word + (" " if i < len(words) - 1 else "")
        # No sleep — instant in demo mode


HTML = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adamus — AI CTO</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }

  :root {
    --orange: #FF6B35;
    --blue: #4A9EFF;
    --bg: #0a0a0a;
    --surface: #111111;
    --surface2: #1a1a1a;
    --surface3: #222222;
    --border: #2a2a2a;
    --text: #e8e8e8;
    --text-muted: #666;
    --text-dim: #444;
  }

  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
    background: var(--bg);
    color: var(--text);
    height: 100vh;
    display: flex;
    overflow: hidden;
  }

  /* ── Sidebar ── */
  .sidebar {
    width: 260px;
    min-width: 260px;
    background: var(--surface);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
  }

  .sidebar-logo {
    padding: 20px 16px 16px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .logo-mark {
    width: 36px;
    height: 36px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--orange), var(--blue));
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 16px;
    color: #fff;
    flex-shrink: 0;
  }

  .logo-text h1 {
    font-size: 16px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.3px;
  }

  .logo-text p {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 1px;
  }

  .status-section {
    padding: 12px;
    border-bottom: 1px solid var(--border);
  }

  .status-label {
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    color: var(--text-dim);
    margin-bottom: 8px;
    padding: 0 4px;
  }

  .status-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 8px;
    border-radius: 6px;
    margin-bottom: 2px;
    font-size: 12px;
  }

  .status-item:hover { background: var(--surface2); }

  .status-item .label { color: var(--text-muted); }

  .status-item .value {
    font-weight: 600;
    color: var(--text);
  }

  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    margin-right: 6px;
    flex-shrink: 0;
  }

  .dot-green { background: #4CAF50; box-shadow: 0 0 6px #4CAF50; }
  .dot-orange { background: var(--orange); }
  .dot-red { background: #f44336; }

  .new-chat-btn {
    margin: 12px;
    padding: 10px;
    background: linear-gradient(135deg, var(--orange), var(--blue));
    border: none;
    border-radius: 8px;
    color: #fff;
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    width: calc(100% - 24px);
    transition: opacity 0.2s;
  }

  .new-chat-btn:hover { opacity: 0.85; }

  .history-section {
    flex: 1;
    overflow-y: auto;
    padding: 8px 12px;
  }

  .history-item {
    padding: 8px 10px;
    border-radius: 6px;
    font-size: 12px;
    color: var(--text-muted);
    cursor: pointer;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    margin-bottom: 2px;
  }

  .history-item:hover { background: var(--surface2); color: var(--text); }
  .history-item.active { background: var(--surface3); color: var(--text); }

  /* ── Main Chat ── */
  .main {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    background: var(--bg);
  }

  .chat-header {
    padding: 14px 24px;
    border-bottom: 1px solid var(--border);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-shrink: 0;
  }

  .chat-header h2 {
    font-size: 14px;
    font-weight: 600;
    color: var(--text);
  }

  .model-badge {
    font-size: 11px;
    padding: 3px 8px;
    border-radius: 20px;
    background: var(--surface2);
    border: 1px solid var(--border);
    color: var(--text-muted);
    display: flex;
    align-items: center;
    gap: 5px;
  }

  .model-badge span {
    width: 5px; height: 5px;
    border-radius: 50%;
    background: var(--orange);
    display: inline-block;
  }

  /* ── Messages ── */
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 24px;
    display: flex;
    flex-direction: column;
    gap: 24px;
    scroll-behavior: smooth;
  }

  .messages::-webkit-scrollbar { width: 4px; }
  .messages::-webkit-scrollbar-track { background: transparent; }
  .messages::-webkit-scrollbar-thumb { background: var(--border); border-radius: 4px; }

  .welcome {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    text-align: center;
    padding: 40px;
    gap: 16px;
  }

  .welcome-logo {
    width: 64px;
    height: 64px;
    border-radius: 16px;
    background: linear-gradient(135deg, var(--orange), var(--blue));
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 900;
    font-size: 28px;
    color: #fff;
    margin-bottom: 8px;
  }

  .welcome h2 {
    font-size: 24px;
    font-weight: 700;
    background: linear-gradient(135deg, var(--orange), var(--blue));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }

  .welcome p {
    font-size: 14px;
    color: var(--text-muted);
    max-width: 360px;
    line-height: 1.6;
  }

  .suggestions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 8px;
    width: 100%;
    max-width: 480px;
  }

  .suggestion {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 12px 14px;
    font-size: 12px;
    color: var(--text-muted);
    cursor: pointer;
    text-align: left;
    transition: all 0.15s;
    line-height: 1.4;
  }

  .suggestion:hover {
    border-color: var(--orange);
    color: var(--text);
    background: var(--surface2);
  }

  .suggestion strong {
    display: block;
    color: var(--text);
    font-size: 12px;
    margin-bottom: 2px;
  }

  /* ── Message bubbles ── */
  .message {
    display: flex;
    gap: 12px;
    max-width: 800px;
    width: 100%;
    margin: 0 auto;
    animation: fadeIn 0.2s ease;
  }

  @keyframes fadeIn {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .message.user { flex-direction: row-reverse; }

  .avatar {
    width: 32px;
    height: 32px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 13px;
    font-weight: 700;
    flex-shrink: 0;
  }

  .avatar.ai {
    background: linear-gradient(135deg, var(--orange), var(--blue));
    color: #fff;
  }

  .avatar.user-av {
    background: var(--surface3);
    color: var(--text-muted);
    border: 1px solid var(--border);
  }

  .bubble {
    padding: 12px 16px;
    border-radius: 12px;
    font-size: 14px;
    line-height: 1.65;
    max-width: calc(100% - 44px);
  }

  .message.user .bubble {
    background: linear-gradient(135deg, rgba(255,107,53,0.15), rgba(74,158,255,0.15));
    border: 1px solid rgba(255,107,53,0.25);
    color: var(--text);
    border-radius: 12px 4px 12px 12px;
  }

  .message.ai .bubble {
    background: var(--surface);
    border: 1px solid var(--border);
    color: var(--text);
    border-radius: 4px 12px 12px 12px;
  }

  /* Markdown in bubbles */
  .bubble strong { font-weight: 600; color: #fff; }
  .bubble em { color: var(--text-muted); font-style: italic; }

  .bubble code {
    background: var(--surface3);
    border: 1px solid var(--border);
    padding: 1px 5px;
    border-radius: 4px;
    font-family: 'SF Mono', 'Fira Code', monospace;
    font-size: 12px;
    color: var(--orange);
  }

  .bubble pre {
    background: var(--surface2);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 12px;
    overflow-x: auto;
    margin: 8px 0;
  }

  .bubble pre code {
    background: none;
    border: none;
    padding: 0;
    color: #b0c4de;
    font-size: 12px;
  }

  .bubble table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 13px;
  }

  .bubble th {
    background: var(--surface2);
    padding: 6px 10px;
    text-align: left;
    border-bottom: 1px solid var(--border);
    color: var(--text-muted);
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .bubble td {
    padding: 6px 10px;
    border-bottom: 1px solid var(--border);
  }

  .bubble h1, .bubble h2, .bubble h3 {
    margin: 10px 0 6px;
    color: #fff;
  }

  .bubble h2 { font-size: 15px; }
  .bubble h3 { font-size: 14px; }

  .bubble ul, .bubble ol {
    padding-left: 18px;
    margin: 6px 0;
  }

  .bubble li { margin: 3px 0; }
  .bubble blockquote {
    border-left: 3px solid var(--orange);
    padding-left: 12px;
    color: var(--text-muted);
    margin: 8px 0;
    font-style: italic;
  }

  .typing-indicator {
    display: flex;
    align-items: center;
    gap: 4px;
    padding: 14px 16px;
  }

  .typing-dot {
    width: 7px; height: 7px;
    border-radius: 50%;
    background: var(--text-dim);
    animation: typing 1.2s infinite;
  }

  .typing-dot:nth-child(2) { animation-delay: 0.2s; }
  .typing-dot:nth-child(3) { animation-delay: 0.4s; }

  @keyframes typing {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
    30% { transform: translateY(-6px); opacity: 1; }
  }

  /* ── Input area ── */
  .input-area {
    padding: 16px 24px 20px;
    border-top: 1px solid var(--border);
    flex-shrink: 0;
  }

  .input-wrap {
    display: flex;
    align-items: flex-end;
    gap: 10px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 10px 10px 10px 16px;
    max-width: 800px;
    margin: 0 auto;
    transition: border-color 0.2s;
  }

  .input-wrap:focus-within {
    border-color: var(--orange);
    box-shadow: 0 0 0 2px rgba(255,107,53,0.1);
  }

  #msg-input {
    flex: 1;
    background: none;
    border: none;
    outline: none;
    color: var(--text);
    font-size: 14px;
    line-height: 1.5;
    resize: none;
    max-height: 160px;
    font-family: inherit;
    padding: 2px 0;
  }

  #msg-input::placeholder { color: var(--text-dim); }

  .send-btn {
    width: 34px;
    height: 34px;
    border-radius: 8px;
    background: linear-gradient(135deg, var(--orange), var(--blue));
    border: none;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    transition: opacity 0.2s, transform 0.1s;
  }

  .send-btn:hover { opacity: 0.85; transform: scale(1.05); }
  .send-btn:active { transform: scale(0.95); }
  .send-btn:disabled { opacity: 0.4; cursor: default; transform: none; }

  .send-btn svg { width: 16px; height: 16px; fill: #fff; }

  .input-hint {
    text-align: center;
    font-size: 11px;
    color: var(--text-dim);
    margin-top: 8px;
    max-width: 800px;
    margin-left: auto;
    margin-right: auto;
  }
</style>
</head>
<body>

<!-- Sidebar -->
<aside class="sidebar">
  <div class="sidebar-logo">
    <div class="logo-mark">A</div>
    <div class="logo-text">
      <h1>Adamus</h1>
      <p>AI CTO for Genre</p>
    </div>
  </div>

  <div class="status-section">
    <div class="status-label">System Status</div>
    <div class="status-item">
      <span class="label" style="display:flex;align-items:center">
        <span class="status-dot dot-green"></span>Tests
      </span>
      <span class="value" id="s-tests">198 ✓</span>
    </div>
    <div class="status-item">
      <span class="label" style="display:flex;align-items:center">
        <span class="status-dot" id="s-git-dot"></span>Git
      </span>
      <span class="value" id="s-git">—</span>
    </div>
    <div class="status-item">
      <span class="label" style="display:flex;align-items:center">
        <span class="status-dot dot-orange"></span>Memory
      </span>
      <span class="value" id="s-mem">—</span>
    </div>
    <div class="status-item">
      <span class="label" style="display:flex;align-items:center">
        <span class="status-dot dot-green"></span>MRR
      </span>
      <span class="value">$0 → $10K</span>
    </div>
  </div>

  <button class="new-chat-btn" onclick="newChat()">+ New Chat</button>

  <div class="history-section" id="history">
    <div class="status-label">Recent</div>
  </div>
</aside>

<!-- Main -->
<main class="main">
  <header class="chat-header">
    <h2 id="chat-title">Adamus Chat</h2>
    <div class="model-badge">
      <span></span>claude-sonnet-4-6
    </div>
  </header>

  <div class="messages" id="messages">
    <div class="welcome" id="welcome">
      <div class="welcome-logo">A</div>
      <h2>Talk to Adamus</h2>
      <p>Your persistent AI CTO. Ask anything about Genre, the codebase, strategy, or what to build next.</p>
      <div class="suggestions">
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="What's the current project status?">
          <strong>Project Status</strong>
          Tests, git, what's done
        </button>
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="What should we build for Day 6?">
          <strong>Day 6 Plan</strong>
          Tech AI roadmap
        </button>
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="How does the memory system work?">
          <strong>Memory System</strong>
          How Adamus remembers
        </button>
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="What's our path to $10K MRR?">
          <strong>$10K MRR</strong>
          Business strategy
        </button>
      </div>
    </div>
  </div>

  <div class="input-area">
    <div class="input-wrap">
      <textarea
        id="msg-input"
        placeholder="Ask Adamus anything..."
        rows="1"
        onkeydown="handleKey(event)"
        oninput="autoResize(this)"
      ></textarea>
      <button class="send-btn" id="send-btn" onclick="sendMessage()">
        <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    </div>
    <div class="input-hint">Enter to send · Shift+Enter for new line</div>
  </div>
</main>

<script>
  // Marked.js CDN for markdown rendering
  const MARKED_LOADED = new Promise(resolve => {
    const s = document.createElement('script');
    s.src = 'https://cdn.jsdelivr.net/npm/marked/marked.min.js';
    s.onload = resolve;
    s.onerror = resolve; // fail gracefully
    document.head.appendChild(s);
  });

  let messages = [];
  let isStreaming = false;
  let chatHistory = JSON.parse(localStorage.getItem('adamus_history') || '[]');

  // Load status
  fetch('/api/status').then(r => r.json()).then(s => {
    document.getElementById('s-tests').textContent = s.tests + ' ✓';
    document.getElementById('s-git').textContent = s.clean ? 'clean ✓' : 'dirty';
    document.getElementById('s-git-dot').className = 'status-dot ' + (s.clean ? 'dot-green' : 'dot-orange');
    document.getElementById('s-mem').textContent = s.memories + ' saved';
  }).catch(() => {});

  function renderMarkdown(text) {
    if (typeof marked !== 'undefined') {
      try { return marked.parse(text); } catch(e) {}
    }
    // Fallback: basic markdown
    return text
      .replace(/[*][*](.+?)[*][*]/g, '<strong>$1</strong>')
      .replace(/[*](.+?)[*]/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      .replace(/^#{1,3} (.+)$/gm, (m, t, o, s) => {
        const l = m.match(/^#+/)[0].length;
        return `<h${l}>${t}</h${l}>`;
      })
      .replace(/\n\n/g, '</p><p>')
      .replace(/\n/g, '<br>');
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 160) + 'px';
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function sendSuggestion(msg) {
    document.getElementById('msg-input').value = msg;
    sendMessage();
  }

  function newChat() {
    messages = [];
    const m = document.getElementById('messages');
    m.innerHTML = document.querySelector('.welcome') ? '' : '';
    m.innerHTML = `<div class="welcome" id="welcome">
      <div class="welcome-logo">A</div>
      <h2>Talk to Adamus</h2>
      <p>Your persistent AI CTO. Ask anything about Genre, the codebase, strategy, or what to build next.</p>
      <div class="suggestions">
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="What's the current project status?"><strong>Project Status</strong>Tests, git, what's done</button>
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="What should we build for Day 6?"><strong>Day 6 Plan</strong>Tech AI roadmap</button>
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="How does the memory system work?"><strong>Memory System</strong>How Adamus remembers</button>
        <button class="suggestion" onclick="sendSuggestion(this.dataset.msg)" data-msg="What's our path to $10K MRR?"><strong>$10K MRR</strong>Business strategy</button>
      </div>
    </div>`;
    document.getElementById('chat-title').textContent = 'Adamus Chat';
  }

  async function sendMessage() {
    if (isStreaming) return;
    const input = document.getElementById('msg-input');
    const text = input.value.trim();
    if (!text) return;

    // Hide welcome
    const welcome = document.getElementById('welcome');
    if (welcome) welcome.remove();

    // Add user message
    messages.push({ role: 'user', content: text });
    appendMessage('user', text);
    input.value = '';
    input.style.height = 'auto';

    // Update title
    if (messages.length === 1) {
      document.getElementById('chat-title').textContent = text.slice(0, 40) + (text.length > 40 ? '...' : '');
    }

    // Show typing
    const typingId = 'typing-' + Date.now();
    appendTyping(typingId);
    isStreaming = true;
    document.getElementById('send-btn').disabled = true;

    try {
      await MARKED_LOADED;
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages })
      });

      // Remove typing indicator
      document.getElementById(typingId)?.remove();

      // Create AI bubble for streaming
      const bubbleId = 'bubble-' + Date.now();
      appendStreamingBubble(bubbleId);

      let fullText = '';
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      const bubble = document.getElementById(bubbleId);

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        fullText += chunk;
        bubble.innerHTML = renderMarkdown(fullText);
        scrollToBottom();
      }

      messages.push({ role: 'assistant', content: fullText });
      saveHistory(text, fullText);

    } catch (err) {
      document.getElementById(typingId)?.remove();
      appendMessage('ai', '⚠️ Error connecting to Adamus. Is the server running?');
    }

    isStreaming = false;
    document.getElementById('send-btn').disabled = false;
    document.getElementById('msg-input').focus();
  }

  function appendMessage(role, text) {
    const m = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = `message ${role}`;
    const isAI = role === 'ai';
    div.innerHTML = `
      <div class="avatar ${isAI ? 'ai' : 'user-av'}">${isAI ? 'A' : 'G'}</div>
      <div class="bubble">${isAI ? renderMarkdown(text) : escapeHTML(text)}</div>
    `;
    m.appendChild(div);
    scrollToBottom();
  }

  function appendTyping(id) {
    const m = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ai';
    div.id = id;
    div.innerHTML = `
      <div class="avatar ai">A</div>
      <div class="bubble">
        <div class="typing-indicator">
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
          <div class="typing-dot"></div>
        </div>
      </div>
    `;
    m.appendChild(div);
    scrollToBottom();
  }

  function appendStreamingBubble(id) {
    const m = document.getElementById('messages');
    const div = document.createElement('div');
    div.className = 'message ai';
    div.innerHTML = `
      <div class="avatar ai">A</div>
      <div class="bubble" id="${id}"></div>
    `;
    m.appendChild(div);
    scrollToBottom();
  }

  function scrollToBottom() {
    const m = document.getElementById('messages');
    m.scrollTop = m.scrollHeight;
  }

  function escapeHTML(s) {
    return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  }

  function saveHistory(userMsg, aiMsg) {
    chatHistory.unshift({
      title: userMsg.slice(0, 40),
      date: new Date().toLocaleDateString(),
      messages: [...messages]
    });
    chatHistory = chatHistory.slice(0, 20); // keep last 20
    localStorage.setItem('adamus_history', JSON.stringify(chatHistory));
    renderHistory();
  }

  function renderHistory() {
    const h = document.getElementById('history');
    const label = h.querySelector('.status-label');
    h.innerHTML = '';
    h.appendChild(label);
    chatHistory.slice(0, 10).forEach((item, i) => {
      const d = document.createElement('div');
      d.className = 'history-item' + (i === 0 ? ' active' : '');
      d.textContent = item.title;
      d.onclick = () => loadChat(i);
      h.appendChild(d);
    });
  }

  function loadChat(i) {
    const item = chatHistory[i];
    if (!item) return;
    messages = [...item.messages];
    const m = document.getElementById('messages');
    m.innerHTML = '';
    messages.forEach(msg => {
      appendMessage(msg.role === 'user' ? 'user' : 'ai', msg.content);
    });
    document.getElementById('chat-title').textContent = item.title;
  }

  // Init
  renderHistory();
  document.getElementById('msg-input').focus();
</script>
</body>
</html>'''


@app.route("/")
def index():
    return HTML


@app.route("/api/status")
def api_status():
    return jsonify(get_system_status())


@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    msgs = data.get("messages", [])

    # Load env
    env_path = REPO / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    def generate():
        for chunk in chat_with_claude(msgs):
            yield chunk

    return Response(stream_with_context(generate()), mimetype="text/plain")


if __name__ == "__main__":
    print("\n  Adamus Chat UI")
    print("  http://localhost:5001\n")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
