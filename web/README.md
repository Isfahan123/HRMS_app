# HRMS Web Application

This directory contains the web-based version of the HRMS application, separating the GUI (HTML) from the business logic (JavaScript/Python).

## Architecture

The web application follows a modern architecture:

- **Frontend (GUI)**: HTML templates with vanilla JavaScript
  - `/web/templates/` - HTML pages (Jinja2 templates)
  - `/web/static/css/` - CSS stylesheets
  - `/web/static/js/` - JavaScript logic for client-side functionality

- **Backend (API)**: FastAPI (Python) with existing business logic
  - `/web_app.py` - Main FastAPI application server
  - Reuses existing services from `/services/` directory
  - Reuses existing business logic from `/core/` directory

## Features

### Current Implementation

1. **Login Page** (`/`)
   - HTML form for username/password
   - JavaScript handles form submission and API calls
   - Session management using browser sessionStorage

2. **Employee Dashboard** (`/dashboard`)
   - Profile information
   - Attendance history
   - Leave requests
   - Tab-based navigation

3. **Admin Dashboard** (`/admin-dashboard`)
   - Employee list management
   - Administrative functions
   - Tab-based navigation

### API Endpoints

- `POST /api/login` - User authentication
- `GET /api/employee/{email}` - Get employee data
- `GET /api/attendance/{email}` - Get attendance history
- `GET /api/leave-requests/{email}` - Get leave requests
- `GET /api/employees` - List all employees (admin)
- `GET /health` - Health check endpoint

## Running the Web Application

### Prerequisites

Install the required dependencies:

```bash
pip install -r requirements.txt
```

The following packages are needed for the web version:
- `fastapi` - Modern web framework
- `uvicorn` - ASGI server
- `jinja2` - Template engine
- `python-multipart` - Form data handling

### Start the Server

```bash
python web_app.py
```

The application will be available at: `http://localhost:8000`

Or run with custom host/port:

```bash
uvicorn web_app:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag enables auto-reload on code changes (useful for development).

## File Structure

```
web/
├── README.md                    # This file
├── templates/                   # HTML templates
│   ├── login.html              # Login page
│   ├── dashboard.html          # Employee dashboard
│   └── admin_dashboard.html    # Admin dashboard
└── static/                      # Static files
    ├── css/
    │   └── style.css           # Main stylesheet
    └── js/
        ├── login.js            # Login page logic
        ├── dashboard.js        # Employee dashboard logic
        └── admin_dashboard.js  # Admin dashboard logic
```

## Design Principles

1. **Separation of Concerns**
   - HTML for structure (GUI)
   - CSS for styling
   - JavaScript for client-side logic
   - Python for server-side business logic

2. **Code Reuse**
   - Backend API reuses existing functions from `/services/` and `/core/`
   - No duplication of business logic
   - Same database connections and authentication

3. **Modern Web Standards**
   - Responsive design
   - RESTful API
   - Session-based authentication
   - AJAX for asynchronous data loading

## Development

### Adding New Pages

1. Create HTML template in `/web/templates/`
2. Create corresponding JavaScript in `/web/static/js/`
3. Add route in `/web_app.py`
4. Add API endpoints as needed

### Adding New API Endpoints

Add new endpoints in `/web_app.py`:

```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    # Reuse existing services/core functions
    return {"data": "your data"}
```

### Styling

Modify `/web/static/css/style.css` to customize the appearance.

## Comparison with Desktop Version

| Feature | Desktop (PyQt5) | Web (HTML/JS) |
|---------|----------------|---------------|
| GUI | PyQt5 widgets | HTML/CSS |
| Client Logic | Python | JavaScript |
| Server Logic | Python | Python (same) |
| Distribution | Standalone executable | Web browser |
| Updates | Reinstall | Refresh browser |
| Platform | Windows/Mac/Linux | Any with browser |

## Security Notes

- Passwords are handled securely using bcrypt (same as desktop version)
- Session data stored in browser sessionStorage
- **TODO**: Add proper authentication tokens (JWT) instead of sessionStorage
- **TODO**: Add HTTPS support for production
- **TODO**: Add CORS configuration for production

## Future Enhancements

- [ ] Implement JWT token-based authentication
- [ ] Add WebSocket support for real-time updates
- [ ] Complete remaining tabs (Payroll, Engagements, etc.)
- [ ] Add form validation on client and server side
- [ ] Implement file upload for documents
- [ ] Add export functionality (PDF, Excel)
- [ ] Mobile-responsive improvements
- [ ] Add unit tests for API endpoints
- [ ] Add integration tests

## Troubleshooting

### Port Already in Use

If port 8000 is already in use, specify a different port:

```bash
python -c "import uvicorn; from web_app import app; uvicorn.run(app, host='0.0.0.0', port=8001)"
```

### Module Import Errors

Make sure you're running from the repository root:

```bash
cd /path/to/HRMS_app
python web_app.py
```

### Database Connection Issues

Ensure your `.env` file has the correct Supabase credentials (same as desktop version).
