#!/usr/bin/env python3
"""
Comprehensive Health Management System Database Setup
Creates database migrations and initializes the database with sample data
"""

import os
import sys
from datetime import datetime, date, timedelta
from decimal import Decimal
import uuid

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from backend import create_app
from backend.database import db
from backend.models import (
    User, Client, Program, ClientProgram, Visit, Appointment,
    Department, Staff, MedicalRecord, VitalSigns, Prescription,
    LabTest, LabOrder, Inventory, Bed, Admission, Billing, BillingItem,
    InsuranceProvider, ClientInsurance
)
from werkzeug.security import generate_password_hash


def create_sample_data():
    """Create comprehensive sample data for the health management system"""
    
    print("Creating sample data...")
    
    # Create admin user
    admin_user = User(
        username='admin',
        email='admin@healthsystem.com',
        password=generate_password_hash('admin123'),
        role='admin'
    )
    db.session.add(admin_user)
    
    # Create doctor user
    doctor_user = User(
        username='dr.smith',
        email='dr.smith@healthsystem.com',
        password=generate_password_hash('doctor123'),
        role='doctor'
    )
    db.session.add(doctor_user)
    
    # Create nurse user
    nurse_user = User(
        username='nurse.jane',
        email='nurse.jane@healthsystem.com',
        password=generate_password_hash('nurse123'),
        role='nurse'
    )
    db.session.add(nurse_user)
    
    # Create departments
    departments = [
        Department(
            name='Emergency Department',
            description='24/7 emergency medical care',
            location='Ground Floor, Wing A',
            phone='+15550101',
            email='emergency@healthsystem.com'
        ),
        Department(
            name='Cardiology',
            description='Heart and cardiovascular care',
            location='2nd Floor, Wing B',
            phone='+15550102',
            email='cardiology@healthsystem.com'
        ),
        Department(
            name='Pediatrics',
            description='Medical care for children',
            location='3rd Floor, Wing C',
            phone='+15550103',
            email='pediatrics@healthsystem.com'
        ),
        Department(
            name='Laboratory',
            description='Medical testing and diagnostics',
            location='Basement Level 1',
            phone='+15550104',
            email='lab@healthsystem.com'
        )
    ]
    
    for dept in departments:
        db.session.add(dept)
    
    db.session.commit()  # Commit to get department IDs
    
    # Create staff members
    staff_members = [
        Staff(
            employee_id='DOC001',
            user_id=doctor_user.id,
            first_name='John',
            last_name='Smith',
            specialization='cardiology',
            license_number='MD12345',
            department_id=departments[1].id,  # Cardiology
            phone='+15551001',
            email='dr.smith@healthsystem.com',
            employment_type='full_time',
            salary=Decimal('120000.00')
        ),
        Staff(
            employee_id='NUR001',
            user_id=nurse_user.id,
            first_name='Jane',
            last_name='Doe',
            specialization='general_medicine',
            license_number='RN12345',
            department_id=departments[0].id,  # Emergency
            phone='+15551002',
            email='nurse.jane@healthsystem.com',
            employment_type='full_time',
            salary=Decimal('65000.00')
        )
    ]
    
    for staff in staff_members:
        db.session.add(staff)
    
    # Create programs
    programs = [
        Program(
            name='Diabetes Management Program',
            description='Comprehensive diabetes care and education program',
            duration_days=90
        ),
        Program(
            name='Cardiac Rehabilitation',
            description='Post-cardiac event rehabilitation program',
            duration_days=180
        ),
        Program(
            name='Weight Management',
            description='Medically supervised weight loss program',
            duration_days=120
        )
    ]
    
    for program in programs:
        db.session.add(program)
    
    # Create sample clients
    clients = [
        Client(
            first_name='John',
            last_name='Patient',
            dob=date(1980, 5, 15),
            gender='male',
            phone='+15552001',
            email='john.patient@email.com',
            address='123 Main St, City, State 12345',
            emergency_contact_name='Jane Patient',
            emergency_contact_phone='+15552002'
        ),
        Client(
            first_name='Mary',
            last_name='Johnson',
            dob=date(1975, 8, 22),
            gender='female',
            phone='+15552003',
            email='mary.johnson@email.com',
            address='456 Oak Ave, City, State 12345',
            emergency_contact_name='Bob Johnson',
            emergency_contact_phone='+15552004'
        ),
        Client(
            first_name='Robert',
            last_name='Brown',
            dob=date(1990, 12, 3),
            gender='male',
            phone='+15552005',
            email='robert.brown@email.com',
            address='789 Pine St, City, State 12345',
            emergency_contact_name='Lisa Brown',
            emergency_contact_phone='+15552006'
        )
    ]
    
    for client in clients:
        db.session.add(client)
    
    db.session.commit()  # Commit to get IDs
    
    # Create beds
    bed_types = ['general', 'icu', 'pediatric', 'emergency']
    for i, dept in enumerate(departments):
        for j in range(5):  # 5 beds per department
            bed = Bed(
                bed_number=f'{dept.name[:3].upper()}-{j+1:02d}',
                department_id=dept.id,
                room_number=f'{i+1}{j+1:02d}',
                bed_type=bed_types[i % len(bed_types)],
                daily_rate=Decimal('250.00') if bed_types[i % len(bed_types)] == 'icu' else Decimal('150.00')
            )
            db.session.add(bed)
    
    # Create lab tests
    lab_tests = [
        LabTest(
            name='Complete Blood Count',
            code='CBC',
            category='blood',
            description='Full blood panel including RBC, WBC, platelets',
            normal_range='Various',
            cost=Decimal('45.00'),
            turnaround_time=4
        ),
        LabTest(
            name='Basic Metabolic Panel',
            code='BMP',
            category='blood',
            description='Glucose, electrolytes, kidney function',
            normal_range='Various',
            cost=Decimal('35.00'),
            turnaround_time=4
        ),
        LabTest(
            name='Lipid Panel',
            code='LIPID',
            category='blood',
            description='Cholesterol and triglycerides',
            normal_range='Various',
            cost=Decimal('55.00'),
            turnaround_time=6
        ),
        LabTest(
            name='Urinalysis',
            code='UA',
            category='urine',
            description='Complete urine analysis',
            normal_range='Various',
            cost=Decimal('25.00'),
            turnaround_time=2
        )
    ]
    
    for test in lab_tests:
        db.session.add(test)
    
    # Create inventory items
    inventory_items = [
        Inventory(
            name='Paracetamol 500mg',
            code='PAR500',
            category='medication',
            manufacturer='PharmaCorp',
            batch_number='PAR2024001',
            expiry_date=date(2025, 12, 31),
            unit='tablets',
            quantity_in_stock=5000,
            minimum_stock_level=1000,
            unit_price=Decimal('0.15'),
            supplier='MedSupply Inc.'
        ),
        Inventory(
            name='Disposable Syringes 5ml',
            code='SYR5ML',
            category='consumable',
            manufacturer='MedDevice Co.',
            batch_number='SYR2024001',
            expiry_date=date(2026, 6, 30),
            unit='pieces',
            quantity_in_stock=2000,
            minimum_stock_level=500,
            unit_price=Decimal('0.25'),
            supplier='MedSupply Inc.'
        ),
        Inventory(
            name='Blood Pressure Monitor',
            code='BPM001',
            category='equipment',
            manufacturer='HealthTech',
            batch_number='BPM2024001',
            unit='pieces',
            quantity_in_stock=25,
            minimum_stock_level=5,
            unit_price=Decimal('125.00'),
            supplier='HealthEquip Ltd.'
        )
    ]
    
    for item in inventory_items:
        db.session.add(item)
    
    # Create insurance providers
    insurance_providers = [
        InsuranceProvider(
            name='HealthCare Plus',
            contact_person='Sarah Wilson',
            phone='+15553001',
            email='contact@healthcareplus.com',
            address='100 Insurance Blvd, City, State 12345',
            coverage_details='Full coverage for in-network providers'
        ),
        InsuranceProvider(
            name='MediCare Solutions',
            contact_person='Mike Davis',
            phone='+15553002',
            email='info@medicaresolutions.com',
            address='200 Coverage St, City, State 12345',
            coverage_details='80% coverage after deductible'
        )
    ]
    
    for provider in insurance_providers:
        db.session.add(provider)
    
    db.session.commit()  # Commit to get all IDs
    
    # Create appointments
    base_date = datetime.now()
    appointments = []
    
    for i, client in enumerate(clients):
        appointment = Appointment(
            client_id=client.id,
            doctor_id=staff_members[0].id,  # Dr. Smith
            department_id=departments[1].id,  # Cardiology
            date=base_date + timedelta(days=i+1, hours=10),
            appointment_type='consultation',
            reason='Regular checkup',
            status='scheduled'
        )
        appointments.append(appointment)
        db.session.add(appointment)
    
    # Create visits
    for i, client in enumerate(clients):
        visit = Visit(
            client_id=client.id,
            visit_date=base_date - timedelta(days=i*7),
            visit_type='consultation',
            purpose='Annual physical examination',
            diagnosis='Routine examination - no acute findings',
            treatment='Continue current medications, lifestyle counseling',
            created_by=doctor_user.id
        )
        db.session.add(visit)
    
    # Create vital signs
    for i, client in enumerate(clients):
        vitals = VitalSigns(
            client_id=client.id,
            temperature=36.5 + (i * 0.2),
            blood_pressure_systolic=120 + (i * 5),
            blood_pressure_diastolic=80 + (i * 2),
            heart_rate=72 + (i * 3),
            respiratory_rate=16 + i,
            oxygen_saturation=98.0 + (i * 0.5),
            height=170.0 + (i * 5),
            weight=70.0 + (i * 10),
            bmi=24.2 + (i * 2),
            recorded_by=nurse_user.id
        )
        db.session.add(vitals)
    
    # Create prescriptions
    medications = ['Lisinopril 10mg', 'Metformin 500mg', 'Atorvastatin 20mg']
    for i, client in enumerate(clients):
        prescription = Prescription(
            client_id=client.id,
            appointment_id=appointments[i].id,
            doctor_id=staff_members[0].id,
            medication_name=medications[i],
            dosage='1 tablet',
            frequency='Once daily',
            duration='30 days',
            quantity=30,
            instructions='Take with food',
            start_date=date.today(),
            end_date=date.today() + timedelta(days=30)
        )
        db.session.add(prescription)
    
    # Create lab orders
    for i, client in enumerate(clients):
        lab_order = LabOrder(
            client_id=client.id,
            appointment_id=appointments[i].id,
            test_id=lab_tests[i].id,
            ordered_by=staff_members[0].id,
            clinical_notes='Routine screening',
            specimen_type='Blood',
            priority='routine'
        )
        db.session.add(lab_order)
    
    # Create client insurance
    for i, client in enumerate(clients):
        if i < len(insurance_providers):
            client_insurance = ClientInsurance(
                client_id=client.id,
                provider_id=insurance_providers[i].id,
                policy_number=f'POL{client.id}001',
                effective_date=date.today() - timedelta(days=365),
                expiry_date=date.today() + timedelta(days=365),
                copay_amount=Decimal('25.00'),
                deductible=Decimal('1000.00'),
                coverage_percentage=80.0
            )
            db.session.add(client_insurance)
    
    # Create admissions
    admission = Admission(
        client_id=clients[0].id,
        bed_id=db.session.query(Bed).first().id,
        attending_doctor_id=staff_members[0].id,
        admission_type='elective',
        reason='Cardiac catheterization procedure',
        diagnosis='Coronary artery disease',
        created_by=doctor_user.id
    )
    db.session.add(admission)
    
    # Create billing
    billing = Billing(
        client_id=clients[0].id,
        invoice_number='INV2024001',
        total_amount=Decimal('2500.00'),
        status='pending',
        due_date=date.today() + timedelta(days=30),
        created_by=admin_user.id
    )
    db.session.add(billing)
    
    db.session.commit()
    
    # Create billing items
    billing_items = [
        BillingItem(
            billing_id=billing.id,
            item_type='consultation',
            description='Cardiology consultation',
            quantity=1,
            unit_price=Decimal('200.00'),
            total_price=Decimal('200.00')
        ),
        BillingItem(
            billing_id=billing.id,
            item_type='procedure',
            description='Cardiac catheterization',
            quantity=1,
            unit_price=Decimal('1500.00'),
            total_price=Decimal('1500.00')
        ),
        BillingItem(
            billing_id=billing.id,
            item_type='bed_charges',
            description='ICU bed (2 days)',
            quantity=2,
            unit_price=Decimal('400.00'),
            total_price=Decimal('800.00')
        )
    ]
    
    for item in billing_items:
        db.session.add(item)
    
    # Create client programs
    client_program = ClientProgram(
        client_id=clients[0].id,
        program_id=programs[1].id,  # Cardiac Rehabilitation
        enrollment_date=date.today(),
        status='active',
        progress=25
    )
    db.session.add(client_program)
    
    db.session.commit()
    print("Sample data created successfully!")


