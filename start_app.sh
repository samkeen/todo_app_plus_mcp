#!/bin/bash
# Bootstrap script to start the Todo API and UI

# Function to check if a process is running on a specific port
check_port() {
  local port=$1
  lsof -i :$port -sTCP:LISTEN > /dev/null 2>&1
  return $?
}

# Function to stop a process running on a specific port
stop_process() {
  local port=$1
  local name=$2
  echo "Stopping $name on port $port..."
  pid=$(lsof -ti :$port -sTCP:LISTEN)
  if [ -n "$pid" ]; then
    kill -9 $pid
    echo "$name stopped successfully."
  else
    echo "No $name process found running on port $port."
  fi
}

# Set ports
API_PORT=8000
UI_PORT=5000

# Check and stop API if already running
if check_port $API_PORT; then
  stop_process $API_PORT "Todo API"
fi

# Check and stop UI if already running
if check_port $UI_PORT; then
  stop_process $UI_PORT "Todo UI"
fi

# Start the API server
echo "Starting Todo API on port $API_PORT..."
cd "$(dirname "$0")"
uv run uvicorn todo_api.main:app --reload --port $API_PORT &
API_PID=$!

# Give the API a moment to start
echo "Waiting for API to initialize..."
sleep 3

# Verify API is running
if ! check_port $API_PORT; then
  echo "Error: Failed to start the API server."
  exit 1
fi

# Start the UI server
echo "Starting Todo UI on port $UI_PORT..."
cd "$(dirname "$0")/todo_ui"
uv run python app.py &
UI_PID=$!

# Give the UI a moment to start
sleep 2

# Verify UI is running
if ! check_port $UI_PORT; then
  echo "Error: Failed to start the UI server."
  # Kill the API server if UI fails to start
  kill -9 $API_PID
  exit 1
fi

echo "================================================"
echo "🚀 Todo Application is now running!"
echo "✅ API server: http://localhost:$API_PORT"
echo "✅ UI interface: http://localhost:$UI_PORT"
echo "✅ API documentation: http://localhost:$API_PORT/docs"
echo "================================================"
echo "Press Ctrl+C to stop both servers"

# Wait for user to terminate
trap "echo 'Stopping servers...'; kill -9 $API_PID $UI_PID; echo 'Servers stopped.'; exit 0" INT
wait
