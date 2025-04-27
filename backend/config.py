import json
import os
from typing import Any, Optional, List, Dict, Union
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class that loads settings from environment variables
    with proper type conversion and default values.
    """

    @staticmethod
    def get(key: str, default: Optional[str] = None) -> Optional[str]:
        """Get string value from environment"""
        return os.getenv(key, default)

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
    def get_float(key: str, default: float = 0.0) -> float:
        """Get float value from environment"""
        try:
            return float(os.getenv(key, str(default)))
        except ValueError:
            return default

    @staticmethod
    def get_list(key: str, default: str = '', sep: str = ',') -> List[str]:
        """Get list from environment variable"""
        val = os.getenv(key, default)
        return [item.strip() for item in val.split(sep) if item.strip()] if val else []

    @staticmethod
    def get_dict(key: str, default: Dict[str, Any] = {}) -> Dict[str, Any]:
        """Get dictionary from JSON environment variable"""
        val = os.getenv(key)
        if val:
            try:
                return json.loads(val)
            except json.JSONDecodeError:
                return default
        return default

    # Database Configuration
    @staticmethod
    def get_db_config() -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'SQLALCHEMY_DATABASE_URI': os.getenv('DATABASE_URL'),
            'SQLALCHEMY_TEST_DATABASE_URI': os.getenv('DATABASE_TEST_URL'),
            'SQLALCHEMY_TRACK_MODIFICATIONS': False,
            'SQLALCHEMY_ENGINE_OPTIONS': {
                'pool_size': Config.get_int('DATABASE_POOL_SIZE', 5),
                'max_overflow': Config.get_int('DATABASE_MAX_OVERFLOW', 10),
                'pool_recycle': Config.get_int('DATABASE_POOL_RECYCLE', 3600),
                'pool_pre_ping': True
            }
        }

    # Authentication Configuration
    @staticmethod
    def get_auth_config() -> Dict[str, Any]:
        """Get authentication configuration"""
        return {
            'SECRET_KEY': Config.get('SECRET_KEY'),
            'JWT_SECRET_KEY': Config.get('JWT_SECRET_KEY'),
            'JWT_ACCESS_TOKEN_EXPIRES': Config.get_int('JWT_ACCESS_TOKEN_EXPIRES', 3600),
            'JWT_REFRESH_TOKEN_EXPIRES': Config.get_int('JWT_REFRESH_TOKEN_EXPIRES', 86400),
            'PASSWORD_HASH_SCHEME': Config.get('PASSWORD_HASH_SCHEME', 'pbkdf2:sha256'),
            'PASSWORD_SALT_LENGTH': Config.get_int('PASSWORD_SALT_LENGTH', 32),
            'DEFAULT_ADMIN_USERNAME': Config.get('DEFAULT_ADMIN_USERNAME', 'admin'),
            'DEFAULT_ADMIN_EMAIL': Config.get('DEFAULT_ADMIN_EMAIL', 'admin@healthsystem.org'),
            'DEFAULT_ADMIN_PASSWORD': Config.get('DEFAULT_ADMIN_PASSWORD'),
            'ADMIN_INITIAL_PASSWORD_CHANGE': Config.get_bool('ADMIN_INITIAL_PASSWORD_CHANGE', True)
        }

    # Application Configuration
    @staticmethod
    def get_app_config() -> Dict[str, Any]:
        """Get application configuration"""
        return {
            'FLASK_ENV': Config.get('FLASK_ENV', 'production'),
            'DEBUG': Config.get_bool('DEBUG', False),
            'TESTING': Config.get_bool('TESTING', False),
            'SERVER_NAME': Config.get('SERVER_NAME'),
            'PREFERRED_URL_SCHEME': Config.get('PREFERRED_URL_SCHEME', 'https'),
            'SESSION_COOKIE_SECURE': Config.get_bool('SESSION_COOKIE_SECURE', True),
            'SESSION_COOKIE_HTTPONLY': Config.get_bool('SESSION_COOKIE_HTTPONLY', True),
            'SESSION_COOKIE_SAMESITE': Config.get('SESSION_COOKIE_SAMESITE', 'Lax'),
            'MAINTENANCE_MODE': Config.get_bool('MAINTENANCE_MODE', False)
        }

    # CORS Configuration
    @staticmethod
    def get_cors_config() -> Dict[str, Any]:
        """Get CORS configuration"""
        return {
            'CORS_ORIGINS': Config.get_list('CORS_ORIGINS'),
            'CORS_SUPPORTS_CREDENTIALS': Config.get_bool('CORS_SUPPORTS_CREDENTIALS', True),
            'CORS_MAX_AGE': Config.get_int('CORS_MAX_AGE', 86400)
        }

    # Logging Configuration
    @staticmethod
    def get_logging_config() -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'LOG_LEVEL': Config.get('LOG_LEVEL', 'INFO'),
            'LOG_FILE': Config.get('LOG_FILE', 'logs/healthsystem.log'),
            'LOG_MAX_BYTES': Config.get_int('LOG_MAX_BYTES', 10485760),  # 10MB
            'LOG_BACKUP_COUNT': Config.get_int('LOG_BACKUP_COUNT', 5),
            'LOG_FORMAT': Config.get('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        }

    # Email Configuration
    @staticmethod
    def get_email_config() -> Dict[str, Any]:
        """Get email configuration"""
        return {
            'MAIL_SERVER': Config.get('EMAIL_HOST'),
            'MAIL_PORT': Config.get_int('EMAIL_PORT', 587),
            'MAIL_USERNAME': Config.get('EMAIL_USERNAME'),
            'MAIL_PASSWORD': Config.get('EMAIL_PASSWORD'),
            'MAIL_DEFAULT_SENDER': Config.get('EMAIL_FROM'),
            'MAIL_USE_TLS': Config.get_bool('EMAIL_USE_TLS', True),
            'MAIL_USE_SSL': Config.get_bool('EMAIL_USE_SSL', False),
            'MAIL_TIMEOUT': Config.get_int('EMAIL_TIMEOUT', 10)
        }

    # Security Configuration
    @staticmethod
    def get_security_config() -> Dict[str, Any]:
        """Get security configuration"""
        return {
            'HSTS_ENABLED': Config.get_bool('HSTS_ENABLED', True),
            'HSTS_MAX_AGE': Config.get_int('HSTS_MAX_AGE', 31536000),
            'HSTS_INCLUDE_SUBDOMAINS': Config.get_bool('HSTS_INCLUDE_SUBDOMAINS', True),
            'HSTS_PRELOAD': Config.get_bool('HSTS_PRELOAD', True),
            'CSP_ENABLED': Config.get_bool('CSP_ENABLED', True),
            'XSS_PROTECTION_ENABLED': Config.get_bool('XSS_PROTECTION_ENABLED', True),
            'CONTENT_TYPE_NOSNIFF': Config.get_bool('CONTENT_TYPE_NOSNIFF', True),
            'FRAME_DENY': Config.get_bool('FRAME_DENY', True)
        }

    # Rate Limiting Configuration
    @staticmethod
    def get_rate_limit_config() -> Dict[str, Any]:
        """Get rate limiting configuration"""
        return {
            'RATELIMIT_STORAGE_URL': Config.get('REDIS_URL'),
            'RATELIMIT_DEFAULT': Config.get('RATE_LIMIT', '200 per day'),
            'RATELIMIT_AUTH': Config.get('RATE_LIMIT_AUTH', '50 per hour'),
            'RATELIMIT_API': Config.get('RATE_LIMIT_API', '1000 per hour'),
            'RATELIMIT_STRATEGY': Config.get('RATE_LIMIT_STRATEGY', 'fixed-window')
        }

    # Feature Flags
    @staticmethod
    def get_feature_flags() -> Dict[str, bool]:
        """Get feature flag configuration"""
        return {
            'REGISTRATION_ENABLED': Config.get_bool('REGISTRATION_ENABLED', True),
            'PASSWORD_RESET_ENABLED': Config.get_bool('PASSWORD_RESET_ENABLED', True),
            'API_DOCS_ENABLED': Config.get_bool('API_DOCS_ENABLED', True)
        }

    # Get all configuration
    @staticmethod
    def get_all_config() -> Dict[str, Any]:
        """Get complete configuration dictionary"""
        config = {}
        config.update(Config.get_db_config())
        config.update(Config.get_auth_config())
        config.update(Config.get_app_config())
        config.update(Config.get_cors_config())
        config.update(Config.get_logging_config())
        config.update(Config.get_email_config())
        config.update(Config.get_security_config())
        config.update(Config.get_rate_limit_config())
        config.update(Config.get_feature_flags())
        return config