# HRMS Web Application

A comprehensive Human Resource Management System with both desktop (PyQt5) and web (FastAPI) interfaces.

## 🌟 Features

- 👥 **Employee Management** - Complete employee profiles and records
- 📅 **Attendance Tracking** - Clock in/out and attendance history
- 📬 **Leave Management** - Submit, approve/reject leave requests
- 💸 **Payroll System** - Automated payroll calculations with EPF, SOCSO, EIS
- 🏛️ **LHDN Tax Integration** - Malaysian tax calculations (PCB)
- 🎁 **Bonus Management** - Employee bonuses and allowances
- 📊 **Salary History** - Track salary changes over time
- 🗂️ **Engagements** - Training courses and overseas work trips
- 📈 **Reports** - Various HR reports and analytics
- 🔐 **Role-Based Access** - Admin and employee roles

## 🚀 Quick Start

### For Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Isfahan123/HRMS_app.git
cd HRMS_app

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment (optional - defaults provided)
cp .env.example .env
nano .env  # Edit with your Supabase credentials if needed

# 4. Start the web server
python start_web.py

# 5. Open browser
# Visit: http://localhost:8000
```

### For Desktop GUI (Optional)

```bash
# Install additional desktop dependencies (requires display + Java)
pip install -r requirements-desktop.txt

# Run desktop application
python main.py
```

### For cPanel Deployment

**🎯 Quickest method** (via Git auto-deploy):

1. **cPanel → Git Version Control → Create**
   - Repository URL: `https://github.com/Isfahan123/HRMS_app.git`
   
2. **cPanel → Setup Python App → Create**
   - Python Version: `3.11`
   - Application Root: `/home/yourusername/public_html/HRMS_app`
   - Application URL: `yourdomain.com`
   - Startup File: `passenger_wsgi.py`
   - Entry Point: `application`

3. **Done!** Access at `https://yourdomain.com`

📚 **Detailed Guides**: 
- **[HOW_TO_CONNECT.md](HOW_TO_CONNECT.md)** - Quick connection guide (start here!) 🚀
- **[EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md)** - Complete Exabytes cPanel guide 🇲🇾
- [CPANEL_DEPLOYMENT.md](CPANEL_DEPLOYMENT.md) - General cPanel guide
- [CPANEL_QUICKSTART.md](CPANEL_QUICKSTART.md) - Quick reference

## 📋 Deployment Options

### 1. cPanel Hosting ⭐ (Recommended for shared hosting)

Perfect for traditional web hosting with cPanel.

- **Quick Connection Guide**: [HOW_TO_CONNECT.md](HOW_TO_CONNECT.md) 🚀
- **Exabytes Hosting (Malaysia)**: [EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md) 🇲🇾
- **General cPanel**: [CPANEL_DEPLOYMENT.md](CPANEL_DEPLOYMENT.md)
- **Quick Reference**: [CPANEL_QUICKSTART.md](CPANEL_QUICKSTART.md)
- **Setup Script**: `./setup_cpanel.sh`

**Files for cPanel**:
- `.htaccess` - Apache/Passenger configuration
- `.cpanel.yml` - Auto-deployment configuration
- `passenger_wsgi.py` - WSGI entry point

### 2. Traditional Server (VPS/Dedicated)

Deploy on Ubuntu, Debian, CentOS, etc.

- **Documentation**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **Method**: Nginx + Systemd service
- **Suitable for**: VPS, DigitalOcean, AWS EC2, Linode

### 3. Docker

Containerized deployment for any platform.

- **Documentation**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **Files**: Dockerfile and docker-compose.yml included in docs
- **Suitable for**: Docker-capable hosts, Kubernetes

### 4. Cloud Platforms

Easy deployment to cloud platforms.

- **Platforms**: Heroku, Railway, Render
- **Documentation**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
- **Method**: Git push deployment

### 5. Local Desktop

Run the PyQt5 desktop application.

```bash
python main.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file (or use the provided defaults):

```env
# Supabase Configuration (Database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Web Server Configuration
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_RELOAD=false

