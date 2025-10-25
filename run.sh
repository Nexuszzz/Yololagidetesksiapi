#!/bin/bash
# Quick start script for Fire Detection System
# Linux/Mac shell script

echo "========================================"
echo "ESP32-CAM Fire Detection System"
echo "========================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found!"
    echo "Run setup first: python setup.py"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if config exists
if [ ! -f "config.json" ]; then
    echo "Config file not found!"
    echo "Run setup first: python setup.py"
    echo ""
    exit 1
fi

echo ""
echo "Starting fire detection..."
echo "Press Ctrl+C to stop"
echo ""

# Run fire detection
python fire_detection.py
