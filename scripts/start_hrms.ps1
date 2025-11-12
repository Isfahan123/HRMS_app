#!/usr/bin/env pwsh
# HRMS Application Startup Script for Windows PowerShell
# This script starts the Human Resources Management System

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "HRMS - Human Resources Management System" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python detected: $pythonVersion" -ForegroundColor Green
    Write-Host ""
} catch {
    Write-Host "ERROR: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8 or higher from https://www.python.org/" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if we're in the correct directory
if (-not (Test-Path "main.py")) {
    Write-Host "ERROR: main.py not found!" -ForegroundColor Red
    Write-Host "Please run this script from the HRMS_app root directory" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if virtual environment exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    Write-Host "Virtual environment activated." -ForegroundColor Green
    Write-Host ""
} elseif (Test-Path "venv/bin/activate") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    & "venv/bin/activate"
    Write-Host "Virtual environment activated." -ForegroundColor Green
    Write-Host ""
} else {
    Write-Host "WARNING: Virtual environment not found at 'venv'" -ForegroundColor Yellow
    Write-Host "It's recommended to use a virtual environment." -ForegroundColor Yellow
    Write-Host "Create one with: python -m venv venv" -ForegroundColor Yellow
    Write-Host ""
}

# Check if required packages are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
try {
    python -c "import PyQt5" 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "PyQt5 not found"
    }
    Write-Host "Dependencies OK" -ForegroundColor Green
} catch {
    Write-Host "Required packages not installed. Installing dependencies..." -ForegroundColor Yellow
    Write-Host ""
    python -m pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
        Write-Host "Please run: pip install -r requirements.txt" -ForegroundColor Yellow
        Write-Host ""
        Read-Host "Press Enter to exit"
        exit 1
    }
}

Write-Host "Starting HRMS Application..." -ForegroundColor Green
Write-Host ""
python main.py

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "ERROR: Application exited with an error" -ForegroundColor Red
    Write-Host "Check the error messages above for details" -ForegroundColor Yellow
    Write-Host ""
    Read-Host "Press Enter to exit"
}
