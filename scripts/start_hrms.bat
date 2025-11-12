@echo off
REM HRMS Application Startup Script for Windows
REM This script starts the Human Resources Management System

echo ========================================
echo HRMS - Human Resources Management System
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://www.python.org/
    echo.
    pause
    exit /b 1
)

echo Python detected: 
python --version
echo.

REM Check if we're in the correct directory
if not exist "main.py" (
    echo ERROR: main.py not found!
    echo Please run this script from the HRMS_app root directory
    echo.
    pause
    exit /b 1
)

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    echo Virtual environment activated.
    echo.
) else (
    echo WARNING: Virtual environment not found at 'venv'
    echo It's recommended to use a virtual environment.
    echo Create one with: python -m venv venv
    echo.
)

REM Check if required packages are installed
echo Checking dependencies...
python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Required packages not installed
    echo Installing dependencies from requirements.txt...
    echo.
    python -m pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        echo Please run: pip install -r requirements.txt
        echo.
        pause
        exit /b 1
    )
)

echo Starting HRMS Application...
echo.
python main.py

if errorlevel 1 (
    echo.
    echo ERROR: Application exited with an error
    echo Check the error messages above for details
    echo.
    pause
)
