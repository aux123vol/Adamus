# Remote Access Doctrine
## How Augustus Accesses Adamus from Anywhere

**Requirement**: Full control of Adamus from phone, any location, any time.

---

## The Setup (Zero Cost)

```yaml
tools:
  tailscale:
    cost: "$0"
    role: "Secure VPN connecting phone to laptop"
    install: "tailscale.com/download"
    
  termius:
    cost: "$0 (basic)"
    role: "SSH client on phone"
    install: "App Store / Play Store"
    
  tmux:
    cost: "$0"
    role: "Persistent terminal sessions"
    install: "Already on Ubuntu"
```

---

## Access Architecture

```
Your Phone
    │
    ▼ (Tailscale VPN - encrypted)
Your Laptop (running Adamus)
    │
    ├─ SSH via Termius (terminal access)
    ├─ War Room on :5000 (dashboard)
    └─ Telegram Bot (OpenClaw control)
```

---

## Setup Commands

```bash
# On laptop:
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up --ssh

# Get your laptop's Tailscale IP
tailscale ip -4
# Note this IP (e.g., 100.x.x.x)

# Setup tmux for persistent sessions
tmux new-session -d -s adamus
tmux send-keys -t adamus "cd ~/adamus && python3 src/coordinator/adamus.py" Enter

# On phone:
# 1. Install Tailscale app, login with same account
# 2. Install Termius
# 3. Add server: IP = your Tailscale IP, user = johan
# 4. SSH in, attach: tmux attach -t adamus
```

---

## Access Levels

```yaml
from_phone:
  war_room: "http://100.x.x.x:5000 (read dashboard)"
  ssh: "Full terminal control"
  telegram: "Natural language commands to OpenClaw"
  
from_anywhere:
  vpn: "Tailscale works on any network"
  no_port_forwarding: "Tailscale handles it"
  no_vps_needed: "Laptop IS the server"
```

---

## Operational Scenarios

```yaml
at_job_5pm_2am:
  - check_telegram: "OpenClaw heartbeats"
  - approve_prs: "Via GitHub mobile"
  - war_room: "Quick metrics check"
  
on_break:
  - ssh_in: "If something needs fixing"
  - telegram: "Quick command to OpenClaw"
  
emergency:
  - ssh: "Full control"
  - kill_switch: "Stop any runaway process"
```

---

## Kill Switch

```bash
# From phone via SSH:
tmux send-keys -t adamus "C-c" Enter  # Stop Adamus
# OR
pkill -f adamus.py                     # Force stop
# OR
tailscale down                         # Cut all remote access
```

---

**Decision**: NO VPS needed until $10K+ MRR
**Cost**: $0
**Status**: READY TO CONFIGURE
