# WEEK 0 BUILD PLAN: Building Adamus
## From Documents → Working System (7 Days)

**Status**: You have 67+ architecture documents. Time to build the actual system.

**Timeline**: This week (Sunday → Saturday)

**Goal**: Working Adamus v0.1 running on your laptop, helping you build Genre

---

## Day 0 (Sunday): Setup Foundation (3-4 hours)

### Morning: Install Core Tools

```bash
# 1. Install Homebrew (Mac) or apt (Linux)
# Mac:
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 2. Install essential tools
brew install python3 node tmux git

# 3. Install Claude Code
npm install -g @anthropic/claude-code

# 4. Install Tailscale (mobile access)
# Download from: https://tailscale.com/download
# Install, login, run: tailscale up --ssh

# 5. Verify everything
python3 --version  # Should be 3.11+
node --version     # Should be 18+
claude --version   # Should show Claude Code version
```

### Afternoon: Create Project Structure

```bash
# Create main directory
mkdir ~/adamus
cd ~/adamus

# Create structure
mkdir -p {docs,src/{business_ai,cambi_ai,tech_ai,coordinator},config,logs,data}

# Initialize git
git init
echo "logs/" > .gitignore
echo "data/" >> .gitignore
echo ".env" >> .gitignore
echo "node_modules/" >> .gitignore
echo "__pycache__/" >> .gitignore

# First commit
git add .
git commit -m "Initial Adamus structure"
```

### Evening: Import All Documents

```bash
# Copy all architecture docs
cd ~/adamus/docs
mkdir architecture

# Download all docs from this conversation
# (I'll tell you how in next section)

# Verify you have:
ls -la architecture/
# Should see:
# - NETWORKED_AI_TRINITY.md
# - TELEMETRY_FREE_SEARCH.md
# - SELF_IMPROVING_ADAMUS.md
# - All 8 security system docs
# - All other architecture files
```

---

## How to Get All Documents into Claude Code

### Option 1: Claude.ai Projects (Easiest)

```yaml
step_1:
  - create_project: "Adamus Architecture"
  - add_all_files: "Upload all 67 docs from /mnt/user-data/outputs/"
  - claude_code_access: "Can now reference all docs"

step_2_use_claude_code:
  - command: "claude"
  - context: "Has access to project knowledge"
  - prompt: "@adamus-architecture Build the AI Coordinator"
```

### Option 2: Direct File Feed (More Control)

```bash
# Create a master index
cd ~/adamus/docs/architecture

# Create MASTER_INDEX.md that lists all docs
cat > MASTER_INDEX.md << 'EOF'
# Adamus Architecture Master Index

## Core Architecture (Read First)
1. NETWORKED_AI_TRINITY.md - The complete system
2. FINAL_INTEGRATION_GENRE_MVP.md - How it fits with Genre
3. SELF_IMPROVING_ADAMUS.md - Meta-layer design

## Infrastructure
4. TELEMETRY_FREE_SEARCH.md - Privacy-first search
5. MOBILE_ACCESS_ARCHITECTURE.md - Work from anywhere
6. HOSTINGER_VPS_DECISION.md - Infrastructure choices

## Security Systems (8 Total)
7. data_governance/DATA_GOVERNANCE_FRAMEWORK.md
8. llm_optimization/LLM_OPTIMIZATION_FRAMEWORK.md
9. multi_method/MULTI_METHOD_AGENT_ARCHITECTURE.md
10. bias_detection/BIAS_DETECTION_FRAMEWORK.md
11. explainable_ai/EXPLAINABLE_AI_FRAMEWORK.md
12. zero_trust/ZERO_TRUST_ARCHITECTURE.md
13. prompt_defense/PROMPT_INJECTION_DEFENSE.md
14. vulnerability_mgmt/VULNERABILITY_MANAGEMENT.md

## Implementation
15. IMPLEMENTATION_ROADMAP.md - Week-by-week plan
16. SYSTEMS_INTEGRATION.md - How systems connect
17. UPDATE_SUMMARY.md - Change log

[... continues for all 67 docs ...]
EOF

# Now Claude Code can read this index
```

