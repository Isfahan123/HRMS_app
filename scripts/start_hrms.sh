#!/bin/bash
# HRMS Application Startup Script for Linux/Mac
# This script starts the Human Resources Management System

echo "========================================"
echo "HRMS - Human Resources Management System"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH"
    echo "Please install Python 3.8 or higher"
    echo "  Ubuntu/Debian: sudo apt-get install python3 python3-pip"
    echo "  macOS: brew install python3"
    echo ""
    read -p "Press Enter to exit"
    exit 1
fi

# Use python3 if available, otherwise python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
    PIP_CMD="pip3"
else
    PYTHON_CMD="python"
    PIP_CMD="pip"
fi

echo "Python detected: "
$PYTHON_CMD --version
echo ""

# Check if we're in the correct directory
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found!"
    echo "Please run this script from the HRMS_app root directory"
    echo ""
    read -p "Press Enter to exit"
    exit 1
fi

# Check if virtual environment exists
if [ -f "venv/bin/activate" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo "Virtual environment activated."
    echo ""
elif [ -f "venv/Scripts/activate" ]; then
    echo "Activating virtual environment..."
    source venv/Scripts/activate
    echo "Virtual environment activated."
    echo ""
else
    echo "WARNING: Virtual environment not found at 'venv'"
    echo "It's recommended to use a virtual environment."
    echo "Create one with: $PYTHON_CMD -m venv venv"
    echo ""
fi

# Check if required packages are installed
echo "Checking dependencies..."
if ! $PYTHON_CMD -c "import PyQt5" &> /dev/null; then
    echo "Required packages not installed. Installing dependencies..."
    echo ""
    $PYTHON_CMD -m pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo ""
        echo "ERROR: Failed to install dependencies"
        echo "Please run: $PIP_CMD install -r requirements.txt"
        echo ""
        read -p "Press Enter to exit"
        exit 1
    fi
else
    echo "Dependencies OK"
fi

echo ""
echo "Starting HRMS Application..."
echo ""
$PYTHON_CMD main.py

if [ $? -ne 0 ]; then
    echo ""
    echo "ERROR: Application exited with an error"
    echo "Check the error messages above for details"
    echo ""
    read -p "Press Enter to exit"
fi
