#!/usr/bin/env python3
"""
Comprehensive sample data seeding script for Health Management System.
This script populates all database tables with realistic sample data.
"""

import os
import sys
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal
import random

# Add the parent directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend import create_app
from backend.database import db
from backend.models import (
    User, Client, Program, ClientProgram, Visit, Appointment, Department, Staff,
    MedicalRecord, VitalSigns, Prescription, LabTest, LabOrder, Inventory,
    Bed, Admission, Billing, BillingItem, InsuranceProvider, ClientInsurance
)
from werkzeug.security import generate_password_hash


def clear_all_tables():
    """Clear all existing data from tables."""
    print("Clearing existing data...")
    
    # Clear in reverse dependency order
    db.session.query(BillingItem).delete()
    db.session.query(Billing).delete()
    db.session.query(ClientInsurance).delete()
    db.session.query(InsuranceProvider).delete()
    db.session.query(Admission).delete()
    db.session.query(Bed).delete()
    db.session.query(Inventory).delete()
    db.session.query(LabOrder).delete()
    db.session.query(LabTest).delete()
    db.session.query(Prescription).delete()
    db.session.query(VitalSigns).delete()
    db.session.query(MedicalRecord).delete()
    db.session.query(Staff).delete()
    db.session.query(Department).delete()
    db.session.query(Appointment).delete()
    db.session.query(Visit).delete()
    db.session.query(ClientProgram).delete()
    db.session.query(Program).delete()
    db.session.query(Client).delete()
    db.session.query(User).delete()
    
    db.session.commit()
    print("All tables cleared successfully.")


def create_users():
    """Create sample users."""
    print("Creating users...")
    
    users_data = [
        {
            'username': 'admin',
            'email': 'admin@hms.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin'
        },
        {
            'username': 'dr.smith',
            'email': 'dr.smith@hms.com',
            'password': generate_password_hash('doctor123'),
            'role': 'doctor'
        },
        {
            'username': 'dr.johnson',
            'email': 'dr.johnson@hms.com',
            'password': generate_password_hash('doctor123'),
            'role': 'doctor'
        },
        {
            'username': 'nurse.jane',
            'email': 'nurse.jane@hms.com',
            'password': generate_password_hash('nurse123'),
            'role': 'nurse'
        },
        {
            'username': 'nurse.bob',
            'email': 'nurse.bob@hms.com',
            'password': generate_password_hash('nurse123'),
            'role': 'nurse'
        },
        {
            'username': 'receptionist',
            'email': 'reception@hms.com',
            'password': generate_password_hash('reception123'),
            'role': 'receptionist'
        },
        {
            'username': 'lab.tech',
            'email': 'lab@hms.com',
            'password': generate_password_hash('lab123'),
            'role': 'lab_tech'
        },
        {
            'username': 'pharmacy',
            'email': 'pharmacy@hms.com',
            'password': generate_password_hash('pharmacy123'),
            'role': 'pharmacy'
        }
    ]
    
    users = []
    for user_data in users_data:
        user = User(**user_data)
        users.append(user)
        db.session.add(user)
    
    db.session.commit()
    print(f"Created {len(users)} users.")
    return users


def create_departments():
    """Create sample departments."""
    print("Creating departments...")
    
    departments_data = [
        {
            'name': 'Emergency Department',
            'description': 'Emergency medical services and trauma care',
            'location': 'Ground Floor, Wing A',
            'phone': '5551001',
            'email': 'emergency@hms.com'
        },
        {
            'name': 'Internal Medicine',
            'description': 'General internal medicine and adult care',
            'location': '2nd Floor, Wing B',
            'phone': '5551002',
            'email': 'internal@hms.com'
        },
        {
            'name': 'Pediatrics',
            'description': 'Child and adolescent healthcare',
            'location': '3rd Floor, Wing A',
            'phone': '5551003',
            'email': 'pediatrics@hms.com'
        },
        {
            'name': 'Cardiology',
            'description': 'Heart and cardiovascular care',
            'location': '2nd Floor, Wing C',
            'phone': '5551004',
            'email': 'cardio@hms.com'
        },
        {
            'name': 'Orthopedics',
            'description': 'Bone, joint, and musculoskeletal care',
            'location': '1st Floor, Wing B',
            'phone': '5551005',
            'email': 'ortho@hms.com'
        },
        {
            'name': 'Laboratory',
            'description': 'Diagnostic testing and pathology services',
            'location': 'Basement Level 1',
            'phone': '5551006',
            'email': 'lab@hms.com'
        },
        {
            'name': 'Pharmacy',
            'description': 'Medication dispensing and pharmaceutical care',
            'location': 'Ground Floor, Wing B',
            'phone': '5551007',
            'email': 'pharmacy@hms.com'
        }
    ]
    
    departments = []
    for dept_data in departments_data:
        dept = Department(**dept_data)
        departments.append(dept)
        db.session.add(dept)
    
    db.session.commit()
    print(f"Created {len(departments)} departments.")
    return departments


