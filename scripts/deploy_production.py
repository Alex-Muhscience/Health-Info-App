#!/usr/bin/env python3
"""
Production Deployment Script for Health Management System
Handles complete production setup, database migration, and configuration.
"""

import os
import sys
import subprocess
import secrets
import click
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_secret_key():
    """Generate a secure secret key"""
    return secrets.token_urlsafe(32)


def create_production_env():
    """Create production environment file with secure defaults"""
    env_content = f"""# Production Environment Configuration - Generated {Path(__file__).stem}
FLASK_ENV=production
DEBUG=false
TESTING=false

# Database Configuration (REQUIRED FOR PRODUCTION)
DATABASE_URL=postgresql://health_user:your_password@localhost:5432/health_system_production
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600

# Security (GENERATED - KEEP SECURE)
SECRET_KEY={generate_secret_key()}
JWT_SECRET_KEY={generate_secret_key()}
JWT_ACCESS_TOKEN_EXPIRES=3600
JWT_REFRESH_TOKEN_EXPIRES=86400

# CORS Configuration (UPDATE WITH YOUR DOMAIN)
CORS_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
CORS_SUPPORTS_CREDENTIALS=true

# Rate Limiting
REDIS_URL=redis://localhost:6379/0
RATE_LIMIT_DEFAULT=500 per hour
RATE_LIMIT_AUTH=100 per hour

# Logging
LOG_LEVEL=INFO
LOG_TO_STDOUT=false
LOG_FILE=logs/health_app_production.log
LOG_MAX_BYTES=52428800
LOG_BACKUP_COUNT=10

# Email Configuration (CONFIGURE WITH YOUR EMAIL PROVIDER)
MAIL_SERVER=smtp.yourmailserver.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@domain.com
MAIL_PASSWORD=your-email-password
MAIL_DEFAULT_SENDER=noreply@yourdomain.com
ADMIN_EMAIL=admin@yourdomain.com

# Security Headers
SESSION_COOKIE_SECURE=true
SESSION_COOKIE_HTTPONLY=true
SESSION_COOKIE_SAMESITE=Lax
HSTS_ENABLED=true
HSTS_MAX_AGE=31536000
HSTS_INCLUDE_SUBDOMAINS=true
CSP_ENABLED=true
XSS_PROTECTION_ENABLED=true
CONTENT_TYPE_NOSNIFF=true
FRAME_DENY=true

# Admin Configuration
DEFAULT_ADMIN_USERNAME=admin
DEFAULT_ADMIN_EMAIL=admin@yourdomain.com
DEFAULT_ADMIN_PASSWORD={generate_secret_key()[:16]}
ADMIN_INITIAL_PASSWORD_CHANGE=true

# File Upload
UPLOAD_FOLDER=uploads
MAX_CONTENT_LENGTH=16777216

# Application Settings
MAINTENANCE_MODE=false
"""
    return env_content


@click.group()
def cli():
    """Production deployment commands for Health Management System"""
    pass


@cli.command()
@click.option('--force', is_flag=True, help='Overwrite existing .env.production file')
def setup_env(force):
    """Create production environment configuration"""
    env_file = Path('.env.production')
    
    if env_file.exists() and not force:
        click.echo("❌ .env.production already exists. Use --force to overwrite.")
        return
    
    click.echo("🔧 Creating production environment configuration...")
    
    env_content = create_production_env()
    env_file.write_text(env_content)
    
    click.echo("✅ Production environment file created: .env.production")
    click.echo("⚠️  IMPORTANT: Edit .env.production and update the following:")
    click.echo("   • DATABASE_URL with your PostgreSQL connection string")
    click.echo("   • CORS_ORIGINS with your actual domain(s)")
    click.echo("   • Email configuration (MAIL_*)")
    click.echo("   • Admin email and domain settings")


@cli.command()
def install_deps():
    """Install production dependencies"""
    click.echo("📦 Installing production dependencies...")
    
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], check=True)
        click.echo("✅ Dependencies installed successfully")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to install dependencies: {e}")
        sys.exit(1)


@cli.command()
@click.option('--db-url', prompt='Database URL', help='PostgreSQL database connection string')
def setup_database(db_url):
    """Initialize production database"""
    click.echo("🗄️  Setting up production database...")
    
    # Set environment variable temporarily
    os.environ['DATABASE_URL'] = db_url
    os.environ['FLASK_ENV'] = 'production'
    
    try:
        # Initialize database
        subprocess.run([sys.executable, 'manage_db.py', 'init', '-e', 'production'], check=True)
        
        # Seed with initial data
        subprocess.run([sys.executable, 'manage_db.py', 'seed', '-e', 'production'], check=True)
        
        click.echo("✅ Database setup completed")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Database setup failed: {e}")
        sys.exit(1)


