#!/bin/bash

# SlyWriter Backend Deployment Script
# For production deployment on Linux/Unix servers

echo "================================"
echo "SlyWriter Backend Deployment"
echo "================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Python 3.8+ is installed
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then 
    echo -e "${RED}Error: Python 3.8+ is required${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python version check passed${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Run startup checks
echo "Running startup checks..."
python startup.py

if [ $? -ne 0 ]; then
    echo -e "${RED}Startup checks failed!${NC}"
    exit 1
fi

# Create systemd service file (optional)
if [ "$1" == "--service" ]; then
    echo "Creating systemd service..."
    sudo tee /etc/systemd/system/slywriter-backend.service > /dev/null <<EOF
[Unit]
Description=SlyWriter Backend API
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$(pwd)
Environment="PATH=$(pwd)/venv/bin"
ExecStart=$(pwd)/venv/bin/python main_complete.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

    sudo systemctl daemon-reload
    sudo systemctl enable slywriter-backend
    echo -e "${GREEN}✓ Systemd service created${NC}"
fi

# Start the application
if [ "$1" == "--start" ]; then
    echo "Starting SlyWriter Backend..."
    nohup python main_complete.py > slywriter.log 2>&1 &
    echo $! > slywriter.pid
    echo -e "${GREEN}✓ Backend started with PID: $(cat slywriter.pid)${NC}"
elif [ "$1" == "--service" ]; then
    sudo systemctl start slywriter-backend
    echo -e "${GREEN}✓ Backend service started${NC}"
else
    echo ""
    echo "Deployment complete! To start the backend:"
    echo "  ./deploy.sh --start    (Run in background)"
    echo "  ./deploy.sh --service  (Create and start systemd service)"
    echo "  python main_complete.py (Run in foreground)"
fi