def create_staff(users, departments):
    """Create sample staff members."""
    print("Creating staff...")
    
    staff_data = [
        {
            'employee_id': 'DOC001',
            'user_id': [u for u in users if u.username == 'dr.smith'][0].id,
            'first_name': 'John',
            'last_name': 'Smith',
            'specialization': 'cardiology',
            'license_number': 'MD123456',
            'department_id': [d for d in departments if d.name == 'Cardiology'][0].id,
            'phone': '5552001',
            'email': 'dr.smith@hms.com',
            'employment_type': 'full_time',
            'hire_date': date(2020, 1, 15),
            'salary': Decimal('120000.00')
        },
        {
            'employee_id': 'DOC002',
            'user_id': [u for u in users if u.username == 'dr.johnson'][0].id,
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'specialization': 'pediatrics',
            'license_number': 'MD789012',
            'department_id': [d for d in departments if d.name == 'Pediatrics'][0].id,
            'phone': '5552002',
            'email': 'dr.johnson@hms.com',
            'employment_type': 'full_time',
            'hire_date': date(2019, 8, 1),
            'salary': Decimal('115000.00')
        },
        {
            'employee_id': 'NUR001',
            'user_id': [u for u in users if u.username == 'nurse.jane'][0].id,
            'first_name': 'Jane',
            'last_name': 'Doe',
            'specialization': 'general_medicine',
            'license_number': 'RN345678',
            'department_id': [d for d in departments if d.name == 'Internal Medicine'][0].id,
            'phone': '5552003',
            'email': 'nurse.jane@hms.com',
            'employment_type': 'full_time',
            'hire_date': date(2021, 3, 10),
            'salary': Decimal('65000.00')
        },
        {
            'employee_id': 'NUR002',
            'user_id': [u for u in users if u.username == 'nurse.bob'][0].id,
            'first_name': 'Robert',
            'last_name': 'Brown',
            'specialization': 'emergency',
            'license_number': 'RN901234',
            'department_id': [d for d in departments if d.name == 'Emergency Department'][0].id,
            'phone': '5552004',
            'email': 'nurse.bob@hms.com',
            'employment_type': 'full_time',
            'hire_date': date(2020, 11, 5),
            'salary': Decimal('68000.00')
        },
        {
            'employee_id': 'LAB001',
            'user_id': [u for u in users if u.username == 'lab.tech'][0].id,
            'first_name': 'Michael',
            'last_name': 'Wilson',
            'specialization': 'pathology',
            'license_number': 'LT567890',
            'department_id': [d for d in departments if d.name == 'Laboratory'][0].id,
            'phone': '5552005',
            'email': 'lab@hms.com',
            'employment_type': 'full_time',
            'hire_date': date(2021, 6, 1),
            'salary': Decimal('55000.00')
        },
        {
            'employee_id': 'PHR001',
            'user_id': [u for u in users if u.username == 'pharmacy'][0].id,
            'first_name': 'Emily',
            'last_name': 'Davis',
            'specialization': 'other',
            'license_number': 'PharmD123',
            'department_id': [d for d in departments if d.name == 'Pharmacy'][0].id,
            'phone': '5552006',
            'email': 'pharmacy@hms.com',
            'employment_type': 'full_time',
            'hire_date': date(2020, 4, 20),
            'salary': Decimal('85000.00')
        }
    ]
    
    staff_members = []
    for staff_info in staff_data:
        staff = Staff(**staff_info)
        staff_members.append(staff)
        db.session.add(staff)
    
    db.session.commit()
    print(f"Created {len(staff_members)} staff members.")
    return staff_members


