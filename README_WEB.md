# HRMS Web Application

This document describes the HTML web application version of the HRMS system, converted from the original PyQt5 desktop application.

## Overview

The HRMS application has been converted from a PyQt5 desktop application to a Flask-based web application with HTML/CSS/JavaScript frontend.

## Architecture

### Backend (Flask)
- **Framework**: Flask 3.0.0
- **Entry Point**: `app.py`
- **Authentication**: Session-based authentication
- **Database**: Supabase (unchanged from original)
- **API Routes**: RESTful API endpoints for data access

### Frontend (HTML/CSS/JavaScript)
- **Templates**: Jinja2 templates in `/templates` directory
- **Styling**: Custom CSS in `/static/css/style.css`
- **JavaScript**: Vanilla JavaScript in `/static/js/main.js`
- **Layout**: Responsive design using CSS Grid and Flexbox

## File Structure

```
HRMS_app/
├── app.py                          # Flask application entry point
├── main.py                         # Original PyQt5 application (deprecated)
├── templates/                      # HTML templates
│   ├── base.html                  # Base template with common layout
│   ├── login.html                 # Login page
│   ├── dashboard.html             # Employee dashboard
│   ├── admin_dashboard.html       # Admin dashboard
│   ├── employee_profile.html      # Employee profile tab
│   ├── employee_attendance.html   # Employee attendance tab
│   ├── employee_leave.html        # Employee leave request tab
│   ├── employee_payroll.html      # Employee payroll tab
│   └── employee_engagements.html  # Employee engagements tab
├── static/                        # Static files
│   ├── css/
│   │   └── style.css             # Main stylesheet
│   ├── js/
│   │   └── main.js               # Main JavaScript file
│   └── img/                      # Images (if any)
├── gui/                          # Original PyQt5 GUI files (66 files)
├── services/                     # Backend services (Supabase, etc.)
├── core/                         # Core business logic
└── requirements.txt              # Python dependencies

```

## Conversion Mapping

### Original PyQt5 → HTML Pages

| PyQt5 File | HTML Template | Description |
|------------|---------------|-------------|
| `main.py` | `app.py` | Main application entry point |
| `gui/login_window.py` | `templates/login.html` | Login interface |
| `gui/dashboard_window.py` | `templates/dashboard.html` | Employee dashboard |
| `gui/admin_dashboard_window.py` | `templates/admin_dashboard.html` | Admin dashboard |
| `gui/employee_profile_tab.py` | `templates/employee_profile.html` | Employee profile |
| `gui/employee_attendance_tab.py` | `templates/employee_attendance.html` | Attendance tracking |
| `gui/employee_leave_tab.py` | `templates/employee_leave.html` | Leave requests |
| `gui/employee_payroll_tab.py` | `templates/employee_payroll.html` | Payroll information |
| `gui/employee_engagements_tab.py` | `templates/employee_engagements.html` | Training & trips |

### UI Components Converted

1. **QWidget → HTML div elements**
2. **QLabel → HTML span/label elements**
3. **QLineEdit → HTML input elements**
4. **QPushButton → HTML button elements**
5. **QTableWidget → HTML table elements**
6. **QTabWidget → JavaScript tab switching**
7. **QMessageBox → JavaScript alerts/modals**
8. **QDialog → HTML modals**

## Installation & Setup

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Supabase account and credentials

### Installation Steps

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd HRMS_app
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   Create a `.env` file with:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   FLASK_SECRET_KEY=your_secret_key
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open your browser and navigate to:
   ```
   http://localhost:5000
   ```

## Features

### Employee Features
- ✅ Login/Authentication
- ✅ Profile Management
- ✅ Attendance Tracking (Check-in/Check-out)
- ✅ Leave Request Management
- ✅ Payroll & Payslip Viewing
- ✅ Training Course Enrollment
- ✅ Overseas Trip Requests

### Admin Features
- ✅ Dashboard with System Overview
- ✅ Employee Profile Management
- ✅ Attendance Management
- ✅ Leave Request Approval/Rejection
- ✅ Payroll Processing
- ✅ Salary History Management
- ✅ Bonus Management
- ✅ Training Course Management
- ✅ Overseas Trip Management
- ✅ Tax Configuration

## API Endpoints

### Authentication
- `POST /login` - User login
- `GET /logout` - User logout

