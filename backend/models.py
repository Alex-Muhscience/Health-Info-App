from backend import db
from datetime import datetime
import uuid
import re
from sqlalchemy import event
from werkzeug.security import generate_password_hash


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

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    visit_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
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
    STATUSES = ('scheduled', 'completed', 'cancelled', 'no_show')

    # Columns
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    client_id = db.Column(db.String(36), db.ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    duration_minutes = db.Column(db.Integer, default=30)
    status = db.Column(db.String(50), default='scheduled')
    reason = db.Column(db.String(200))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


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