def create_clients():
    """Create sample clients."""
    print("Creating clients...")
    
    clients_data = [
        {
            'first_name': 'Alice',
            'last_name': 'Johnson',
            'dob': date(1985, 3, 15),
            'gender': 'female',
            'phone': '1234567890',
            'email': 'alice.johnson@email.com',
            'address': '123 Main St, Anytown, ST 12345',
            'emergency_contact_name': 'Bob Johnson',
            'emergency_contact_phone': '0987654321',
            'notes': 'Allergic to penicillin'
        },
        {
            'first_name': 'Robert',
            'last_name': 'Smith',
            'dob': date(1978, 11, 22),
            'gender': 'male',
            'phone': '2345678901',
            'email': 'robert.smith@email.com',
            'address': '456 Oak Ave, Somewhere, ST 54321',
            'emergency_contact_name': 'Mary Smith',
            'emergency_contact_phone': '1098765432',
            'notes': 'Diabetes Type 2'
        },
        {
            'first_name': 'Maria',
            'last_name': 'Garcia',
            'dob': date(1992, 7, 8),
            'gender': 'female',
            'phone': '3456789012',
            'email': 'maria.garcia@email.com',
            'address': '789 Pine St, Elsewhere, ST 67890',
            'emergency_contact_name': 'Carlos Garcia',
            'emergency_contact_phone': '2109876543',
            'notes': 'Pregnant - 2nd trimester'
        },
        {
            'first_name': 'James',
            'last_name': 'Wilson',
            'dob': date(1965, 12, 3),
            'gender': 'male',
            'phone': '4567890123',
            'email': 'james.wilson@email.com',
            'address': '321 Elm Dr, Nowhere, ST 09876',
            'emergency_contact_name': 'Linda Wilson',
            'emergency_contact_phone': '3210987654',
            'notes': 'Hypertension, regular monitoring needed'
        },
        {
            'first_name': 'Emma',
            'last_name': 'Brown',
            'dob': date(2010, 4, 18),
            'gender': 'female',
            'phone': '5678901234',
            'email': 'emma.brown@email.com',
            'address': '654 Maple Ln, Anywhere, ST 13579',
            'emergency_contact_name': 'Jennifer Brown',
            'emergency_contact_phone': '4321098765',
            'notes': 'Pediatric patient - asthma'
        },
        {
            'first_name': 'David',
            'last_name': 'Lee',
            'dob': date(1988, 9, 14),
            'gender': 'male',
            'phone': '6789012345',
            'email': 'david.lee@email.com',
            'address': '987 Cedar St, Someplace, ST 24680',
            'emergency_contact_name': 'Susan Lee',
            'emergency_contact_phone': '5432109876',
            'notes': 'Recent surgery - follow-up needed'
        }
    ]
    
    clients = []
    for client_data in clients_data:
        client = Client(**client_data)
        clients.append(client)
        db.session.add(client)
    
    db.session.commit()
    print(f"Created {len(clients)} clients.")
    return clients


def create_programs():
    """Create sample health programs."""
    print("Creating programs...")
    
    programs_data = [
        {
            'name': 'Diabetes Management Program',
            'description': 'Comprehensive diabetes care and education program',
            'duration_days': 90
        },
        {
            'name': 'Cardiac Rehabilitation',
            'description': 'Post-cardiac event rehabilitation and lifestyle modification',
            'duration_days': 180
        },
        {
            'name': 'Weight Management Program',
            'description': 'Medically supervised weight loss program',
            'duration_days': 120
        },
        {
            'name': 'Smoking Cessation Program',
            'description': 'Support program for quitting smoking',
            'duration_days': 60
        },
        {
            'name': 'Prenatal Care Program',
            'description': 'Comprehensive prenatal care for expecting mothers',
            'duration_days': 270
        }
    ]
    
    programs = []
    for program_data in programs_data:
        program = Program(**program_data)
        programs.append(program)
        db.session.add(program)
    
    db.session.commit()
    print(f"Created {len(programs)} programs.")
    return programs


