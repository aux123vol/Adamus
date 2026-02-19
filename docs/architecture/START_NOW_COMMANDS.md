# START NOW - Exact Commands to Build Adamus

**Status**: All questions answered. Time to build.

**Timeline**: Start tonight, working Adamus by next Sunday

---

## Your Final Configuration

### ✅ Model Strategy: Hybrid
- **Claude API**: Genre features (fast to PMF)
- **Ollama**: Self-improvement (free, runs while you sleep)
- **Migrate**: Full Ollama after $5K MRR

### ✅ Autonomous Mode: Enabled
- Reads all 67 architecture docs
- Implements during downtime
- You wake up to new capabilities
- Focus 100% on Genre

### ✅ Security: All 8 Systems
- Protect both Claude and Ollama
- Telemetry-free
- Mobile access via Tailscale
- $12/month total infrastructure

---

## STEP 1: Right Now (5 minutes)

### Download Architecture Docs

1. **Download** `adamus_architecture_v1.tar.gz` (from this conversation ↑)

2. **Extract**:
```bash
tar -xzf adamus_architecture_v1.tar.gz
# Creates adamus_systems/ folder with all 67 docs
```

---

## STEP 2: Setup Project (10 minutes)

```bash
# Create main directory
mkdir ~/adamus
cd ~/adamus

# Copy architecture docs
cp -r /path/to/adamus_systems/ docs/architecture/

# Create structure
mkdir -p src/{coordinator,war_room,business_ai,cambi_ai,tech_ai}
mkdir -p config logs tests data

# Initialize git
git init
cat > .gitignore << 'EOF'
logs/
data/
.env
node_modules/
__pycache__/
*.pyc
.DS_Store
EOF

git add .
git commit -m "Initial Adamus structure"

# Verify docs are there
ls docs/architecture/
# Should see: adamus_systems folder with all docs
```

---

## STEP 3: Install Tools (15 minutes)

### Install Claude Code

```bash
# Install via npm
npm install -g @anthropic/claude-code

# Verify
claude --version
# Should show version number
```

### Install Ollama (For Free Self-Improvement)

```bash
# Mac/Linux
curl -fsSL https://ollama.com/install.sh | sh

# Or download from: https://ollama.com/download

# Pull a coding model
ollama pull codellama
ollama pull deepseek-coder

# Verify
ollama list
# Should show: codellama, deepseek-coder
```

### Install Python Dependencies

```bash
cd ~/adamus

# Create requirements.txt
cat > requirements.txt << 'EOF'
anthropic==0.18.1
flask==3.0.0
requests==2.31.0
beautifulsoup4==4.12.2
feedparser==6.0.10
python-dotenv==1.0.0
redis==5.0.1
psycopg2-binary==2.9.9
pgvector==0.2.4
openai==1.12.0
litellm==1.30.0
EOF

# Install
pip3 install -r requirements.txt

# Verify
python3 -c "import anthropic; print('✅ Anthropic SDK installed')"
```

---

## STEP 4: Configure API Keys (5 minutes)

```bash
cd ~/adamus

# Create .env file
cat > .env << 'EOF'
# Anthropic API (for Claude)
ANTHROPIC_API_KEY=your_api_key_here

# Ollama (runs locally, no key needed)
OLLAMA_HOST=http://localhost:11434

# Budget limits
MAX_MONTHLY_SPEND=200
ALERT_AT_SPEND=150

# Search (will setup later)
SEARXNG_URL=http://localhost:8080
EOF

# Edit with your actual API key
nano .env
# Replace your_api_key_here with real key

# Verify
cat .env | grep ANTHROPIC_API_KEY
# Should show your key
```

---

## STEP 5: Create Context for Claude Code (5 minutes)

```bash
cd ~/adamus
mkdir -p .claude

# Create context file
cat > .claude/context.md << 'EOF'
# Adamus Build Context

## Mission
Build Adamus - an AI CTO system that builds Genre 10x faster.

## Architecture Location
All architecture docs: ~/adamus/docs/architecture/adamus_systems/

## Key Documents to Read
1. NETWORKED_AI_TRINITY.md - Core architecture
2. SELF_IMPROVING_ADAMUS.md - Meta-layer design
3. HYBRID_STRATEGY_FINAL.md - Model strategy (Claude + Ollama)
4. WEEK_0_BUILD_PLAN.md - Week-by-week implementation

## Model Strategy: Hybrid
- Claude API: Genre features (speed critical)
- Ollama: Self-improvement (free, background)
- Budget: $200/month max
- Auto-switch if over budget

## Autonomous Mode: ENABLED
During downtime:
1. Read all architecture docs
2. Extract requirements (156 items)
3. Implement missing capabilities
4. Use Ollama (free)
5. Test and deploy
6. Report to War Room

## Tech Stack
- Python 3.11+ (main language)
- Flask (War Room web UI)
- Anthropic SDK (Claude API)
- Ollama (local models)
- PostgreSQL + pgvector (coming later)
- Redis (coming later)

## Build Order (Week 0)
Day 1: AI Coordinator (orchestrates 3 AIs)
Day 2: War Room (monitoring dashboard)
Day 3: Business AI v0.1 (finance + competitors)
Day 4: SearxNG (private search)
Day 5: CAMBI AI v0.1 (community + content)
Day 6: Adamus Core v0.1 (self-improvement)
Day 7: Integration testing

## Constraints
- Bootstrap budget: $12/month infrastructure
- Solo founder: Augustus
- Timeline: Genre MVP in 90 days
- Privacy: Telemetry-free, self-hosted

## Start Building
Read WEEK_0_BUILD_PLAN.md and begin with Day 1: AI Coordinator.
EOF
```

