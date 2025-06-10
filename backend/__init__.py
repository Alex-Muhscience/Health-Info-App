from flask import Flask, jsonify
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman

import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Optional

# Load environment variables from .env file
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
jwt = JWTManager()
limiter = Limiter(key_func=get_remote_address)


class Config:
    """Base configuration class that loads from environment variables"""

    @staticmethod
    def get_bool(key: str, default: bool = False) -> bool:
        """Get boolean value from environment"""
        val = os.getenv(key, str(default)).lower()
        return val in ('true', '1', 't', 'y', 'yes')

    @staticmethod
    def get_int(key: str, default: int = 0) -> int:
        """Get integer value from environment"""
        try:
            return int(os.getenv(key, str(default)))
        except ValueError:
            return default

    @staticmethod
    def get_list(key: str, default: str = '', sep: str = ',') -> list[str]:
        """Get list from environment variable"""
        val = os.getenv(key, default)
        return [item.strip() for item in val.split(sep) if item.strip()] if val else []

    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            # Database Configuration
            'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL'),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                "pool_size": cls.get_int('DATABASE_POOL_SIZE', 5),
                "max_overflow": cls.get_int('DATABASE_MAX_OVERFLOW', 10),
                "pool_recycle": cls.get_int('DATABASE_POOL_RECYCLE', 3600),
                "pool_pre_ping": True
            },

            # Authentication & Security
            'SECRET_KEY': os.getenv('SECRET_KEY'),
            'JWT_SECRET_KEY': os.getenv('JWT_SECRET_KEY'),
            'JWT_ACCESS_TOKEN_EXPIRES': cls.get_int('JWT_ACCESS_TOKEN_EXPIRES', 3600),
            'JWT_REFRESH_TOKEN_EXPIRES': cls.get_int('JWT_REFRESH_TOKEN_EXPIRES', 86400),

            # CORS Configuration
            'CORS_ORIGINS': cls.get_list('CORS_ORIGINS'),
            'CORS_SUPPORTS_CREDENTIALS': cls.get_bool('CORS_SUPPORTS_CREDENTIALS', True),

            # Rate Limiting
            'RATELIMIT_STORAGE_URI': os.getenv('REDIS_URL'),
            'RATELIMIT_DEFAULT': os.getenv('RATE_LIMIT', '200 per day'),

            # Logging
            'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
            'LOG_FILE': os.getenv('LOG_FILE', 'logs/healthsystem.log'),
            'LOG_MAX_BYTES': cls.get_int('LOG_MAX_BYTES', 10485760),  # 10MB
            'LOG_BACKUP_COUNT': cls.get_int('LOG_BACKUP_COUNT', 5),

            # Application Settings
            'DEBUG': cls.get_bool('DEBUG', False),
            'TESTING': cls.get_bool('TESTING', False),
            'FLASK_ENV': os.getenv('FLASK_ENV', 'production'),
            'SESSION_COOKIE_SECURE': cls.get_bool('SESSION_COOKIE_SECURE', True),
            'SESSION_COOKIE_HTTPONLY': cls.get_bool('SESSION_COOKIE_HTTPONLY', True),
            'SESSION_COOKIE_SAMESITE': os.getenv('SESSION_COOKIE_SAMESITE', 'Lax'),

            # Security Headers
            'HSTS_ENABLED': cls.get_bool('HSTS_ENABLED', True),
            'HSTS_MAX_AGE': cls.get_int('HSTS_MAX_AGE', 31536000),
            'HSTS_INCLUDE_SUBDOMAINS': cls.get_bool('HSTS_INCLUDE_SUBDOMAINS', True),
            'HSTS_PRELOAD': cls.get_bool('HSTS_PRELOAD', True),
            'CSP_ENABLED': cls.get_bool('CSP_ENABLED', True),
            'XSS_PROTECTION_ENABLED': cls.get_bool('XSS_PROTECTION_ENABLED', True),
            'CONTENT_TYPE_NOSNIFF': cls.get_bool('CONTENT_TYPE_NOSNIFF', True),
            'FRAME_DENY': cls.get_bool('FRAME_DENY', True),
        }


jwt = JWTManager()

def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:

    """Application factory pattern"""
    app = Flask(__name__)

    # Load configuration
    app.config.update(Config.to_dict())
    if config:
        app.config.update(config)

    # Configure logging
    if not app.debug and not app.testing:
        log_dir = os.path.dirname(app.config['LOG_FILE'])
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=app.config['LOG_MAX_BYTES'],
            backupCount=app.config['LOG_BACKUP_COUNT']
        )
        file_handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
        file_handler.setLevel(app.config['LOG_LEVEL'])
        app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config['LOG_LEVEL'])
        app.logger.info('Health System starting up')

    # Security Headers
    csp_policy = None
    if app.config['CSP_ENABLED']:
        csp_policy = {
            'default-src': "'self'",
            'style-src': ["'self'", "'unsafe-inline'"],
            'script-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:"]
        }

    Talisman(
        app,
        content_security_policy=csp_policy,
        force_https=app.config['SESSION_COOKIE_SECURE'],
        strict_transport_security=app.config['HSTS_ENABLED'],
        strict_transport_security_max_age=app.config['HSTS_MAX_AGE'],
        strict_transport_security_include_subdomains=app.config['HSTS_INCLUDE_SUBDOMAINS'],
        strict_transport_security_preload=app.config['HSTS_PRELOAD'],
        session_cookie_secure=app.config['SESSION_COOKIE_SECURE'],
        session_cookie_http_only=app.config['SESSION_COOKIE_HTTPONLY'],
        x_content_type_options=app.config['CONTENT_TYPE_NOSNIFF'],
        x_xss_protection=app.config['XSS_PROTECTION_ENABLED'],
        frame_options='DENY' if app.config['FRAME_DENY'] else 'SAMEORIGIN'
    )

    # CORS Configuration
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config['CORS_ORIGINS'],
                "supports_credentials": app.config['CORS_SUPPORTS_CREDENTIALS']
            }
        }
    )

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.clients import clients_bp
    from backend.routes.programs import programs_bp
    from backend.routes.visits import visits_bp
    from backend.routes.dashboard import system_bp
    from backend.routes.appointments import appointments_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(programs_bp, url_prefix='/api/programs')
    app.register_blueprint(visits_bp, url_prefix='/api/visits')
    app.register_blueprint(system_bp, url_prefix='/api/dashboard')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')

    # Error handlers
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({'error': 'Bad request'}), 400

    @app.errorhandler(401)
    def unauthorized(error):
        return jsonify({'error': 'Unauthorized'}), 401

    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({'error': 'Forbidden'}), 403

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server error: {str(error)}')
        return jsonify({'error': 'Internal server error'}), 500

    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'environment': app.config['FLASK_ENV'],
            'debug': app.debug,
            'maintenance_mode': app.config.get('MAINTENANCE_MODE', False)
        })

    return app