def create_client_programs(clients, programs):
    """Create sample client program enrollments."""
    print("Creating client program enrollments...")
    
    enrollments = []
    
    # Enroll some clients in programs
    client_program_pairs = [
        (clients[1], programs[0]),  # Robert in Diabetes Management
        (clients[2], programs[4]),  # Maria in Prenatal Care
        (clients[3], programs[1]),  # James in Cardiac Rehabilitation
        (clients[0], programs[2]),  # Alice in Weight Management
        (clients[5], programs[3]),  # David in Smoking Cessation
    ]
    
    for client, program in client_program_pairs:
        enrollment = ClientProgram(
            client_id=client.id,
            program_id=program.id,
            enrollment_date=date.today() - timedelta(days=random.randint(10, 60)),
            status='active',
            progress=random.randint(10, 80),
            notes=f'Enrolled in {program.name}'
        )
        enrollments.append(enrollment)
        db.session.add(enrollment)
    
    db.session.commit()
    print(f"Created {len(enrollments)} client program enrollments.")
    return enrollments


def create_appointments(clients, staff, departments):
    """Create sample appointments."""
    print("Creating appointments...")
    
    appointments = []
    
    # Create appointments for the next 30 days
    for i in range(15):
        appointment_date = datetime.now() + timedelta(
            days=random.randint(1, 30),
            hours=random.randint(8, 17),
            minutes=random.choice([0, 15, 30, 45])
        )
        
        appointment = Appointment(
            client_id=random.choice(clients).id,
            doctor_id=random.choice([s for s in staff if 'DOC' in s.employee_id]).id,
            department_id=random.choice(departments).id,
            date=appointment_date,
            duration_minutes=random.choice([30, 45, 60]),
            appointment_type=random.choice(['consultation', 'follow_up', 'procedure']),
            status=random.choice(['scheduled', 'completed']),
            reason=random.choice([
                'Regular checkup',
                'Follow-up visit',
                'Consultation',
                'Lab results review',
                'Medication adjustment'
            ]),
            priority=random.choice(['normal', 'high']),
            notes='Scheduled appointment'
        )
        appointments.append(appointment)
        db.session.add(appointment)
    
    db.session.commit()
    print(f"Created {len(appointments)} appointments.")
    return appointments


def create_visits(clients, users):
    """Create sample visits."""
    print("Creating visits...")
    
    visits = []
    
    for i in range(20):
        visit_date = datetime.now() - timedelta(days=random.randint(1, 90))
        
        visit = Visit(
            client_id=random.choice(clients).id,
            visit_date=visit_date,
            visit_type=random.choice(['consultation', 'follow_up', 'emergency']),
            purpose=random.choice([
                'Annual physical exam',
                'Flu symptoms',
                'Blood pressure check',
                'Medication refill',
                'Injury assessment',
                'Routine checkup'
            ]),
            diagnosis=random.choice([
                'Hypertension',
                'Upper respiratory infection',
                'Diabetes mellitus',
                'Anxiety disorder',
                'Musculoskeletal pain'
            ]),
            treatment=random.choice([
                'Prescribed medication',
                'Physical therapy recommended',
                'Follow-up in 2 weeks',
                'Lab tests ordered',
                'Lifestyle counseling provided'
            ]),
            notes='Standard visit documentation',
            created_by=random.choice(users).id
        )
        visits.append(visit)
        db.session.add(visit)
    
    db.session.commit()
    print(f"Created {len(visits)} visits.")
    return visits


def create_medical_records(clients, visits, users):
    """Create sample medical records."""
    print("Creating medical records...")
    
    records = []
    
    for i in range(10):
        record = MedicalRecord(
            client_id=random.choice(clients).id,
            visit_id=random.choice(visits).id,
            chief_complaint=random.choice([
                'Chest pain',
                'Shortness of breath',
                'Headache',
                'Abdominal pain',
                'Joint pain'
            ]),
            history_present_illness='Patient reports symptoms for the past few days',
            past_medical_history='No significant past medical history',
            family_history='Family history of hypertension and diabetes',
            social_history='Non-smoker, occasional alcohol use',
            allergies='NKDA (No Known Drug Allergies)',
            current_medications='Multivitamin, as needed pain medication',
            physical_examination='Vital signs stable, general examination normal',
            assessment=random.choice([
                'Hypertension, controlled',
                'Upper respiratory infection',
                'Anxiety, mild',
                'Back pain, chronic',
                'Routine health maintenance'
            ]),
            plan='Continue current treatment, follow-up as needed',
            created_by=random.choice(users).id
        )
        records.append(record)
        db.session.add(record)
    
    db.session.commit()
    print(f"Created {len(records)} medical records.")
    return records


