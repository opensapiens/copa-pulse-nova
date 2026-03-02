#!/bin/bash

# Function to clean up background processes on exit
cleanup() {
    echo ""
    echo "Stopping CopaPulse servers..."
    kill $(jobs -p) 2>/dev/null || true
    exit
}

# Trap SIGINT (Ctrl+C) and SIGTERM
trap cleanup SIGINT SIGTERM

echo "Starting CopaPulse FastAPI Backend (Port 8000)..."
uvicorn api:app --reload --port 8000 &

echo "Starting CopaPulse React Frontend (Port 5173)..."
cd frontend && npm run dev &

echo ""
echo "========================================="
echo "✅ Both servers are running in the background."
echo "▶️ Backend API: http://localhost:8000"
echo "▶️ Frontend UI: http://localhost:5173"
echo "========================================="
echo "Press Ctrl+C to stop both servers."
echo ""

# Wait indefinitely to keep the script running and trap signals
wait
