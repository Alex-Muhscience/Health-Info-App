from backend.database import db
from datetime import datetime
import uuid
import re
from sqlalchemy import event, Index, CheckConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash
import secrets


def validate_email(email):
    """Validate email format using regex."""
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None


class User(db.Model):
    """User model representing system users."""
    __tablename__ = 'users'

    # Constants
    ROLES = ('admin', 'doctor', 'nurse', 'receptionist', 'lab_tech', 'pharmacy', 'staff')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='user')
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    visits = db.relationship('Visit', backref='user', lazy=True)

    @staticmethod
    def validate_role(role):
        """Validate user role."""
        return role in User.ROLES


class Client(db.Model):
    """Client model representing patients or clients."""
    __tablename__ = 'clients'

    # Constants
    GENDERS = ('male', 'female', 'other', 'prefer_not_to_say')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    address = db.Column(db.String(200))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    programs = db.relationship('ClientProgram', backref='client', lazy=True, cascade='all, delete-orphan')
    visits = db.relationship('Visit', backref='client', lazy=True, cascade='all, delete-orphan')
    appointments = db.relationship('Appointment', backref='client', lazy=True, cascade='all, delete-orphan')


class Program(db.Model):
    """Program model representing health programs."""
    __tablename__ = 'programs'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    clients = db.relationship('ClientProgram', backref='program', lazy=True)


class ClientProgram(db.Model):
    """ClientProgram model linking clients to programs."""
    __tablename__ = 'client_programs'

    # Constants
    STATUSES = ('active', 'completed', 'dropped', 'on_hold')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    program_id = db.Column(db.String(36), db.ForeignKey('programs.id', ondelete='CASCADE'), nullable=False)
    enrollment_date = db.Column(db.Date, default=datetime.utcnow)
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')
    progress = db.Column(db.Integer, default=0)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('client_id', 'program_id', name='_client_program_uc'),
    )


class Visit(db.Model):
    """Visit model representing client visits."""
    __tablename__ = 'visits'

    # Constants
    VISIT_TYPES = ('consultation', 'follow_up', 'emergency', 'vaccination', 'test', 'procedure', 'other')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    visit_type = db.Column(db.String(20), default='consultation')
    purpose = db.Column(db.String(200), nullable=False)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Appointment(db.Model):
    """Appointment model representing client appointments."""
    __tablename__ = 'appointments'

    # Constants
    STATUSES = ('scheduled', 'completed', 'cancelled', 'no_show', 'rescheduled')
    TYPES = ('consultation', 'follow_up', 'emergency', 'procedure', 'surgery', 'therapy', 'other')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    doctor_id = db.Column(db.String(36), db.ForeignKey('staff.id', ondelete='SET NULL'))
    department_id = db.Column(db.String(36), db.ForeignKey('departments.id', ondelete='SET NULL'))
    date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    appointment_type = db.Column(db.String(50), default='consultation')
    status = db.Column(db.String(50), default='scheduled')
    reason = db.Column(db.String(200))
    priority = db.Column(db.String(20), default='normal')  # low, normal, high, emergency
    notes = db.Column(db.Text)
    reminder_sent = db.Column(db.Boolean, default=False)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    prescriptions = db.relationship('Prescription', backref='appointment', lazy=True)
    lab_orders = db.relationship('LabOrder', backref='appointment', lazy=True)


class Department(db.Model):
    """Department model representing hospital departments."""
    __tablename__ = 'departments'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    head_id = db.Column(db.String(36), db.ForeignKey('staff.id', ondelete='SET NULL'))
    location = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    staff = db.relationship('Staff', backref='department', lazy=True, foreign_keys='Staff.department_id')
    appointments = db.relationship('Appointment', backref='department', lazy=True)
    beds = db.relationship('Bed', backref='department', lazy=True)
    department_head = db.relationship('Staff', foreign_keys=[head_id], post_update=True)


