from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()

# Initialize limiter with Redis
redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=redis_url,
    storage_options={"socket_connect_timeout": 30},
    strategy="fixed-window"  # or "moving-window"
)

# Real-time
from backend.realtime.socket import socketio, init_socketio


def create_app():
    app = Flask(__name__)

    # Load configuration from .env file
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
    if not app.config['SQLALCHEMY_DATABASE_URI']:
        raise ValueError("No DATABASE_URL set in .env file")

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
    jwt_expires = os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600').split('#')[0].strip()
    app.config['JWT_ACCESS_TOKEN_EXPIRES'] = int(jwt_expires)
    app.config['UPLOAD_FOLDER'] = '/path/to/upload/directory'  # Absolute path preferred
    app.config['MAX_FILE_SIZE'] = 16 * 1024 * 1024  # 16MB
    app.config['FILE_SERVER_BASE_URL'] = 'https://yourdomain.com/uploads'
    app.config['REDIS_URL'] = redis_url  # Make Redis URL available app-wide

    # Security headers
    Talisman(
        app,
        force_https=os.getenv('HSTS_ENABLED', 'True') == 'True',
        strict_transport_security=os.getenv('HSTS_ENABLED', 'True') == 'True',
        session_cookie_secure=True,
        content_security_policy={
            'default-src': "'self'",
            'script-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net"],
            'style-src': ["'self'", "'unsafe-inline'", "cdn.jsdelivr.net", "fonts.googleapis.com"],
            'font-src': ["'self'", "fonts.gstatic.com"],
            'img-src': ["'self'", "data:"]
        } if os.getenv('CSP_ENABLED', 'True') == 'True' else None
    )

    # CORS
    CORS(app, resources={r"/*": {
        "origins": os.getenv('CORS_ORIGINS', '').split(',')
    }})

    # Rate limiting - now properly initialized with Redis
    limiter.init_app(app)

    # Initialize DB and Marshmallow
    db.init_app(app)
    ma.init_app(app)

    # Init socket.io for real-time events
    init_socketio(app)

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.clients import clients_bp
    from backend.routes.programs import programs_bp
    from backend.routes.visits import visits_bp
    from backend.routes.system import system_bp
    from backend.routes.analytics import analytics_bp
    from backend.routes.uploads import uploads_bp
    from backend.routes.pdf_export import export_pdf_bp
    from backend.routes.logs import logs_bp
    from backend.routes.admin import admin_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(programs_bp, url_prefix='/api/programs')
    app.register_blueprint(visits_bp, url_prefix='/api/visits')
    app.register_blueprint(system_bp, url_prefix='/api')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
    app.register_blueprint(uploads_bp, url_prefix='/api/uploads')
    app.register_blueprint(export_pdf_bp, url_prefix='/api/export')
    app.register_blueprint(logs_bp, url_prefix='/api/logs')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')

    return app