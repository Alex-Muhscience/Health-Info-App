#!/usr/bin/env python3
"""Database initialization script for Health App backend."""
import sys
from datetime import date
from typing import Optional

from werkzeug.security import generate_password_hash

from backend import db, create_app
from backend.models import (
    User, Client, Program, ClientProgram,
    ActivityLog
)


def print_header(message: str) -> None:
    """Print formatted header message."""
    print(f"\n{'=' * 50}")
    print(f"🛠️  {message.upper()}")
    print(f"{'=' * 50}")


def print_success(message: str, count: Optional[int] = None) -> None:
    """Print success message with optional count."""
    if count is not None:
        print(f"✅ [{count}] {message}")
    else:
        print(f"✅ {message}")


def print_warning(message: str) -> None:
    """Print warning message."""
    print(f"⚠️  {message}")


def create_default_programs() -> int:
    """Create default health programs if they don't exist."""
    default_programs = [
        {
            'name': 'TB Treatment',
            'description': 'Tuberculosis treatment program',
            'duration_days': 180,
            'requirements': 'Diagnosis confirmation'
        },
        {
            'name': 'HIV Care',
            'description': 'HIV management and care program',
            'duration_days': None,  # Ongoing
            'requirements': 'Lab confirmation'
        },
        {
            'name': 'Malaria Prevention',
            'description': 'Malaria prevention and treatment',
            'duration_days': 30,
            'requirements': 'None'
        },
        {
            'name': 'Maternal Health',
            'description': 'Prenatal and postnatal care',
            'duration_days': 270,
            'requirements': 'Pregnancy confirmation'
        },
        {
            'name': 'Child Immunization',
            'description': 'Childhood vaccination program',
            'duration_days': 365 * 2,
            'requirements': 'Child under 5 years'
        },
        {
            'name': 'Nutrition Support',
            'description': 'Nutritional counseling and support',
            'duration_days': 90,
            'requirements': 'Nutritional assessment'
        },
        {
            'name': 'Chronic Disease Management',
            'description': 'Management of chronic conditions',
            'duration_days': None,  # Ongoing
            'requirements': 'Diagnosis confirmation'
        }
    ]

    created = 0
    for data in default_programs:
        if not Program.query.filter_by(name=data['name']).first():
            program = Program(**data)
            db.session.add(program)
            created += 1
    return created


def create_admin_user() -> bool:
    """Create default admin user if not exists."""
    if User.query.filter_by(username='admin').first():
        return False

    admin = User(
        username='admin',
        email='admin@healthsystem.org',
        password=generate_password_hash('Admin@1234', method='pbkdf2:sha256:600000'),
        role='admin',
        is_active=True
    )
    db.session.add(admin)
    return True


def create_test_data(app) -> None:
    """Create test data for development environment."""
    if app.config.get('FLASK_ENV') != 'development':
        return

    # Test client
    if not Client.query.first():
        test_client = Client(
            first_name='Test',
            last_name='Patient',
            dob=date(1990, 1, 1),
            gender='Other',
            phone='+1234567890',
            email='test@healthsystem.org',
            address='123 Test St, Testville',
            emergency_contact_name='Test Contact',
            emergency_contact_phone='+1987654321',
            medical_history='None',
            allergies='None'
        )
        db.session.add(test_client)
        print_success("Test client created")

    # Test programs for client
    client = Client.query.first()
    if client and not ClientProgram.query.first():
        programs = Program.query.limit(3).all()
        for program in programs:
            enrollment = ClientProgram(
                client_id=client.id,
                program_id=program.id,
                enrollment_date=date.today(),
                status='active'
            )
            db.session.add(enrollment)
        print_success(f"Added {len(programs)} test program enrollments")


def log_initialization() -> None:
    """Log the initialization event."""
    activity = ActivityLog(
        user_id=None,  # System action
        action='system_init',
        entity='database',
        details={'action': 'initial_setup'},
        ip_address='127.0.0.1',
        user_agent='init_db.py'
    )
    db.session.add(activity)


def init_db() -> None:
    """Initialize the database with required data."""
    app = create_app()

    with app.app_context():
        try:
            print_header("Database Initialization Started")

            # Create tables
            db.create_all()
            print_success("Database tables created")

            # Add default programs
            programs_created = create_default_programs()
            if programs_created:
                print_success("Default programs added", programs_created)
            else:
                print_warning("Default programs already exist")

            # Create admin user
            if create_admin_user():
                print_success("Admin user created (username: admin, password: Admin@1234)")
                print_warning("CHANGE THE DEFAULT ADMIN PASSWORD IMMEDIATELY!")
            else:
                print_warning("Admin user already exists")

            # Development test data
            create_test_data(app)

            # Log initialization
            log_initialization()

            # Commit all changes
            db.session.commit()
            print_header("Database Initialization Completed Successfully")

        except Exception as e:
            db.session.rollback()
            print(f"\n❌ CRITICAL ERROR: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    init_db()