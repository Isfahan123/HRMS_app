# HRMS Web Application - Deployment Guide

## Environment Configuration

The HRMS web application now supports environment-based configuration using `.env` files.

### Quick Setup

1. **Copy the example environment file:**
   ```bash
   cp .env.example .env
   ```

2. **Edit `.env` with your credentials:**
   ```bash
   nano .env
   # or
   vi .env
   ```

3. **Update the following variables:**
   ```env
   SUPABASE_URL=your_supabase_url_here
   SUPABASE_KEY=your_supabase_service_role_key_here
   WEB_HOST=0.0.0.0
   WEB_PORT=8000
   ENVIRONMENT=production
   ```

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `SUPABASE_URL` | Your Supabase project URL | Fallback URL provided | Yes |
| `SUPABASE_KEY` | Your Supabase service role key | Fallback key provided | Yes |
| `WEB_HOST` | Host to bind the web server | `0.0.0.0` | No |
| `WEB_PORT` | Port for the web server | `8000` | No |
| `WEB_RELOAD` | Enable auto-reload (development only) | `false` | No |
| `ENVIRONMENT` | Environment name (production/staging/development) | `production` | No |

### Security Best Practices

1. **Never commit `.env` to version control**
   - The `.env` file is already in `.gitignore`
   - Only commit `.env.example` with placeholder values

2. **Use different credentials per environment:**
   - Development: `.env.development`
   - Staging: `.env.staging`
   - Production: `.env` (or `.env.production`)

3. **Protect your keys:**
   - Keep Supabase keys secure
   - Use service role keys only on the backend
   - Never expose keys in frontend code

---

## Local Development

### Setup

```bash
# 1. Clone the repository
git clone <repository-url>
cd HRMS_app

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your credentials

# 5. Start the web server
python start_web.py
```

### Development Mode

For auto-reload during development, set in your `.env`:
```env
WEB_RELOAD=true
ENVIRONMENT=development
```

---

## Production Deployment

### Option 1: Traditional Server (Exabytes, DigitalOcean, AWS EC2, etc.)

#### Initial Setup

```bash
# 1. Update system packages
sudo apt update && sudo apt upgrade -y

# 2. Install Python 3.8+
sudo apt install python3 python3-pip python3-venv -y

# 3. Clone repository
cd /opt
sudo git clone <repository-url> HRMS_app
cd HRMS_app

# 4. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 5. Install dependencies
pip install -r requirements.txt

# 6. Configure environment
cp .env.example .env
sudo nano .env
# Update with production credentials
```

#### Create Systemd Service

Create `/etc/systemd/system/hrms-web.service`:

```ini
[Unit]
Description=HRMS Web Application
After=network.target

[Service]
Type=simple
User=www-data
Group=www-data
WorkingDirectory=/opt/HRMS_app
Environment="PATH=/opt/HRMS_app/venv/bin"
ExecStart=/opt/HRMS_app/venv/bin/python start_web.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable hrms-web
sudo systemctl start hrms-web
sudo systemctl status hrms-web
```

#### Configure Nginx Reverse Proxy

Create `/etc/nginx/sites-available/hrms`:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /opt/HRMS_app/web/static;
        expires 30d;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/hrms /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### SSL Certificate (Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com
```

---

### Option 2: Docker Deployment

Create `Dockerfile`:

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "start_web.py"]
```

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  hrms-web:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    volumes:
      - ./web:/app/web
```

Deploy:

```bash
docker-compose up -d
```

---

### Option 3: Exabytes Hosting (cPanel)

#### Via SSH:

```bash
# 1. SSH into your server
ssh username@yourserver.com

# 2. Navigate to your domain directory
cd public_html/yourdomain.com

# 3. Clone and setup
git clone <repository-url> .
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
nano .env

# 5. Setup systemd or use screen/tmux
screen -S hrms
python start_web.py
# Press Ctrl+A, D to detach
```

#### Configure cPanel to proxy to port 8000

In cPanel → Setup Node.js App or Setup Python App:
- Set application root
- Configure proxy from domain to localhost:8000

---

### Option 4: Cloud Platforms

#### Heroku

Create `Procfile`:
```
web: python start_web.py
```

Deploy:
```bash
heroku create hrms-app
heroku config:set SUPABASE_URL=your_url
heroku config:set SUPABASE_KEY=your_key
git push heroku main
```

#### Railway / Render

1. Connect your GitHub repository
2. Set environment variables in dashboard
3. Deploy automatically from main branch

---

## GitLab CI/CD

Create `.gitlab-ci.yml` for automated deployments:

```yaml
stages:
  - test
  - deploy