### Option 3: Context File (Recommended for Claude Code)

```bash
# Create .claude/context.md in project root
mkdir -p ~/adamus/.claude
cat > ~/adamus/.claude/context.md << 'EOF'
# Adamus Architecture Context

You are building Adamus, an AI CTO system for Genre.

## Architecture Location
All architecture documents are in: ~/adamus/docs/architecture/

## Key Documents
- NETWORKED_AI_TRINITY.md: Core architecture
- SELF_IMPROVING_ADAMUS.md: Meta-layer design
- All 8 security system specs in subdirectories

## Mission
Build a networked AI system that:
1. Helps Augustus build Genre 10x faster
2. Self-improves while building
3. Maintains enterprise security
4. Costs $0 to bootstrap

## Tech Stack
- Python 3.11+ (main language)
- Node.js (Claude Code)
- PostgreSQL + pgvector (memory)
- Redis (cache/queue)
- Docker (optional, for deployment)

## Constraints
- Bootstrap budget: ~$12/month
- Solo founder: Augustus
- Timeline: Ship Genre MVP in 90 days
- Privacy: Telemetry-free, self-hosted

## Start Here
Build in this order:
1. AI Coordinator (orchestrates 3 AIs)
2. Basic War Room (monitoring)
3. Business AI v0.1
4. CAMBI AI v0.1
5. Tech AI (Adamus core) v0.1
6. Self-improvement meta-layer
EOF
```

---

## Day 1 (Monday): Build AI Coordinator (Core)

### Use Claude Code to Build

```bash
cd ~/adamus
claude

# In Claude Code session:
```

**Prompt for Claude Code**:
```
Read ~/adamus/docs/architecture/NETWORKED_AI_TRINITY.md

Build the AI Coordinator class in Python:

Requirements:
1. Orchestrates 3 AIs (Business, CAMBI, Tech/Adamus)
2. Routes tasks between them
3. Daily coordination cycle
4. Weekly A/B testing cycle
5. Logging and monitoring

Create:
- src/coordinator/ai_coordinator.py (main class)
- src/coordinator/task_router.py (routing logic)
- src/coordinator/config.yaml (configuration)
- tests/test_coordinator.py (unit tests)

Follow the spec exactly from NETWORKED_AI_TRINITY.md.

Start with minimal viable - can expand later.
```

**Expected Output**:
- Claude Code creates all files
- Runs tests
- Shows you the code
- Explains what it built

### Test It Works

```bash
# Run the coordinator
python3 src/coordinator/ai_coordinator.py

# Should see:
# ✅ AI Coordinator initialized
# ✅ 3 AI agents registered
# ✅ Daily cycle started
```

---

## Day 2 (Tuesday): Build War Room (Monitoring)

**Prompt for Claude Code**:
```
Read ~/adamus/docs/architecture/COMPLETE_ARCHITECTURE.md

Build the War Room monitoring system:

Requirements:
1. Web dashboard (Next.js or Flask)
2. Real-time metrics display
3. Three panels: Internal Vitals, External Radar, Strategic Horizon
4. Mobile-responsive (phone access)
5. Read-only by default, approval actions require auth

Create:
- src/war_room/dashboard.py (backend API)
- src/war_room/frontend/ (web UI)
- src/war_room/metrics.py (metric collection)
- docs: How to access from browser

Tech stack: Flask + simple HTML/JS (keep it simple for MVP)

Make it beautiful but minimal - we're bootstrapped.
```

### Test It Works

```bash
# Start War Room
python3 src/war_room/dashboard.py

# Open browser: http://localhost:5000
# Should see: Dashboard with 3 panels
```

---

## Day 3 (Wednesday): Build Business AI v0.1

