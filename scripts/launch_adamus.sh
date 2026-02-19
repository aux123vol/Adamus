#!/bin/bash
# Launch Adamus Chat UI — opens browser automatically

cd /home/johan/adamus
source .venv/bin/activate

# Kill any previous instance
pkill -f "chat_app.py" 2>/dev/null
sleep 0.5

# Start the server in background
python -m src.ui.chat_app &
SERVER_PID=$!

# Wait for server to be ready
sleep 1.5

# Open browser
xdg-open http://localhost:5001 2>/dev/null || \
  firefox http://localhost:5001 2>/dev/null || \
  chromium-browser http://localhost:5001 2>/dev/null

# Keep script alive (so desktop icon process doesn't die)
wait $SERVER_PID