def create_vital_signs(clients, visits, users):
    """Create sample vital signs."""
    print("Creating vital signs...")
    
    vitals = []
    
    for i in range(25):
        vital = VitalSigns(
            client_id=random.choice(clients).id,
            visit_id=random.choice(visits).id,
            recorded_at=datetime.now() - timedelta(days=random.randint(1, 60)),
            temperature=round(random.uniform(36.0, 38.5), 1),
            blood_pressure_systolic=random.randint(110, 180),
            blood_pressure_diastolic=random.randint(70, 110),
            heart_rate=random.randint(60, 100),
            respiratory_rate=random.randint(12, 20),
            oxygen_saturation=round(random.uniform(95.0, 100.0), 1),
            height=round(random.uniform(150.0, 190.0), 1),
            weight=round(random.uniform(50.0, 120.0), 1),
            bmi=round(random.uniform(18.5, 35.0), 1),
            notes='Vital signs recorded during visit',
            recorded_by=random.choice(users).id
        )
        vitals.append(vital)
        db.session.add(vital)
    
    db.session.commit()
    print(f"Created {len(vitals)} vital signs records.")
    return vitals


def create_lab_tests():
    """Create sample lab tests."""
    print("Creating lab tests...")
    
    tests_data = [
        {
            'name': 'Complete Blood Count (CBC)',
            'code': 'CBC001',
            'category': 'blood',
            'description': 'Complete blood count with differential',
            'normal_range': 'Various parameters',
            'unit': 'Various',
            'cost': Decimal('45.00'),
            'turnaround_time': 24
        },
        {
            'name': 'Basic Metabolic Panel (BMP)',
            'code': 'BMP001',
            'category': 'blood',
            'description': 'Basic metabolic panel including glucose, electrolytes',
            'normal_range': 'Various parameters',
            'unit': 'Various',
            'cost': Decimal('35.00'),
            'turnaround_time': 12
        },
        {
            'name': 'Lipid Panel',
            'code': 'LIP001',
            'category': 'blood',
            'description': 'Cholesterol and triglyceride testing',
            'normal_range': 'Total cholesterol < 200 mg/dL',
            'unit': 'mg/dL',
            'cost': Decimal('40.00'),
            'turnaround_time': 24
        },
        {
            'name': 'Urinalysis',
            'code': 'URA001',
            'category': 'urine',
            'description': 'Complete urinalysis with microscopy',
            'normal_range': 'No abnormal findings',
            'unit': 'Various',
            'cost': Decimal('25.00'),
            'turnaround_time': 4
        },
        {
            'name': 'Chest X-Ray',
            'code': 'CXR001',
            'category': 'imaging',
            'description': 'Chest radiograph, 2 views',
            'normal_range': 'No acute findings',
            'unit': 'Imaging',
            'cost': Decimal('120.00'),
            'turnaround_time': 2
        }
    ]
    
    tests = []
    for test_data in tests_data:
        test = LabTest(**test_data)
        tests.append(test)
        db.session.add(test)
    
    db.session.commit()
    print(f"Created {len(tests)} lab tests.")
    return tests