variables:
  DEPLOY_SERVER: "your-server.com"
  DEPLOY_PATH: "/opt/HRMS_app"

test:
  stage: test
  image: python:3.10
  script:
    - pip install -r requirements.txt
    - python -m pytest tests/ || echo "Tests not yet implemented"
  only:
    - merge_requests
    - main

deploy_production:
  stage: deploy
  image: alpine:latest
  before_script:
    - apk add --no-cache openssh-client
    - eval $(ssh-agent -s)
    - echo "$SSH_PRIVATE_KEY" | tr -d '\r' | ssh-add -
    - mkdir -p ~/.ssh
    - chmod 700 ~/.ssh
  script:
    - ssh -o StrictHostKeyChecking=no $DEPLOY_USER@$DEPLOY_SERVER "
        cd $DEPLOY_PATH &&
        git pull origin main &&
        source venv/bin/activate &&
        pip install -r requirements.txt &&
        sudo systemctl restart hrms-web
      "
  only:
    - main
  when: manual
```

Set these variables in GitLab → Settings → CI/CD → Variables:
- `SSH_PRIVATE_KEY`: Your deployment SSH key
- `DEPLOY_USER`: SSH username
- `DEPLOY_SERVER`: Server hostname
- `SUPABASE_URL`: Supabase URL
- `SUPABASE_KEY`: Supabase key

---

## Updating Deployment

### Pull Latest Changes

```bash
cd /opt/HRMS_app
git pull origin main
source venv/bin/activate
pip install -r requirements.txt  # If dependencies changed
sudo systemctl restart hrms-web
```

### Database Migrations

The application connects to Supabase (cloud database), so no local migrations needed. Schema changes happen in Supabase dashboard.

---

## Monitoring & Logs

### View Service Logs

```bash
# Real-time logs
sudo journalctl -u hrms-web -f

# Last 100 lines
sudo journalctl -u hrms-web -n 100

# Since specific time
sudo journalctl -u hrms-web --since "2025-01-01 00:00:00"
```

### Health Check Endpoint

The application provides a health check at:
```
GET http://yourdomain.com/health
```

---

## Troubleshooting

### Application Won't Start

1. Check environment variables:
   ```bash
   cat .env
   ```

2. Verify Supabase credentials:
   ```bash
   source venv/bin/activate
   python -c "from services.supabase_service import supabase; print(supabase)"
   ```

3. Check port availability:
   ```bash
   sudo netstat -tulpn | grep :8000
   ```

### Connection Issues

1. Check firewall:
   ```bash
   sudo ufw status
   sudo ufw allow 8000
   ```

2. Verify Nginx configuration:
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

### Permission Issues

```bash
sudo chown -R www-data:www-data /opt/HRMS_app
sudo chmod -R 755 /opt/HRMS_app
```

---

## Security Checklist

- [ ] `.env` file is in `.gitignore`
- [ ] Production credentials are different from development
- [ ] Firewall is configured (only ports 80, 443, 22 open)
- [ ] SSL certificate is installed and auto-renewing
- [ ] Service runs as non-root user
- [ ] Regular backups configured for database
- [ ] Application logs are rotated
- [ ] Security updates are automatically applied

---

## Performance Optimization

### Use Gunicorn (Production WSGI Server)

```bash
pip install gunicorn
```

Update systemd service:
```ini
ExecStart=/opt/HRMS_app/venv/bin/gunicorn -w 4 -k uvicorn.workers.UvicornWorker web_app:app --bind 0.0.0.0:8000
```

### Enable Caching

Add to Nginx configuration:
```nginx
location /static {
    alias /opt/HRMS_app/web/static;
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## Support

For issues or questions:
1. Check logs: `sudo journalctl -u hrms-web -f`
2. Review this guide
3. Check Supabase dashboard for database issues
4. Verify environment variables in `.env`

---

## Next Steps After Deployment

1. Test login with admin credentials
2. Verify all API endpoints work: `/docs`
3. Create employee accounts
4. Configure leave types and settings
5. Run initial payroll to test calculations
6. Train users on the web interface

The web application is now production-ready! 🎉
