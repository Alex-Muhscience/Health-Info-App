"""Production-ready Flask application factory"""

import os
import logging
from typing import Optional, Dict, Any
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
from flask_caching import Cache
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database and configuration
from backend.database import db, migrate, init_database
from backend.config import get_config

# Initialize extensions
ma = Marshmallow()
jwt = JWTManager()
cache = Cache()

# Initialize limiter with fallback
try:
    limiter = Limiter(key_func=get_remote_address)
except Exception:
    # Fallback limiter for development
    class DummyLimiter:
        def limit(self, *args, **kwargs):
            def decorator(f): return f
            return decorator
        def init_app(self, app): pass
    limiter = DummyLimiter()


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


def create_app(config_name: str = None) -> Flask:
    """Production-ready application factory"""
    app = Flask(__name__)
    
    # Load configuration based on environment
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    
    # Initialize configuration
    config_class.init_app(app)
    
    # Initialize database
    init_database(app)
    
    # Initialize other extensions
    ma.init_app(app)
    jwt.init_app(app)
    cache.init_app(app)
    limiter.init_app(app)
    
    # CORS Configuration
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config.get('CORS_ORIGINS', ['*']),
                "supports_credentials": app.config.get('CORS_SUPPORTS_CREDENTIALS', True)
            }
        }
    )
    
    # Security Headers (conditionally apply Talisman)
    if not app.config.get('TESTING', False):
        try:
            Talisman(
                app,
                force_https=False,  # Allow HTTP in development
                strict_transport_security=False,  # Disable HSTS in development
                content_security_policy=False  # Disable CSP for development
            )
        except Exception as e:
            app.logger.warning(f"Talisman setup failed: {e}")

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.clients import clients_bp
    from backend.routes.programs import programs_bp
    from backend.routes.visits import visits_bp
    from backend.routes.dashboard import system_bp
    from backend.routes.appointments import appointments_bp
    from backend.routes.staff import staff_bp
    from backend.routes.departments import departments_bp
    from backend.routes.medical_records import medical_records_bp
    from backend.routes.laboratory import laboratory_bp
    from backend.routes.pharmacy import pharmacy_bp
    from backend.routes.admissions import admissions_bp
    from backend.routes.billing import billing_bp
    from backend.routes.telemedicine import telemedicine_bp
    from backend.routes.analytics import analytics_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(programs_bp, url_prefix='/api/programs')
    app.register_blueprint(visits_bp, url_prefix='/api/visits')
    app.register_blueprint(system_bp, url_prefix='/api/dashboard')
    app.register_blueprint(appointments_bp, url_prefix='/api/appointments')
    app.register_blueprint(staff_bp, url_prefix='/api')
    app.register_blueprint(departments_bp, url_prefix='/api')
    app.register_blueprint(medical_records_bp, url_prefix='/api')
    app.register_blueprint(laboratory_bp, url_prefix='/api')
    app.register_blueprint(pharmacy_bp, url_prefix='/api')
    app.register_blueprint(admissions_bp, url_prefix='/api')
    app.register_blueprint(billing_bp, url_prefix='/api')
    app.register_blueprint(telemedicine_bp, url_prefix='/api/telemedicine')
    app.register_blueprint(analytics_bp, url_prefix='/api/analytics')

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