---

## STEP 6: Start Building (RIGHT NOW)

### Launch Claude Code

```bash
cd ~/adamus
claude
```

### First Prompt to Claude Code

Copy and paste this EXACTLY:

```
I'm building Adamus, an AI CTO system that will help me build Genre (my startup) 10x faster.

CONTEXT:
- All architecture docs are in: ~/adamus/docs/architecture/adamus_systems/
- 67 documents with complete specifications
- Hybrid model strategy: Claude for Genre, Ollama for self-improvement
- Autonomous mode: Read docs and implement during downtime

FIRST TASK: Build the AI Coordinator

Read these docs:
1. ~/adamus/docs/architecture/adamus_systems/NETWORKED_AI_TRINITY.md
2. ~/adamus/docs/architecture/adamus_systems/WEEK_0_BUILD_PLAN.md
3. ~/adamus/docs/architecture/adamus_systems/HYBRID_STRATEGY_FINAL.md

Build the AI Coordinator in Python that:

Requirements:
1. Orchestrates 3 AIs (Business, CAMBI, Tech/Adamus)
2. Routes tasks between them intelligently
3. Daily coordination cycle
4. Weekly A/B testing cycle
5. Hybrid model routing (Claude + Ollama)
6. Budget tracking ($200/month max)

Create these files:
- src/coordinator/ai_coordinator.py (main class)
- src/coordinator/task_router.py (smart routing)
- src/coordinator/model_router.py (Claude vs Ollama)
- config/coordinator.yaml (configuration)
- tests/test_coordinator.py (unit tests)

Follow the specs in NETWORKED_AI_TRINITY.md exactly.

Start with minimal viable - prove the pattern works.

Let's build.
```

---

## STEP 7: While Claude Code Builds (Setup Ollama)

In a separate terminal:

```bash
# Start Ollama server
ollama serve

# In another terminal, test it
ollama run codellama "Write a Python function to add two numbers"

# Should see: Code generated
# Press Ctrl+D to exit

# Leave ollama serve running
```

---

## STEP 8: Test First Component

After Claude Code finishes building AI Coordinator:

```bash
cd ~/adamus

# Run the coordinator
python3 src/coordinator/ai_coordinator.py

# Expected output:
# ✅ AI Coordinator initialized
# ✅ Hybrid model routing configured
# ✅ Claude API: Connected
# ✅ Ollama: Connected
# ✅ Budget: $0/$200 spent
# ✅ 3 AI agents registered
# ✅ Daily cycle started
```

---

## STEP 9: Enable Autonomous Mode

Add this to your coordinator after it works:

```bash
# Tell Claude Code:
```

```
Great! AI Coordinator works.

Now add autonomous self-improvement mode:

Read ~/adamus/docs/architecture/adamus_systems/SELF_IMPROVING_ADAMUS.md

Add these capabilities:

1. Doc Reader:
   - Read all .md files in ~/adamus/docs/architecture/
   - Extract requirements, TODOs, implementation specs
   - Create backlog of 156 items to build

2. Autonomous Builder:
   - When no Genre tasks: Read backlog
   - Implement highest priority capability
   - Use Ollama (free) for self-improvement
   - Test and deploy
   - Log progress

3. Smart Scheduling:
   - If Augustus requests Genre task: Use Claude, priority 1
   - If idle: Self-improve using Ollama
   - Never stop building

Create:
- src/tech_ai/doc_reader.py (reads architecture)
- src/tech_ai/autonomous_builder.py (builds from backlog)
- src/tech_ai/improvement_backlog.py (prioritized queue)

This way Adamus builds itself while I sleep.
```

---

## STEP 10: First Night (Let It Run)

```bash
# Before bed:
cd ~/adamus

# Start Adamus in tmux (persistent)
tmux new -s adamus

# Inside tmux:
python3 src/coordinator/ai_coordinator.py

# Detach tmux (keeps running)
# Press: Ctrl+B then D

# Adamus now runs overnight:
# - No Genre tasks = enters autonomous mode
# - Reads all 67 architecture docs
# - Starts implementing capabilities
# - Uses Ollama (free, no API costs)

# Next morning:
tmux attach -s adamus

# Check what it built:
tail -f logs/adamus.log
# Should see:
# ✅ Read 67 architecture docs
# ✅ Created backlog: 156 requirements
# ✅ Implemented Data Governance v0.1
# ✅ Implemented Credential Vault v0.1
# ✅ Implemented Input Filter v0.1
# Progress: 3/156 (1.9%)
```