def create_lab_orders(clients, appointments, lab_tests, staff, users):
    """Create sample lab orders."""
    print("Creating lab orders...")
    
    orders = []
    
    for i in range(15):
        order = LabOrder(
            client_id=random.choice(clients).id,
            appointment_id=random.choice(appointments).id,
            test_id=random.choice(lab_tests).id,
            ordered_by=random.choice([s for s in staff if 'DOC' in s.employee_id]).id,
            status=random.choice(['ordered', 'collected', 'processing', 'completed']),
            priority=random.choice(['routine', 'urgent']),
            clinical_notes='Lab test ordered for diagnostic purposes',
            specimen_type=random.choice(['Blood', 'Urine', 'Saliva']),
            collection_date=datetime.now() - timedelta(days=random.randint(1, 30)),
            result_value=random.choice(['Normal', 'Abnormal', 'Pending']),
            result_notes='Results reviewed by physician',
            processed_by=random.choice(users).id
        )
        orders.append(order)
        db.session.add(order)
    
    db.session.commit()
    print(f"Created {len(orders)} lab orders.")
    return orders


def create_prescriptions(clients, appointments, staff):
    """Create sample prescriptions."""
    print("Creating prescriptions...")
    
    medications = [
        ('Lisinopril 10mg', '10mg', 'Once daily', '30 days', 30),
        ('Metformin 500mg', '500mg', 'Twice daily', '90 days', 180),
        ('Amoxicillin 500mg', '500mg', 'Three times daily', '10 days', 30),
        ('Ibuprofen 400mg', '400mg', 'As needed for pain', '30 days', 60),
        ('Atorvastatin 20mg', '20mg', 'Once daily at bedtime', '90 days', 90)
    ]
    
    prescriptions = []
    
    for i in range(12):
        med_name, dosage, frequency, duration, quantity = random.choice(medications)
        
        prescription = Prescription(
            client_id=random.choice(clients).id,
            appointment_id=random.choice(appointments).id,
            doctor_id=random.choice([s for s in staff if 'DOC' in s.employee_id]).id,
            medication_name=med_name,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            quantity=quantity,
            refills=random.randint(0, 3),
            instructions=f'Take {frequency.lower()}',
            status=random.choice(['active', 'completed']),
            prescribed_date=datetime.now() - timedelta(days=random.randint(1, 60)),
            start_date=date.today() - timedelta(days=random.randint(1, 30)),
            dispensed=random.choice([True, False])
        )
        prescriptions.append(prescription)
        db.session.add(prescription)
    
    db.session.commit()
    print(f"Created {len(prescriptions)} prescriptions.")
    return prescriptions


def create_inventory():
    """Create sample inventory items."""
    print("Creating inventory...")
    
    inventory_data = [
        {
            'name': 'Aspirin 325mg',
            'code': 'MED001',
            'category': 'medication',
            'description': 'Pain reliever and anti-inflammatory',
            'manufacturer': 'Generic Pharma',
            'batch_number': 'ASP2024001',
            'expiry_date': date(2025, 12, 31),
            'unit': 'bottles',
            'quantity_in_stock': 150,
            'minimum_stock_level': 25,
            'unit_price': Decimal('8.50'),
            'supplier': 'MedSupply Inc.',
            'location': 'Pharmacy Storage A1'
        },
        {
            'name': 'Surgical Gloves (Box)',
            'code': 'SUP001',
            'category': 'consumable',
            'description': 'Latex-free surgical gloves, size M',
            'manufacturer': 'MedGlove Co.',
            'batch_number': 'GLV2024002',
            'expiry_date': date(2026, 6, 30),
            'unit': 'boxes',
            'quantity_in_stock': 75,
            'minimum_stock_level': 20,
            'unit_price': Decimal('15.00'),
            'supplier': 'Medical Supplies Ltd.',
            'location': 'Supply Room B2'
        },
        {
            'name': 'Blood Pressure Monitor',
            'code': 'EQP001',
            'category': 'equipment',
            'description': 'Digital blood pressure monitor',
            'manufacturer': 'HealthTech Systems',
            'batch_number': 'BPM2024003',
            'unit': 'pieces',
            'quantity_in_stock': 12,
            'minimum_stock_level': 3,
            'unit_price': Decimal('125.00'),
            'supplier': 'Medical Equipment Co.',
            'location': 'Equipment Room C1'
        }
    ]
    
    inventory = []
    for item_data in inventory_data:
        item = Inventory(**item_data)
        inventory.append(item)
        db.session.add(item)
    
    db.session.commit()
    print(f"Created {len(inventory)} inventory items.")
    return inventory