class Staff(db.Model):
    """Staff model representing hospital staff."""
    __tablename__ = 'staff'

    # Constants
    SPECIALIZATIONS = (
        'general_medicine', 'cardiology', 'neurology', 'orthopedics', 'pediatrics',
        'gynecology', 'dermatology', 'psychiatry', 'surgery', 'emergency',
        'radiology', 'pathology', 'anesthesiology', 'oncology', 'other'
    )
    
    EMPLOYMENT_TYPES = ('full_time', 'part_time', 'contract', 'intern', 'resident')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    employee_id = db.Column(db.String(20), unique=True, nullable=False)
    user_id = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='CASCADE'), unique=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    specialization = db.Column(db.String(50))
    license_number = db.Column(db.String(50))
    department_id = db.Column(db.String(36), db.ForeignKey('departments.id', ondelete='SET NULL'))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    employment_type = db.Column(db.String(20), default='full_time')
    hire_date = db.Column(db.Date, default=datetime.utcnow)
    salary = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)
    prescriptions = db.relationship('Prescription', backref='doctor', lazy=True)
    lab_orders = db.relationship('LabOrder', backref='ordered_by_staff', lazy=True)


class MedicalRecord(db.Model):
    """Medical record model for comprehensive patient history."""
    __tablename__ = 'medical_records'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    visit_id = db.Column(db.String(36), db.ForeignKey('visits.id', ondelete='CASCADE'))
    chief_complaint = db.Column(db.Text)
    history_present_illness = db.Column(db.Text)
    past_medical_history = db.Column(db.Text)
    family_history = db.Column(db.Text)
    social_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    current_medications = db.Column(db.Text)
    physical_examination = db.Column(db.Text)
    assessment = db.Column(db.Text)
    plan = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class VitalSigns(db.Model):
    """Vital signs model for tracking patient vitals."""
    __tablename__ = 'vital_signs'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    visit_id = db.Column(db.String(36), db.ForeignKey('visits.id', ondelete='CASCADE'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    temperature = db.Column(db.Float)  # Celsius
    blood_pressure_systolic = db.Column(db.Integer)
    blood_pressure_diastolic = db.Column(db.Integer)
    heart_rate = db.Column(db.Integer)  # beats per minute
    respiratory_rate = db.Column(db.Integer)  # breaths per minute
    oxygen_saturation = db.Column(db.Float)  # percentage
    height = db.Column(db.Float)  # cm
    weight = db.Column(db.Float)  # kg
    bmi = db.Column(db.Float)  # calculated
    notes = db.Column(db.Text)
    recorded_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Prescription(db.Model):
    """Prescription model for medication prescriptions."""
    __tablename__ = 'prescriptions'

    # Constants
    STATUSES = ('active', 'completed', 'cancelled', 'expired')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    appointment_id = db.Column(db.String(36), db.ForeignKey('appointments.id', ondelete='CASCADE'))
    doctor_id = db.Column(db.String(36), db.ForeignKey('staff.id', ondelete='SET NULL'), nullable=False)
    medication_name = db.Column(db.String(200), nullable=False)
    dosage = db.Column(db.String(100), nullable=False)
    frequency = db.Column(db.String(100), nullable=False)
    duration = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    refills = db.Column(db.Integer, default=0)
    instructions = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    prescribed_date = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    dispensed = db.Column(db.Boolean, default=False)
    dispensed_date = db.Column(db.DateTime)
    dispensed_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LabTest(db.Model):
    """Lab test definitions model."""
    __tablename__ = 'lab_tests'

    # Constants
    CATEGORIES = ('blood', 'urine', 'stool', 'culture', 'imaging', 'biopsy', 'other')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False, unique=True)
    code = db.Column(db.String(20), unique=True)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    normal_range = db.Column(db.String(100))
    unit = db.Column(db.String(50))
    cost = db.Column(db.Numeric(10, 2))
    turnaround_time = db.Column(db.Integer)  # hours
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    orders = db.relationship('LabOrder', backref='test', lazy=True)


class LabOrder(db.Model):
    """Lab order model for test orders."""
    __tablename__ = 'lab_orders'

    # Constants
    STATUSES = ('ordered', 'collected', 'processing', 'completed', 'cancelled')
    PRIORITIES = ('routine', 'urgent', 'stat')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    appointment_id = db.Column(db.String(36), db.ForeignKey('appointments.id', ondelete='CASCADE'))
    test_id = db.Column(db.String(36), db.ForeignKey('lab_tests.id', ondelete='CASCADE'), nullable=False)
    ordered_by = db.Column(db.String(36), db.ForeignKey('staff.id', ondelete='SET NULL'), nullable=False)
    status = db.Column(db.String(20), default='ordered')
    priority = db.Column(db.String(20), default='routine')
    clinical_notes = db.Column(db.Text)
    specimen_type = db.Column(db.String(100))
    collection_date = db.Column(db.DateTime)
    result_date = db.Column(db.DateTime)
    result_value = db.Column(db.String(200))
    result_notes = db.Column(db.Text)
    abnormal_flag = db.Column(db.Boolean, default=False)
    processed_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Inventory(db.Model):
    """Inventory model for medical supplies and medications."""
    __tablename__ = 'inventory'

    # Constants
    CATEGORIES = ('medication', 'equipment', 'consumable', 'other')
    UNITS = ('pieces', 'boxes', 'bottles', 'vials', 'tubes', 'kg', 'liters', 'other')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(50), unique=True)
    category = db.Column(db.String(50))
    description = db.Column(db.Text)
    manufacturer = db.Column(db.String(100))
    batch_number = db.Column(db.String(50))
    expiry_date = db.Column(db.Date)
    unit = db.Column(db.String(20))
    quantity_in_stock = db.Column(db.Integer, default=0)
    minimum_stock_level = db.Column(db.Integer, default=0)
    unit_price = db.Column(db.Numeric(10, 2))
    supplier = db.Column(db.String(100))
    location = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Bed(db.Model):
    """Bed model for patient bed management."""
    __tablename__ = 'beds'

    # Constants
    TYPES = ('general', 'icu', 'pediatric', 'maternity', 'isolation', 'emergency')
    STATUSES = ('available', 'occupied', 'maintenance', 'reserved')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    bed_number = db.Column(db.String(20), unique=True, nullable=False)
    department_id = db.Column(db.String(36), db.ForeignKey('departments.id', ondelete='CASCADE'), nullable=False)
    room_number = db.Column(db.String(20))
    bed_type = db.Column(db.String(20), default='general')
    status = db.Column(db.String(20), default='available')
    daily_rate = db.Column(db.Numeric(10, 2))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    admissions = db.relationship('Admission', backref='bed', lazy=True)