---

## Complete Week 0 Schedule

### Sunday (Today)
- ✅ Steps 1-10 above (2 hours)
- ✅ Let Adamus run overnight

### Monday
- Morning: Check progress, review logs
- Afternoon: Build War Room with Claude Code (3 hours)
- Evening: Let Adamus self-improve overnight

### Tuesday
- Morning: Check War Room, verify working
- Afternoon: Build Business AI v0.1 (3 hours)
- Evening: Adamus continues self-improving

### Wednesday
- Morning: Review progress
- Afternoon: Setup SearxNG search (2 hours)
- Evening: Adamus self-improves

### Thursday
- Morning: Configure search for Business AI
- Afternoon: Build CAMBI AI v0.1 (3 hours)
- Evening: Adamus self-improves

### Friday
- Morning: Test all 3 AIs
- Afternoon: Build Adamus Core v0.1 (4 hours)
- Evening: Adamus self-improves

### Saturday
- Morning: Integration testing
- Afternoon: Setup Tailscale mobile access
- Evening: Full system test

### Sunday (Next Week)
- Morning: Verify everything works
- Afternoon: Feed Genre MVP docs to Adamus
- Result: **Adamus ready to build Genre**

---

## Success Criteria (End of Week 0)

```yaml
must_be_working:
  - ai_coordinator: "Orchestrating 3 AIs"
  - hybrid_models: "Claude + Ollama routing"
  - autonomous_mode: "Self-implementing during downtime"
  - war_room: "Dashboard shows all metrics"
  - business_ai: "Monitoring competitors"
  - cambi_ai: "Detecting trends"
  - adamus_core: "Self-improving meta-layer"
  - mobile_access: "War Room on phone"
  
capabilities_self_implemented: "20-30 from 156 backlog"
cost_so_far: "$0-50 (mostly free with Ollama)"
augustus_time: "~20 hours building, Adamus built rest"
```

---

## Week 1 Plan (After Adamus Works)

### Feed Genre Mission

```bash
# Monday morning:
cd ~/adamus
claude

# Tell Adamus:
```

```
Read my Genre MVP specification:
- Genre-AI-MVP-Spec-v2-Canonical.docx
- MVP_and_IPO_Roadmap.docx

Understand the mission:
- AI writing platform for storytellers
- Lore (IP tracking) + Saga (payments) + World Bible (memory)
- 90-day MVP timeline
- Current: 147 users, $1K MRR
- Goal: PMF at $10K MRR

Build Genre authentication system:
- User signup/login
- Email verification
- Password reset
- OAuth (Google, Twitter)
- JWT tokens

Use Claude API (speed matters for Genre).
Create:
- Backend: Flask or FastAPI
- Database: PostgreSQL
- Tests: pytest
- Deploy: Vercel or Railway

Let's build Genre.
```

---

## The Bottom Line

### What You're Building

```yaml
week_0:
  - adamus_v0_1: "AI CTO that builds Genre"
  - hybrid_models: "Claude + Ollama"
  - autonomous: "Self-improves during downtime"
  - cost: "$12/month infrastructure"
  
week_1_plus:
  - genre_features: "Built 10x faster with Adamus"
  - ship_mvp: "90 days to PMF"
  - adamus_matured: "156 capabilities from docs"
  
month_3_plus:
  - genre_at_pmf: "$10K+ MRR"
  - full_ollama: "Migrate to $0/month AI"
  - sovereignty: "Complete control"
```

### Questions Answered

**Q: Claude or open source?**  
A: Both (hybrid). Claude for speed now, Ollama after PMF.

**Q: Can Adamus self-implement from docs?**  
A: Yes. Reads all 67 docs, implements during downtime.

**Q: Does it conflict with anything?**  
A: No. 8 security systems protect both models.

---

## START NOW Commands (Copy-Paste)

```bash
# 1. Setup
mkdir ~/adamus && cd ~/adamus
# [Extract architecture docs here]
mkdir -p src/{coordinator,war_room,business_ai,cambi_ai,tech_ai} config logs tests
git init

# 2. Install
npm install -g @anthropic/claude-code
curl -fsSL https://ollama.com/install.sh | sh
ollama pull codellama
pip3 install anthropic flask requests beautifulsoup4

# 3. Configure
# [Create .env with API key]
# [Create .claude/context.md]

# 4. Build
claude
# [Paste first prompt from STEP 6]

# 5. Let it run
tmux new -s adamus
python3 src/coordinator/ai_coordinator.py
# Ctrl+B then D to detach

# Done. Adamus building itself overnight.
```

**Status**: ✅ READY TO BUILD

**Start**: RIGHT NOW (Steps 1-6 take 40 minutes)

**Result**: Adamus v0.1 by next Sunday, Genre building starts Week 1

**LET'S BUILD.** 🚀
