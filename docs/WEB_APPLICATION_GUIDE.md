# HRMS Web Application Guide

## Overview

The HRMS application now provides two interfaces:

1. **Desktop Application** - PyQt5-based GUI (existing)
2. **Web Application** - HTML/JavaScript-based GUI (new)

Both interfaces share the same backend business logic and database, ensuring consistency across platforms.

## Architecture

### Separation of Concerns

The web application follows a clean architecture separating:

- **GUI Layer**: HTML templates (`/web/templates/`)
- **Presentation Logic**: JavaScript files (`/web/static/js/`)
- **Styling**: CSS files (`/web/static/css/`)
- **API Layer**: FastAPI backend (`web_app.py`)
- **Business Logic**: Python functions in `/core/` and `/services/` (shared with desktop)

### Request Flow

```
Browser (HTML/JS) → FastAPI (Python) → Services/Core → Supabase
     ↑                                                      ↓
     └──────────────── JSON Response ──────────────────────┘
```

## Getting Started

### Prerequisites

Install dependencies:
```bash
pip install -r requirements.txt
```

Key web packages:
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `python-multipart` - Form data handling

### Starting the Web Server

**Option 1: Using the startup script (recommended)**
```bash
python start_web.py
```

**Option 2: Using uvicorn directly**
```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reload during development.

**Option 3: Using the FastAPI app directly**
```bash
python web_app.py
```

### Accessing the Application

- **Main Application**: http://localhost:8000
- **API Documentation (Swagger)**: http://localhost:8000/docs
- **API Documentation (ReDoc)**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## Features

### Implemented Features

#### 1. Authentication
- Login with username/password
- Session management using browser sessionStorage
- Role-based routing (admin vs employee)
- Account lockout handling

#### 2. Employee Dashboard
- **Home Tab**: Summary of attendance and leave requests
- **Profile Tab**: Employee information display
- **Attendance Tab**: Full attendance history with table view
- **Leave Tab**: Leave requests with status tracking
- **Payroll Tab**: Placeholder for future implementation
- **Engagements Tab**: Placeholder for training and trips

#### 3. Admin Dashboard
- **Employees Tab**: Complete employee list with details
- **Attendance Tab**: Placeholder for attendance management
- **Leave Tab**: Placeholder for leave approval
- **Payroll Tab**: Placeholder for payroll processing
- **Bonus Tab**: Placeholder for bonus management

### API Endpoints

All API endpoints are documented at `/docs` (Swagger UI):

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/login` | Authenticate user |
| GET | `/api/employee/{email}` | Get employee details |
| GET | `/api/attendance/{email}` | Get attendance records |
| GET | `/api/leave-requests/{email}` | Get leave requests |
| GET | `/api/employees` | List all employees |
| GET | `/health` | Health check |

## Development

### Adding a New Page

1. **Create HTML template** in `/web/templates/`:
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <title>My Page</title>
    <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
    <div id="content"></div>
    <script src="/static/js/mypage.js"></script>
</body>
</html>
```

2. **Create JavaScript file** in `/web/static/js/`:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    // Your page logic here
    loadData();
});

async function loadData() {
    const response = await fetch('/api/your-endpoint');
    const data = await response.json();
    // Update DOM
}
```

3. **Add route** in `web_app.py`:
```python
@app.get("/mypage", response_class=HTMLResponse)
async def my_page(request: Request):
    return templates.TemplateResponse("mypage.html", {"request": request})
```

### Adding a New API Endpoint

Add to `web_app.py`:

```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    # Reuse existing business logic
    from services.supabase_service import your_function
    
    try:
        result = your_function()
        return {"success": True, "data": result}
    except Exception as e:
        return {"success": False, "message": str(e)}
```

### Reusing Business Logic

The web application reuses all existing Python functions:

```python
# In web_app.py
from services.supabase_service import (
    login_user_by_username,  # Authentication
    get_attendance_history,  # Attendance data
    fetch_user_leave_requests  # Leave data
)

from core.employee_service import (
    calculate_cumulative_service  # Employee calculations
)

# Use in API endpoints
@app.get("/api/example")
async def example():
    data = get_attendance_history(email)
    return {"data": data}
```

## File Structure

```
HRMS_app/
├── web_app.py                  # FastAPI application entry point
├── start_web.py               # Web server startup script
├── web/
│   ├── README.md              # Web app documentation
│   ├── templates/             # HTML templates (Jinja2)
│   │   ├── login.html
│   │   ├── dashboard.html
│   │   └── admin_dashboard.html
│   └── static/                # Static files
│       ├── css/
│       │   └── style.css      # Main stylesheet
│       └── js/
│           ├── login.js       # Login logic
│           ├── dashboard.js   # Employee dashboard logic
│           └── admin_dashboard.js  # Admin dashboard logic
├── services/                  # Shared business logic
├── core/                      # Shared core functions
└── data/                      # Shared data/config
```

## Testing

### Manual Testing

1. Start the server:
```bash
python start_web.py
```

2. Open browser to http://localhost:8000

3. Test login with valid credentials