**Prompt for Claude Code**:
```
Read ~/adamus/docs/architecture/NETWORKED_AI_TRINITY.md
Read ~/adamus/docs/architecture/TELEMETRY_FREE_SEARCH.md

Build Business AI agent:

Requirements:
1. Daily finance pulse (track MRR, burn, runway)
2. Competitor monitoring (Notion, Mem, Reflect)
3. Uses SearxNG for search (provide URL: http://localhost:8080)
4. Reports to War Room
5. Connects to AI Coordinator

Create:
- src/business_ai/business_agent.py (main class)
- src/business_ai/finance_tracker.py (MRR/burn tracking)
- src/business_ai/competitor_intel.py (monitoring)
- config: Competitor list, search settings

For now: Mock the finance data (we'll connect to real Genre DB later)
For search: Assume SearxNG running (we'll set that up Day 4)
```

---

## Day 4 (Thursday): Setup Privacy Infrastructure

### Deploy SearxNG (Self-Hosted Search)

```bash
# Option 1: Docker (easiest)
cd ~/adamus
mkdir searxng
cd searxng

# Download docker-compose
curl https://raw.githubusercontent.com/searxng/searxng-docker/master/docker-compose.yaml -o docker-compose.yaml

# Generate secret
sed -i "s|ultrasecretkey|$(openssl rand -hex 32)|g" searxng/settings.yml

# Start
docker-compose up -d

# Test
curl http://localhost:8080

# Should see SearxNG interface
```

### Option 2: DigitalOcean VPS (if no Docker)

```bash
# Follow TELEMETRY_FREE_SEARCH.md
# Deploy to DigitalOcean ($12/month)
# Configure for private use only
```

### Connect Business AI to SearxNG

```python
# Update business_ai/config.yaml
search:
  primary: "http://localhost:8080"  # Your SearxNG
  fallback: "direct_scraping"
```

---

## Day 5 (Friday): Build CAMBI AI v0.1

**Prompt for Claude Code**:
```
Read ~/adamus/docs/architecture/NETWORKED_AI_TRINITY.md

Build CAMBI AI agent:

Requirements:
1. Community pulse (sentiment analysis)
2. Content generation (blog posts, social)
3. Trend detection (HackerNews, ProductHunt)
4. Reports to War Room
5. Connects to AI Coordinator

Create:
- src/cambi_ai/cambi_agent.py (main class)
- src/cambi_ai/sentiment.py (community monitoring)
- src/cambi_ai/content_gen.py (content creation)
- src/cambi_ai/trends.py (trend detection)

Use Claude API for content generation (you already have API key)
Use direct scraping for HN/PH (no search needed)
```

---

## Day 6 (Saturday): Build Tech AI v0.1 (Adamus Core)

**Prompt for Claude Code**:
```
Read ~/adamus/docs/architecture/SELF_IMPROVING_ADAMUS.md

Build Adamus (Tech AI) core:

Requirements:
1. Self-improvement meta-layer
2. Capability detection
3. Genre feature building (scaffold only for now)
4. Reports to War Room
5. Connects to AI Coordinator

Create:
- src/tech_ai/adamus_core.py (main class)
- src/tech_ai/self_improvement.py (meta-layer)
- src/tech_ai/capability_builder.py (builds missing capabilities)
- src/tech_ai/genre_builder.py (scaffold for Genre features)

This is the most complex component. Start minimal:
- Can detect what capabilities it needs
- Can build simple Python modules
- Can test and deploy them
- Self-improvement loop works

Full implementation comes later. For now: prove the pattern.
```

---

## Day 7 (Sunday): Integration & Testing

### Full System Test

```bash
cd ~/adamus

# Start everything
tmux new -s adamus

# Window 1: AI Coordinator
python3 src/coordinator/ai_coordinator.py

# Window 2: War Room
python3 src/war_room/dashboard.py

# Window 3: All 3 AIs
python3 src/business_ai/business_agent.py &
python3 src/cambi_ai/cambi_agent.py &
python3 src/tech_ai/adamus_core.py &

# Open browser: http://localhost:5000
# Should see: War Room with all 3 AIs reporting
```

### Test the Network

