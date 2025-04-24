from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_talisman import Talisman
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize extensions
db = SQLAlchemy()
ma = Marshmallow()
limiter = Limiter(key_func=get_remote_address)


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

    # CORS configuration
    CORS(
        app,
        resources={r"/*": {
            "origins": os.getenv('CORS_ORIGINS', '').split(',')
        }}
    )

    # Rate limiting
    limiter.init_app(app)

    # Initialize extensions
    db.init_app(app)
    ma.init_app(app)

    # Register blueprints
    from backend.routes.auth import auth_bp
    from backend.routes.clients import clients_bp
    from backend.routes.programs import programs_bp
    from backend.routes.visits import visits_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(clients_bp, url_prefix='/api/clients')
    app.register_blueprint(programs_bp, url_prefix='/api/programs')
    app.register_blueprint(visits_bp, url_prefix='/api/visits')

    return app