@cli.command()
def validate_config():
    """Validate production configuration"""
    click.echo("🔍 Validating production configuration...")
    
    try:
        subprocess.run([sys.executable, 'manage_db.py', 'validate'], check=True)
        click.echo("✅ Configuration validation passed")
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Configuration validation failed: {e}")
        sys.exit(1)


@cli.command()
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--port', default=8000, help='Port to bind to')
@click.option('--workers', default=4, help='Number of worker processes')
def start_production(host, port, workers):
    """Start production server with Gunicorn"""
    click.echo("🚀 Starting production server...")
    
    # Ensure logs directory exists
    Path('logs').mkdir(exist_ok=True)
    
    # Gunicorn command
    cmd = [
        'gunicorn',
        '--bind', f'{host}:{port}',
        '--workers', str(workers),
        '--worker-class', 'sync',
        '--timeout', '120',
        '--keepalive', '5',
        '--max-requests', '1000',
        '--max-requests-jitter', '100',
        '--preload',
        '--access-logfile', 'logs/access.log',
        '--error-logfile', 'logs/error.log',
        '--log-level', 'info',
        'backend.app:app'
    ]
    
    try:
        os.environ['FLASK_ENV'] = 'production'
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        click.echo(f"❌ Failed to start production server: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("🛑 Production server stopped")


@cli.command()
def create_systemd_service():
    """Create systemd service file for production deployment"""
    service_content = f"""[Unit]
Description=Health Management System
After=network.target postgresql.service redis.service
Wants=postgresql.service redis.service

[Service]
Type=notify
User=www-data
Group=www-data
WorkingDirectory={Path.cwd()}
Environment=PATH={Path.cwd()}/venv/bin
Environment=FLASK_ENV=production
ExecStart={Path.cwd()}/venv/bin/gunicorn --bind 0.0.0.0:8000 --workers 4 --worker-class sync --timeout 120 --keepalive 5 --max-requests 1000 --max-requests-jitter 100 --preload --access-logfile logs/access.log --error-logfile logs/error.log --log-level info backend.app:app
ExecReload=/bin/kill -s HUP $MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path('health-management-system.service')
    service_file.write_text(service_content)
    
    click.echo("✅ Systemd service file created: health-management-system.service")
    click.echo("📋 To install and start the service:")
    click.echo("   sudo cp health-management-system.service /etc/systemd/system/")
    click.echo("   sudo systemctl daemon-reload")
    click.echo("   sudo systemctl enable health-management-system")
    click.echo("   sudo systemctl start health-management-system")


@cli.command()
def create_nginx_config():
    """Create Nginx configuration for production"""
    nginx_content = """server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header X-XSS-Protection "1; mode=block";
    
    # API Backend
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health Check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Frontend (Streamlit) - if running separately
    location / {
        proxy_pass http://127.0.0.1:8501;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support for Streamlit
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    
    # Static files
    location /static/ {
        alias /path/to/your/static/files/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # File uploads
    client_max_body_size 16M;
}
"""
    
    nginx_file = Path('nginx-health-system.conf')
    nginx_file.write_text(nginx_content)
    
    click.echo("✅ Nginx configuration created: nginx-health-system.conf")
    click.echo("📋 To install the configuration:")
    click.echo("   sudo cp nginx-health-system.conf /etc/nginx/sites-available/health-system")
    click.echo("   sudo ln -s /etc/nginx/sites-available/health-system /etc/nginx/sites-enabled/")
    click.echo("   sudo nginx -t")
    click.echo("   sudo systemctl reload nginx")


@cli.command()
def full_deploy():
    """Complete production deployment (interactive)"""
    click.echo("🚀 Starting full production deployment...")
    
    # Step 1: Setup environment
    if not Path('.env.production').exists():
        if click.confirm('Create production environment file?'):
            setup_env.callback(force=False)
    
    # Step 2: Install dependencies
    if click.confirm('Install production dependencies?'):
        install_deps.callback()
    
    # Step 3: Setup database
    if click.confirm('Setup production database?'):
        db_url = click.prompt('Enter PostgreSQL database URL')
        setup_database.callback(db_url)
    
    # Step 4: Validate configuration
    if click.confirm('Validate production configuration?'):
        validate_config.callback()
    
    # Step 5: Create service files
    if click.confirm('Create systemd service file?'):
        create_systemd_service.callback()
    
    if click.confirm('Create Nginx configuration?'):
        create_nginx_config.callback()
    
    click.echo("\n✅ Production deployment completed!")
    click.echo("📋 Next steps:")
    click.echo("   1. Review and edit .env.production with your settings")
    click.echo("   2. Install and configure systemd service")
    click.echo("   3. Install and configure Nginx")
    click.echo("   4. Obtain SSL certificates")
    click.echo("   5. Start the services")


if __name__ == '__main__':
    cli()
