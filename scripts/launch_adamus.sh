#!/bin/bash
# Launch Adamus Chat UI

REPO="/home/johan/adamus"
PORT=5001

cd "$REPO"
source .venv/bin/activate

# Kill any old instance on this port
fuser -k ${PORT}/tcp 2>/dev/null
sleep 1

# Start server
python src/ui/chat_app.py &
sleep 2

# Open browser
xdg-open "http://localhost:${PORT}" 2>/dev/null &

# Keep alive
wait
