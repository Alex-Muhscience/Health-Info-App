"""
Production Configuration Management
"""

import os
import secrets
from typing import Dict, Any, Type
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class BaseConfig:
    """Base configuration with common settings"""
    
    # Application
    SECRET_KEY = os.getenv('SECRET_KEY') or secrets.token_urlsafe(32)
    
    # Security
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None
    
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY') or secrets.token_urlsafe(32)
    JWT_ACCESS_TOKEN_EXPIRES = int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', '3600'))  # 1 hour
    JWT_REFRESH_TOKEN_EXPIRES = int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', '2592000'))  # 30 days
    JWT_ALGORITHM = 'HS256'
    JWT_BLACKLIST_ENABLED = True
    JWT_BLACKLIST_TOKEN_CHECKS = ['access', 'refresh']
    
    # Database Configuration
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = False
    
    # Redis Configuration (for rate limiting and caching)
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = os.getenv('REDIS_URL', 'memory://')
    RATELIMIT_DEFAULT = os.getenv('RATE_LIMIT_DEFAULT', '1000 per hour')
    RATELIMIT_HEADERS_ENABLED = True
    
    # CORS Configuration
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
    CORS_SUPPORTS_CREDENTIALS = True
    CORS_MAX_AGE = 86400
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    
    # File Upload Configuration
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'doc', 'docx'}
    
    # Email Configuration
    MAIL_SERVER = os.getenv('MAIL_SERVER')
    MAIL_PORT = int(os.getenv('MAIL_PORT', '587'))
    MAIL_USE_TLS = os.getenv('MAIL_USE_TLS', 'true').lower() == 'true'
    MAIL_USE_SSL = os.getenv('MAIL_USE_SSL', 'false').lower() == 'true'
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    
    # Health Check Configuration
    HEALTH_CHECK_ENABLED = True
    HEALTH_CHECK_PATH = '/health'
    
    # API Configuration
    API_TITLE = 'Health Management System API'
    API_VERSION = 'v1'
    OPENAPI_VERSION = '3.0.2'
    OPENAPI_URL_PREFIX = '/api/docs'
    OPENAPI_SWAGGER_UI_PATH = '/swagger'
    OPENAPI_SWAGGER_UI_URL = 'https://cdn.jsdelivr.net/npm/swagger-ui-dist/'
    
    # Pagination
    DEFAULT_PAGE_SIZE = 20
    MAX_PAGE_SIZE = 100
    
    @staticmethod
    def init_app(app):
        """Initialize application with base configuration"""
        pass


class DevelopmentConfig(BaseConfig):
    """Development configuration"""
    
    DEBUG = True
    FLASK_ENV = 'development'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_DEV_URL', 'sqlite:///dev_health_system.db')
    SQLALCHEMY_ECHO = os.getenv('SQL_ECHO', 'false').lower() == 'true'
    SQLALCHEMY_RECORD_QUERIES = True
    
    # Security (relaxed for development)
    WTF_CSRF_ENABLED = False
    
    # CORS (allow all origins in development)
    CORS_ORIGINS = ['*']
    
    # Rate Limiting (disabled in development)
    RATELIMIT_ENABLED = False
    
    # Logging
    LOG_LEVEL = 'DEBUG'
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
        
        # Development-specific initialization
        import logging
        logging.basicConfig(level=logging.DEBUG)


class TestingConfig(BaseConfig):
    """Testing configuration"""
    
    TESTING = True
    FLASK_ENV = 'testing'
    
    # Database (in-memory SQLite for tests)
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_TEST_URL', 'sqlite:///:memory:')
    
    # Security
    WTF_CSRF_ENABLED = False
    
    # Rate Limiting (disabled for testing)
    RATELIMIT_ENABLED = False
    
    # JWT (shorter expiration for testing)
    JWT_ACCESS_TOKEN_EXPIRES = 300  # 5 minutes
    
    # Disable logging during tests
    LOG_LEVEL = 'ERROR'
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)


