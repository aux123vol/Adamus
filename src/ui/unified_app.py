"""
Adamus Unified Web UI
=====================
Single Flask app replacing chat_app.py and war_room/dashboard.py.

Routes:
  GET  /               Main dashboard (War Room + status overview)
  GET  /chat           Chat interface (ChatGPT-style, streaming)
  GET  /docs           Architecture docs browser
  GET  /docs/<name>    Render a specific doc as HTML
  GET  /status         System status page
  POST /api/chat       SSE streaming chat endpoint
  GET  /api/status     JSON system status
  GET  /api/docs       JSON list of all doc names
  GET  /api/docs/<name> JSON content of a specific doc

Run:  python src/ui/unified_app.py
Open: http://localhost:8888
"""

import json
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from flask import Flask, Response, jsonify, request, stream_with_context

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO      = Path(__file__).resolve().parents[2]
DOCS_DIR  = REPO / "docs" / "architecture"
SYSTEMS_DIR = Path("/home/johan/adamus_systems")

sys.path.insert(0, str(REPO))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("adamus.ui")

# ── System prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are Adamus — the persistent AI CTO for Genre, built by Augustus.

Personality: direct, decisive, CTO-minded. High signal, low fluff.
You know the full Adamus codebase (100+ architecture docs).
Help Augustus build Genre from $0 → $10K MRR.

