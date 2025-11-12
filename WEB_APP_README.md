# HRMS Web Application

This is the web-based version of the HRMS (Human Resources Management System) application, converted from the PyQt5 desktop application.

## Overview

The HRMS web application provides the same core functionality as the desktop version, but accessible through a web browser. It's built using Flask and maintains compatibility with the existing Supabase backend.

## Features

### Employee Dashboard
- View personal profile information
- Check attendance status
- View leave balance and history
- Submit leave requests
- Access payroll information and payslips

### Admin Dashboard
- Employee management (add, edit, view)
- Attendance tracking and reporting
- Leave request approval and management
- Payroll processing
- Generate reports and analytics

## Technology Stack

- **Backend**: Flask (Python web framework)
- **Frontend**: Bootstrap 5, jQuery, Font Awesome
- **Database**: Supabase (PostgreSQL)
- **Session Management**: Flask-Session
- **Authentication**: bcrypt
- **PDF Generation**: ReportLab (for payslips)

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)
- Supabase account and credentials

### Setup Steps

1. **Clone the repository** (if not already done):
   ```bash
   git clone <repository-url>
   cd HRMS_app
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv venv
   
   # On Windows:
   venv\Scripts\activate
   
   # On Linux/Mac:
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**:
   Create a `.env` file in the root directory with your Supabase credentials:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   FLASK_SECRET_KEY=your_secret_key_here
   FLASK_DEBUG=True
   FLASK_PORT=5000
   ```

## Running the Application

### Development Mode

Run the Flask development server:
```bash
python app.py
```

The application will be available at: `http://localhost:5000`

### Production Mode

For production deployment, use Gunicorn:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

Or with more workers and timeout:
```bash
gunicorn -w 4 -b 0.0.0.0:5000 --timeout 120 app:app
```

## Deployment Options

### 1. Traditional Server (VPS/Dedicated)
- Install Python, pip, and dependencies
- Use Nginx as reverse proxy
- Use Gunicorn as WSGI server
- Set up SSL certificate with Let's Encrypt

### 2. Platform as a Service (PaaS)
- **Heroku**: Deploy with Procfile
- **Railway**: Direct deployment from Git
- **Render**: Auto-deploy from GitHub
- **DigitalOcean App Platform**: One-click deployment

### 3. Docker Container
A Dockerfile is provided for containerized deployment:
```bash
docker build -t hrms-webapp .
docker run -p 5000:5000 hrms-webapp
```

## File Structure

```
HRMS_app/
├── app.py                 # Main Flask application
├── templates/             # HTML templates
│   ├── base.html         # Base template with navigation
│   ├── login.html        # Login page
│   ├── dashboard.html    # Employee dashboard
│   ├── admin_dashboard.html  # Admin dashboard
│   └── error.html        # Error page
├── static/               # Static assets
│   ├── css/
│   │   └── style.css    # Custom CSS
│   └── js/
│       └── main.js      # Custom JavaScript
├── core/                 # Business logic (reused from desktop app)
├── services/             # Supabase services (reused from desktop app)
└── requirements.txt      # Python dependencies
```

## Key Differences from Desktop App

### Advantages of Web App
1. **Cross-platform**: Works on any device with a web browser
2. **No installation**: Access from anywhere without installing software
3. **Easy updates**: Update once on the server, all users get the latest version
4. **Mobile-friendly**: Responsive design works on phones and tablets
5. **Multi-user**: Better concurrent access handling

### Desktop App Advantages
1. **Offline access**: Works without internet connection
2. **Native performance**: Better for resource-intensive operations
3. **System integration**: Can integrate with local files and hardware

## Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Session Security**: Sessions expire after 8 hours of inactivity
3. **Password Hashing**: Uses bcrypt for password storage
4. **CSRF Protection**: Implement CSRF tokens for forms
5. **Environment Variables**: Never commit secrets to version control

## API Endpoints

The web app provides REST API endpoints for AJAX requests:

- `GET /api/profile` - Get current user profile
- `GET /api/employees` - Get all employees (admin only)
- `GET /api/leave/types` - Get leave types

More endpoints can be added as needed for specific features.

## Development Guide

### Adding New Features

1. **Add route in app.py**:
   ```python
   @app.route('/new-feature')
   @login_required
   def new_feature():
       return render_template('new_feature.html')
   ```

2. **Create template**:
   Create `templates/new_feature.html` extending `base.html`

3. **Add API endpoint if needed**:
   ```python
   @app.route('/api/new-data')
   @login_required
   def api_new_data():
       return jsonify({'data': 'value'})
   ```

### Testing

Test the application locally:
```bash
# Run the app
python app.py

# Access in browser
http://localhost:5000
```

## Troubleshooting

### Port Already in Use
Change the port in `.env` or command line:
```bash
FLASK_PORT=8000 python app.py
```

### Database Connection Issues
- Verify Supabase credentials in `.env`
- Check network connectivity
- Ensure Supabase project is active

### Session Issues
- Clear browser cookies
- Check FLASK_SECRET_KEY is set
- Verify session configuration

## Support

For issues, questions, or contributions:
1. Check existing documentation
2. Review error logs
3. Open an issue in the repository

## License

Same license as the original HRMS desktop application.

## Migration Notes

Both desktop and web versions can coexist and share the same Supabase database. Users can choose which interface they prefer, or use both depending on their needs.

The core business logic in `/core` and `/services` directories is shared between both versions, ensuring consistency in calculations and data handling.
