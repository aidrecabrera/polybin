#!/bin/bash

# set logging
LOG_FILE="/home/admin/polybin_autostart.log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo "Starting autostart script at $(date)"

cd /home/admin/polybin || { echo "Failed to change to /home/admin/polybin"; exit 1; }
echo "Changed to polybin directory"

source venv/bin/activate || { echo "Failed to activate virtual environment"; exit 1; }
echo "Activated virtual environment"

# start python server
python server.py &
PYTHON_PID=$!
echo "Started Python server with PID $PYTHON_PID"

cd /home/admin/polybin/app || { echo "Failed to change to /home/admin/polybin/app"; exit 1; }
echo "Changed to app directory"

# check pnpm
if command -v pnpm &> /dev/null; then
    echo "pnpm is installed, using pnpm"
    PACKAGE_MANAGER="pnpm"
elif command -v npm &> /dev/null; then
    echo "pnpm not found, falling back to npm"
    PACKAGE_MANAGER="npm"
else
    echo "Neither pnpm nor npm found. Please install a package manager."
    exit 1
fi

# run frontend application
echo "Starting frontend application with $PACKAGE_MANAGER"
$PACKAGE_MANAGER run dev -- --host &
FRONTEND_PID=$!

# wait for a moment to see if the frontend starts successfully
sleep 10

# check if both processes are still running
if kill -0 $PYTHON_PID 2>/dev/null && kill -0 $FRONTEND_PID 2>/dev/null; then
    echo "Both Python server and frontend application are running"
    echo "Python server PID: $PYTHON_PID"
    echo "Frontend application PID: $FRONTEND_PID"
    # keep the script running
    wait
else
    echo "One or both processes failed to start or crashed"
    if ! kill -0 $PYTHON_PID 2>/dev/null; then
        echo "Python server is not running"
    fi
    if ! kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "Frontend application is not running"
    fi
    exit 1
fi