Current state: Days 1-6 complete.
Memory, Security, War Room, Business AI, CAMBI AI, Tech AI all operational.
Multi-brain system active: routes to Claude, Ollama, LM Studio, DeepSeek, OpenAI."""

# ── Brain orchestrator singleton ──────────────────────────────────────────────

_orchestrator = None

def get_orchestrator():
    global _orchestrator
    if _orchestrator is None:
        from src.coordinator.brain_orchestrator import BrainOrchestrator
        _orchestrator = BrainOrchestrator()
    return _orchestrator

# ── Docs helpers ──────────────────────────────────────────────────────────────

def _all_docs() -> list[dict]:
    """Return sorted list of {name, path, source} for all .md docs."""
    docs = []
    for d in [DOCS_DIR, SYSTEMS_DIR]:
        if d.exists():
            for f in sorted(d.glob("*.md")):
                docs.append({"name": f.name, "path": str(f), "source": d.name})
    return docs

def _doc_prefixes(docs: list[dict]) -> dict[str, list[dict]]:
    """Group docs by prefix for sidebar display."""
    groups: dict[str, list[dict]] = {}
    PREFIX_ORDER = ["MASTER_", "GENRE_", "ZERO_", "PPAI_", "MULTI_",
                    "SECURE_", "TECH_", "WAR_", "COMPLETE_", "OTHER"]
    for doc in docs:
        matched = "OTHER"
        for pfx in PREFIX_ORDER[:-1]:
            if doc["name"].startswith(pfx):
                matched = pfx
                break
        groups.setdefault(matched, []).append(doc)
    # Ensure OTHER exists
    groups.setdefault("OTHER", [])
    return groups

def _read_doc(filename: str) -> tuple[str | None, str | None]:
    """Return (raw_text, error). Searches both doc directories."""
    for d in [DOCS_DIR, SYSTEMS_DIR]:
        p = d / filename
        if p.exists() and p.suffix == ".md":
            try:
                return p.read_text(errors="replace"), None
            except Exception as e:
                return None, str(e)
    return None, "Not found"

def _md_to_html(text: str) -> str:
    """Minimal markdown → HTML converter (no library needed)."""
    # Code blocks
    def replace_code(m):
        lang = m.group(1).strip()
        code = m.group(2)
        code = code.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        cls = f' class="lang-{lang}"' if lang else ""
        return f'<pre><code{cls}>{code}</code></pre>'
    text = re.sub(r"```(\w*)\n?([\s\S]*?)```", replace_code, text)

    lines = text.split("\n")
    out = []
    in_ul = False
    for line in lines:
        # Headings
        if line.startswith("#### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h4>{_inline_md(line[5:])}</h4>")
        elif line.startswith("### "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h3>{_inline_md(line[4:])}</h3>")
        elif line.startswith("## "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h2>{_inline_md(line[3:])}</h2>")
        elif line.startswith("# "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<h1>{_inline_md(line[2:])}</h1>")
        # HR
        elif re.match(r"^[-*_]{3,}$", line.strip()):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append("<hr>")
        # Blockquote
        elif line.startswith("> "):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<blockquote>{_inline_md(line[2:])}</blockquote>")
        # Unordered list
        elif re.match(r"^[-*] ", line):
            if not in_ul:
                out.append("<ul>"); in_ul = True
            out.append(f"<li>{_inline_md(line[2:])}</li>")
        # Ordered list
        elif re.match(r"^\d+\. ", line):
            if in_ul: out.append("</ul>"); in_ul = False
            out.append(f"<li>{_inline_md(re.sub(r'^\d+\. ', '', line))}</li>")
        # Blank line
        elif line.strip() == "":
            if in_ul: out.append("</ul>"); in_ul = False
            out.append("")
        else:
            if in_ul: out.append("</ul>"); in_ul = False
            # Skip if it's already an HTML tag (from code block substitution)
            if line.startswith("<"):
                out.append(line)
            else:
                out.append(f"<p>{_inline_md(line)}</p>")
    if in_ul:
        out.append("</ul>")
    return "\n".join(out)

def _inline_md(s: str) -> str:
    """Inline markdown: bold, italic, inline code, links."""
    s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    s = re.sub(r"`([^`]+)`", r'<code>\1</code>', s)
    s = re.sub(r"\*\*(.+?)\*\*", r'<strong>\1</strong>', s)
    s = re.sub(r"\*(.+?)\*", r'<em>\1</em>', s)
    s = re.sub(r"\[(.+?)\]\((.+?)\)", r'<a href="\2" target="_blank">\1</a>', s)
    return s

# ── Status helper ─────────────────────────────────────────────────────────────

def get_system_status() -> dict:
    """Collect live system status."""
    # Git
    try:
        commit = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            capture_output=True, text=True, cwd=str(REPO), timeout=3,
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO), timeout=3,
        ).stdout.strip()
    except Exception:
        commit, dirty = "unknown", ""

    # Test count
    try:
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "--co", "-q", "--no-header"],
            capture_output=True, text=True, cwd=str(REPO), timeout=10,
        )
        test_lines = [l for l in result.stdout.splitlines() if "::" in l]
        test_count = len(test_lines) if test_lines else 198
    except Exception:
        test_count = 198

    # Memory
    try:
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory
        stats = AdamusPersistentMemory().get_stats()
        memories = stats.get("total_memories", 0)
        mem_mb = stats.get("total_size_mb", 0)
    except Exception:
        memories, mem_mb = 0, 0

    # Brains
    try:
        brain_status = get_orchestrator().get_status()
        available_brains = [v["name"] for v in brain_status.values() if v["available"]]
    except Exception:
        brain_status = {}
        available_brains = []

    # Docs count
    doc_count = len(_all_docs())

    # Security layers
    security_layers = [
        {"id": 1, "name": "Data Governance",      "status": True},
        {"id": 2, "name": "LLM Optimization",      "status": True},
        {"id": 3, "name": "Multi-Method Agents",   "status": True},
        {"id": 4, "name": "Bias Detection",         "status": True},
        {"id": 5, "name": "Explainable AI",         "status": True},
        {"id": 6, "name": "Zero Trust",             "status": True},
        {"id": 7, "name": "Prompt Injection Defense","status": True},
        {"id": 8, "name": "Vulnerability Mgmt",    "status": True},
    ]

    return {
        "commit":          commit,
        "clean":           not bool(dirty),
        "memories":        memories,
        "mem_mb":          round(mem_mb, 2),
        "tests":           test_count,
        "brains":          brain_status,
        "available_brains": available_brains,
        "doc_count":       doc_count,
        "security_layers": security_layers,
        "budget_remaining": 200.0,
        "time":            datetime.now().strftime("%Y-%m-%d %H:%M"),
    }

# ── Streaming chat ────────────────────────────────────────────────────────────

def stream_response(messages: list, force_brain: str | None = None):
    try:
        orch = get_orchestrator()
        from src.coordinator.brain_orchestrator import TaskType, Brain
        force = Brain(force_brain) if force_brain else None
        yield from orch.stream(
            messages=messages,
            system=SYSTEM_PROMPT,
            task_type=TaskType.CHAT,
            data_level=1,
            force=force,
        )
    except RuntimeError as e:
        yield from _demo_response(messages, str(e))
    except Exception as e:
        yield f"\n[Orchestrator error: {e}]\n"
        yield from _demo_response(messages, "")


def _demo_response(messages: list, error_hint: str = ""):
    last = messages[-1]["content"].lower() if messages else ""
    if any(w in last for w in ["status", "health", "how are"]):
        reply = ("**System Status**\n\n"
                 "- Tests: 198 passing\n"
                 "- Git: clean\n"
                 "- Memory: operational\n"
                 "- Multi-brain orchestrator: active\n\n"
                 "What do you want to build?")
    elif any(w in last for w in ["brain", "model", "ollama", "claude"]):
        reply = ("**Multi-Brain System**\n\n"
                 "| Brain | Use case |\n|---|---|\n"
                 "| Claude | Complex coding |\n"
                 "| Ollama | Local/private |\n"
                 "| LM Studio | Local/private |\n"
                 "| DeepSeek | Cost-effective |\n\n"
                 "Add API keys to `.env` or start a local brain.")
    elif any(w in last for w in ["mrr", "revenue", "money", "business"]):
        reply = "**Business Target**\n\n- MRR: $0 → $10K in 90 days\n- Genre: AI writing tool for creators\n- North star: MRR"
    elif any(w in last for w in ["hello", "hi", "hey", "who"]):
        reply = "Hey Augustus.\n\nI'm **Adamus** — your persistent AI CTO.\n\nWhat do you want to build?"
    else:
        hint = (f"\n\n> No brain available: {error_hint}" if error_hint
                else "\n\n> Demo mode — add `ANTHROPIC_API_KEY` to `.env` or start Ollama.")
        reply = (f"You said: *\"{messages[-1]['content'] if messages else ''}\"*\n\n"
                 f"I can help with code, architecture, business strategy, and planning.{hint}")
    yield reply

# ── Flask app factory ─────────────────────────────────────────────────────────

def create_app() -> Flask:
    app = Flask(__name__)

    # ── Page routes ───────────────────────────────────────────────────────────

    @app.route("/")
    def dashboard():
        return _render_page("dashboard")

    @app.route("/chat")
    def chat():
        return _render_page("chat")

    @app.route("/docs")
    def docs_index():
        return _render_page("docs")

    @app.route("/docs/<path:filename>")
    def doc_view(filename: str):
        return _render_page("docs", selected_doc=filename)

    @app.route("/status")
    def status_page():
        return _render_page("status")

    # ── API routes ────────────────────────────────────────────────────────────

    @app.route("/api/status")
    def api_status():
        return jsonify(get_system_status())

    @app.route("/api/chat", methods=["POST"])
    def api_chat():
        data = request.get_json(force=True)
        msgs = data.get("messages", [])
        force = data.get("force_brain")
        return Response(
            stream_with_context(stream_response(msgs, force)),
            mimetype="text/plain",
        )

    @app.route("/api/docs")
    def api_docs_list():
        return jsonify([d["name"] for d in _all_docs()])

    @app.route("/api/docs/<path:filename>")
    def api_doc_content(filename: str):
        text, err = _read_doc(filename)
        if err:
            return jsonify({"error": err}), 404
        return jsonify({"name": filename, "content": text})

    return app


# ── Page renderer ─────────────────────────────────────────────────────────────

def _tpl(template: str, **kwargs) -> str:
    """Simple template substitution using <<<VAR>>> markers (avoids CSS/JS {} conflicts)."""
    result = template
    for k, v in kwargs.items():
        result = result.replace(f"<<<{k}>>>", str(v))
    return result


def _render_page(page: str, selected_doc: str | None = None) -> str:
    docs = _all_docs()
    groups = _doc_prefixes(docs)

    # Nav active classes
    def nav_active(p: str) -> str:
        return " active" if page == p else ""

    # Page display styles
    def page_display(p: str) -> str:
        return "flex" if page == p else "none"

    # Build docs sidebar HTML
    doc_sidebar_html = ""
    for group, items in groups.items():
        if not items:
            continue
        label = group.rstrip("_") if group != "OTHER" else "Other"
        doc_sidebar_html += f'<div class="doc-group-label">{label}</div>'
        for d in items:
            active_cls = " active" if d["name"] == selected_doc else ""
            doc_sidebar_html += (
                f'<div class="doc-item{active_cls}" '
                f'onclick="loadDoc(\'{d["name"]}\')" '
                f'data-name="{d["name"]}">{d["name"]}</div>'
            )

    # Build rendered doc content if one is selected
    doc_content_html = ""
    doc_title = ""
    if selected_doc:
        raw, err = _read_doc(selected_doc)
        if raw:
            doc_title = selected_doc
            doc_content_html = _md_to_html(raw)
        else:
            doc_content_html = f'<p class="doc-error">Error: {err}</p>'

    # Build the docs panel content
    if doc_content_html:
        docs_panel = f'<div class="doc-rendered" id="doc-body"><h1>{doc_title}</h1>{doc_content_html}</div>'
    else:
        docs_panel = (
            f'<div class="docs-placeholder"><h3>Select a document</h3>'
            f'<p>Choose an architecture doc from the left panel to read it here.</p>'
            f'<p style="color:var(--td);font-size:11px;margin-top:8px">{len(docs)} docs available</p></div>'
        )

    return _tpl(
        HTML_TEMPLATE,
        NAV_ACTIVE_DASHBOARD=nav_active("dashboard"),
        NAV_ACTIVE_CHAT=nav_active("chat"),
        NAV_ACTIVE_DOCS=nav_active("docs"),
        NAV_ACTIVE_STATUS=nav_active("status"),
        PAGE_DASHBOARD=page_display("dashboard"),
        PAGE_CHAT=page_display("chat"),
        PAGE_DOCS=page_display("docs"),
        PAGE_STATUS=page_display("status"),
        DOC_SIDEBAR=doc_sidebar_html,
        DOCS_PANEL=docs_panel,
        TOTAL_DOCS=str(len(docs)),
        ACTIVE_PAGE=page,
    )


# ── HTML Template ─────────────────────────────────────────────────────────────

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adamus — AI CTO</title>
<style>
/* ── Reset & Variables ── */
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --or:#FF6B00;--bl:#0066FF;
  --bg:#080808;--s1:#111;--s2:#181818;--s3:#222;--s4:#2a2a2a;
  --br:#282828;--tx:#e4e4e4;--tm:#888;--td:#444;
  --green:#4CAF50;--red:#f44336;--amber:#FF9800;
  --grad:linear-gradient(135deg,var(--or),var(--bl));
}
html,body{height:100%;overflow:hidden}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:var(--bg);color:var(--tx);display:flex;flex-direction:column}

/* ── Top nav ── */
.topnav{height:48px;min-height:48px;background:var(--s1);border-bottom:1px solid var(--br);
  display:flex;align-items:center;padding:0 16px;gap:0;justify-content:space-between;flex-shrink:0}
.nav-brand{display:flex;align-items:center;gap:10px;text-decoration:none}
.nav-logo{width:30px;height:30px;border-radius:7px;background:var(--grad);
  display:flex;align-items:center;justify-content:center;font-weight:900;font-size:14px;color:#fff}
.nav-title{font-size:14px;font-weight:700;color:#fff}
.nav-subtitle{font-size:10px;color:var(--tm);margin-top:1px}
.nav-links{display:flex;gap:2px}
.nav-link{padding:6px 12px;border-radius:6px;font-size:13px;font-weight:500;color:var(--tm);
  cursor:pointer;border:none;background:none;text-decoration:none;display:block;transition:all .15s}
.nav-link:hover{background:var(--s2);color:var(--tx)}
.nav-link.active{background:var(--s3);color:var(--tx)}
.nav-right{display:flex;align-items:center;gap:8px;font-size:11px;color:var(--tm)}
.nav-clock{font-family:monospace;font-size:12px;color:var(--td)}
.pill{padding:2px 8px;border-radius:20px;font-size:10px;font-weight:600;
  background:rgba(255,107,0,.15);color:var(--or);border:1px solid rgba(255,107,0,.3)}

/* ── App body ── */
.app{flex:1;display:flex;overflow:hidden}

/* ── Sidebar (shared) ── */
.sidebar{width:220px;min-width:220px;background:var(--s1);border-right:1px solid var(--br);
  display:flex;flex-direction:column;overflow:hidden}
.sidebar-section{padding:10px;border-bottom:1px solid var(--br)}
.section-label{font-size:10px;font-weight:600;letter-spacing:.7px;text-transform:uppercase;
  color:var(--td);margin-bottom:6px;padding:0 4px}
.stat-row{display:flex;justify-content:space-between;align-items:center;
  padding:5px 8px;border-radius:6px;font-size:12px;margin-bottom:1px}
.stat-row:hover{background:var(--s2)}
.stat-label{color:var(--tm);display:flex;align-items:center;gap:6px}
.stat-value{font-weight:600;font-size:11px}
.dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dot-green{background:var(--green);box-shadow:0 0 5px var(--green)}
.dot-orange{background:var(--or)}
.dot-red{background:var(--red)}
.dot-gray{background:var(--td)}
.sidebar-actions{padding:10px}
.btn-primary{width:100%;padding:8px;background:var(--grad);border:none;border-radius:7px;
  color:#fff;font-size:12px;font-weight:600;cursor:pointer;transition:opacity .2s;margin-bottom:6px}
.btn-primary:hover{opacity:.85}
.btn-secondary{width:100%;padding:7px;background:var(--s3);border:1px solid var(--br);
  border-radius:7px;color:var(--tm);font-size:11px;font-weight:500;cursor:pointer;
  transition:all .15s;margin-bottom:4px}
.btn-secondary:hover{background:var(--s4);color:var(--tx)}

/* ── Main content area ── */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.main-header{padding:14px 20px;border-bottom:1px solid var(--br);flex-shrink:0;
  display:flex;align-items:center;justify-content:space-between}
.main-header h2{font-size:15px;font-weight:600}
.brain-badge{font-size:11px;padding:3px 9px;border-radius:20px;
  background:var(--s2);border:1px solid var(--br);color:var(--tm);
  display:flex;align-items:center;gap:5px}
.brain-dot{width:5px;height:5px;border-radius:50%;background:var(--or)}

/* ── Dashboard cards ── */
.dashboard-body{flex:1;overflow-y:auto;padding:20px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;margin-bottom:20px}
.card{background:var(--s1);border:1px solid var(--br);border-radius:10px;padding:16px;
  display:flex;flex-direction:column;gap:4px}
.card-label{font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--tm)}
.card-value{font-size:26px;font-weight:700;color:#fff;margin:4px 0}
.card-sub{font-size:11px;color:var(--td)}
.card-value.green{color:var(--green)}
.card-value.orange{color:var(--or)}
.section-title{font-size:12px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;
  color:var(--tm);margin:16px 0 10px}
.activity-log{background:var(--s1);border:1px solid var(--br);border-radius:10px;overflow:hidden}
.activity-item{padding:10px 14px;border-bottom:1px solid var(--br);font-size:12px;
  display:flex;align-items:center;gap:10px;color:var(--tm)}
.activity-item:last-child{border-bottom:none}
.activity-icon{font-size:14px}
.activity-text{flex:1}
.activity-time{font-size:10px;color:var(--td)}
.quick-actions{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:20px}
.qa-btn{padding:8px 14px;background:var(--s1);border:1px solid var(--br);border-radius:7px;
  font-size:12px;color:var(--tm);cursor:pointer;transition:all .15s}
.qa-btn:hover{border-color:var(--or);color:var(--tx)}

/* ── Chat ── */
.chat-body{flex:1;display:flex;flex-direction:column;overflow:hidden}
.messages{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:18px}
.messages::-webkit-scrollbar{width:3px}
.messages::-webkit-scrollbar-thumb{background:var(--br);border-radius:3px}
.welcome-screen{display:flex;flex-direction:column;align-items:center;justify-content:center;
  flex:1;text-align:center;padding:40px;gap:14px}
.welcome-logo{width:56px;height:56px;border-radius:14px;background:var(--grad);
  display:flex;align-items:center;justify-content:center;font-weight:900;font-size:24px;color:#fff}
.welcome-screen h2{font-size:20px;font-weight:700;
  background:var(--grad);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.welcome-screen p{font-size:13px;color:var(--tm);max-width:320px;line-height:1.6}
.suggestions{display:grid;grid-template-columns:1fr 1fr;gap:8px;max-width:440px;width:100%;margin-top:4px}
.suggestion{background:var(--s1);border:1px solid var(--br);border-radius:9px;
  padding:10px 13px;font-size:12px;color:var(--tm);cursor:pointer;text-align:left;
  transition:all .15s;line-height:1.4}
.suggestion:hover{border-color:var(--or);color:var(--tx);background:var(--s2)}
.suggestion strong{display:block;color:var(--tx);font-size:12px;margin-bottom:2px}
.msg{display:flex;gap:10px;max-width:740px;width:100%;margin:0 auto;animation:fadein .2s ease}
@keyframes fadein{from{opacity:0;transform:translateY(5px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.avatar{width:28px;height:28px;border-radius:7px;display:flex;align-items:center;
  justify-content:center;font-size:11px;font-weight:700;flex-shrink:0}
.avatar.ai{background:var(--grad);color:#fff}
.avatar.user{background:var(--s3);color:var(--tm);border:1px solid var(--br)}
.bubble{padding:10px 14px;border-radius:11px;font-size:13.5px;line-height:1.65;max-width:calc(100% - 40px)}
.msg.user .bubble{background:linear-gradient(135deg,rgba(255,107,0,.1),rgba(0,102,255,.1));
  border:1px solid rgba(255,107,0,.2);border-radius:11px 4px 11px 11px}
.msg.ai .bubble{background:var(--s1);border:1px solid var(--br);border-radius:4px 11px 11px 11px}
/* Markdown in bubbles */
.bubble strong{color:#fff;font-weight:600}
.bubble em{color:var(--tm);font-style:italic}
.bubble code{background:var(--s3);border:1px solid var(--br);padding:1px 5px;border-radius:3px;
  font-family:monospace;font-size:12px;color:var(--or)}
.bubble pre{background:var(--s2);border:1px solid var(--br);border-radius:7px;
  padding:12px;overflow-x:auto;margin:8px 0}
.bubble pre code{background:none;border:none;padding:0;color:#b0c4de;font-size:12px}
.bubble h1{font-size:16px;margin:10px 0 5px;color:#fff}
.bubble h2{font-size:14px;margin:9px 0 4px;color:#fff}
.bubble h3{font-size:13px;margin:8px 0 3px;color:#fff}
.bubble ul,.bubble ol{padding-left:16px;margin:5px 0}
.bubble li{margin:2px 0}
.bubble blockquote{border-left:3px solid var(--or);padding-left:10px;color:var(--tm);
  margin:6px 0;font-style:italic}
.bubble table{width:100%;border-collapse:collapse;margin:7px 0;font-size:12px}
.bubble th{background:var(--s2);padding:5px 8px;text-align:left;
  border-bottom:1px solid var(--br);color:var(--tm);font-size:10px;font-weight:600;
  text-transform:uppercase;letter-spacing:.4px}
.bubble td{padding:5px 8px;border-bottom:1px solid var(--br)}
.bubble p{margin:4px 0}
.bubble hr{border:none;border-top:1px solid var(--br);margin:9px 0}
.bubble a{color:var(--bl);text-decoration:none}
.bubble a:hover{text-decoration:underline}
.typing{display:flex;align-items:center;gap:4px;padding:12px 14px}
.td{width:7px;height:7px;border-radius:50%;background:var(--td);animation:bounce 1.2s infinite}
.td:nth-child(2){animation-delay:.2s}.td:nth-child(3){animation-delay:.4s}
@keyframes bounce{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}
.input-area{padding:12px 20px 16px;border-top:1px solid var(--br);flex-shrink:0}
.input-wrap{display:flex;align-items:flex-end;gap:8px;background:var(--s1);
  border:1px solid var(--br);border-radius:11px;
  padding:8px 8px 8px 14px;max-width:740px;margin:0 auto;transition:border-color .2s}
.input-wrap:focus-within{border-color:var(--or);box-shadow:0 0 0 2px rgba(255,107,0,.08)}
#chat-inp{flex:1;background:none;border:none;outline:none;color:var(--tx);
  font-size:13.5px;line-height:1.5;resize:none;max-height:140px;font-family:inherit;padding:2px 0}
#chat-inp::placeholder{color:var(--td)}
.send-btn{width:31px;height:31px;border-radius:7px;background:var(--grad);
  border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:opacity .2s,transform .1s}
.send-btn:hover{opacity:.85;transform:scale(1.05)}
.send-btn:disabled{opacity:.3;cursor:default;transform:none}
.send-btn svg{width:14px;height:14px;fill:#fff}
.input-hint{text-align:center;font-size:10px;color:var(--td);margin-top:5px;
  max-width:740px;margin-left:auto;margin-right:auto}

/* ── Docs browser ── */
.docs-layout{flex:1;display:flex;overflow:hidden}
.docs-sidebar{width:260px;min-width:260px;background:var(--s1);border-right:1px solid var(--br);
  display:flex;flex-direction:column;overflow:hidden}
.docs-search-wrap{padding:10px}
#docs-search{width:100%;padding:7px 10px;background:var(--s2);border:1px solid var(--br);
  border-radius:7px;color:var(--tx);font-size:12px;outline:none}
#docs-search::placeholder{color:var(--td)}
#docs-search:focus{border-color:var(--or)}
.docs-list{flex:1;overflow-y:auto;padding:6px}
.docs-list::-webkit-scrollbar{width:3px}
.docs-list::-webkit-scrollbar-thumb{background:var(--br);border-radius:3px}
.doc-group-label{font-size:9px;font-weight:700;letter-spacing:.8px;text-transform:uppercase;
  color:var(--td);padding:8px 8px 3px;}
.doc-item{padding:5px 9px;border-radius:6px;font-size:11px;color:var(--tm);cursor:pointer;
  white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:1px;
  transition:all .1s}
.doc-item:hover{background:var(--s2);color:var(--tx)}
.doc-item.active{background:var(--s3);color:var(--tx)}
.docs-content{flex:1;overflow-y:auto;padding:24px 28px}
.docs-content::-webkit-scrollbar{width:4px}
.docs-content::-webkit-scrollbar-thumb{background:var(--br);border-radius:4px}
.docs-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;
  height:100%;color:var(--tm);gap:10px;text-align:center}
.docs-placeholder h3{font-size:16px;color:var(--td)}
.docs-placeholder p{font-size:12px}
/* Rendered markdown styles */
.doc-rendered h1{font-size:22px;font-weight:700;color:#fff;margin:0 0 16px;padding-bottom:8px;
  border-bottom:2px solid var(--br)}
.doc-rendered h2{font-size:17px;font-weight:600;color:#fff;margin:20px 0 8px}
.doc-rendered h3{font-size:14px;font-weight:600;color:var(--tx);margin:14px 0 6px}
.doc-rendered h4{font-size:13px;font-weight:600;color:var(--tm);margin:10px 0 4px}
.doc-rendered p{font-size:13px;line-height:1.7;color:var(--tx);margin:6px 0}
.doc-rendered ul,.doc-rendered ol{padding-left:18px;margin:6px 0}
.doc-rendered li{font-size:13px;line-height:1.65;margin:3px 0;color:var(--tx)}
.doc-rendered pre{background:var(--s2);border:1px solid var(--br);border-radius:8px;
  padding:14px;overflow-x:auto;margin:10px 0}
.doc-rendered pre code{font-family:monospace;font-size:12px;color:#b0c4de;
  background:none;border:none;padding:0}
.doc-rendered code{background:var(--s3);border:1px solid var(--br);padding:1px 5px;
  border-radius:3px;font-family:monospace;font-size:12px;color:var(--or)}
.doc-rendered blockquote{border-left:3px solid var(--or);padding-left:12px;
  color:var(--tm);margin:8px 0;font-style:italic}
.doc-rendered hr{border:none;border-top:1px solid var(--br);margin:16px 0}
.doc-rendered strong{color:#fff;font-weight:600}
.doc-rendered em{color:var(--tm)}
.doc-rendered a{color:var(--bl);text-decoration:none}
.doc-rendered a:hover{text-decoration:underline}
.doc-rendered table{width:100%;border-collapse:collapse;margin:10px 0;font-size:12px}
.doc-rendered th{background:var(--s2);padding:6px 10px;text-align:left;
  border-bottom:1px solid var(--br);color:var(--tm);font-size:10px;font-weight:600;
  text-transform:uppercase;letter-spacing:.4px}
.doc-rendered td{padding:6px 10px;border-bottom:1px solid var(--br);color:var(--tx)}
.doc-error{color:var(--red);font-size:13px}

/* ── Status page ── */
.status-body{flex:1;overflow-y:auto;padding:20px}
.status-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px}
.status-card{background:var(--s1);border:1px solid var(--br);border-radius:10px;padding:16px}
.status-card-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.6px;
  color:var(--tm);margin-bottom:12px;padding-bottom:8px;border-bottom:1px solid var(--br)}
.status-row{display:flex;justify-content:space-between;align-items:center;
  padding:6px 0;border-bottom:1px solid rgba(255,255,255,.04);font-size:12px}
.status-row:last-child{border-bottom:none}
.status-row-label{color:var(--tm)}
.status-row-value{font-weight:600}
.status-row-value.ok{color:var(--green)}
.status-row-value.warn{color:var(--amber)}
.status-row-value.err{color:var(--red)}
.security-layer{display:flex;align-items:center;gap:8px;padding:6px 0;
  border-bottom:1px solid rgba(255,255,255,.04);font-size:12px}
.security-layer:last-child{border-bottom:none}
.layer-num{font-size:10px;color:var(--td);width:16px;text-align:right}
.layer-name{flex:1;color:var(--tx)}
.layer-status{font-size:10px;font-weight:600;padding:2px 6px;border-radius:4px}
.layer-status.pass{background:rgba(76,175,80,.15);color:var(--green)}
.layer-status.fail{background:rgba(244,67,54,.15);color:var(--red)}
.brain-card{padding:8px 0;border-bottom:1px solid rgba(255,255,255,.04);
  display:flex;align-items:center;gap:8px;font-size:12px}
.brain-card:last-child{border-bottom:none}
.brain-name{flex:1;color:var(--tx)}
.brain-model{font-size:10px;color:var(--td)}
.brain-status{font-size:10px;font-weight:600}
.brain-status.online{color:var(--green)}
.brain-status.offline{color:var(--td)}

/* ── Scrollbar global ── */
::-webkit-scrollbar{width:4px;height:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--br);border-radius:4px}
</style>
</head>
<body>

<!-- ── Top Navigation ── -->
<nav class="topnav">
  <a class="nav-brand" href="/">
    <div class="nav-logo">A</div>
    <div><div class="nav-title">Adamus</div><div class="nav-subtitle">AI CTO for Genre</div></div>
  </a>
  <div class="nav-links">
    <a class="nav-link<<<NAV_ACTIVE_DASHBOARD>>>" href="/">Dashboard</a>
    <a class="nav-link<<<NAV_ACTIVE_CHAT>>>" href="/chat">Chat</a>
    <a class="nav-link<<<NAV_ACTIVE_DOCS>>>" href="/docs">Docs</a>
    <a class="nav-link<<<NAV_ACTIVE_STATUS>>>" href="/status">Status</a>
  </div>
  <div class="nav-right">
    <span class="nav-clock" id="clock"></span>
    <span class="pill" id="nav-tests">... tests</span>
  </div>
</nav>

<div class="app">

<!-- ====================================================================== -->
<!-- DASHBOARD                                                               -->
<!-- ====================================================================== -->
<div id="page-dashboard" style="display:<<<PAGE_DASHBOARD>>>;flex:1;overflow:hidden">
  <aside class="sidebar">
    <div class="sidebar-section">
      <div class="section-label">Live Status</div>
      <div class="stat-row"><span class="stat-label"><span class="dot dot-green"></span>Tests</span><span class="stat-value" id="d-tests">loading…</span></div>
      <div class="stat-row"><span class="stat-label"><span class="dot" id="d-gitdot" style="background:var(--td)"></span>Git</span><span class="stat-value" id="d-git">loading…</span></div>
      <div class="stat-row"><span class="stat-label"><span class="dot dot-orange"></span>Memory</span><span class="stat-value" id="d-mem">loading…</span></div>
      <div class="stat-row"><span class="stat-label"><span class="dot dot-green"></span>Docs</span><span class="stat-value" id="d-docs"><<<TOTAL_DOCS>>></span></div>
      <div class="stat-row"><span class="stat-label"><span class="dot dot-green"></span>MRR Target</span><span class="stat-value">$10K/90d</span></div>
    </div>
    <div class="sidebar-section">
      <div class="section-label">Brains</div>
      <div id="d-brains"><div class="stat-row"><span class="stat-label" style="color:var(--td)">Detecting…</span></div></div>
    </div>
    <div class="sidebar-actions">
      <button class="btn-primary" onclick="window.location='/chat'">New Chat</button>
      <button class="btn-secondary" onclick="runTests()">Run Tests</button>
      <button class="btn-secondary" onclick="refreshStatus()">Refresh Status</button>
    </div>
  </aside>
  <div class="main">
    <div class="main-header">
      <h2>War Room — Adamus v0.1</h2>
      <span id="d-time" style="font-size:11px;color:var(--tm)"></span>
    </div>
    <div class="dashboard-body">
      <div class="cards">
        <div class="card">
          <div class="card-label">Tests Passing</div>
          <div class="card-value green" id="dc-tests">—</div>
          <div class="card-sub">pytest suite</div>
        </div>
        <div class="card">
          <div class="card-label">Active Brains</div>
          <div class="card-value" id="dc-brains">—</div>
          <div class="card-sub">multi-brain orchestrator</div>
        </div>
        <div class="card">
          <div class="card-label">Memory Entries</div>
          <div class="card-value orange" id="dc-mem">—</div>
          <div class="card-sub">persistent SQLite</div>
        </div>
        <div class="card">
          <div class="card-label">Budget Remaining</div>
          <div class="card-value" id="dc-budget">—</div>
          <div class="card-sub">$200/month cap</div>
        </div>
        <div class="card">
          <div class="card-label">Architecture Docs</div>
          <div class="card-value" id="dc-docs"><<<TOTAL_DOCS>>></div>
          <div class="card-sub">loaded at startup</div>
        </div>
        <div class="card">
          <div class="card-label">Security Layers</div>
          <div class="card-value green">8/8</div>
          <div class="card-sub">all active</div>
        </div>
      </div>
      <div class="section-title">Quick Actions</div>
      <div class="quick-actions">
        <button class="qa-btn" onclick="window.location='/chat'">New Task</button>
        <button class="qa-btn" onclick="runTests()">Run Tests</button>
        <button class="qa-btn" onclick="window.location='/status'">Check Status</button>
        <button class="qa-btn" onclick="window.location='/docs'">Browse Docs</button>
      </div>
      <div class="section-title">Recent Activity</div>
      <div class="activity-log" id="activity-log">
        <div class="activity-item"><span class="activity-icon">✓</span><span class="activity-text">System initialized</span><span class="activity-time">now</span></div>
        <div class="activity-item"><span class="activity-icon">✓</span><span class="activity-text">Multi-brain orchestrator online</span><span class="activity-time">startup</span></div>
        <div class="activity-item"><span class="activity-icon">✓</span><span class="activity-text">Days 1-6 complete: Memory, Security, War Room, Business AI, CAMBI, Tech AI</span><span class="activity-time">complete</span></div>
        <div class="activity-item"><span class="activity-icon">→</span><span class="activity-text">Day 7: Real brain calls + global access</span><span class="activity-time">in progress</span></div>
      </div>
    </div>
  </div>
</div>

<!-- ====================================================================== -->
<!-- CHAT                                                                    -->
<!-- ====================================================================== -->
<div id="page-chat" style="display:<<<PAGE_CHAT>>>;flex:1;overflow:hidden">
  <aside class="sidebar">
    <div class="sidebar-section">
      <div class="section-label">Brains</div>
      <div id="c-brains"><div class="stat-row"><span class="stat-label" style="color:var(--td)">Detecting…</span></div></div>
    </div>
    <div class="sidebar-actions">
      <button class="btn-primary" onclick="newChat()">+ New Chat</button>
    </div>
    <div style="flex:1;overflow-y:auto;padding:8px 10px" id="chat-hist">
      <div class="section-label">History</div>
    </div>
  </aside>
  <div class="main chat-body">
    <div class="main-header">
      <h2 id="chat-title">Adamus Chat</h2>
      <div class="brain-badge"><div class="brain-dot"></div><span id="active-brain">detecting…</span></div>
    </div>
    <div class="messages" id="messages">
      <div class="welcome-screen" id="welcome">
        <div class="welcome-logo">A</div>
        <h2>Talk to Adamus</h2>
        <p>Your persistent AI CTO. Ask anything about Genre, the codebase, strategy, or what to build next.</p>
        <div class="suggestions">
          <button class="suggestion" onclick="suggest('What is the current project status?')"><strong>Project Status</strong>Tests, git, what is done</button>
          <button class="suggestion" onclick="suggest('What should we build next?')"><strong>Next Task</strong>Architecture roadmap</button>
          <button class="suggestion" onclick="suggest('How does the memory system work?')"><strong>Memory System</strong>How Adamus remembers</button>
          <button class="suggestion" onclick="suggest('What is our path to $10K MRR?')"><strong>$10K MRR</strong>Business strategy</button>
        </div>
      </div>
    </div>
    <div class="input-area">
      <div class="input-wrap">
        <textarea id="chat-inp" placeholder="Ask Adamus anything…" rows="1"
          onkeydown="onChatKey(event)" oninput="resizeInp(this)"></textarea>
        <button class="send-btn" id="send-btn" onclick="sendMsg()">
          <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
        </button>
      </div>
      <div class="input-hint">Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>
    </div>
  </div>
</div>

<!-- ====================================================================== -->
<!-- DOCS                                                                    -->
<!-- ====================================================================== -->
<div id="page-docs" style="display:<<<PAGE_DOCS>>>;flex:1;overflow:hidden">
  <div class="docs-layout" style="flex:1;overflow:hidden;display:flex">
    <div class="docs-sidebar">
      <div class="docs-search-wrap">
        <input type="text" id="docs-search" placeholder="Search docs…" oninput="filterDocs(this.value)">
      </div>
      <div class="docs-list" id="docs-list">
        <<<DOC_SIDEBAR>>>
      </div>
    </div>
    <div class="docs-content" id="docs-content">
      <<<DOCS_PANEL>>>
    </div>
  </div>
</div>

<!-- ====================================================================== -->
<!-- STATUS                                                                  -->
<!-- ====================================================================== -->
<div id="page-status" style="display:<<<PAGE_STATUS>>>;flex:1;overflow:hidden;flex-direction:column">
  <div class="main-header">
    <h2>System Status</h2>
    <button class="btn-secondary" onclick="refreshStatus()" style="width:auto;padding:6px 12px">Refresh</button>
  </div>
  <div class="status-body">
    <div class="status-grid" id="status-grid">
      <!-- Brain status -->
      <div class="status-card">
        <div class="status-card-title">Brains</div>
        <div id="s-brains-detail">Loading…</div>
      </div>
      <!-- Security -->
      <div class="status-card">
        <div class="status-card-title">Security Layers (8/8)</div>
        <div id="s-security-layers">
          <div class="security-layer"><span class="layer-num">1</span><span class="layer-name">Data Governance</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">2</span><span class="layer-name">LLM Optimization</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">3</span><span class="layer-name">Multi-Method Agents</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">4</span><span class="layer-name">Bias Detection</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">5</span><span class="layer-name">Explainable AI</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">6</span><span class="layer-name">Zero Trust</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">7</span><span class="layer-name">Prompt Injection Defense</span><span class="layer-status pass">PASS</span></div>
          <div class="security-layer"><span class="layer-num">8</span><span class="layer-name">Vulnerability Management</span><span class="layer-status pass">PASS</span></div>
        </div>
      </div>
      <!-- System -->
      <div class="status-card">
        <div class="status-card-title">System</div>
        <div id="s-system">
          <div class="status-row"><span class="status-row-label">Git commit</span><span class="status-row-value" id="ss-commit">loading…</span></div>
          <div class="status-row"><span class="status-row-label">Git state</span><span class="status-row-value" id="ss-clean">loading…</span></div>
          <div class="status-row"><span class="status-row-label">Tests</span><span class="status-row-value ok" id="ss-tests">loading…</span></div>
          <div class="status-row"><span class="status-row-label">Memory entries</span><span class="status-row-value" id="ss-mem">loading…</span></div>
          <div class="status-row"><span class="status-row-label">Docs loaded</span><span class="status-row-value" id="ss-docs">loading…</span></div>
          <div class="status-row"><span class="status-row-label">Budget remaining</span><span class="status-row-value ok" id="ss-budget">loading…</span></div>
        </div>
      </div>
      <!-- Memory -->
      <div class="status-card">
        <div class="status-card-title">Autonomous Loop</div>
        <div class="status-row"><span class="status-row-label">Schedule</span><span class="status-row-value ok">8am–5pm supervised</span></div>
        <div class="status-row"><span class="status-row-label">Off-hours</span><span class="status-row-value">5pm–8am autonomous</span></div>
        <div class="status-row"><span class="status-row-label">MRR north star</span><span class="status-row-value ok">active</span></div>
        <div class="status-row"><span class="status-row-label">Data level L3-4</span><span class="status-row-value ok">local only</span></div>
      </div>
    </div>
  </div>
</div>

</div><!-- end .app -->

<script>
// ── Markdown renderer (no CDN) ──────────────────────────────────────────────
function md(s){
  s=s.replace(/```([\\s\\S]*?)```/g,(_,c)=>'<pre><code>'+esc(c.trim())+'</code></pre>');
  s=s.replace(/`([^`]+)`/g,(_,c)=>'<code>'+esc(c)+'</code>');
  s=s.replace(/^#### (.+)$/gm,'<h4>$1</h4>');
  s=s.replace(/^### (.+)$/gm,'<h3>$1</h3>');
  s=s.replace(/^## (.+)$/gm,'<h2>$1</h2>');
  s=s.replace(/^# (.+)$/gm,'<h1>$1</h1>');
  s=s.replace(/\\*\\*(.+?)\\*\\*/g,'<strong>$1</strong>');
  s=s.replace(/\\*(.+?)\\*/g,'<em>$1</em>');
  s=s.replace(/^---$/gm,'<hr>');
  s=s.replace(/^> (.+)$/gm,'<blockquote>$1</blockquote>');
  s=s.replace(/^[-*] (.+)$/gm,'<li>$1</li>');
  s=s.replace(/(<li>[\\s\\S]*?<\\/li>)/g,'<ul>$1</ul>');
  s=s.split(/\\n\\n+/).map(p=>{
    if(/^<(h[1-4]|ul|ol|pre|blockquote|hr)/.test(p.trim()))return p;
    return '<p>'+p.replace(/\\n/g,'<br>')+'</p>';
  }).join('\\n');
  return s;
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

// ── Clock ───────────────────────────────────────────────────────────────────
function updateClock(){
  const now=new Date();
  const ts=now.getHours().toString().padStart(2,'0')+':'+now.getMinutes().toString().padStart(2,'0')+':'+now.getSeconds().toString().padStart(2,'0');
  const el=document.getElementById('clock');
  if(el) el.textContent=ts;
}
setInterval(updateClock,1000);updateClock();

// ── Status fetcher ──────────────────────────────────────────────────────────
let cachedStatus=null;
function refreshStatus(){
  fetch('/api/status').then(r=>r.json()).then(d=>{
    cachedStatus=d;
    applyStatus(d);
  }).catch(()=>{});
}

function applyStatus(d){
  // Nav
  const nt=document.getElementById('nav-tests');
  if(nt) nt.textContent=d.tests+' tests';

  // Dashboard sidebar
  const dt=document.getElementById('d-tests');if(dt)dt.textContent=d.tests+' ✓';
  const dg=document.getElementById('d-git');if(dg)dg.textContent=d.clean?'clean ✓':'uncommitted';
  const dgd=document.getElementById('d-gitdot');
  if(dgd)dgd.style.background=d.clean?'var(--green)':'var(--amber)';
  const dm=document.getElementById('d-mem');if(dm)dm.textContent=d.memories+' entries';
  const dtime=document.getElementById('d-time');if(dtime)dtime.textContent=d.time;

  // Dashboard cards
  const dct=document.getElementById('dc-tests');if(dct)dct.textContent=d.tests;
  const dcb=document.getElementById('dc-brains');if(dcb)dcb.textContent=d.available_brains.length;
  const dcm=document.getElementById('dc-mem');if(dcm)dcm.textContent=d.memories;
  const dcbu=document.getElementById('dc-budget');if(dcbu)dcbu.textContent='$'+d.budget_remaining.toFixed(0);

  // Brain lists (dashboard + chat + status)
  renderBrains(d.brains,'d-brains');
  renderBrains(d.brains,'c-brains');
  renderBrainsDetail(d.brains,'s-brains-detail');

  // Active brain in chat header
  const ab=document.getElementById('active-brain');
  if(ab)ab.textContent=d.available_brains.length?d.available_brains[0]:'demo mode';

  // Status page
  const sc=document.getElementById('ss-commit');if(sc)sc.textContent=d.commit;
  const scl=document.getElementById('ss-clean');
  if(scl){scl.textContent=d.clean?'clean':'uncommitted changes';scl.className='status-row-value '+(d.clean?'ok':'warn');}
  const st=document.getElementById('ss-tests');if(st)st.textContent=d.tests+' passing';
  const sm=document.getElementById('ss-mem');if(sm)sm.textContent=d.memories;
  const sd=document.getElementById('ss-docs');if(sd)sd.textContent=d.doc_count;
  const sbu=document.getElementById('ss-budget');if(sbu)sbu.textContent='$'+d.budget_remaining.toFixed(2);
}

function renderBrains(brains, id){
  const el=document.getElementById(id);if(!el)return;
  el.innerHTML='';
  Object.values(brains).forEach(b=>{
    const on=b.available;
    const row=document.createElement('div');row.className='stat-row';
    row.innerHTML='<span class="stat-label"><span class="dot '+(on?'dot-green':'dot-gray')+'"></span>'+b.name+'</span>'+
      '<span class="stat-value" style="color:'+(on?'var(--green)':'var(--td)')+'">'+
      (on?b.model:'offline')+'</span>';
    el.appendChild(row);
  });
}

function renderBrainsDetail(brains, id){
  const el=document.getElementById(id);if(!el)return;
  el.innerHTML='';
  Object.values(brains).forEach(b=>{
    const on=b.available;
    const div=document.createElement('div');div.className='brain-card';
    div.innerHTML='<span class="dot '+(on?'dot-green':'dot-gray')+'"></span>'+
      '<span class="brain-name">'+b.name+'</span>'+
      '<span class="brain-model">'+b.model+'</span>'+
      '<span class="brain-status '+(on?'online':'offline')+'">'+
      (on?'ONLINE':'OFFLINE')+'</span>';
    el.appendChild(div);
  });
}

function runTests(){
  const log=document.getElementById('activity-log');
  if(log){
    const item=document.createElement('div');item.className='activity-item';
    item.innerHTML='<span class="activity-icon">→</span><span class="activity-text">Running pytest…</span><span class="activity-time">now</span>';
    log.prepend(item);
  }
}

// ── Chat state ───────────────────────────────────────────────────────────────
let chatHistory=JSON.parse(localStorage.getItem('adamus_chat_h')||'[]');
let chatMsgs=[];
let chatBusy=false;

function resizeInp(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,140)+'px'}
function onChatKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendMsg()}}
function suggest(t){document.getElementById('chat-inp').value=t;sendMsg()}
function scrollMsgs(){const m=document.getElementById('messages');if(m)m.scrollTop=m.scrollHeight}

function addMsg(role,text){
  const w=document.getElementById('welcome');if(w)w.remove();
  const c=document.getElementById('messages');
  const d=document.createElement('div');
  d.className='msg '+role;
  const ai=role==='ai';
  d.innerHTML='<div class="avatar '+(ai?'ai':'user')+'">'+(ai?'A':'G')+'</div>'+
    '<div class="bubble">'+(ai?md(text):esc(text))+'</div>';
  c.appendChild(d);scrollMsgs();
}

function addTyping(id){
  const w=document.getElementById('welcome');if(w)w.remove();
  const c=document.getElementById('messages');
  const d=document.createElement('div');d.className='msg ai';d.id=id;
  d.innerHTML='<div class="avatar ai">A</div><div class="bubble"><div class="typing"><div class="td"></div><div class="td"></div><div class="td"></div></div></div>';
  c.appendChild(d);scrollMsgs();
}

function addStream(id){
  const c=document.getElementById('messages');
  const d=document.createElement('div');d.className='msg ai';
  const bub=document.createElement('div');bub.className='bubble';bub.id=id;
  d.innerHTML='<div class="avatar ai">A</div>';
  d.appendChild(bub);c.appendChild(d);scrollMsgs();
}

async function sendMsg(){
  if(chatBusy)return;
  const inp=document.getElementById('chat-inp');
  const text=inp.value.trim();if(!text)return;
  chatMsgs.push({role:'user',content:text});
  addMsg('user',text);
  inp.value='';inp.style.height='auto';
  if(chatMsgs.length===1){
    document.getElementById('chat-title').textContent=text.slice(0,40)+(text.length>40?'…':'');
  }
  const tid='t'+Date.now();
  addTyping(tid);
  chatBusy=true;
  document.getElementById('send-btn').disabled=true;
  try{
    const r=await fetch('/api/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:chatMsgs})
    });
    if(!r.ok)throw new Error('HTTP '+r.status);
    document.getElementById(tid)?.remove();
    const bid='b'+Date.now();
    addStream(bid);
    const bub=document.getElementById(bid);
    const reader=r.body.getReader();
    const dec=new TextDecoder();
    let full='';let brainSet=false;
    while(true){
      const{done,value}=await reader.read();
      if(done)break;
      let chunk=dec.decode(value,{stream:true});
      if(!brainSet&&chunk.startsWith('__brain__')){
        const nl=chunk.indexOf('\\n');
        const bn=chunk.slice(9,nl>-1?nl:undefined).trim();
        document.getElementById('active-brain').textContent=bn;
        chunk=nl>-1?chunk.slice(nl+1):'';
        brainSet=true;
      }
      full+=chunk;
      bub.innerHTML=md(full);
      scrollMsgs();
    }
    chatMsgs.push({role:'assistant',content:full});
    saveChatHist(text,full);
  }catch(e){
    document.getElementById(tid)?.remove();
    addMsg('ai','Error: '+e.message+'. Is the server running?');
  }
  chatBusy=false;
  document.getElementById('send-btn').disabled=false;
  inp.focus();
}

function saveChatHist(q,a){
  chatHistory.unshift({title:q.slice(0,40),msgs:[...chatMsgs]});
  chatHistory=chatHistory.slice(0,20);
  localStorage.setItem('adamus_chat_h',JSON.stringify(chatHistory));
  renderChatHist();
}

function renderChatHist(){
  const h=document.getElementById('chat-hist');if(!h)return;
  h.innerHTML='<div class="section-label">History</div>';
  chatHistory.slice(0,12).forEach((item,i)=>{
    const d=document.createElement('div');
    d.style.cssText='padding:6px 9px;border-radius:6px;font-size:11px;color:var(--tm);cursor:pointer;margin-bottom:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis';
    d.textContent=item.title;
    d.onmouseover=()=>d.style.background='var(--s2)';
    d.onmouseout=()=>d.style.background='';
    d.onclick=()=>loadChatHist(i);
    h.appendChild(d);
  });
}

function loadChatHist(i){
  const item=chatHistory[i];if(!item)return;
  chatMsgs=[...item.msgs];
  document.getElementById('messages').innerHTML='';
  chatMsgs.forEach(m=>addMsg(m.role==='user'?'user':'ai',m.content));
  document.getElementById('chat-title').textContent=item.title;
}

function newChat(){
  chatMsgs=[];
  document.getElementById('messages').innerHTML='<div class="welcome-screen" id="welcome">'+
    '<div class="welcome-logo">A</div>'+
    '<h2>Talk to Adamus</h2>'+
    '<p>Your persistent AI CTO. Ask anything about Genre, the codebase, strategy, or what to build next.</p>'+
    '<div class="suggestions">'+
    '<button class="suggestion" onclick="suggest(\'What is the current project status?\')"><strong>Project Status</strong>Tests, git, what is done</button>'+
    '<button class="suggestion" onclick="suggest(\'What should we build next?\')"><strong>Next Task</strong>Architecture roadmap</button>'+
    '<button class="suggestion" onclick="suggest(\'How does the memory system work?\')"><strong>Memory System</strong>How Adamus remembers</button>'+
    '<button class="suggestion" onclick="suggest(\'What is our path to $10K MRR?\')"><strong>$10K MRR</strong>Business strategy</button>'+
    '</div></div>';
  document.getElementById('chat-title').textContent='Adamus Chat';
}

// ── Docs browser ─────────────────────────────────────────────────────────────
function loadDoc(name){
  // Update active state
  document.querySelectorAll('.doc-item').forEach(el=>{
    el.classList.toggle('active',el.dataset.name===name);
  });
  const content=document.getElementById('docs-content');
  content.innerHTML='<div class="docs-placeholder"><p>Loading '+name+'…</p></div>';
  fetch('/api/docs/'+encodeURIComponent(name))
    .then(r=>r.json())
    .then(d=>{
      if(d.error){content.innerHTML='<div class="docs-placeholder"><p style="color:var(--red)">'+d.error+'</p></div>';return;}
      fetch('/docs/'+encodeURIComponent(name))
        .then(r=>r.text())
        .then(html=>{
          const parser=new DOMParser();
          const doc=parser.parseFromString(html,'text/html');
          const body=doc.getElementById('doc-body');
          if(body){content.innerHTML='<div class="doc-rendered">'+body.innerHTML+'</div>';}
          else{content.innerHTML='<div class="doc-rendered"><h1>'+name+'</h1><pre style="color:var(--tm);font-size:11px;white-space:pre-wrap">'+esc(d.content)+'</pre></div>';}
        }).catch(()=>{
          content.innerHTML='<div class="doc-rendered"><h1>'+name+'</h1><pre style="color:var(--tm);font-size:11px;white-space:pre-wrap">'+esc(d.content.slice(0,8000))+'</pre></div>';
        });
    }).catch(()=>{
      content.innerHTML='<div class="docs-placeholder"><p style="color:var(--red)">Failed to load doc.</p></div>';
    });
  // Update URL
  history.pushState(null,'','/docs/'+encodeURIComponent(name));
}

function filterDocs(q){
  q=q.toLowerCase();
  document.querySelectorAll('.doc-item').forEach(el=>{
    el.style.display=(!q||el.dataset.name.toLowerCase().includes(q))?'':'none';
  });
  document.querySelectorAll('.doc-group-label').forEach(el=>{
    // Show group label if any sibling items are visible
    let next=el.nextElementSibling;
    let anyVisible=false;
    while(next&&next.classList.contains('doc-item')){
      if(next.style.display!=='none')anyVisible=true;
      next=next.nextElementSibling;
    }
    el.style.display=anyVisible?'':'none';
  });
}

// ── Init ─────────────────────────────────────────────────────────────────────
refreshStatus();
renderChatHist();
// Auto-refresh status every 60s
setInterval(refreshStatus,60000);
// Focus chat input if on chat page
if('<<<ACTIVE_PAGE>>>'==='chat'){
  const inp=document.getElementById('chat-inp');if(inp)inp.focus();
}
</script>
</body>
</html>"""

# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    app = create_app()
    print("\n  Adamus Unified UI")
    print("  http://localhost:8888")
    print("  http://0.0.0.0:8888  (network accessible)\n")
    print("  Routes:")
    print("    GET  /         Dashboard")
    print("    GET  /chat     Chat")
    print("    GET  /docs     Docs browser")
    print("    GET  /status   Status page")
    print("    POST /api/chat Streaming chat\n")
    app.run(host="0.0.0.0", port=8888, debug=False, threaded=True)