class Admission(db.Model):
    """Admission model for patient admissions."""
    __tablename__ = 'admissions'

    # Constants
    STATUSES = ('active', 'discharged', 'transferred', 'deceased')
    ADMISSION_TYPES = ('emergency', 'elective', 'outpatient', 'observation')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    bed_id = db.Column(db.String(36), db.ForeignKey('beds.id', ondelete='SET NULL'))
    attending_doctor_id = db.Column(db.String(36), db.ForeignKey('staff.id', ondelete='SET NULL'))
    admission_date = db.Column(db.DateTime, default=datetime.utcnow)
    discharge_date = db.Column(db.DateTime)
    admission_type = db.Column(db.String(20), default='elective')
    status = db.Column(db.String(20), default='active')
    reason = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    discharge_summary = db.Column(db.Text)
    total_cost = db.Column(db.Numeric(12, 2))
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Billing(db.Model):
    """Billing model for patient billing and invoicing."""
    __tablename__ = 'billing'

    # Constants
    STATUSES = ('pending', 'paid', 'partially_paid', 'overdue', 'cancelled')
    PAYMENT_METHODS = ('cash', 'card', 'insurance', 'bank_transfer', 'other')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    visit_id = db.Column(db.String(36), db.ForeignKey('visits.id', ondelete='CASCADE'))
    admission_id = db.Column(db.String(36), db.ForeignKey('admissions.id', ondelete='CASCADE'))
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    total_amount = db.Column(db.Numeric(12, 2), nullable=False)
    paid_amount = db.Column(db.Numeric(12, 2), default=0)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(20))
    insurance_provider = db.Column(db.String(100))
    insurance_claim_number = db.Column(db.String(50))
    due_date = db.Column(db.Date)
    payment_date = db.Column(db.DateTime)
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id', ondelete='SET NULL'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('BillingItem', backref='billing', lazy=True, cascade='all, delete-orphan')


