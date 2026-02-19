# Runbooks
## Operational Playbooks for Adamus

---

## Runbook 1: Starting Adamus

```bash
# Every morning, run in order:
cd ~/adamus

# 1. Pull latest changes
git pull origin main

# 2. Check environment
python3 -c "import os; print('API Key:', 'SET' if os.getenv('ANTHROPIC_API_KEY') else 'MISSING')"

# 3. Load all docs into memory
python3 scripts/load_docs.py

# 4. Start Adamus coordinator
tmux new-session -d -s adamus
tmux send-keys -t adamus "python3 src/coordinator/adamus.py" Enter

# 5. Start War Room
tmux new-window -t adamus
tmux send-keys -t adamus "python3 src/war_room/app.py" Enter

# 6. Verify
curl http://localhost:5000/health
# Should return: {"status": "ok", "docs_loaded": 90+}
```

## Runbook 2: Enabling Autonomous Mode

```bash
# Before leaving for job at 5pm:

# 1. Commit all work
git add -A && git commit -m "[Manual] EOD commit"
git push origin develop

# 2. Set tonight's priorities
python3 scripts/set_priorities.py \
  --priority-1 "Implement data governance" \
  --priority-2 "Add error handling to coordinator" \
  --priority-3 "Write tests for task router"

# 3. Verify OpenClaw running
openclaw status
# Should show: Gateway running

# 4. Enable autonomous mode
python3 scripts/enable_autonomous.py

# 5. Confirm via Telegram
# Should receive: "Autonomous mode enabled. Starting in 5 minutes."
```

## Runbook 3: Reviewing Overnight Work

```bash
# Every morning at 8am:

# 1. Check War Room
open http://localhost:5000

# 2. List overnight PRs
gh pr list --label "openclaw"

# 3. Review each PR
gh pr view [PR_NUMBER]

# 4. Approve good PRs
gh pr review [PR_NUMBER] --approve
gh pr merge [PR_NUMBER] --squash

# 5. Request changes
gh pr review [PR_NUMBER] --request-changes --body "Fix: [specific issue]"
```

## Runbook 4: Emergency Stop

```bash
# If something goes wrong:

# Stop autonomous mode immediately
tmux send-keys -t adamus "q" Enter

# Or force kill
pkill -f "adamus.py"
pkill -f "openclaw"

# Cut all network access
# sudo tailscale down

# Check what happened
tail -100 ~/adamus/logs/adamus.log
tail -100 ~/.openclaw/logs/gateway.log
```

**Status**: ACTIVE — Follow these daily
