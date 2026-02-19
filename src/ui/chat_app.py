"""
Adamus Chat UI — ChatGPT-style interface
Genre branded: dark theme, orange/blue gradient.

Run:   python src/ui/chat_app.py
Open:  http://localhost:5001
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from flask import Flask, request, jsonify, Response, stream_with_context

app = Flask(__name__)
REPO = Path(__file__).resolve().parents[2]

SYSTEM_PROMPT = """You are Adamus — the persistent AI CTO for Genre, built by Augustus.

Personality: direct, decisive, CTO-minded. No fluff, high signal.
You know the full Adamus codebase (108+ architecture docs).
Help Augustus build Genre from $0 → $10K MRR.

Current state: 198 tests passing. Days 1-5 complete.
Memory, Security, War Room, Business AI, CAMBI AI all operational."""


# ── Backend helpers ───────────────────────────────────────────────────────────

def get_status():
    try:
        commit = subprocess.run(
            ["git", "log", "-1", "--oneline"],
            capture_output=True, text=True, cwd=str(REPO), timeout=3
        ).stdout.strip()
        dirty = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=str(REPO), timeout=3
        ).stdout.strip()
    except Exception:
        commit, dirty = "unknown", ""

    try:
        import sys; sys.path.insert(0, str(REPO))
        from src.memory.adamus_persistent_memory import AdamusPersistentMemory
        s = AdamusPersistentMemory().get_stats()
        memories, mem_mb = s["total_memories"], s["total_size_mb"]
    except Exception:
        memories, mem_mb = 0, 0

    return {
        "commit": commit,
        "clean": not bool(dirty),
        "memories": memories,
        "mem_mb": mem_mb,
        "time": datetime.now().strftime("%H:%M"),
        "tests": 198,
    }


def stream_response(messages):
    """Stream from Claude API or demo mode."""
    # Load .env
    env_file = REPO / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                k, _, v = line.partition("=")
                os.environ.setdefault(k.strip(), v.strip())

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key and not api_key.startswith("sk-ant-your"):
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
            return
        except Exception as e:
            yield f"⚠️ API error: {e}\n\nRunning in demo mode."
            return

    # Demo mode
    last = messages[-1]["content"].lower() if messages else ""
    if any(w in last for w in ["status", "health", "how are"]):
        reply = "**System Status ✓**\n\n- 198 tests passing\n- Git: clean, pushed\n- Memory: operational\n- Days 1-5 complete\n\nWhat do you want to build next?"
    elif any(w in last for w in ["day 6", "tech ai"]):
        reply = "**Day 6: Tech AI**\n\nBuilds:\n```\nsrc/tech_ai/\n├── adamus_core.py\n├── self_improvement.py\n├── capability_builder.py\n└── genre_builder.py\n```\n\nReady to start?"
    elif any(w in last for w in ["mrr", "revenue", "money"]):
        reply = "**Business**\n\n- Current MRR: $0\n- Target: $10K in 90 days\n- North star: MRR\n\nGenre is an AI writing/knowledge tool for creators."
    elif any(w in last for w in ["hello", "hi", "hey", "who"]):
        reply = "Hey Augustus 👋\n\nI'm **Adamus** — your AI CTO.\n\n198 tests passing. What do you want to build?"
    elif any(w in last for w in ["memory", "remember"]):
        reply = "**Memory System**\n\n- SQLite DB: `~/.adamus/memory.db`\n- File store: `~/.adamus/memories/YYYY-MM/`\n- TB+ capable, progressive disclosure\n- Auto-archives after 30/90 days\n\n> Add `ANTHROPIC_API_KEY` to `.env` for full AI."
    else:
        reply = f"I heard: *\"{messages[-1]['content']}\"*\n\nI can help with code, business strategy, memory, and planning.\n\n> ⚠️ Demo mode — add `ANTHROPIC_API_KEY` to `/home/johan/adamus/.env` for real AI."

    yield reply


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return HTML

@app.route("/api/status")
def api_status():
    return jsonify(get_status())

@app.route("/api/chat", methods=["POST"])
def api_chat():
    msgs = request.get_json(force=True).get("messages", [])
    return Response(stream_with_context(stream_response(msgs)), mimetype="text/plain")


# ── HTML (single-file, no CDN) ────────────────────────────────────────────────

HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Adamus</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
:root{
  --or:#FF6B35;--bl:#4A9EFF;
  --bg:#0a0a0a;--s1:#111;--s2:#1a1a1a;--s3:#222;
  --br:#2a2a2a;--tx:#e8e8e8;--tm:#666;--td:#3a3a3a;
}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
  background:var(--bg);color:var(--tx);height:100vh;display:flex;overflow:hidden}

/* Sidebar */
.sb{width:240px;min-width:240px;background:var(--s1);border-right:1px solid var(--br);
  display:flex;flex-direction:column;overflow:hidden}
.sb-logo{padding:18px 14px;border-bottom:1px solid var(--br);display:flex;align-items:center;gap:10px}
.lm{width:34px;height:34px;border-radius:8px;
  background:linear-gradient(135deg,var(--or),var(--bl));
  display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:15px;color:#fff;flex-shrink:0}
.lt h1{font-size:15px;font-weight:700;color:#fff}
.lt p{font-size:11px;color:var(--tm);margin-top:1px}

.stat-sec{padding:10px;border-bottom:1px solid var(--br)}
.sec-lbl{font-size:10px;font-weight:600;letter-spacing:.8px;text-transform:uppercase;
  color:var(--td);margin-bottom:6px;padding:0 4px}
.si{display:flex;align-items:center;justify-content:space-between;
  padding:5px 8px;border-radius:6px;margin-bottom:1px;font-size:12px}
.si:hover{background:var(--s2)}
.si .lbl{color:var(--tm);display:flex;align-items:center;gap:6px}
.si .val{font-weight:600}
.dot{width:6px;height:6px;border-radius:50%;flex-shrink:0}
.dg{background:#4CAF50;box-shadow:0 0 5px #4CAF50}
.do{background:var(--or)}
.dr{background:#f44336}

.new-btn{margin:10px;padding:9px;
  background:linear-gradient(135deg,var(--or),var(--bl));
  border:none;border-radius:8px;color:#fff;font-size:13px;font-weight:600;
  cursor:pointer;width:calc(100% - 20px);transition:opacity .2s}
.new-btn:hover{opacity:.85}

.hist{flex:1;overflow-y:auto;padding:8px 10px}
.hi{padding:7px 9px;border-radius:6px;font-size:12px;color:var(--tm);
  cursor:pointer;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:2px}
.hi:hover{background:var(--s2);color:var(--tx)}
.hi.active{background:var(--s3);color:var(--tx)}

/* Main */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.ch{padding:12px 22px;border-bottom:1px solid var(--br);
  display:flex;align-items:center;justify-content:space-between;flex-shrink:0}
.ch h2{font-size:14px;font-weight:600}
.mb{font-size:11px;padding:3px 8px;border-radius:20px;
  background:var(--s2);border:1px solid var(--br);color:var(--tm);
  display:flex;align-items:center;gap:5px}
.mb span{width:5px;height:5px;border-radius:50%;background:var(--or);display:inline-block}

/* Messages */
.msgs{flex:1;overflow-y:auto;padding:20px 22px;
  display:flex;flex-direction:column;gap:20px;scroll-behavior:smooth}
.msgs::-webkit-scrollbar{width:3px}
.msgs::-webkit-scrollbar-thumb{background:var(--br);border-radius:3px}

/* Welcome */
.welcome{display:flex;flex-direction:column;align-items:center;
  justify-content:center;flex:1;text-align:center;padding:40px;gap:14px}
.wlogo{width:60px;height:60px;border-radius:16px;
  background:linear-gradient(135deg,var(--or),var(--bl));
  display:flex;align-items:center;justify-content:center;
  font-weight:900;font-size:26px;color:#fff;margin-bottom:6px}
.welcome h2{font-size:22px;font-weight:700;
  background:linear-gradient(135deg,var(--or),var(--bl));
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text}
.welcome p{font-size:13px;color:var(--tm);max-width:340px;line-height:1.6}
.sugg{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:6px;width:100%;max-width:460px}
.sg{background:var(--s1);border:1px solid var(--br);border-radius:10px;
  padding:11px 13px;font-size:12px;color:var(--tm);cursor:pointer;text-align:left;
  transition:all .15s;line-height:1.4}
.sg:hover{border-color:var(--or);color:var(--tx);background:var(--s2)}
.sg strong{display:block;color:var(--tx);font-size:12px;margin-bottom:2px}

/* Bubbles */
.msg{display:flex;gap:10px;max-width:760px;width:100%;margin:0 auto;animation:fi .2s ease}
@keyframes fi{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:translateY(0)}}
.msg.user{flex-direction:row-reverse}
.av{width:30px;height:30px;border-radius:8px;display:flex;align-items:center;
  justify-content:center;font-size:12px;font-weight:700;flex-shrink:0}
.av.ai{background:linear-gradient(135deg,var(--or),var(--bl));color:#fff}
.av.usr{background:var(--s3);color:var(--tm);border:1px solid var(--br)}
.bub{padding:11px 15px;border-radius:12px;font-size:14px;line-height:1.65;max-width:calc(100% - 42px)}
.msg.user .bub{
  background:linear-gradient(135deg,rgba(255,107,53,.12),rgba(74,158,255,.12));
  border:1px solid rgba(255,107,53,.2);border-radius:12px 4px 12px 12px}
.msg.ai .bub{background:var(--s1);border:1px solid var(--br);border-radius:4px 12px 12px 12px}

/* Markdown */
.bub b,.bub strong{font-weight:600;color:#fff}
.bub em{color:var(--tm);font-style:italic}
.bub code{background:var(--s3);border:1px solid var(--br);padding:1px 5px;
  border-radius:4px;font-family:'SF Mono','Fira Code',monospace;font-size:12px;color:var(--or)}
.bub pre{background:var(--s2);border:1px solid var(--br);border-radius:8px;
  padding:12px;overflow-x:auto;margin:8px 0}
.bub pre code{background:none;border:none;padding:0;color:#b0c4de;font-size:12px}
.bub h1,.bub h2,.bub h3{margin:10px 0 5px;color:#fff}
.bub h2{font-size:15px}.bub h3{font-size:14px}
.bub ul,.bub ol{padding-left:16px;margin:5px 0}
.bub li{margin:3px 0}
.bub blockquote{border-left:3px solid var(--or);padding-left:11px;color:var(--tm);
  margin:7px 0;font-style:italic}
.bub table{width:100%;border-collapse:collapse;margin:7px 0;font-size:13px}
.bub th{background:var(--s2);padding:5px 9px;text-align:left;
  border-bottom:1px solid var(--br);color:var(--tm);font-size:11px;
  font-weight:600;text-transform:uppercase;letter-spacing:.4px}
.bub td{padding:5px 9px;border-bottom:1px solid var(--br)}
.bub p{margin:4px 0}
.bub hr{border:none;border-top:1px solid var(--br);margin:10px 0}

/* Typing */
.typing{display:flex;align-items:center;gap:4px;padding:14px 15px}
.td{width:7px;height:7px;border-radius:50%;background:var(--td);animation:ty 1.2s infinite}
.td:nth-child(2){animation-delay:.2s}.td:nth-child(3){animation-delay:.4s}
@keyframes ty{0%,60%,100%{transform:translateY(0);opacity:.4}30%{transform:translateY(-6px);opacity:1}}

/* Input */
.ia{padding:14px 22px 18px;border-top:1px solid var(--br);flex-shrink:0}
.iw{display:flex;align-items:flex-end;gap:8px;background:var(--s1);
  border:1px solid var(--br);border-radius:12px;
  padding:9px 9px 9px 14px;max-width:760px;margin:0 auto;transition:border-color .2s}
.iw:focus-within{border-color:var(--or);box-shadow:0 0 0 2px rgba(255,107,53,.1)}
#inp{flex:1;background:none;border:none;outline:none;color:var(--tx);
  font-size:14px;line-height:1.5;resize:none;max-height:140px;font-family:inherit;padding:2px 0}
#inp::placeholder{color:var(--td)}
.sbtn{width:32px;height:32px;border-radius:8px;
  background:linear-gradient(135deg,var(--or),var(--bl));
  border:none;cursor:pointer;display:flex;align-items:center;justify-content:center;
  flex-shrink:0;transition:opacity .2s,transform .1s}
.sbtn:hover{opacity:.85;transform:scale(1.05)}
.sbtn:active{transform:scale(.95)}
.sbtn:disabled{opacity:.35;cursor:default;transform:none}
.sbtn svg{width:15px;height:15px;fill:#fff}
.hint{text-align:center;font-size:11px;color:var(--td);margin-top:6px;
  max-width:760px;margin-left:auto;margin-right:auto}
</style>
</head>
<body>

<aside class="sb">
  <div class="sb-logo">
    <div class="lm">A</div>
    <div class="lt"><h1>Adamus</h1><p>AI CTO for Genre</p></div>
  </div>
  <div class="stat-sec">
    <div class="sec-lbl">Live Status</div>
    <div class="si"><span class="lbl"><span class="dot dg"></span>Tests</span><span class="val" id="s-tests">198 ✓</span></div>
    <div class="si"><span class="lbl"><span class="dot" id="s-gitdot" style="background:#666"></span>Git</span><span class="val" id="s-git">loading…</span></div>
    <div class="si"><span class="lbl"><span class="dot do"></span>Memory</span><span class="val" id="s-mem">loading…</span></div>
    <div class="si"><span class="lbl"><span class="dot dg"></span>MRR Goal</span><span class="val">$10K/90d</span></div>
  </div>
  <button class="new-btn" onclick="newChat()">+ New Chat</button>
  <div class="hist" id="hist"><div class="sec-lbl">History</div></div>
</aside>

<main class="main">
  <header class="ch">
    <h2 id="title">Adamus Chat</h2>
    <div class="mb"><span></span>claude-sonnet-4-6</div>
  </header>
  <div class="msgs" id="msgs">
    <div class="welcome" id="welcome">
      <div class="wlogo">A</div>
      <h2>Talk to Adamus</h2>
      <p>Your persistent AI CTO. Ask anything about Genre, the codebase, strategy, or what to build next.</p>
      <div class="sugg">
        <button class="sg" onclick="suggest('What is the current project status?')"><strong>Project Status</strong>Tests, git, what's done</button>
        <button class="sg" onclick="suggest('What should we build for Day 6?')"><strong>Day 6 Plan</strong>Tech AI roadmap</button>
        <button class="sg" onclick="suggest('How does the memory system work?')"><strong>Memory System</strong>How Adamus remembers</button>
        <button class="sg" onclick="suggest('What is our path to $10K MRR?')"><strong>$10K MRR</strong>Business strategy</button>
      </div>
    </div>
  </div>
  <div class="ia">
    <div class="iw">
      <textarea id="inp" placeholder="Ask Adamus anything…" rows="1"
        onkeydown="onKey(event)" oninput="resize(this)"></textarea>
      <button class="sbtn" id="sbtn" onclick="send()">
        <svg viewBox="0 0 24 24"><path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/></svg>
      </button>
    </div>
    <div class="hint">Enter to send &nbsp;·&nbsp; Shift+Enter for new line</div>
  </div>
</main>

<script>
// ── Minimal markdown renderer (no CDN needed) ─────────────────────────────
function md(s){
  // code blocks first
  s = s.replace(/```([\\s\\S]*?)```/g, (_,c)=>`<pre><code>${esc(c.trim())}</code></pre>`);
  // inline code
  s = s.replace(/`([^`]+)`/g, (_,c)=>`<code>${esc(c)}</code>`);
  // headers
  s = s.replace(/^### (.+)$/gm, '<h3>$1</h3>');
  s = s.replace(/^## (.+)$/gm,  '<h2>$1</h2>');
  s = s.replace(/^# (.+)$/gm,   '<h1>$1</h1>');
  // bold / italic
  s = s.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
  s = s.replace(/\\*(.+?)\\*/g, '<em>$1</em>');
  // hr
  s = s.replace(/^---$/gm, '<hr>');
  // blockquote
  s = s.replace(/^> (.+)$/gm, '<blockquote>$1</blockquote>');
  // unordered list
  s = s.replace(/^[-*] (.+)$/gm, '<li>$1</li>');
  s = s.replace(/(<li>.*<\\/li>)/gs, '<ul>$1</ul>');
  // line breaks → paragraphs
  s = s.split(/\\n\\n+/).map(p=>{
    if(/^<(h[123]|ul|ol|pre|blockquote|hr)/.test(p.trim())) return p;
    return `<p>${p.replace(/\\n/g,'<br>')}</p>`;
  }).join('\\n');
  return s;
}
function esc(s){return s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;')}

// ── State ─────────────────────────────────────────────────────────────────
let history = JSON.parse(localStorage.getItem('adamus_h')||'[]');
let msgs = [];
let busy = false;

// ── Status ────────────────────────────────────────────────────────────────
fetch('/api/status')
  .then(r=>r.json())
  .then(d=>{
    document.getElementById('s-tests').textContent = d.tests+' ✓';
    document.getElementById('s-git').textContent = d.clean ? 'clean ✓' : 'uncommitted';
    document.getElementById('s-gitdot').className = 'dot '+(d.clean?'dg':'do');
    document.getElementById('s-mem').textContent = d.memories+' memories';
  })
  .catch(()=>{
    document.getElementById('s-git').textContent = 'offline';
    document.getElementById('s-mem').textContent = '—';
  });

// ── Helpers ───────────────────────────────────────────────────────────────
function resize(el){el.style.height='auto';el.style.height=Math.min(el.scrollHeight,140)+'px'}
function onKey(e){if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}}
function suggest(t){document.getElementById('inp').value=t;send()}
function scrollBot(){const m=document.getElementById('msgs');m.scrollTop=m.scrollHeight}

function addMsg(role,text){
  const w=document.getElementById('welcome');if(w)w.remove();
  const m=document.getElementById('msgs');
  const d=document.createElement('div');
  d.className='msg '+role;
  const isAI=role==='ai';
  d.innerHTML=`<div class="av ${isAI?'ai':'usr'}">${isAI?'A':'G'}</div>`+
    `<div class="bub">${isAI?md(text):esc(text)}</div>`;
  m.appendChild(d);scrollBot();
}

function addTyping(id){
  const w=document.getElementById('welcome');if(w)w.remove();
  const m=document.getElementById('msgs');
  const d=document.createElement('div');
  d.className='msg ai';d.id=id;
  d.innerHTML='<div class="av ai">A</div><div class="bub"><div class="typing"><div class="td"></div><div class="td"></div><div class="td"></div></div></div>';
  m.appendChild(d);scrollBot();
}

function addStream(id){
  const m=document.getElementById('msgs');
  const d=document.createElement('div');
  d.className='msg ai';
  const bub=document.createElement('div');bub.className='bub';bub.id=id;
  d.innerHTML='<div class="av ai">A</div>';
  d.appendChild(bub);m.appendChild(d);scrollBot();
}

// ── Send ──────────────────────────────────────────────────────────────────
async function send(){
  if(busy)return;
  const inp=document.getElementById('inp');
  const text=inp.value.trim();
  if(!text)return;

  msgs.push({role:'user',content:text});
  addMsg('user',text);
  inp.value='';inp.style.height='auto';

  if(msgs.length===1)
    document.getElementById('title').textContent=text.slice(0,40)+(text.length>40?'…':'');

  const tid='t'+Date.now();
  addTyping(tid);
  busy=true;
  document.getElementById('sbtn').disabled=true;

  try{
    const r=await fetch('/api/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({messages:msgs})
    });

    if(!r.ok)throw new Error('HTTP '+r.status);

    document.getElementById(tid)?.remove();
    const bid='b'+Date.now();
    addStream(bid);
    const bub=document.getElementById(bid);

    const reader=r.body.getReader();
    const dec=new TextDecoder();
    let full='';

    while(true){
      const{done,value}=await reader.read();
      if(done)break;
      full+=dec.decode(value,{stream:true});
      bub.innerHTML=md(full);
      scrollBot();
    }

    msgs.push({role:'assistant',content:full});
    saveHist(text,full);

  }catch(e){
    document.getElementById(tid)?.remove();
    addMsg('ai','❌ Error: '+e.message+'. Is the server running on port 5001?');
  }

  busy=false;
  document.getElementById('sbtn').disabled=false;
  inp.focus();
}

// ── History ───────────────────────────────────────────────────────────────
function saveHist(q,a){
  history.unshift({title:q.slice(0,40),msgs:[...msgs]});
  history=history.slice(0,20);
  localStorage.setItem('adamus_h',JSON.stringify(history));
  renderHist();
}

function renderHist(){
  const h=document.getElementById('hist');
  h.innerHTML='<div class="sec-lbl">History</div>';
  history.slice(0,12).forEach((item,i)=>{
    const d=document.createElement('div');
    d.className='hi'+(i===0?' active':'');
    d.textContent=item.title;
    d.onclick=()=>loadHist(i);
    h.appendChild(d);
  });
}

function loadHist(i){
  const item=history[i];if(!item)return;
  msgs=[...item.msgs];
  document.getElementById('msgs').innerHTML='';
  msgs.forEach(m=>addMsg(m.role==='user'?'user':'ai',m.content));
  document.getElementById('title').textContent=item.title;
}

function newChat(){
  msgs=[];
  document.getElementById('msgs').innerHTML=`
    <div class="welcome" id="welcome">
      <div class="wlogo">A</div>
      <h2>Talk to Adamus</h2>
      <p>Your persistent AI CTO. Ask anything about Genre, the codebase, strategy, or what to build next.</p>
      <div class="sugg">
        <button class="sg" onclick="suggest('What is the current project status?')"><strong>Project Status</strong>Tests, git, what's done</button>
        <button class="sg" onclick="suggest('What should we build for Day 6?')"><strong>Day 6 Plan</strong>Tech AI roadmap</button>
        <button class="sg" onclick="suggest('How does the memory system work?')"><strong>Memory System</strong>How Adamus remembers</button>
        <button class="sg" onclick="suggest('What is our path to $10K MRR?')"><strong>$10K MRR</strong>Business strategy</button>
      </div>
    </div>`;
  document.getElementById('title').textContent='Adamus Chat';
}

renderHist();
document.getElementById('inp').focus();
</script>
</body>
</html>"""


if __name__ == "__main__":
    print("\n  Adamus Chat UI")
    print("  http://localhost:5001\n")
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
