#!/bin/bash

# ================================
# AI Marketplace Startup Script
# ================================
# Pure Python Backend

cd /home/angel/ai-marketplace

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded .env"
else
    echo "⚠️  .env file not found"
    exit 1
fi

echo ""
echo "🚀 Starting AI Marketplace (Python Backend)"
echo "============================================"
echo ""

# Kill any existing processes
pkill -f "app.py" 2>/dev/null
pkill -f "ai_agent.py" 2>/dev/null
pkill -f "node server" 2>/dev/null
sleep 1

# Activate Python virtual environment
source venv/bin/activate

# Install dependencies if needed
pip install -q -r requirements.txt

# Start Python Backend (port 3001)
echo "🐍 Starting Python Backend (port 3001)..."
python server/app.py &
BACKEND_PID=$!

sleep 3

echo ""
echo "✅ Backend started!"
echo ""
echo "   🐍 Python API:  http://localhost:3001"
echo "   🌐 Frontend:    http://localhost:5173"
echo ""
echo "   Start frontend with: npm run dev"
echo ""

# Handle shutdown
trap "kill $BACKEND_PID 2>/dev/null; exit" SIGINT SIGTERM

# Wait
wait