# Environment
ENVIRONMENT=production
```

**Note**: The application includes default Supabase credentials for quick testing. For production, use your own credentials.

## 📖 Documentation

### Getting Started
- [QUICKSTART_WEB.md](QUICKSTART_WEB.md) - Quick start for web interface
- [START_HERE.md](START_HERE.md) - Implementation verification guide
- [WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md) - Web UI user guide

### Deployment
- **[HOW_TO_CONNECT.md](HOW_TO_CONNECT.md)** - Quick connection guide (start here!) 🚀
- **[EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md)** - Complete guide for Exabytes hosting 🇲🇾
- **[EXABYTES_TROUBLESHOOTING.md](EXABYTES_TROUBLESHOOTING.md)** - Fix deployment issues 🔧
- **[CPANEL_DEPLOYMENT.md](CPANEL_DEPLOYMENT.md)** - Complete cPanel deployment guide
- **[CPANEL_QUICKSTART.md](CPANEL_QUICKSTART.md)** - Quick reference for cPanel
- [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md) - General deployment guide
- [setup_cpanel.sh](setup_cpanel.sh) - Automated setup script for cPanel

### Development
- [docs/WEB_APPLICATION_GUIDE.md](docs/WEB_APPLICATION_GUIDE.md) - Web app architecture
- [docs/WEB_VS_DESKTOP.md](docs/WEB_VS_DESKTOP.md) - Comparison of interfaces
- [web/BACKEND_INTEGRATION_GUIDE.md](web/BACKEND_INTEGRATION_GUIDE.md) - API integration

## 🏗️ Architecture

```
HRMS_app/
├── web_app.py              # FastAPI main application
├── passenger_wsgi.py       # WSGI adapter for cPanel/Passenger
├── start_web.py            # Development server launcher
├── main.py                 # Desktop application (PyQt5)
├── .htaccess               # Apache/cPanel configuration
├── .cpanel.yml             # cPanel deployment automation
├── requirements.txt          # Python dependencies (web-compatible)
├── requirements-web.txt      # Web-only dependencies (same as requirements.txt)
├── requirements-desktop.txt  # Desktop GUI dependencies (PyQt5, tabula-py)
├── .env                    # Environment configuration
│
├── core/                   # Business logic
├── services/               # Database services (Supabase)
├── gui/                    # Desktop GUI components
│
├── web/
│   ├── templates/          # HTML templates (Jinja2)
│   ├── static/             # CSS, JavaScript, images
│   │   ├── css/
│   │   └── js/
│   └── README.md
│
└── docs/                   # Documentation
```

## 🌐 Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.8+)
- **Database**: Supabase (PostgreSQL)
- **Authentication**: Bcrypt
- **WSGI Server**: Passenger (cPanel) / Uvicorn (development)

### Frontend
- **Templates**: Jinja2
- **Styling**: Custom CSS with modern gradients
- **JavaScript**: Vanilla JS (no framework dependencies)
- **Icons**: Unicode emojis

### Desktop
- **Framework**: PyQt5
- **Reports**: ReportLab (PDF generation)

## 📊 API Documentation

Once the server is running, interactive API documentation is available at:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🧪 Testing

### Health Check

```bash
curl http://localhost:8000/health
```

Response:
```json
{"status": "healthy", "timestamp": "2024-11-21T..."}
```

### API Endpoints

Test login:
```bash
curl -X POST http://localhost:8000/api/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```

## 🔐 Default Credentials

For testing (change these in production!):

- **Username**: Check with your administrator
- **Password**: Check with your administrator

## 📝 Requirements

- **Python**: 3.8 or higher
- **Database**: Supabase account (free tier available)
- **For Desktop**: PyQt5 and system GUI support (install with `pip install -r requirements-desktop.txt`)
- **For Web**: Modern web browser (Chrome, Firefox, Safari, Edge)

## 🆘 Troubleshooting

### Web Application Won't Start

```bash
# Check dependencies
pip install -r requirements.txt

# Verify imports
python3 -c "from web_app import app; print('OK')"

# Check environment
cat .env
```

### cPanel Deployment Issues

```bash
# Restart application
touch passenger_wsgi.py

# Check logs
cat ~/public_html/HRMS_app/log/passenger.log

# Run setup script
./setup_cpanel.sh
```

### Database Connection Errors

- Verify `.env` has correct Supabase URL and key
- Check internet connectivity
- Verify Supabase project is active

See [TROUBLESHOOTING_UI.md](TROUBLESHOOTING_UI.md) for more details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📜 License

This project is private and proprietary. All rights reserved.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Supabase for the backend-as-a-service platform
- PyQt5 for the desktop GUI framework
- The Python community for amazing tools and libraries

## 📞 Support

- **Documentation**: Check the `docs/` folder
- **Issues**: Check logs and troubleshooting guides
- **Questions**: Review the comprehensive guides provided

---

## 🎯 Next Steps After Deployment

1. ✅ Test login with credentials
2. ✅ Configure leave types and settings
3. ✅ Add employee records
4. ✅ Run a test payroll cycle
5. ✅ Train users on the interface
6. ✅ Enable SSL/HTTPS (recommended)
7. ✅ Set up regular backups
8. ✅ Configure monitoring

---

**Made with ❤️ for efficient HR management**

For questions about deployment, see the appropriate deployment guide:
- **Quick Connection Guide**: [HOW_TO_CONNECT.md](HOW_TO_CONNECT.md) - Start here! 🚀
- **Exabytes (Malaysia)**: [EXABYTES_DEPLOYMENT.md](EXABYTES_DEPLOYMENT.md) 🇲🇾
- **General cPanel**: [CPANEL_DEPLOYMENT.md](CPANEL_DEPLOYMENT.md) or [CPANEL_QUICKSTART.md](CPANEL_QUICKSTART.md)
- **Other platforms**: [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)
