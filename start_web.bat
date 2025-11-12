@echo off
REM Start script for HRMS Web Application (Windows)

echo Starting HRMS Web Application...

REM Check if .env file exists
if not exist .env (
    echo Warning: .env file not found. Please create one with your Supabase credentials.
    echo Example .env file:
    echo SUPABASE_URL=your_supabase_url_here
    echo SUPABASE_KEY=your_supabase_key_here
    echo FLASK_SECRET_KEY=your_secret_key_here
    echo FLASK_DEBUG=True
    echo FLASK_PORT=5000
    pause
    exit /b 1
)

REM Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Run the application
echo Starting Flask application on http://localhost:5000
python app.py

pause
