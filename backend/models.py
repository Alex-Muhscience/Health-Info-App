"""Database models for the Health App backend."""
from backend import db
from datetime import datetime
import uuid
from sqlalchemy import event, Index
from sqlalchemy.dialects.postgresql import UUID
from werkzeug.security import generate_password_hash, check_password_hash
from typing import Optional, List
import re
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates


class BaseModel(db.Model):
    """Abstract base model with common fields and methods."""
    __abstract__ = True

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(
        db.DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )

    def to_dict(self) -> dict:
        """Convert model instance to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class User(BaseModel):
    """User model for authentication and authorization."""
    __tablename__ = 'users'

    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    _password = db.Column('password', db.String(256), nullable=False)
    role = db.Column(db.String(20), default='user', nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime)

    # Relationships
    visits = db.relationship('Visit', backref='creator', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='creator', lazy='dynamic')
    uploads = db.relationship('FileUpload', backref='uploader', lazy='dynamic')
    activity_logs = db.relationship('ActivityLog', backref='user', lazy='dynamic')

    # Indexes
    __table_args__ = (
        Index('ix_users_email_lower', db.func.lower(email), unique=True),
        Index('ix_users_username_lower', db.func.lower(username), unique=True),
    )

    @hybrid_property
    def password(self) -> str:
        """Password getter."""
        return self._password

    @password.setter
    def password(self, password: str) -> None:
        """Password setter that automatically hashes the password."""
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        self._password = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return check_password_hash(self._password, password)

    @validates('email')
    def validate_email(self, key: str, email: str) -> str:
        """Validate email format."""
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address format")
        return email.lower()

    @validates('role')
    def validate_role(self, key: str, role: str) -> str:
        """Validate user role."""
        valid_roles = {'admin', 'clinician', 'staff', 'user'}
        if role not in valid_roles:
            raise ValueError(f"Invalid role. Must be one of {valid_roles}")
        return role


class Client(BaseModel):
    """Client/Patient model for health records."""
    __tablename__ = 'clients'

    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120), index=True)
    address = db.Column(db.String(200))
    emergency_contact_name = db.Column(db.String(100))
    emergency_contact_phone = db.Column(db.String(20))
    medical_history = db.Column(db.Text)
    allergies = db.Column(db.Text)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Relationships
    programs = db.relationship('ClientProgram', backref='client', lazy='dynamic')
    visits = db.relationship('Visit', backref='client', lazy='dynamic')
    appointments = db.relationship('Appointment', backref='client', lazy='dynamic')
    files = db.relationship('FileUpload', backref='client', lazy='dynamic')

    # Indexes
    __table_args__ = (
        Index('ix_clients_name', db.func.lower(first_name), db.func.lower(last_name)),
        Index('ix_clients_dob', dob),
    )

    @hybrid_property
    def full_name(self) -> str:
        """Client's full name."""
        return f"{self.first_name} {self.last_name}"

    @validates('email')
    def validate_email(self, key: str, email: str) -> Optional[str]:
        """Validate email format if provided."""
        if email and not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            raise ValueError("Invalid email address format")
        return email.lower() if email else None

    @validates('phone')
    def validate_phone(self, key: str, phone: str) -> str:
        """Validate phone number format."""
        if not re.match(r"^\+?[\d\s\-()]{10,}$", phone):
            raise ValueError("Invalid phone number format")
        return phone.replace(" ", "")


class Program(BaseModel):
    """Treatment program model."""
    __tablename__ = 'programs'

    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    requirements = db.Column(db.Text)

    # Relationships
    client_programs = db.relationship('ClientProgram', backref='program', lazy='dynamic')

    @validates('name')
    def validate_name(self, key: str, name: str) -> str:
        """Ensure program name is title case."""
        return name.title()