class BillingItem(db.Model):
    """Billing item model for individual billing line items."""
    __tablename__ = 'billing_items'

    # Constants
    ITEM_TYPES = ('consultation', 'procedure', 'medication', 'lab_test', 'bed_charges', 'other')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    billing_id = db.Column(db.String(36), db.ForeignKey('billing.id', ondelete='CASCADE'), nullable=False)
    item_type = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    discount = db.Column(db.Numeric(10, 2), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class InsuranceProvider(db.Model):
    """Insurance provider model."""
    __tablename__ = 'insurance_providers'

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False, unique=True)
    contact_person = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    address = db.Column(db.Text)
    coverage_details = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    client_insurances = db.relationship('ClientInsurance', backref='provider', lazy=True)


class ClientInsurance(db.Model):
    """Client insurance model for patient insurance information."""
    __tablename__ = 'client_insurance'

    # Constants
    STATUSES = ('active', 'expired', 'suspended', 'cancelled')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    provider_id = db.Column(db.String(36), db.ForeignKey('insurance_providers.id', ondelete='CASCADE'), nullable=False)
    policy_number = db.Column(db.String(100), nullable=False)
    group_number = db.Column(db.String(100))
    status = db.Column(db.String(20), default='active')
    effective_date = db.Column(db.Date, nullable=False)
    expiry_date = db.Column(db.Date)
    copay_amount = db.Column(db.Numeric(10, 2))
    deductible = db.Column(db.Numeric(10, 2))
    coverage_percentage = db.Column(db.Float)
    is_primary = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Constraints
    __table_args__ = (
        db.UniqueConstraint('client_id', 'provider_id', 'policy_number', name='_client_insurance_uc'),
    )


# Model Validations
@event.listens_for(User, 'before_insert')
@event.listens_for(User, 'before_update')
def validate_user(mapper, connection, target):
    """Validate user fields before insert or update."""
    if not validate_email(target.email):
        raise ValueError("Invalid email format")
    if not User.validate_role(target.role):
        raise ValueError(f"Invalid role. Must be one of: {', '.join(User.ROLES)}")


@event.listens_for(Client, 'before_insert')
@event.listens_for(Client, 'before_update')
def validate_client(mapper, connection, target):
    """Validate client fields before insert or update."""
    if target.gender not in Client.GENDERS:
        raise ValueError(f"Invalid gender. Must be one of: {', '.join(Client.GENDERS)}")
    if target.phone and not re.match(r'^\+?[0-9]{7,15}$', target.phone):
        raise ValueError("Invalid phone number format. Expected format: +1234567890 or 1234567890.")


@event.listens_for(ClientProgram, 'before_insert')
@event.listens_for(ClientProgram, 'before_update')
def validate_client_program(mapper, connection, target):
    """Validate client program fields before insert or update."""
    if target.status not in ClientProgram.STATUSES:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(ClientProgram.STATUSES)}")
    if not (0 <= target.progress <= 100):
        raise ValueError("Progress must be between 0 and 100.")


@event.listens_for(Appointment, 'before_insert')
@event.listens_for(Appointment, 'before_update')
def validate_appointment(mapper, connection, target):
    """Validate appointment fields before insert or update."""
    if target.status not in Appointment.STATUSES:
        raise ValueError(f"Invalid status. Must be one of: {', '.join(Appointment.STATUSES)}")