**Prompt to AI Coordinator**:
```
Test task: "Monitor Notion for new features"

Expected flow:
1. Coordinator receives task
2. Routes to Business AI
3. Business AI uses SearxNG to search
4. Business AI reports findings
5. War Room displays results
```

### Test Self-Improvement

**Prompt to Adamus**:
```
Build a simple capability: "Email notification system"

Expected flow:
1. Adamus detects: "Missing email capability"
2. Adamus builds: email_notifier.py
3. Adamus tests: Sends test email
4. Adamus deploys: Adds to capabilities
5. War Room shows: "New capability: email"
```

---

## Success Criteria (End of Week 0)

### Must Have Working ✅
```yaml
infrastructure:
  - laptop: "Running all components"
  - tmux: "Persistent sessions"
  - tailscale: "Mobile access configured"
  - searxng: "Self-hosted search running"

core_systems:
  - ai_coordinator: "Orchestrating 3 AIs"
  - war_room: "Dashboard accessible via browser"
  - business_ai: "Basic competitor monitoring"
  - cambi_ai: "Basic trend detection"
  - adamus_core: "Basic self-improvement working"

network:
  - all_ais_connected: "Communicating through coordinator"
  - tasks_routing: "Can route tasks between AIs"
  - war_room_updating: "Real-time metrics display"

mobile:
  - phone_access: "Can SSH via Tailscale"
  - war_room_mobile: "Dashboard works on phone"

telemetry:
  - searxng: "Private search working"
  - zero_tracking: "No external APIs for search"
```

### Should Have (Nice to Have)
```yaml
polish:
  - logging: "All actions logged"
  - error_handling: "Graceful failures"
  - documentation: "How to use each component"

optional:
  - tests: "Unit tests for core functions"
  - monitoring: "Basic health checks"
```

---

## Week 1 Plan (Next Week): Build Genre

### Now That Adamus Works

```yaml
monday:
  - adamus_task: "Build Genre user authentication"
  - augustus: "Design Genre UI mockups"

tuesday:
  - adamus_task: "Build Genre editor interface"
  - augustus: "Write Genre marketing copy"

wednesday:
  - adamus_task: "Integrate Claude API for AI writing"
  - augustus: "User research calls"

thursday:
  - adamus_task: "Build Genre database schema"
  - augustus: "Setup Genre hosting"

friday:
  - adamus_deploys: "Genre v0.1 to staging"
  - augustus_tests: "Try it, give feedback"

result: "Genre MVP foundation in 1 week with Adamus helping"
```

---

## Critical Tips for Using Claude Code

### 1. Feed Context Properly

```bash
# Bad:
claude
> Build the AI Coordinator

# Good:
claude
> Read ~/adamus/docs/architecture/NETWORKED_AI_TRINITY.md
> 
> Build the AI Coordinator class following the spec exactly.
> Use Python 3.11+, follow the architecture in the doc.
> 
> Create:
> - src/coordinator/ai_coordinator.py
> - tests/test_coordinator.py
>
> Make it minimal but functional.
```

### 2. Reference Docs Explicitly

```bash
# Tell Claude Code where docs are:
> All architecture docs are in ~/adamus/docs/architecture/
> 
> Read NETWORKED_AI_TRINITY.md for the coordinator design.
> Read SELF_IMPROVING_ADAMUS.md for meta-layer design.
>
> Build according to those specs.
```

### 3. Iterate Quickly

```bash
# Build → Test → Fix cycle:
claude
> Build X
# Claude builds it
> Test X
# See what breaks
> Fix Y issue
# Claude fixes it
> Test again
# Repeat until works
```

### 4. Use tmux Sessions

```bash
# One terminal:
tmux new -s build

# Window 1: Claude Code building
claude

# Window 2: Testing
python3 test.py

# Window 3: Logs
tail -f logs/adamus.log

# Switch windows: Ctrl+B then number (0,1,2)
# Detach: Ctrl+B then D
# Reattach: tmux attach -s build
```

---

## Common Issues & Fixes

### Issue 1: "Claude Code can't find docs"