class ClientProgram(BaseModel):
    """Association table between clients and programs."""
    __tablename__ = 'client_programs'

    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    program_id = db.Column(db.String(36), db.ForeignKey('programs.id'), nullable=False)
    enrollment_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    completion_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active', nullable=False)
    progress = db.Column(db.Integer, default=0, nullable=False)
    notes = db.Column(db.Text)
    clinician_notes = db.Column(db.Text)

    # Indexes
    __table_args__ = (
        Index('ix_client_programs_client_program', client_id, program_id, unique=True),
        db.CheckConstraint('progress >= 0 AND progress <= 100', name='progress_range_check'),
    )

    @validates('status')
    def validate_status(self, key: str, status: str) -> str:
        """Validate program status."""
        valid_statuses = {'active', 'completed', 'paused', 'terminated'}
        if status not in valid_statuses:
            raise ValueError(f"Invalid status. Must be one of {valid_statuses}")
        return status


class Visit(BaseModel):
    """Client visit record model."""
    __tablename__ = 'visits'

    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    purpose = db.Column(db.String(200), nullable=False)
    diagnosis = db.Column(db.Text)
    treatment = db.Column(db.Text)
    medications = db.Column(db.Text)
    vital_signs = db.Column(db.JSON)  # Stores blood pressure, temp, etc.
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    is_follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_date = db.Column(db.DateTime)

    # Indexes
    __table_args__ = (
        Index('ix_visits_client_date', client_id, visit_date),
    )


class Appointment(BaseModel):
    """Appointment scheduling model."""
    __tablename__ = 'appointments'

    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30, nullable=False)
    status = db.Column(db.String(50), default='scheduled', nullable=False)
    reason = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    reminder_sent = db.Column(db.Boolean, default=False)

    # Indexes
    __table_args__ = (
        Index('ix_appointments_client_status', client_id, status),
        Index('ix_appointments_date_status', date, status),
        db.CheckConstraint(
            "status IN ('scheduled', 'confirmed', 'completed', 'cancelled', 'no-show')",
            name='valid_status_check'
        ),
    )


class FileUpload(BaseModel):
    """File upload model for client documents."""
    __tablename__ = 'file_uploads'

    filename = db.Column(db.String(255), nullable=False)
    file_url = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.String(50), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)  # in bytes
    description = db.Column(db.String(200))
    uploaded_by = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id'))
    is_confidential = db.Column(db.Boolean, default=False, nullable=False)

    # Indexes
    __table_args__ = (
        Index('ix_file_uploads_client', client_id),
        Index('ix_file_uploads_type', file_type),
    )

    @validates('file_type')
    def validate_file_type(self, key: str, file_type: str) -> str:
        """Validate file type against allowed types."""
        allowed_types = {
            'medical_record', 'prescription', 'lab_result',
            'imaging', 'consent_form', 'other'
        }
        if file_type not in allowed_types:
            raise ValueError(f"Invalid file type. Must be one of {allowed_types}")
        return file_type


class ActivityLog(BaseModel):
    """System activity log model."""
    __tablename__ = 'activity_logs'

    user_id = db.Column(db.String(36), db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    entity_type = db.Column(db.String(100))
    entity_id = db.Column(db.String(36))
    details = db.Column(db.JSON)  # Structured details in JSON format
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(200))

    # Indexes
    __table_args__ = (
        Index('ix_activity_logs_user_action', user_id, action),
        Index('ix_activity_logs_entity', entity_type, entity_id),
    )


# Add database indexes after table creation
@event.listens_for(Client.__table__, 'after_create')
def create_client_indexes(target, connection, **kw):
    connection.execute(
        "CREATE INDEX idx_clients_full_text ON clients "
        "USING gin(to_tsvector('english', "
        "coalesce(first_name, '') || ' ' || coalesce(last_name, '') || ' ' || "
        "coalesce(email, '') || ' ' || coalesce(phone, ''))"
    )


@event.listens_for(Visit.__table__, 'after_create')
def create_visit_indexes(target, connection, **kw):
    connection.execute(
        "CREATE INDEX idx_visits_full_text ON visits "
        "USING gin(to_tsvector('english', "
        "coalesce(purpose, '') || ' ' || coalesce(diagnosis, '') || ' ' || "
        "coalesce(treatment, '') || ' ' || coalesce(notes, '')))"
    )