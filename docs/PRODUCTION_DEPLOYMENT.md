# 🏥 Health Management System - Production Deployment Guide

This guide covers the complete production deployment of the Health Management System with enterprise-grade security, scalability, and reliability.

## 📋 Prerequisites

### System Requirements
- **Operating System**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **Python**: 3.9+
- **Database**: PostgreSQL 13+
- **Cache**: Redis 6+
- **Web Server**: Nginx 1.18+
- **Memory**: 4GB+ RAM
- **Storage**: 20GB+ SSD

### Required Services
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y python3 python3-pip python3-venv postgresql postgresql-contrib redis-server nginx supervisor

# CentOS/RHEL
sudo dnf install -y python3 python3-pip postgresql postgresql-server postgresql-contrib redis nginx supervisor
```

## 🚀 Quick Production Setup

### 1. Clone and Setup
```bash
git clone https://github.com/your-repo/health-management-system.git
cd health-management-system

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Automated Production Setup
```bash
# Run the automated deployment script
python deploy_production.py full-deploy
```

This interactive script will:
- Create production environment configuration
- Install all dependencies
- Setup and configure PostgreSQL database
- Validate configuration
- Create systemd service files
- Generate Nginx configuration

## 🔧 Manual Production Setup

### 1. Database Setup

#### PostgreSQL Installation and Configuration
```bash
# Install PostgreSQL
sudo apt install postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql
```

```sql
-- Create database user
CREATE USER health_user WITH PASSWORD 'your_secure_password';

-- Create database
CREATE DATABASE health_system_production OWNER health_user;

-- Grant privileges
ALTER USER health_user CREATEDB;
GRANT ALL PRIVILEGES ON DATABASE health_system_production TO health_user;

-- Exit
\q
```

#### Database Migration
```bash
# Initialize database with migrations
python manage_db.py init -e production

# Create and apply initial migration
python manage_db.py create-migration -m "Initial production setup" -e production
python manage_db.py upgrade-db -e production

# Seed with initial data
python manage_db.py seed -e production
```

### 2. Environment Configuration

Create `.env.production`:
```bash
# Copy template and edit
cp .env.production.example .env.production
nano .env.production
```

**Critical settings to update:**
```env
# Database (REQUIRED)
DATABASE_URL=postgresql://health_user:your_secure_password@localhost:5432/health_system_production

# Security Keys (REQUIRED - Generate new ones)
SECRET_KEY=your-super-secure-secret-key-32-chars-min
JWT_SECRET_KEY=your-jwt-secret-key-32-chars-min

# Domain Configuration (REQUIRED)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com

# Email Configuration (OPTIONAL but recommended)
MAIL_SERVER=smtp.yourmailserver.com
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
```

### 3. Redis Setup
```bash
# Install and configure Redis
sudo apt install redis-server

# Configure Redis
sudo nano /etc/redis/redis.conf
# Set: bind 127.0.0.1
# Set: requirepass your_redis_password

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

### 4. Application Server (Gunicorn)

#### Create Gunicorn Configuration
```python
# gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 100
preload_app = True
user = "www-data"
group = "www-data"
tmp_upload_dir = None
logfile = "logs/gunicorn.log"
loglevel = "info"
access_logfile = "logs/gunicorn-access.log"
access_logformat = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
```

#### Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/health-management-system.service
```

```ini
[Unit]
Description=Health Management System
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory=/path/to/health-management-system
Environment=PATH=/path/to/health-management-system/venv/bin
Environment=FLASK_ENV=production
ExecStart=/path/to/health-management-system/venv/bin/gunicorn --config gunicorn.conf.py backend.app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable health-management-system
sudo systemctl start health-management-system
```

### 5. Nginx Configuration

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/health-system
```

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/ssl/certificate.crt;
    ssl_certificate_key /path/to/ssl/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/m;
    
    # API Backend
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Login endpoint with stricter rate limiting
    location /api/auth/login {
        limit_req zone=login burst=5 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend (Streamlit)
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files
    location /static/ {
        alias /path/to/health-management-system/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # File upload size
    client_max_body_size 16M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/health-system /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. SSL Certificate Setup

#### Using Let's Encrypt (Recommended)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## 🔐 Security Hardening

### 1. Firewall Configuration
```bash
# Configure UFW
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2. Database Security
```bash
# PostgreSQL security
sudo nano /etc/postgresql/13/main/postgresql.conf
# Set: listen_addresses = 'localhost'

sudo nano /etc/postgresql/13/main/pg_hba.conf
# Set: local all all md5
# Set: host all all 127.0.0.1/32 md5

sudo systemctl restart postgresql
```

### 3. Application Security
- ✅ Secure secret keys generated
- ✅ HTTPS-only cookies
- ✅ CORS properly configured
- ✅ Rate limiting enabled
- ✅ SQL injection protection
- ✅ XSS protection headers
- ✅ CSRF protection enabled

## 📊 Monitoring and Maintenance

### 1. Log Management
```bash
# Create log rotation
sudo nano /etc/logrotate.d/health-system

/path/to/health-management-system/logs/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    copytruncate
}
```

### 2. Database Maintenance
```bash
# Regular maintenance tasks
# Create cron job for database optimization
sudo crontab -e

# Add these lines:
# Daily database optimization (3 AM)
0 3 * * * cd /path/to/health-management-system && python manage_db.py optimize -e production

# Weekly backup (Sunday 2 AM)
0 2 * * 0 cd /path/to/health-management-system && python manage_db.py backup -p "backups/health_system_$(date +\%Y\%m\%d).sql" -e production

# Monthly cleanup (1st day, 1 AM)
0 1 1 * * cd /path/to/health-management-system && python manage_db.py cleanup -d 365 -e production
```

### 3. Health Checks
```bash
# Monitor application health
curl -f http://localhost:8000/health || echo "Health check failed"

# Monitor database
python manage_db.py status -e production
```

## 🔄 Deployment Updates

### Zero-Downtime Deployment
```bash
# 1. Pull latest code
git pull origin main

# 2. Install new dependencies
source venv/bin/activate
pip install -r requirements.txt

# 3. Run database migrations
python manage_db.py upgrade-db -e production

# 4. Reload application
sudo systemctl reload health-management-system

# 5. Verify deployment
curl -f https://yourdomain.com/health
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Issues**
   ```bash
   # Check PostgreSQL status
   sudo systemctl status postgresql
   
   # Check database health
   python manage_db.py status -e production
   ```

2. **Application Won't Start**
   ```bash
   # Check service logs
   sudo journalctl -u health-management-system -f
   
   # Check Gunicorn logs
   tail -f logs/gunicorn.log
   ```

3. **Nginx Issues**
   ```bash
   # Check Nginx configuration
   sudo nginx -t
   
   # Check Nginx logs
   sudo tail -f /var/log/nginx/error.log
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   sudo certbot certificates
   
   # Renew certificates
   sudo certbot renew
   ```

## 📚 Production Checklist

- [ ] PostgreSQL installed and configured
- [ ] Redis installed and configured
- [ ] Application environment configured
- [ ] Database migrations applied
- [ ] SSL certificates installed
- [ ] Nginx configured and running
- [ ] Systemd service created and running
- [ ] Firewall configured
- [ ] Log rotation configured
- [ ] Backup schedule configured
- [ ] Monitoring setup
- [ ] Health checks working
- [ ] Admin account created and secured

## 📞 Support

For production deployment support:
- Check application logs: `sudo journalctl -u health-management-system`
- Check database status: `python manage_db.py status -e production`
- Validate configuration: `python manage_db.py validate`

---

**🎉 Your Health Management System is now production-ready!**
