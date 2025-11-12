#!/bin/bash
# Start script for HRMS Web Application

echo "Starting HRMS Web Application..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Warning: .env file not found. Creating from example..."
    cat > .env << EOF
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_key_here
FLASK_SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')
FLASK_DEBUG=True
FLASK_PORT=5000
EOF
    echo "Please edit .env file with your Supabase credentials"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting Flask application on http://localhost:5000"
python app.py