def main():
    """Main function to set up the comprehensive database"""
    
    # Set environment for development
    os.environ.setdefault('FLASK_ENV', 'development')
    
    print("Initializing Comprehensive Health Management System Database...")
    
    # Create Flask app
    app = create_app('development')
    
    with app.app_context():
        print("Creating database tables...")
        
        # Create all tables (if they don't exist)
        db.create_all()
        
        # Clear existing data if any
        try:
            # Delete in reverse order of dependencies
            db.session.query(BillingItem).delete()
            db.session.query(ClientInsurance).delete()
            db.session.query(ClientProgram).delete()
            db.session.query(LabOrder).delete()
            db.session.query(Prescription).delete()
            db.session.query(VitalSigns).delete()
            db.session.query(MedicalRecord).delete()
            db.session.query(Billing).delete()
            db.session.query(Admission).delete()
            db.session.query(Visit).delete()
            db.session.query(Appointment).delete()
            db.session.query(Staff).delete()
            db.session.query(Bed).delete()
            db.session.query(LabTest).delete()
            db.session.query(Inventory).delete()
            db.session.query(InsuranceProvider).delete()
            db.session.query(Department).delete()
            db.session.query(Program).delete()
            db.session.query(Client).delete()
            db.session.query(User).delete()
            db.session.commit()
            print("Existing data cleared successfully.")
        except Exception as e:
            print(f"Warning: Error clearing existing data: {e}")
            db.session.rollback()
        
        print("Database tables created successfully!")
        
        # Create sample data
        try:
            create_sample_data()
            print("\nDatabase setup completed successfully!")
            print("\nDefault login credentials:")
            print("Admin - Username: admin, Password: admin123")
            print("Doctor - Username: dr.smith, Password: doctor123")
            print("Nurse - Username: nurse.jane, Password: nurse123")
            
        except Exception as e:
            print(f"\nError creating sample data: {str(e)}")
            db.session.rollback()
            return False
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
