import sys
from datetime import date
from werkzeug.security import generate_password_hash
from backend import db, create_app
from backend.models import User, Client, Program
from backend.config import Config
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

DEFAULT_PROGRAMS: List[Dict[str, str]] = [
    {'name': 'TB Treatment', 'description': 'Tuberculosis treatment program'},
    {'name': 'HIV Care', 'description': 'HIV management and care program'},
    {'name': 'Malaria Prevention', 'description': 'Malaria prevention and treatment'},
    {'name': 'Maternal Health', 'description': 'Prenatal and postnatal care'},
    {'name': 'Child Immunization', 'description': 'Childhood vaccination program'},
    {'name': 'Nutrition Support', 'description': 'Nutritional counseling and support'},
    {'name': 'Chronic Disease Management', 'description': 'Management of chronic conditions'}
]


def create_default_programs() -> int:
    """Create default health programs in the database."""
    programs_created = 0
    for program_data in DEFAULT_PROGRAMS:
        if not Program.query.filter_by(name=program_data['name']).first():
            program = Program(**program_data)
            db.session.add(program)
            programs_created += 1
            logger.info(f"Created program: {program_data['name']}")
    return programs_created


def create_admin_user() -> bool:
    """Create the default admin user if it doesn't exist."""
    if User.query.filter_by(username='admin').first():
        return False

    # Get admin credentials from environment or use defaults
    admin_username = Config.get('DEFAULT_ADMIN_USERNAME', 'admin')
    admin_email = Config.get('DEFAULT_ADMIN_EMAIL', 'admin@healthsystem.org')
    admin_password = Config.get('DEFAULT_ADMIN_PASSWORD')

    if not admin_password:
        logger.warning("No admin password set in environment. Using default (change in production!)")
        admin_password = 'admin123'  # This should be changed immediately after setup

    hashed_password = generate_password_hash(
        admin_password,
        method=Config.get('PASSWORD_HASH_SCHEME', 'pbkdf2:sha256'),
        salt_length=Config.get_int('PASSWORD_SALT_LENGTH', 16)
    )

    admin = User(
        username=admin_username,
        email=admin_email,
        password=hashed_password,
        role='admin',
        is_active=True
    )
    db.session.add(admin)
    logger.info(f"Admin user created: {admin_username}")
    return True


def create_test_client() -> bool:
    """Create a test client in development environment."""
    if Client.query.first():
        return False

    test_client = Client(
        first_name='Test',
        last_name='Patient',
        dob=date(1990, 1, 1),
        gender='other',
        phone='+1234567890',
        email='test@healthsystem.org',
        is_active=True
    )
    db.session.add(test_client)
    logger.info("Test client created")
    return True


def init_db() -> None:
    """Initialize the database and populate it with default data."""
    app = create_app()

    with app.app_context():
        try:
            logger.info("Starting database initialization...")

            # Create all tables
            logger.info("Creating database tables...")
            db.create_all()
            logger.info("Tables created successfully")

            # Add default programs
            programs_created = create_default_programs()
            logger.info(f"Added {programs_created} default programs")

            # Create admin user
            admin_created = create_admin_user()
            if not admin_created:
                logger.info("Admin user already exists")

            # Create test data in development
            if app.config['FLASK_ENV'] == 'development':
                test_client_created = create_test_client()
                if not test_client_created:
                    logger.info("Test client already exists")

            # Commit all changes
            db.session.commit()
            logger.info("✅ Database initialized successfully!")

        except Exception as e:
            db.session.rollback()
            logger.error(f"❌ Error initializing database: {str(e)}", exc_info=True)
            sys.exit(1)


if __name__ == '__main__':
    try:
        init_db()
    except KeyboardInterrupt:
        logger.info("Database initialization cancelled by user")
        sys.exit(0)