def create_beds(departments):
    """Create sample beds."""
    print("Creating beds...")
    
    beds = []
    bed_counter = 1
    
    for dept in departments[:5]:  # Only create beds for first 5 departments
        for room in range(1, 4):  # 3 rooms per department
            for bed_num in range(1, 3):  # 2 beds per room
                bed = Bed(
                    bed_number=f'BED{bed_counter:03d}',
                    department_id=dept.id,
                    room_number=f'{room:03d}',
                    bed_type=random.choice(['general', 'icu', 'pediatric']),
                    status=random.choice(['available', 'occupied', 'maintenance']),
                    daily_rate=Decimal(str(random.randint(200, 800))),
                )
                beds.append(bed)
                db.session.add(bed)
                bed_counter += 1
    
    db.session.commit()
    print(f"Created {len(beds)} beds.")
    return beds


def create_admissions(clients, beds, staff, users):
    """Create sample admissions."""
    print("Creating admissions...")
    
    admissions = []
    
    for i in range(8):
        admission_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        admission = Admission(
            client_id=random.choice(clients).id,
            bed_id=random.choice([b for b in beds if b.status == 'occupied']).id if beds else None,
            attending_doctor_id=random.choice([s for s in staff if 'DOC' in s.employee_id]).id,
            admission_date=admission_date,
            admission_type=random.choice(['emergency', 'elective']),
            status=random.choice(['active', 'discharged']),
            reason=random.choice([
                'Chest pain evaluation',
                'Pneumonia treatment',
                'Surgical procedure',
                'Observation',
                'Emergency condition'
            ]),
            diagnosis=random.choice([
                'Acute myocardial infarction',
                'Community-acquired pneumonia',
                'Appendicitis',
                'Hypertensive crisis',
                'Diabetic ketoacidosis'
            ]),
            total_cost=Decimal(str(random.randint(5000, 25000))),
            created_by=random.choice(users).id
        )
        
        # Set discharge date for discharged patients
        if admission.status == 'discharged':
            admission.discharge_date = admission_date + timedelta(days=random.randint(1, 14))
            admission.discharge_summary = 'Patient recovered well and discharged home'
        
        admissions.append(admission)
        db.session.add(admission)
    
    db.session.commit()
    print(f"Created {len(admissions)} admissions.")
    return admissions


def create_insurance_providers():
    """Create sample insurance providers."""
    print("Creating insurance providers...")
    
    providers_data = [
        {
            'name': 'BlueCross BlueShield',
            'contact_person': 'John Administrator',
            'phone': '8001234567',
            'email': 'claims@bcbs.com',
            'address': '123 Insurance Blvd, City, ST 12345',
            'coverage_details': 'Full medical coverage with co-pays'
        },
        {
            'name': 'Aetna Health',
            'contact_person': 'Sarah Manager',
            'phone': '8002345678',
            'email': 'claims@aetna.com',
            'address': '456 Health Ave, Town, ST 54321',
            'coverage_details': 'PPO and HMO plans available'
        },
        {
            'name': 'United Healthcare',
            'contact_person': 'Mike Director',
            'phone': '8003456789',
            'email': 'claims@uhc.com',
            'address': '789 Medical St, Village, ST 67890',
            'coverage_details': 'Comprehensive health coverage'
        }
    ]
    
    providers = []
    for provider_data in providers_data:
        provider = InsuranceProvider(**provider_data)
        providers.append(provider)
        db.session.add(provider)
    
    db.session.commit()
    print(f"Created {len(providers)} insurance providers.")
    return providers


def create_client_insurance(clients, providers):
    """Create sample client insurance records."""
    print("Creating client insurance...")
    
    insurances = []
    
    for i, client in enumerate(clients[:4]):  # First 4 clients have insurance
        insurance = ClientInsurance(
            client_id=client.id,
            provider_id=providers[i % len(providers)].id,
            policy_number=f'POL{random.randint(100000, 999999)}',
            group_number=f'GRP{random.randint(1000, 9999)}',
            status='active',
            effective_date=date(2024, 1, 1),
            expiry_date=date(2024, 12, 31),
            copay_amount=Decimal('25.00'),
            deductible=Decimal('1500.00'),
            coverage_percentage=80.0,
            is_primary=True
        )
        insurances.append(insurance)
        db.session.add(insurance)
    
    db.session.commit()
    print(f"Created {len(insurances)} client insurance records.")
    return insurances


