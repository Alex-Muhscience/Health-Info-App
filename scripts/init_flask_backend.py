#!/usr/bin/env python3
"""
Initialize Flask backend with admin user and sample data
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend import create_app
from backend.database import db
from backend.models import User, Client, Program, ClientProgram, Visit, Appointment
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_admin_user():
    """Initialize admin user"""
    try:
        # Check if admin already exists
        admin_user = User.query.filter_by(username='admin').first()
        if admin_user:
            logger.info("Admin user already exists")
            return
        
        # Create admin user
        admin_user = User(
            username='admin',
            email='admin@healthsystem.org',
            password=generate_password_hash('admin123'),
            role='admin',
            is_active=True
        )
        
        db.session.add(admin_user)
        db.session.commit()
        logger.info("✅ Admin user created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating admin user: {e}")
        db.session.rollback()

def init_sample_data():  
    """Initialize sample data for demonstration"""
    try:
        # Check if sample data already exists
        if Client.query.count() > 0:
            logger.info("Sample data already exists")
            return
        
        # Create sample clients
        clients_data = [
            {
                'first_name': 'John',
                'last_name': 'Doe',
                'dob': date(1990, 5, 15),
                'gender': 'male',
                'phone': '+1234567890',
                'email': 'john.doe@example.com',
                'address': '123 Main St, Anytown, USA',
                'emergency_contact_name': 'Jane Doe',
                'emergency_contact_phone': '+1234567891',
                'notes': 'Regular checkup patient'
            },
            {
                'first_name': 'Alice',
                'last_name': 'Smith',
                'dob': date(1985, 8, 22),
                'gender': 'female',
                'phone': '+1987654321',
                'email': 'alice.smith@example.com',
                'address': '456 Oak Ave, Somewhere, USA',
                'emergency_contact_name': 'Bob Smith',
                'emergency_contact_phone': '+1987654322',
                'notes': 'Diabetes management patient'
            },
            {
                'first_name': 'Michael',
                'last_name': 'Johnson',
                'dob': date(1978, 12, 3),
                'gender': 'male',
                'phone': '+1122334455',
                'email': 'michael.johnson@example.com',
                'address': '789 Pine St, Elsewhere, USA',
                'emergency_contact_name': 'Sarah Johnson',
                'emergency_contact_phone': '+1122334456',
                'notes': 'Hypertension monitoring'
            }
        ]
        
        sample_clients = []
        for client_data in clients_data:
            client = Client(**client_data)
            db.session.add(client)
            sample_clients.append(client)
        
        db.session.flush()  # Flush to get IDs
        
        # Create sample programs
        programs_data = [
            {
                'name': 'Diabetes Management Program',
                'description': 'Comprehensive diabetes care and education program',
                'duration_days': 90,
                'is_active': True
            },
            {
                'name': 'Heart Health Program',
                'description': 'Cardiovascular health monitoring and lifestyle counseling',
                'duration_days': 180,
                'is_active': True
            },
            {
                'name': 'Weight Management Program',
                'description': 'Nutritional counseling and weight loss support',
                'duration_days': 120,
                'is_active': True
            }
        ]
        
        sample_programs = []
        for program_data in programs_data:
            program = Program(**program_data)
            db.session.add(program)
            sample_programs.append(program)
        
        db.session.flush()  # Flush to get IDs
        
        # Enroll clients in programs
        enrollments = [
            {
                'client_id': sample_clients[1].id,  # Alice in Diabetes Program
                'program_id': sample_programs[0].id,
                'enrollment_date': date.today() - timedelta(days=30),
                'status': 'active',
                'progress': 75
            },
            {
                'client_id': sample_clients[2].id,  # Michael in Heart Health Program
                'program_id': sample_programs[1].id,
                'enrollment_date': date.today() - timedelta(days=60),
                'status': 'active',
                'progress': 50
            }
        ]
        
        for enrollment_data in enrollments:
            enrollment = ClientProgram(**enrollment_data)
            db.session.add(enrollment)
        
        # Create sample appointments
        appointments_data = [
            {
                'client_id': sample_clients[0].id,
                'date': datetime.now() + timedelta(days=7),
                'duration_minutes': 30,
                'status': 'scheduled',
                'reason': 'Annual checkup'
            },
            {
                'client_id': sample_clients[1].id,
                'date': datetime.now() + timedelta(days=14),
                'duration_minutes': 45,
                'status': 'scheduled',
                'reason': 'Diabetes follow-up'
            }
        ]
        
        for appointment_data in appointments_data:
            appointment = Appointment(**appointment_data)
            db.session.add(appointment)
        
        # Create sample visits
        visits_data = [
            {
                'client_id': sample_clients[0].id,
                'visit_date': datetime.now() - timedelta(days=30),
                'visit_type': 'consultation',
                'purpose': 'Routine physical examination',
                'diagnosis': 'Patient in good health',
                'treatment': 'Continue current lifestyle',
                'notes': 'All vital signs normal'
            },
            {
                'client_id': sample_clients[1].id,
                'visit_date': datetime.now() - timedelta(days=15),
                'visit_type': 'follow_up',
                'purpose': 'Diabetes management review',
                'diagnosis': 'Type 2 diabetes, well controlled',
                'treatment': 'Continue current medication',
                'notes': 'HbA1c levels improved'
            }
        ]
        
        for visit_data in visits_data:
            visit = Visit(**visit_data)
            db.session.add(visit)
        
        db.session.commit()
        logger.info("✅ Sample data created successfully")
        
    except Exception as e:
        logger.error(f"❌ Error creating sample data: {e}")
        db.session.rollback()

def main():
    """Main function to initialize Flask backend"""
    logger.info("🚀 Initializing Flask Backend...")
    
    app = create_app()
    
    with app.app_context():
        # Create all database tables
        db.create_all()
        logger.info("✅ Database tables created")
        
        # Initialize admin user
        init_admin_user()
        
        # Initialize sample data
        init_sample_data()
        
        logger.info("🎉 Flask backend initialization completed!")

if __name__ == '__main__':
    main()