4. Navigate through dashboard tabs

5. Check browser console for errors (F12)

### API Testing

Use the built-in Swagger UI:
1. Navigate to http://localhost:8000/docs
2. Test endpoints directly from the interface
3. View request/response schemas

Or use curl:
```bash
# Health check
curl http://localhost:8000/health

# Login
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"test","password":"test123"}'
```

## Styling

### CSS Structure

The main stylesheet (`/web/static/css/style.css`) includes:

- **Global styles**: Reset, body, fonts
- **Login page**: Form styling, button effects
- **Dashboard**: Header, tabs, content areas
- **Components**: Tables, cards, buttons
- **Responsive**: Mobile-friendly media queries

### Customization

Modify colors, fonts, and layout in `style.css`:

```css
/* Primary colors */
body {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

/* Or use custom colors */
body {
    background: linear-gradient(135deg, #your-color1 0%, #your-color2 100%);
}
```

## Security Considerations

### Current Implementation

- ✅ Password hashing with bcrypt
- ✅ SQL injection prevention (Supabase client)
- ✅ HTTPS support (via reverse proxy)

### Recommendations for Production

1. **Authentication**
   - Implement JWT tokens instead of sessionStorage
   - Add token refresh mechanism
   - Set secure httpOnly cookies

2. **CORS Configuration**
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

3. **Rate Limiting**
```python
from slowapi import Limiter
limiter = Limiter(key_func=lambda: "global")

@app.post("/api/login")
@limiter.limit("5/minute")
async def login():
    ...
```

4. **HTTPS**
   - Use a reverse proxy (nginx, Caddy)
   - Or configure uvicorn with SSL:
```bash
uvicorn web_app:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
```

## Deployment

### Development
```bash
python start_web.py
```

### Production

**Option 1: Using Gunicorn + Uvicorn workers**
```bash
pip install gunicorn
gunicorn web_app:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

**Option 2: Using systemd service**

Create `/etc/systemd/system/hrms-web.service`:
```ini
[Unit]
Description=HRMS Web Application
After=network.target

[Service]
User=www-data
WorkingDirectory=/path/to/HRMS_app
ExecStart=/usr/bin/python3 /path/to/HRMS_app/start_web.py
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable hrms-web
sudo systemctl start hrms-web
```

**Option 3: Using Docker**

Create `Dockerfile`:
```dockerfile
FROM python:3.12
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["python", "start_web.py"]
```

Build and run:
```bash
docker build -t hrms-web .
docker run -p 8000:8000 hrms-web
```

## Troubleshooting

### Common Issues

**1. Port already in use**
```bash
# Find process using port 8000
lsof -i :8000
# Or on Windows
netstat -ano | findstr :8000

# Use different port
uvicorn web_app:app --port 8001
```

**2. Module import errors**
```bash
# Ensure you're in the repo root
cd /path/to/HRMS_app
python web_app.py

# Check Python path
python -c "import sys; print('\n'.join(sys.path))"
```

**3. Database connection errors**
- Verify `.env` file exists with Supabase credentials
- Check Supabase URL and API key
- Ensure network connectivity

**4. Static files not loading**
- Check file paths in HTML templates
- Verify `/web/static/` directory structure
- Check browser console for 404 errors

## Comparison: Desktop vs Web

| Feature | Desktop (PyQt5) | Web (HTML/JS) |
|---------|----------------|---------------|
| **Distribution** | Executable file | Web browser |
| **Installation** | Download & install | Just open URL |
| **Updates** | Re-download/reinstall | Refresh browser |
| **Platform** | Windows/Mac/Linux | Any device with browser |
| **Offline** | Yes | No (requires server) |
| **GUI** | PyQt5 widgets | HTML/CSS |
| **Client Logic** | Python | JavaScript |
| **Server Logic** | Python | Python (same code) |
| **Database** | Supabase | Supabase (shared) |
| **Performance** | Native | Network dependent |
| **Multi-user** | One per install | Unlimited simultaneous |

## Future Enhancements

### Short-term (Planned)
- [ ] Complete all dashboard tabs (Payroll, Engagements, etc.)
- [ ] Add form validation (client + server)
- [ ] Implement JWT authentication
- [ ] Add file upload functionality
- [ ] Implement real-time updates with WebSocket

### Medium-term
- [ ] Mobile-responsive design improvements
- [ ] Progressive Web App (PWA) support
- [ ] Offline mode with service workers
- [ ] Export functionality (PDF, Excel)
- [ ] Advanced search and filtering

### Long-term
- [ ] Admin configuration UI
- [ ] Report builder
- [ ] Dashboard customization
- [ ] Multi-language support
- [ ] Integration with third-party services

## Support

For issues or questions:
1. Check this documentation
2. Review API docs at `/docs`
3. Check browser console for errors
4. Review server logs
5. Check existing issues in the repository

## Contributing

When adding features:
1. Keep HTML, CSS, and JS separate
2. Reuse existing Python business logic
3. Follow RESTful API conventions
4. Document new endpoints
5. Test on multiple browsers
6. Ensure mobile responsiveness
