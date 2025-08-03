#!/usr/bin/env python3
"""Sample data seeding script for the Health Management System."""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import db
from backend.models import (
    User, Client, Program, Department, Staff, Visit, Appointment, 
    MedicalRecord, VitalSigns, LabTest, LabOrder, Prescription, 
    Inventory, Bed, Admission, Billing, BillingItem, 
    InsuranceProvider, ClientInsurance, ClientProgram
)
from werkzeug.security import generate_password_hash
import datetime
import random
from decimal import Decimal


def clear_existing_data():
    """Clear all existing data from the database."""
    print("Clearing existing data...")
    
    # Drop all tables and recreate them
    db.drop_all()
    db.create_all()
    
    print("Database cleared and recreated.")


def generate_sample_data():
    """Generate comprehensive sample data for the Health Management System."""
    print("Generating sample data...")
    
    try:
        # Step 1: Create Users
        print("Creating users...")
        users = [
            User(
                username='admin',
                email='admin@healthsystem.com',
                password=generate_password_hash('admin123'),
                role='admin',
                is_active=True
            ),
            User(
                username='dr_johnson',
                email='dr.johnson@healthsystem.com',
                password=generate_password_hash('doctor123'),
                role='doctor',
                is_active=True
            ),
            User(
                username='dr_wilson',
                email='dr.wilson@healthsystem.com',
                password=generate_password_hash('doctor123'),
                role='doctor',
                is_active=True
            ),
            User(
                username='nurse_mary',
                email='nurse.mary@healthsystem.com',
                password=generate_password_hash('nurse123'),
                role='nurse',
                is_active=True
            ),
            User(
                username='receptionist',
                email='reception@healthsystem.com',
                password=generate_password_hash('reception123'),
                role='receptionist',
                is_active=True
            ),
            User(
                username='lab_tech',
                email='lab@healthsystem.com',
                password=generate_password_hash('lab123'),
                role='lab_tech',
                is_active=True
            )
        ]
        db.session.add_all(users)
        db.session.commit()
        
        # Step 2: Create Departments
        print("Creating departments...")
        departments = [
            Department(
                name='Cardiology',
                description='Heart and cardiovascular specialists',
                location='Building A, Floor 2',
                phone='+1-555-0101',
                email='cardio@healthsystem.com'
            ),
            Department(
                name='Neurology',
                description='Brain and nervous system specialists',
                location='Building B, Floor 3',
                phone='+1-555-0102',
                email='neuro@healthsystem.com'
            ),
            Department(
                name='Emergency',
                description='Emergency and trauma care',
                location='Building A, Ground Floor',
                phone='+1-555-0103',
                email='emergency@healthsystem.com'
            ),
            Department(
                name='Pediatrics',
                description='Children healthcare',
                location='Building C, Floor 1',
                phone='+1-555-0104',
                email='pediatrics@healthsystem.com'
            ),
            Department(
                name='Laboratory',
                description='Medical testing and diagnostics',
                location='Building A, Basement',
                phone='+1-555-0105',
                email='lab@healthsystem.com'
            )
        ]
        db.session.add_all(departments)
        db.session.commit()

        # Step 3: Create Staff
        print("Creating staff...")
        staff = [
            Staff(
                employee_id='DOC001',
                user_id=users[1].id,  # dr_johnson
                first_name='Robert',
                last_name='Johnson',
                specialization='cardiology',
                license_number='MD123456',
                department_id=departments[0].id,  # Cardiology
                phone='+1-555-1001',
                email='dr.johnson@healthsystem.com',
                employment_type='full_time',
                hire_date=datetime.date(2020, 1, 15),
                salary=Decimal('150000.00')
            ),
            Staff(
                employee_id='DOC002',
                user_id=users[2].id,  # dr_wilson
                first_name='Sarah',
                last_name='Wilson',
                specialization='neurology',
                license_number='MD789012',
                department_id=departments[1].id,  # Neurology
                phone='+1-555-1002',
                email='dr.wilson@healthsystem.com',
                employment_type='full_time',
                hire_date=datetime.date(2019, 6, 10),
                salary=Decimal('145000.00')
            ),
            Staff(
                employee_id='NUR001',
                user_id=users[3].id,  # nurse_mary
                first_name='Mary',
                last_name='Thompson',
                specialization='general_medicine',
                license_number='RN345678',
                department_id=departments[0].id,  # Cardiology
                phone='+1-555-2001',
                email='nurse.mary@healthsystem.com',
                employment_type='full_time',
                hire_date=datetime.date(2021, 3, 20),
                salary=Decimal('65000.00')
            ),
            Staff(
                employee_id='LAB001',
                user_id=users[5].id,  # lab_tech
                first_name='James',
                last_name='Rodriguez',
                specialization='pathology',
                license_number='LT987654',
                department_id=departments[4].id,  # Laboratory
                phone='+1-555-3001',
                email='lab@healthsystem.com',
                employment_type='full_time',
                hire_date=datetime.date(2020, 8, 5),
                salary=Decimal('55000.00')
            )
        ]
        db.session.add_all(staff)
        db.session.commit()
        
        # Update department heads
        departments[0].head_id = staff[0].id  # Dr. Johnson heads Cardiology
        departments[1].head_id = staff[1].id  # Dr. Wilson heads Neurology
        departments[4].head_id = staff[3].id  # James heads Laboratory
        db.session.commit()

        # Step 4: Create Programs
        print("Creating programs...")
        programs = [
            Program(
                name='Cardiac Rehabilitation',
                description='Comprehensive cardiac recovery program for post-surgery patients',
                duration_days=90
            ),
            Program(
                name='Diabetes Management',
                description='Long-term diabetes care and monitoring program',
                duration_days=180
            ),
            Program(
                name='Hypertension Control',
                description='Blood pressure monitoring and lifestyle management',
                duration_days=120
            ),
            Program(
                name='Weight Management',
                description='Structured weight loss and nutrition program',
                duration_days=60
            ),
            Program(
                name='Preventive Care',
                description='Regular health screenings and preventive measures',
                duration_days=365
            )
        ]
        db.session.add_all(programs)
        db.session.commit()

        # Step 5: Create Clients
        print("Creating clients...")
        clients = [
            Client(
                first_name='John',
                last_name='Doe',
                dob=datetime.date(1980, 5, 15),
                gender='male',
                phone='+1-555-4001',
                email='john.doe@email.com',
                address='123 Main St, Anytown, State 12345',
                emergency_contact_name='Jane Doe',
                emergency_contact_phone='+1-555-4002',
                notes='Patient with history of hypertension'
            ),
            Client(
                first_name='Jane',
                last_name='Smith',
                dob=datetime.date(1990, 8, 22),
                gender='female',
                phone='+1-555-4003',
                email='jane.smith@email.com',
                address='456 Oak Ave, Somewhere, State 67890',
                emergency_contact_name='Robert Smith',
                emergency_contact_phone='+1-555-4004',
                notes='Regular checkup patient'
            ),
            Client(
                first_name='Michael',
                last_name='Brown',
                dob=datetime.date(1975, 12, 3),
                gender='male',
                phone='+1-555-4005',
                email='michael.brown@email.com',
                address='789 Pine St, Elsewhere, State 13579',
                emergency_contact_name='Lisa Brown',
                emergency_contact_phone='+1-555-4006',
                notes='Diabetic patient requiring regular monitoring'
            ),
            Client(
                first_name='Sarah',
                last_name='Davis',
                dob=datetime.date(1985, 3, 18),
                gender='female',
                phone='+1-555-4007',
                email='sarah.davis@email.com',
                address='321 Elm Dr, Nowhere, State 24680',
                emergency_contact_name='Tom Davis',
                emergency_contact_phone='+1-555-4008',
                notes='Pregnant patient - regular prenatal care'
            ),
            Client(
                first_name='Robert',
                last_name='Wilson',
                dob=datetime.date(1965, 9, 10),
                gender='male',
                phone='+1-555-4009',
                email='robert.wilson@email.com',
                address='654 Maple Ln, Anywhere, State 97531',
                emergency_contact_name='Betty Wilson',
                emergency_contact_phone='+1-555-4010',
                notes='Post-cardiac surgery patient'
            )
        ]
        db.session.add_all(clients)
        db.session.commit()

        # Step 6: Create Client Programs
        print("Creating client programs...")
        client_programs = [
            ClientProgram(
                client_id=clients[0].id,
                program_id=programs[2].id,  # Hypertension Control
                enrollment_date=datetime.date(2024, 1, 15),
                status='active',
                progress=45
            ),
            ClientProgram(
                client_id=clients[2].id,
                program_id=programs[1].id,  # Diabetes Management
                enrollment_date=datetime.date(2023, 12, 1),
                status='active',
                progress=70
            ),
            ClientProgram(
                client_id=clients[4].id,
                program_id=programs[0].id,  # Cardiac Rehabilitation
                enrollment_date=datetime.date(2024, 2, 1),
                status='active',
                progress=30
            )
        ]
        db.session.add_all(client_programs)
        db.session.commit()

        # Step 7: Create Insurance Providers
        print("Creating insurance providers...")
        insurance_providers = [
            InsuranceProvider(
                name='HealthFirst Insurance',
                contact_person='Amanda Miller',
                phone='+1-800-555-0001',
                email='claims@healthfirst.com',
                address='100 Insurance Blvd, Metro City, State 11111',
                coverage_details='Comprehensive health coverage with dental and vision'
            ),
            InsuranceProvider(
                name='MediCare Plus',
                contact_person='David Chen',
                phone='+1-800-555-0002',
                email='support@medicareplus.com',
                address='200 Healthcare Way, Capital City, State 22222',
                coverage_details='Basic health coverage with optional add-ons'
            ),
            InsuranceProvider(
                name='United Health Group',
                contact_person='Jennifer Taylor',
                phone='+1-800-555-0003',
                email='customercare@uhg.com',
                address='300 Medical Center Dr, Health City, State 33333',
                coverage_details='Premium health insurance with global coverage'
            )
        ]
        db.session.add_all(insurance_providers)
        db.session.commit()

        # Step 8: Create Client Insurance
        print("Creating client insurance...")
        client_insurances = [
            ClientInsurance(
                client_id=clients[0].id,
                provider_id=insurance_providers[0].id,
                policy_number='HF2024001',
                group_number='GRP001',
                status='active',
                effective_date=datetime.date(2024, 1, 1),
                expiry_date=datetime.date(2024, 12, 31),
                copay_amount=Decimal('25.00'),
                deductible=Decimal('1000.00'),
                coverage_percentage=80.0
            ),
            ClientInsurance(
                client_id=clients[1].id,
                provider_id=insurance_providers[1].id,
                policy_number='MP2024002',
                group_number='GRP002',
                status='active',
                effective_date=datetime.date(2024, 1, 1),
                expiry_date=datetime.date(2024, 12, 31),
                copay_amount=Decimal('30.00'),
                deductible=Decimal('1500.00'),
                coverage_percentage=70.0
            )
        ]
        db.session.add_all(client_insurances)
        db.session.commit()

        # Step 9: Create Beds
        print("Creating beds...")
        beds = [
            Bed(
                bed_number='A101',
                department_id=departments[0].id,
                room_number='101',
                bed_type='general',
                status='available',
                daily_rate=Decimal('250.00')
            ),
            Bed(
                bed_number='A102',
                department_id=departments[0].id,
                room_number='102',
                bed_type='general',
                status='occupied',
                daily_rate=Decimal('250.00')
            ),
            Bed(
                bed_number='B201',
                department_id=departments[1].id,
                room_number='201',
                bed_type='general',
                status='available',
                daily_rate=Decimal('275.00')
            ),
            Bed(
                bed_number='ICU001',
                department_id=departments[2].id,
                room_number='ICU1',
                bed_type='icu',
                status='available',
                daily_rate=Decimal('500.00')
            )
        ]
        db.session.add_all(beds)
        db.session.commit()

        # Step 10: Create Visits
        print("Creating visits...")
        visits = [
            Visit(
                client_id=clients[0].id,
                visit_date=datetime.datetime.now() - datetime.timedelta(days=7),
                visit_type='consultation',
                purpose='Hypertension follow-up',
                diagnosis='Essential hypertension',
                treatment='Continue current medication, lifestyle modifications',
                notes='Blood pressure well controlled',
                created_by=users[1].id
            ),
            Visit(
                client_id=clients[1].id,
                visit_date=datetime.datetime.now() - datetime.timedelta(days=3),
                visit_type='consultation',
                purpose='Annual physical exam',
                diagnosis='No acute findings',
                treatment='Continue preventive care',
                notes='Patient in good health',
                created_by=users[2].id
            ),
            Visit(
                client_id=clients[2].id,
                visit_date=datetime.datetime.now() - datetime.timedelta(days=1),
                visit_type='follow_up',
                purpose='Diabetes management',
                diagnosis='Type 2 diabetes mellitus',
                treatment='Adjust insulin dosage',
                notes='HbA1c improving',
                created_by=users[1].id
            )
        ]
        db.session.add_all(visits)
        db.session.commit()

        # Step 11: Create Appointments
        print("Creating appointments...")
        today = datetime.datetime.now()
        appointments = [
            Appointment(
                client_id=clients[0].id,
                doctor_id=staff[0].id,
                department_id=departments[0].id,
                date=today + datetime.timedelta(days=1, hours=9),
                duration_minutes=30,
                appointment_type='follow_up',
                status='scheduled',
                reason='Hypertension follow-up',
                priority='normal',
                notes='Regular follow-up appointment',
                created_by=users[4].id
            ),
            Appointment(
                client_id=clients[1].id,
                doctor_id=staff[1].id,
                department_id=departments[1].id,
                date=today + datetime.timedelta(days=2, hours=14),
                duration_minutes=45,
                appointment_type='consultation',
                status='scheduled',
                reason='Neurological consultation',
                priority='normal',
                notes='New patient consultation',
                created_by=users[4].id
            ),
            Appointment(
                client_id=clients[2].id,
                doctor_id=staff[0].id,
                department_id=departments[0].id,
                date=today + datetime.timedelta(days=3, hours=11),
                duration_minutes=30,
                appointment_type='follow_up',
                status='scheduled',
                reason='Diabetes check-up',
                priority='normal',
                notes='Routine diabetes monitoring',
                created_by=users[4].id
            ),
            Appointment(
                client_id=clients[3].id,
                doctor_id=staff[0].id,
                department_id=departments[0].id,
                date=today - datetime.timedelta(days=1, hours=-10),
                duration_minutes=30,
                appointment_type='consultation',
                status='completed',
                reason='Prenatal checkup',
                priority='high',
                notes='Routine prenatal care',
                created_by=users[4].id
            )
        ]
        db.session.add_all(appointments)
        db.session.commit()

        # Step 12: Create Lab Tests
        print("Creating lab tests...")
        lab_tests = [
            LabTest(
                name='Complete Blood Count (CBC)',
                code='CBC001',
                category='blood',
                description='Complete blood count with differential',
                normal_range='WBC: 4-11 K/uL, RBC: 4.5-5.5 M/uL',
                unit='Various',
                cost=Decimal('45.00'),
                turnaround_time=4
            ),
            LabTest(
                name='Basic Metabolic Panel',
                code='BMP001',
                category='blood',
                description='Basic chemistry panel',
                normal_range='Glucose: 70-100 mg/dL, Sodium: 136-145 mEq/L',
                unit='mg/dL, mEq/L',
                cost=Decimal('35.00'),
                turnaround_time=2
            ),
            LabTest(
                name='Lipid Panel',
                code='LIP001',
                category='blood',
                description='Cholesterol and triglycerides',
                normal_range='Total Chol: <200 mg/dL, HDL: >40 mg/dL',
                unit='mg/dL',
                cost=Decimal('55.00'),
                turnaround_time=6
            ),
            LabTest(
                name='HbA1c',
                code='A1C001',
                category='blood',
                description='Hemoglobin A1c for diabetes monitoring',
                normal_range='<5.7%',
                unit='%',
                cost=Decimal('40.00'),
                turnaround_time=8
            ),
            LabTest(
                name='Chest X-Ray',
                code='CXR001',
                category='imaging',
                description='Chest radiograph',
                normal_range='No acute findings',
                unit='N/A',
                cost=Decimal('85.00'),
                turnaround_time=1
            ),
            LabTest(
                name='Urinalysis',
                code='UA001',
                category='urine',
                description='Complete urinalysis',
                normal_range='Clear, yellow, specific gravity 1.003-1.030',
                unit='Various',
                cost=Decimal('25.00'),
                turnaround_time=2
            )
        ]
        db.session.add_all(lab_tests)
        db.session.commit()

        # Step 13: Create Lab Orders
        print("Creating lab orders...")
        lab_orders = [
            LabOrder(
                client_id=clients[0].id,
                appointment_id=appointments[0].id,
                test_id=lab_tests[0].id,  # CBC
                ordered_by=staff[0].id,
                status='completed',
                priority='routine',
                clinical_notes='Annual physical exam',
                specimen_type='Blood',
                collection_date=datetime.datetime.now() - datetime.timedelta(days=2),
                result_date=datetime.datetime.now() - datetime.timedelta(days=1),
                result_value='WBC: 7.2, RBC: 4.8, Hgb: 14.2, Hct: 42.1',
                result_notes='Normal complete blood count',
                abnormal_flag=False,
                processed_by=users[5].id
            ),
            LabOrder(
                client_id=clients[2].id,
                test_id=lab_tests[3].id,  # HbA1c
                ordered_by=staff[0].id,
                status='completed',
                priority='routine',
                clinical_notes='Diabetes monitoring',
                specimen_type='Blood',
                collection_date=datetime.datetime.now() - datetime.timedelta(days=3),
                result_date=datetime.datetime.now() - datetime.timedelta(days=1),
                result_value='7.2%',
                result_notes='Elevated HbA1c, diabetes suboptimally controlled',
                abnormal_flag=True,
                processed_by=users[5].id
            )
        ]
        db.session.add_all(lab_orders)
        db.session.commit()

        # Step 14: Create Medical Records
        print("Creating medical records...")
        medical_records = [
            MedicalRecord(
                client_id=clients[0].id,
                visit_id=visits[0].id,
                chief_complaint='Follow-up for high blood pressure',
                history_present_illness='Patient reports adherence to medications. No chest pain, shortness of breath, or palpitations.',
                past_medical_history='Hypertension diagnosed 2020, Type 2 diabetes 2018',
                family_history='Father with CAD, Mother with diabetes',
                social_history='Non-smoker, occasional alcohol use, sedentary lifestyle',
                allergies='NKDA',
                current_medications='Lisinopril 10mg daily, Metformin 1000mg twice daily',
                physical_examination='BP 138/82, HR 72, RR 16, Temp 98.6F. Heart regular rhythm, lungs clear.',
                assessment='Hypertension, well controlled. Type 2 diabetes.',
                plan='Continue current medications. Lifestyle counseling. Follow-up in 3 months.',
                created_by=users[1].id
            ),
            MedicalRecord(
                client_id=clients[2].id,
                visit_id=visits[2].id,
                chief_complaint='Diabetes follow-up',
                history_present_illness='Patient reports good medication compliance. Monitoring blood glucose at home.',
                past_medical_history='Type 2 diabetes mellitus since 2018',
                family_history='Strong family history of diabetes',
                social_history='Non-smoker, exercises regularly',
                allergies='Penicillin - rash',
                current_medications='Metformin 1000mg BID, Glipizide 5mg daily',
                physical_examination='BP 125/78, HR 68, RR 14. No acute distress.',
                assessment='Type 2 diabetes mellitus, suboptimal control per HbA1c',
                plan='Increase Glipizide to 10mg daily. Nutrition counseling. Recheck HbA1c in 3 months.',
                created_by=users[1].id
            )
        ]
        db.session.add_all(medical_records)
        db.session.commit()

        # Step 15: Create Vital Signs
        print("Creating vital signs...")
        vital_signs = [
            VitalSigns(
                client_id=clients[0].id,
                visit_id=visits[0].id,
                recorded_at=datetime.datetime.now() - datetime.timedelta(days=7),
                temperature=36.8,
                blood_pressure_systolic=138,
                blood_pressure_diastolic=82,
                heart_rate=72,
                respiratory_rate=16,
                oxygen_saturation=98.0,
                height=175.0,
                weight=80.5,
                bmi=26.2,
                notes='Vital signs stable',
                recorded_by=users[3].id
            ),
            VitalSigns(
                client_id=clients[1].id,
                visit_id=visits[1].id,
                recorded_at=datetime.datetime.now() - datetime.timedelta(days=3),
                temperature=36.6,
                blood_pressure_systolic=118,
                blood_pressure_diastolic=75,
                heart_rate=65,
                respiratory_rate=14,
                oxygen_saturation=99.0,
                height=165.0,
                weight=62.0,
                bmi=22.8,
                notes='Normal vital signs',
                recorded_by=users[3].id
            )
        ]
        db.session.add_all(vital_signs)
        db.session.commit()

        # Step 16: Create Prescriptions
        print("Creating prescriptions...")
        prescriptions = [
            Prescription(
                client_id=clients[0].id,
                appointment_id=appointments[0].id,
                doctor_id=staff[0].id,
                medication_name='Lisinopril',
                dosage='10mg',
                frequency='Once daily',
                duration='30 days',
                quantity=30,
                refills=2,
                instructions='Take with or without food. Monitor blood pressure.',
                status='active',
                prescribed_date=datetime.datetime.now() - datetime.timedelta(days=7),
                start_date=datetime.date.today(),
                end_date=datetime.date.today() + datetime.timedelta(days=30)
            ),
            Prescription(
                client_id=clients[2].id,
                doctor_id=staff[0].id,
                medication_name='Glipizide',
                dosage='10mg',
                frequency='Once daily',
                duration='30 days',
                quantity=30,
                refills=1,
                instructions='Take 30 minutes before breakfast. Monitor blood sugar.',
                status='active',
                prescribed_date=datetime.datetime.now() - datetime.timedelta(days=1),
                start_date=datetime.date.today(),
                end_date=datetime.date.today() + datetime.timedelta(days=30)
            )
        ]
        db.session.add_all(prescriptions)
        db.session.commit()

        # Step 17: Create Inventory
        print("Creating inventory...")
        inventory = [
            Inventory(
                name='Latex Examination Gloves',
                code='GLOVE001',
                category='consumable',
                description='Disposable latex examination gloves, size large',
                manufacturer='MedSupply Inc.',
                batch_number='LG240215',
                expiry_date=datetime.date(2025, 12, 31),
                unit='pieces',
                quantity_in_stock=500,
                minimum_stock_level=100,
                unit_price=Decimal('0.15'),
                supplier='Medical Supplies Co.',
                location='Storage Room A'
            ),
            Inventory(
                name='Digital Stethoscope',
                code='STETH001',
                category='equipment',
                description='Digital stethoscope with amplification',
                manufacturer='CardioTech',
                unit='pieces',
                quantity_in_stock=8,
                minimum_stock_level=2,
                unit_price=Decimal('299.99'),
                supplier='Medical Equipment Ltd.',
                location='Equipment Room'
            ),
            Inventory(
                name='Disposable Syringes 5ml',
                code='SYR005',
                category='consumable',
                description='Sterile disposable syringes, 5ml capacity',
                manufacturer='SafeInject Corp.',
                batch_number='SI240301',
                expiry_date=datetime.date(2027, 3, 1),
                unit='pieces',
                quantity_in_stock=200,
                minimum_stock_level=50,
                unit_price=Decimal('0.75'),
                supplier='Medical Supplies Co.',
                location='Storage Room B'
            ),
            Inventory(
                name='Blood Pressure Monitor',
                code='BPM001',
                category='equipment',
                description='Digital blood pressure monitor with cuff',
                manufacturer='VitalCheck',
                unit='pieces',
                quantity_in_stock=12,
                minimum_stock_level=3,
                unit_price=Decimal('89.99'),
                supplier='Medical Equipment Ltd.',
                location='Equipment Room'
            )
        ]
        db.session.add_all(inventory)
        db.session.commit()

        # Step 18: Create Admissions
        print("Creating admissions...")
        admissions = [
            Admission(
                client_id=clients[4].id,
                bed_id=beds[1].id,  # A102
                attending_doctor_id=staff[0].id,
                admission_date=datetime.datetime.now() - datetime.timedelta(days=2),
                admission_type='elective',
                status='active',
                reason='Elective cardiac catheterization',
                diagnosis='Coronary artery disease, stable angina',
                total_cost=Decimal('15000.00'),
                created_by=users[1].id
            )
        ]
        db.session.add_all(admissions)
        db.session.commit()

        # Step 19: Create Billing
        print("Creating billing records...")
        billings = [
            Billing(
                client_id=clients[0].id,
                visit_id=visits[0].id,
                invoice_number='INV-2024-001',
                total_amount=Decimal('185.00'),
                paid_amount=Decimal('0.00'),
                status='pending',
                payment_method=None,
                insurance_provider='HealthFirst Insurance',
                insurance_claim_number='HF2024-001-001',
                due_date=datetime.date.today() + datetime.timedelta(days=30),
                notes='Regular follow-up visit',
                created_by=users[4].id
            ),
            Billing(
                client_id=clients[1].id,
                visit_id=visits[1].id,
                invoice_number='INV-2024-002',
                total_amount=Decimal('220.00'),
                paid_amount=Decimal('220.00'),
                status='paid',
                payment_method='card',
                due_date=datetime.date.today() - datetime.timedelta(days=1),
                payment_date=datetime.datetime.now() - datetime.timedelta(days=1),
                notes='Annual physical exam - paid in full',
                created_by=users[4].id
            ),
            Billing(
                client_id=clients[4].id,
                admission_id=admissions[0].id,
                invoice_number='INV-2024-003',
                total_amount=Decimal('15750.00'),
                paid_amount=Decimal('0.00'),
                status='pending',
                payment_method=None,
                due_date=datetime.date.today() + datetime.timedelta(days=45),
                notes='Inpatient admission - cardiac catheterization',
                created_by=users[4].id
            )
        ]
        db.session.add_all(billings)
        db.session.commit()

        # Step 20: Create Billing Items
        print("Creating billing items...")
        billing_items = [
            # Items for first billing (visit)
            BillingItem(
                billing_id=billings[0].id,
                item_type='consultation',
                description='Cardiology consultation',
                quantity=1,
                unit_price=Decimal('150.00'),
                total_price=Decimal('150.00')
            ),
            BillingItem(
                billing_id=billings[0].id,
                item_type='lab_test',
                description='Complete Blood Count',
                quantity=1,
                unit_price=Decimal('45.00'),
                total_price=Decimal('45.00')
            ),
            # Items for second billing (annual physical)
            BillingItem(
                billing_id=billings[1].id,
                item_type='consultation',
                description='Annual physical examination',
                quantity=1,
                unit_price=Decimal('200.00'),
                total_price=Decimal('200.00')
            ),
            BillingItem(
                billing_id=billings[1].id,
                item_type='other',
                description='Administrative fee',
                quantity=1,
                unit_price=Decimal('20.00'),
                total_price=Decimal('20.00')
            ),
            # Items for third billing (admission)
            BillingItem(
                billing_id=billings[2].id,
                item_type='procedure',
                description='Cardiac catheterization',
                quantity=1,
                unit_price=Decimal('12000.00'),
                total_price=Decimal('12000.00')
            ),
            BillingItem(
                billing_id=billings[2].id,
                item_type='bed_charges',
                description='Room charges (2 days)',
                quantity=2,
                unit_price=Decimal('250.00'),
                total_price=Decimal('500.00')
            ),
            BillingItem(
                billing_id=billings[2].id,
                item_type='medication',
                description='IV medications and supplies',
                quantity=1,
                unit_price=Decimal('1250.00'),
                total_price=Decimal('1250.00')
            ),
            BillingItem(
                billing_id=billings[2].id,
                item_type='lab_test',
                description='Pre-procedure lab work',
                quantity=1,
                unit_price=Decimal('2000.00'),
                total_price=Decimal('2000.00')
            )
        ]
        db.session.add_all(billing_items)
        db.session.commit()

        print("\n✅ Sample data generation completed successfully!")
        print("\n📊 Generated data summary:")
        print(f"   • Users: {len(users)}")
        print(f"   • Departments: {len(departments)}")
        print(f"   • Staff: {len(staff)}")
        print(f"   • Programs: {len(programs)}")
        print(f"   • Clients: {len(clients)}")
        print(f"   • Client Programs: {len(client_programs)}")
        print(f"   • Insurance Providers: {len(insurance_providers)}")
        print(f"   • Client Insurance: {len(client_insurances)}")
        print(f"   • Beds: {len(beds)}")
        print(f"   • Visits: {len(visits)}")
        print(f"   • Appointments: {len(appointments)}")
        print(f"   • Lab Tests: {len(lab_tests)}")
        print(f"   • Lab Orders: {len(lab_orders)}")
        print(f"   • Medical Records: {len(medical_records)}")
        print(f"   • Vital Signs: {len(vital_signs)}")
        print(f"   • Prescriptions: {len(prescriptions)}")
        print(f"   • Inventory Items: {len(inventory)}")
        print(f"   • Admissions: {len(admissions)}")
        print(f"   • Billing Records: {len(billings)}")
        print(f"   • Billing Items: {len(billing_items)}")
        
        print("\n🔐 Test user credentials:")
        print("   • Admin: admin / admin123")
        print("   • Doctor: dr_johnson / doctor123")
        print("   • Nurse: nurse_mary / nurse123")
        print("   • Receptionist: receptionist / reception123")
        print("   • Lab Tech: lab_tech / lab123")
        
    except Exception as e:
        print(f"❌ Error generating sample data: {str(e)}")
        db.session.rollback()
        raise


generate_sample_data()
