#!/bin/zsh

# Ensure script runs from its directory
DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$DIR"

if [ ! -d ".venv" ]; then
    echo "Virtual environment not found. Setting up..."
    uv venv .venv
    uv pip install rumps mss pillow anthropic google-genai
fi

echo "=========================================================="
echo "🎓 Starting Local Mock Quiz Server on http://127.0.0.1:8000"
echo "=========================================================="
.venv/bin/python mock_practice_server.py --open &
SERVER_PID=$!

cleanup() {
    echo "\nStopping mock server (PID: $SERVER_PID)..."
    kill $SERVER_PID 2>/dev/null
    exit 0
}

trap cleanup INT TERM EXIT

echo "=========================================================="
echo "🚀 Launching Study Copilot macOS Menu Bar App..."
echo "=========================================================="
echo "Look for '🎓 Study Copilot' in your macOS top menu bar."
echo "Press Ctrl+C in this terminal when finished to exit."

.venv/bin/python app.py