### Employee APIs
- `GET /api/attendance` - Get attendance history
- `GET /api/leave-requests` - Get leave requests
- `POST /api/leave-request` - Submit leave request
- `GET /api/payroll` - Get payroll information
- `GET /api/training` - Get training courses
- `GET /api/trips` - Get overseas trips

### Admin APIs
- `GET /api/admin/employees` - List all employees
- `GET /api/admin/pending-leaves` - Get pending leave requests
- `POST /api/admin/approve-leave` - Approve leave request
- `POST /api/admin/reject-leave` - Reject leave request

## Styling

The application uses a modern, responsive design with:
- **Color Scheme**: Purple gradient (#667eea to #764ba2)
- **Typography**: System fonts with fallbacks
- **Layout**: Flexbox and CSS Grid
- **Components**: Custom styled buttons, tables, cards, and modals
- **Responsive**: Mobile-friendly design with media queries

## Browser Support

- ✅ Chrome/Edge (Latest)
- ✅ Firefox (Latest)
- ✅ Safari (Latest)
- ⚠️ Internet Explorer (Not supported)

## Development

### Adding New Pages

1. Create HTML template in `/templates`
2. Add route in `app.py`
3. Add API endpoints if needed
4. Style in `/static/css/style.css`
5. Add JavaScript in `/static/js/main.js` or inline

### Running in Development Mode

```bash
export FLASK_ENV=development
python app.py
```

### Running in Production

Use a production WSGI server like Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

## Migration Notes

### Differences from Desktop Version

1. **Session Management**: Web-based sessions instead of in-memory state
2. **Real-time Updates**: Requires API polling or WebSocket implementation
3. **File Dialogs**: Replaced with HTML file inputs and modals
4. **Offline Access**: Requires additional service worker implementation
5. **Native Features**: Some desktop-specific features may need alternatives

### Advantages of Web Version

- ✅ Cross-platform compatibility (Windows, Mac, Linux)
- ✅ No installation required for users
- ✅ Centralized deployment and updates
- ✅ Accessible from any device with a browser
- ✅ Easier to scale horizontally
- ✅ Better for remote work scenarios

### Limitations

- ⚠️ Requires internet connection
- ⚠️ Browser compatibility considerations
- ⚠️ Security considerations for web deployment
- ⚠️ No native OS integration

## Security Considerations

1. **HTTPS**: Always use HTTPS in production
2. **Session Security**: Use secure session cookies
3. **CSRF Protection**: Implement CSRF tokens
4. **Input Validation**: Validate all user inputs
5. **SQL Injection**: Use parameterized queries (Supabase handles this)
6. **XSS Protection**: Escape user-generated content
7. **Rate Limiting**: Implement API rate limiting
8. **Authentication**: Use strong password policies

## Testing

### Manual Testing
1. Test all login scenarios
2. Test each tab functionality
3. Test form submissions
4. Test API endpoints
5. Test responsive design on different devices

### Automated Testing (To be implemented)
- Unit tests for backend routes
- Integration tests for API endpoints
- End-to-end tests for user workflows
- Browser compatibility testing

## Troubleshooting

### Common Issues

**Issue**: Application won't start
- **Solution**: Check that all dependencies are installed and `.env` file is configured

**Issue**: Login fails
- **Solution**: Verify Supabase credentials and database connectivity

**Issue**: Styles not loading
- **Solution**: Check that static files are being served correctly

**Issue**: API calls failing
- **Solution**: Check browser console for errors and verify API endpoints

## Future Enhancements

- [ ] Real-time notifications using WebSockets
- [ ] Progressive Web App (PWA) support for offline access
- [ ] Advanced reporting and analytics
- [ ] Mobile native app using React Native
- [ ] Multi-language support
- [ ] Dark mode toggle
- [ ] Export data to Excel/PDF
- [ ] Email notifications
- [ ] Two-factor authentication
- [ ] Audit logging

## Contributing

When contributing to the web version:
1. Follow the existing code structure
2. Maintain consistent styling
3. Test across multiple browsers
4. Update documentation
5. Write clean, commented code

## License

[Same as original project]

## Support

For issues or questions about the web application:
- Create an issue on GitHub
- Contact the development team
- Check the documentation

---

**Note**: This web application is a conversion of the original PyQt5 desktop application. While it maintains the core functionality, some features may differ in implementation details.
