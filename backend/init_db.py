import sys
from werkzeug.security import generate_password_hash
from backend import db, create_app
from backend.models import User, Client, Program, ClientProgram, Visit


def init_db():
    app = create_app()

    with app.app_context():
        try:
            # Create all tables
            print("Creating database tables...")
            db.create_all()

            # Create default programs
            default_programs = [
                {'name': 'TB Treatment', 'description': 'Tuberculosis treatment program'},
                {'name': 'HIV Care', 'description': 'HIV management and care program'},
                {'name': 'Malaria Prevention', 'description': 'Malaria prevention and treatment'},
                {'name': 'Maternal Health', 'description': 'Prenatal and postnatal care'},
                {'name': 'Child Immunization', 'description': 'Childhood vaccination program'},
                {'name': 'Nutrition Support', 'description': 'Nutritional counseling and support'},
                {'name': 'Chronic Disease Management', 'description': 'Management of chronic conditions'}
            ]

            programs_created = 0
            for program_data in default_programs:
                if not Program.query.filter_by(name=program_data['name']).first():
                    program = Program(**program_data)
                    db.session.add(program)
                    programs_created += 1
            print(f"Added {programs_created} default programs")

            # Create admin user if not exists
            if not User.query.filter_by(username='admin').first():
                hashed_password = generate_password_hash(
                    'admin123',  # Change this in production!
                    method='pbkdf2:sha256:600000'  # Strong hashing
                )
                admin = User(
                    username='admin',
                    email='admin@healthsystem.org',
                    password=hashed_password,
                    role='admin'
                )
                db.session.add(admin)
                print("Admin user created")

            # Create test client if in development
            if app.config.get('FLASK_ENV') == 'development':
                if not Client.query.first():
                    test_client = Client(
                        first_name='Test',
                        last_name='Patient',
                        dob='1990-01-01',
                        gender='Other',
                        phone='+1234567890',
                        email='test@healthsystem.org'
                    )
                    db.session.add(test_client)
                    print("Test client created")

            db.session.commit()
            print("✅ Database initialized successfully!")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error initializing database: {str(e)}", file=sys.stderr)
            sys.exit(1)


if __name__ == '__main__':
    print("Starting database initialization...")
    init_db()