```bash
# Fix: Create explicit context file
cat > .claude/context.md << 'EOF'
Architecture docs are in: ~/adamus/docs/architecture/

Key files:
- NETWORKED_AI_TRINITY.md (main architecture)
- SELF_IMPROVING_ADAMUS.md (meta-layer)

Read these before building.
EOF
```

### Issue 2: "Python dependencies missing"

```bash
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
EOF

# Install
pip3 install -r requirements.txt
```

### Issue 3: "Ports already in use"

```bash
# Check what's using port:
lsof -i :5000

# Kill it:
kill -9 <PID>

# Or use different port:
flask run --port 5001
```

---

## File Structure (End of Week 0)

```
~/adamus/
├── .claude/
│   └── context.md (Claude Code context)
├── docs/
│   └── architecture/
│       ├── NETWORKED_AI_TRINITY.md
│       ├── SELF_IMPROVING_ADAMUS.md
│       ├── TELEMETRY_FREE_SEARCH.md
│       ├── (all 67 docs here)
│       └── MASTER_INDEX.md
├── src/
│   ├── coordinator/
│   │   ├── ai_coordinator.py
│   │   ├── task_router.py
│   │   └── config.yaml
│   ├── war_room/
│   │   ├── dashboard.py
│   │   ├── metrics.py
│   │   └── frontend/
│   ├── business_ai/
│   │   ├── business_agent.py
│   │   ├── finance_tracker.py
│   │   └── competitor_intel.py
│   ├── cambi_ai/
│   │   ├── cambi_agent.py
│   │   ├── sentiment.py
│   │   └── content_gen.py
│   └── tech_ai/
│       ├── adamus_core.py
│       ├── self_improvement.py
│       └── capability_builder.py
├── config/
│   ├── .env (API keys, secrets)
│   └── config.yaml (main config)
├── logs/
│   └── adamus.log
├── tests/
│   └── test_*.py
├── requirements.txt
└── README.md
```

---

## Your Genre MVP Documents

### When to Add Them

```yaml
NOT_this_week:
  - genre_mvp_spec: "Wait until Adamus v0.1 works"
  - war_bibles: "Wait until privacy infrastructure secured"
  - strategy_docs: "Wait until foundation stable"

WHY:
  - prove_adamus_works: "First validate the builder works"
  - then_give_mission: "Then give it Genre mission"
  - foundation_first: "Security before sensitive docs"

week_1:
  - genre_mvp_spec: "Feed to Adamus to build"
  - adamus_knows_mission: "What to build"
```

---

## The Bottom Line

### This Week's Mission

**Build Adamus v0.1**:
- 7 days
- 3-4 hours/day
- Basic but working
- All 3 AIs coordinating
- War Room monitoring
- Telemetry-free
- Mobile access
- $12/month cost

**NOT building yet**:
- Full 8 security systems (scaffolds only)
- Complete self-improvement (prove pattern only)
- Genre features (that's Week 1+)

**Proof it works**:
- Can route tasks between AIs
- Can monitor via War Room
- Can access from phone
- Can search privately

### Next Week (Week 1)

**Build Genre with Adamus**:
- Feed Genre MVP spec to Adamus
- Adamus builds features 10x faster
- Augustus focuses on design/marketing
- Ship Genre MVP in 90 days

---

## START NOW (Step 1)

```bash
# Right now, run this:
mkdir ~/adamus
cd ~/adamus

# Download Claude Code:
npm install -g @anthropic/claude-code

# Create structure:
mkdir -p {docs/architecture,src/{coordinator,war_room,business_ai,cambi_ai,tech_ai},config,logs,tests}

# Copy all 67 docs to docs/architecture/
# (Download from this conversation's artifacts)

# Start building:
claude

# In Claude Code:
> I'm building Adamus, an AI CTO system.
> All architecture docs are in ~/adamus/docs/architecture/
> Read NETWORKED_AI_TRINITY.md
> Build the AI Coordinator in Python
> Start with minimal viable version
```

**YOU'RE BUILDING ADAMUS THIS WEEK. LET'S GO.**
