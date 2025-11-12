# HRMS Quick Start Guide

This guide will help you quickly set up and run the HRMS application in both desktop and web modes.

## Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- Supabase account with credentials

## Option 1: Desktop Application (PyQt5)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/Isfahan123/HRMS_app.git
cd HRMS_app
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On Linux/Mac:
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Configure Supabase credentials in your environment or `.env` file:
```
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

### Run Desktop Application

**Windows:**
```batch
scripts\start_hrms.bat
```

**Linux/Mac:**
```bash
python main.py
```

## Option 2: Web Application (Flask)

### Setup

1. Complete steps 1-4 from the Desktop Application setup above

2. Copy the example environment file:
```bash
cp .env.example .env
```

3. Edit `.env` and add your credentials:
```env
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
FLASK_SECRET_KEY=generate_a_random_secret_key_here
FLASK_DEBUG=True
FLASK_PORT=5000
```

To generate a secure secret key, run:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Run Web Application

**Quick Start Script (Linux/Mac):**
```bash
./start_web.sh
```

**Quick Start Script (Windows):**
```batch
start_web.bat
```

**Manual Start:**
```bash
python app.py
```

The web application will be available at: `http://localhost:5000`

### Access the Web Application

1. Open your web browser
2. Navigate to `http://localhost:5000`
3. Log in with your credentials

## Docker Deployment (Web Application Only)

### Build Docker Image

```bash
docker build -t hrms-webapp .
```

### Run Docker Container

```bash
docker run -p 5000:5000 \
  -e SUPABASE_URL=your_url \
  -e SUPABASE_KEY=your_key \
  -e FLASK_SECRET_KEY=your_secret \
  hrms-webapp
```

Or use docker-compose (create `docker-compose.yml`):

```yaml
version: '3.8'
services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - SUPABASE_URL=${SUPABASE_URL}
      - SUPABASE_KEY=${SUPABASE_KEY}
      - FLASK_SECRET_KEY=${FLASK_SECRET_KEY}
    env_file:
      - .env
```

Then run:
```bash
docker-compose up
```

## Production Deployment (Web Application)

### Using Gunicorn

```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

### Platform as a Service (PaaS)

#### Heroku

```bash
# Install Heroku CLI, then:
heroku create your-hrms-app
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_KEY=your_key
heroku config:set FLASK_SECRET_KEY=your_secret
git push heroku main
```

#### Railway / Render

1. Connect your GitHub repository
2. Set environment variables in the dashboard
3. Deploy automatically

## Default Login Credentials

The default credentials depend on your Supabase setup. Check your `user_logins` table for available users.

Example:
- **Username**: admin / employee_username
- **Password**: (as configured in your database)

## Features Available

### Desktop Application
- Full offline support
- Native performance
- All HRMS features

### Web Application
- Cross-platform browser access
- Mobile-friendly responsive design
- No installation required
- Easy deployment and updates
- Core HRMS features:
  - Employee Dashboard
  - Admin Dashboard
  - Attendance Tracking
  - Leave Management
  - Payroll Access
  - Profile Management

## Troubleshooting

### Port Already in Use

**Desktop App**: Close any running PyQt5 instances

**Web App**: Change port in `.env`:
```env
FLASK_PORT=8000
```

### Cannot Connect to Database

1. Verify your Supabase credentials
2. Check your internet connection
3. Ensure your Supabase project is active
4. Check if you're using the correct URL and key (not the service role key)

### Module Not Found Errors

Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

### Session/Login Issues (Web App)

1. Clear browser cookies
2. Verify FLASK_SECRET_KEY is set in `.env`
3. Check that your username exists in the `user_logins` table

## Getting Help

- Check the documentation in `/docs` directory
- Review [WEB_APP_README.md](WEB_APP_README.md) for web-specific information
- Open an issue on GitHub

## Next Steps

- Explore the application features
- Configure leave types and policies
- Set up employee profiles
- Review payroll settings
- Customize for your organization's needs

## Choosing Between Desktop and Web

**Use Desktop App when:**
- Need offline access
- Prefer traditional desktop interface
- Single-user or local network deployment
- Need maximum performance

**Use Web App when:**
- Need remote access from anywhere
- Multiple concurrent users
- Mobile device access required
- Easy deployment and maintenance preferred
- Cloud-first infrastructure

Both versions share the same Supabase database, so you can use them interchangeably!
