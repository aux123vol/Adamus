#!/usr/bin/env bash
# install_global.sh — Make `adamus` command accessible from anywhere

set -euo pipefail

ADAMUS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_BIN="$HOME/.local/bin"
SYSTEMD_USER="$HOME/.config/systemd/user"

echo "=============================="
echo " Adamus Global Install"
echo "=============================="
echo "Project: $ADAMUS_DIR"

# ── 1. Create ~/.local/bin/adamus CLI wrapper ──────────────────────────────
mkdir -p "$INSTALL_BIN"

cat > "$INSTALL_BIN/adamus" << WRAPPER
#!/usr/bin/env bash
# Adamus CLI — accessible from anywhere
ADAMUS_DIR="$ADAMUS_DIR"
VENV="$ADAMUS_DIR/.venv"

if [ -f "\$VENV/bin/python" ]; then
    PYTHON="\$VENV/bin/python"
else
    PYTHON=python3
fi

cd "\$ADAMUS_DIR"

case "\${1:-}" in
    start)      \$PYTHON -m src.main ;;
    ui)         \$PYTHON -m src.main --ui ;;
    cli)        \$PYTHON -m src.main --cli ;;
    chat)       \$PYTHON src/ui/unified_app.py ;;
    status)     \$PYTHON -c "
import sys, os
sys.path.insert(0, '\$ADAMUS_DIR')
from src.coordinator.brain_orchestrator import BrainOrchestrator
import json, subprocess
b = BrainOrchestrator()
s = b.get_status()
print('=== Adamus Status ===')
for name, info in s.items():
    avail = '✅' if info['available'] else '❌'
    print(f'  {avail} {info[\"name\"]:12} {info[\"model\"]}')
try:
    r = subprocess.run(['git','log','-1','--oneline'], capture_output=True, text=True, cwd='\$ADAMUS_DIR')
    print(f'  Git: {r.stdout.strip()}')
except: pass
"   ;;
    test)       cd "\$ADAMUS_DIR" && pytest tests/ -v --tb=short ;;
    logs)       tail -f "\$ADAMUS_DIR/logs/adamus.log" 2>/dev/null || echo "No logs yet" ;;
    loop-logs)  tail -f "\$HOME/.adamus/loop.log" 2>/dev/null || echo "No loop logs yet" ;;
    service)
        case "\${2:-}" in
            start)   systemctl --user start adamus ;;
            stop)    systemctl --user stop adamus ;;
            restart) systemctl --user restart adamus ;;
            status)  systemctl --user status adamus ;;
            *)       echo "Usage: adamus service [start|stop|restart|status]" ;;
        esac ;;
    help|--help|-h)
        echo "Adamus CLI — AI CTO Orchestrator"
        echo ""
        echo "Usage: adamus <command>"
        echo ""
        echo "Commands:"
        echo "  start        Start full Adamus stack (UI + coordinator + loop)"
        echo "  ui           Start web UI only (http://localhost:8888)"
        echo "  cli          Start CLI interactive mode"
        echo "  chat         Start chat UI only"
        echo "  status       Show brain/system status"
        echo "  test         Run test suite"
        echo "  logs         Tail main logs"
        echo "  loop-logs    Tail autonomous loop logs"
        echo "  service      Manage systemd service [start|stop|restart|status]"
        echo ""
        echo "Web UI: http://localhost:8888"
        ;;
    *)
        # Pass all args as a task to Adamus
        if [ -n "\${1:-}" ]; then
            \$PYTHON -c "
import sys, asyncio
sys.path.insert(0, '\$ADAMUS_DIR')
from dotenv import load_dotenv
load_dotenv('\$ADAMUS_DIR/.env')
from src.coordinator.ai_coordinator import AICoordinator
async def run():
    c = AICoordinator()
    await c.initialize()
    r = await c.execute_task(' '.join(sys.argv[1:]))
    print(r.result)
asyncio.run(run())
" "\$@"
        else
            adamus help
        fi
        ;;
esac
WRAPPER

chmod +x "$INSTALL_BIN/adamus"
echo "✅ CLI installed: $INSTALL_BIN/adamus"

# ── 2. Ensure ~/.local/bin is in PATH ─────────────────────────────────────
if [[ ":$PATH:" != *":$INSTALL_BIN:"* ]]; then
    echo ""
    echo "Adding ~/.local/bin to PATH in ~/.bashrc..."
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    echo "✅ PATH updated (restart terminal or: source ~/.bashrc)"
else
    echo "✅ ~/.local/bin already in PATH"
fi

# ── 3. Install systemd user service ───────────────────────────────────────
mkdir -p "$SYSTEMD_USER"

cat > "$SYSTEMD_USER/adamus.service" << SERVICE
[Unit]
Description=Adamus AI CTO Orchestrator
After=network.target
Wants=network.target

[Service]
Type=simple
WorkingDirectory=$ADAMUS_DIR
Environment=PATH=$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin
Environment=HOME=$HOME
ExecStart=$INSTALL_BIN/adamus start
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=default.target
SERVICE

# Enable systemd lingering so user service runs without login
loginctl enable-linger "$USER" 2>/dev/null || true

systemctl --user daemon-reload
systemctl --user enable adamus 2>/dev/null || true
echo "✅ Systemd service installed: adamus.service"

# ── 4. Create ~/.adamus directory ─────────────────────────────────────────
mkdir -p "$HOME/.adamus"
echo "✅ Data directory: ~/.adamus/"

# ── Summary ───────────────────────────────────────────────────────────────
echo ""
echo "=============================="
echo " Installation Complete"
echo "=============================="
echo ""
echo "Run from anywhere:"
echo "  adamus start          # full stack"
echo "  adamus ui             # web UI → http://localhost:8888"
echo "  adamus status         # quick status check"
echo "  adamus service start  # run as background service"
echo ""
echo "Restart terminal or: source ~/.bashrc"