class ProductionConfig(BaseConfig):
    """Production configuration"""
    
    DEBUG = False
    FLASK_ENV = 'production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # HTTPS Redirect
    PREFERRED_URL_SCHEME = 'https'
    
    # Rate Limiting
    RATELIMIT_ENABLED = True
    RATELIMIT_DEFAULT = '500 per hour'
    
    # CORS (restricted in production)
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', 'https://yourdomain.com').split(',')
    
    # Error Handling
    PROPAGATE_EXCEPTIONS = False
    
    # Logging
    LOG_TO_STDOUT = os.getenv('LOG_TO_STDOUT', 'false').lower() == 'true'
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
        
        # Production-specific initialization
        import logging
        from logging.handlers import RotatingFileHandler, SMTPHandler
        
        # File logging
        if not app.debug and not app.testing:
            if ProductionConfig.LOG_TO_STDOUT:
                stream_handler = logging.StreamHandler()
                stream_handler.setLevel(logging.INFO)
                app.logger.addHandler(stream_handler)
            else:
                if not os.path.exists('logs'):
                    os.mkdir('logs')
                file_handler = RotatingFileHandler(
                    'logs/health_app.log',
                    maxBytes=10240000,  # 10MB
                    backupCount=10
                )
                file_handler.setFormatter(logging.Formatter(
                    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
                ))
                file_handler.setLevel(logging.INFO)
                app.logger.addHandler(file_handler)
            
            app.logger.setLevel(logging.INFO)
            app.logger.info('Health Management System startup')
        
        # Email error notifications
        if os.getenv('MAIL_SERVER'):
            auth = None
            if os.getenv('MAIL_USERNAME') or os.getenv('MAIL_PASSWORD'):
                auth = (os.getenv('MAIL_USERNAME'), os.getenv('MAIL_PASSWORD'))
            secure = None
            if os.getenv('MAIL_USE_TLS'):
                secure = ()
            mail_handler = SMTPHandler(
                mailhost=(os.getenv('MAIL_SERVER'), os.getenv('MAIL_PORT', 587)),
                fromaddr=os.getenv('MAIL_DEFAULT_SENDER'),
                toaddrs=[os.getenv('ADMIN_EMAIL', 'admin@example.com')],
                subject='Health App Failure',
                credentials=auth,
                secure=secure
            )
            mail_handler.setLevel(logging.ERROR)
            app.logger.addHandler(mail_handler)


class DockerConfig(ProductionConfig):
    """Docker container configuration"""
    
    # Override for containerized environments
    LOG_TO_STDOUT = True
    
    @staticmethod
    def init_app(app):
        ProductionConfig.init_app(app)
        
        # Container-specific logging
        import logging
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)
        app.logger.setLevel(logging.INFO)


# Configuration mapping
config: Dict[str, Type[BaseConfig]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


def get_config(config_name: str = None) -> Type[BaseConfig]:
    """Get configuration class by name"""
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'default')
    
    return config.get(config_name, config['default'])


def validate_config() -> Dict[str, Any]:
    """Validate critical configuration settings"""
    issues = []
    warnings = []
    
    # Check critical environment variables
    critical_vars = ['SECRET_KEY', 'JWT_SECRET_KEY']
    for var in critical_vars:
        if not os.getenv(var):
            issues.append(f"Missing critical environment variable: {var}")
    
    # Check database URL for production
    if os.getenv('FLASK_ENV') == 'production':
        if not os.getenv('DATABASE_URL'):
            issues.append("DATABASE_URL must be set for production")
        
        # Check security settings
        if not os.getenv('CORS_ORIGINS') or os.getenv('CORS_ORIGINS') == '*':
            warnings.append("CORS_ORIGINS should be restricted in production")
    
    # Check mail configuration
    if os.getenv('MAIL_SERVER') and not os.getenv('MAIL_USERNAME'):
        warnings.append("MAIL_USERNAME should be set when MAIL_SERVER is configured")
    
    return {
        'issues': issues,
        'warnings': warnings,
        'valid': len(issues) == 0
    }