def create_billing(clients, visits, admissions, users):
    """Create sample billing records."""
    print("Creating billing records...")
    
    billings = []
    
    for i in range(10):
        total_amount = Decimal(str(random.randint(100, 5000)))
        paid_amount = Decimal(str(random.randint(0, int(total_amount))))
        
        billing = Billing(
            client_id=random.choice(clients).id,
            visit_id=random.choice(visits).id if random.choice([True, False]) else None,
            admission_id=random.choice(admissions).id if random.choice([True, False]) else None,
            invoice_number=f'INV{datetime.now().year}{i+1:04d}',
            total_amount=total_amount,
            paid_amount=paid_amount,
            status='paid' if paid_amount >= total_amount else 'partially_paid' if paid_amount > 0 else 'pending',
            payment_method=random.choice(['cash', 'card', 'insurance']),
            due_date=date.today() + timedelta(days=30),
            notes='Standard billing for services provided',
            created_by=random.choice(users).id
        )
        
        if billing.status in ['paid', 'partially_paid']:
            billing.payment_date = datetime.now() - timedelta(days=random.randint(1, 30))
        
        billings.append(billing)
        db.session.add(billing)
    
    db.session.commit()
    print(f"Created {len(billings)} billing records.")
    return billings


def create_billing_items(billings):
    """Create sample billing items."""
    print("Creating billing items...")
    
    items = []
    
    service_types = [
        ('consultation', 'Medical consultation', 150.00),
        ('lab_test', 'Laboratory test', 75.00),
        ('procedure', 'Medical procedure', 300.00),
        ('medication', 'Prescription medication', 25.00),
        ('bed_charges', 'Hospital bed charges', 250.00)
    ]
    
    for billing in billings:
        # Create 1-3 items per bill
        num_items = random.randint(1, 3)
        billing_total = Decimal('0.00')
        
        for _ in range(num_items):
            item_type, description, base_price = random.choice(service_types)
            quantity = random.randint(1, 3)
            unit_price = Decimal(str(base_price + random.randint(-50, 100)))
            total_price = unit_price * quantity
            
            item = BillingItem(
                billing_id=billing.id,
                item_type=item_type,
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                discount=Decimal('0.00')
            )
            items.append(item)
            db.session.add(item)
            billing_total += total_price
        
        # Update billing total
        billing.total_amount = billing_total
    
    db.session.commit()
    print(f"Created {len(items)} billing items.")
    return items


def main():
    """Main function to seed all sample data."""
    app = create_app()
    
    with app.app_context():
        print("Starting HMS database seeding...")
        print("=" * 50)
        
        # Clear existing data
        clear_all_tables()
        
        # Create sample data in dependency order
        users = create_users()
        departments = create_departments()
        staff = create_staff(users, departments)
        clients = create_clients()
        programs = create_programs()
        client_programs = create_client_programs(clients, programs)
        appointments = create_appointments(clients, staff, departments)
        visits = create_visits(clients, users)
        medical_records = create_medical_records(clients, visits, users)
        vital_signs = create_vital_signs(clients, visits, users)
        lab_tests = create_lab_tests()
        lab_orders = create_lab_orders(clients, appointments, lab_tests, staff, users)
        prescriptions = create_prescriptions(clients, appointments, staff)
        inventory = create_inventory()
        beds = create_beds(departments)
        admissions = create_admissions(clients, beds, staff, users)
        insurance_providers = create_insurance_providers()
        client_insurance = create_client_insurance(clients, insurance_providers)
        billings = create_billing(clients, visits, admissions, users)
        billing_items = create_billing_items(billings)
        
        print("=" * 50)
        print("HMS database seeding completed successfully!")
        print("\nSample login credentials:")
        print("- Admin: admin / admin123")
        print("- Doctor: dr.smith / doctor123")
        print("- Nurse: nurse.jane / nurse123")
        print("- Receptionist: receptionist / reception123")
        print("- Lab Tech: lab.tech / lab123")
        print("- Pharmacy: pharmacy / pharmacy123")


if __name__ == '__main__':
    main()
