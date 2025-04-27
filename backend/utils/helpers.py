import re
from datetime import datetime
from dateutil.parser import parse
from werkzeug.security import generate_password_hash
from flask import current_app

def validate_email(email):
    """Validate email format"""
    if not email or not isinstance(email, str):
        return False
    pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    """Validate phone number format"""
    if not phone or not isinstance(phone, str):
        return False
    # Basic international phone validation
    pattern = r'^\+?[0-9\s\-\(\)]{7,20}$'
    return re.match(pattern, phone) is not None

def validate_password(password):
    """Validate password complexity"""
    if not password or len(password) < 8:
        return False
    # At least one digit, one letter, and one special character
    return bool(re.search(r'\d', password)) and \
           bool(re.search(r'[A-Za-z]', password)) and \
           bool(re.search(r'[^A-Za-z0-9]', password))

def validate_name(name):
    """Validate person or program name"""
    if not name or not isinstance(name, str) or len(name.strip()) < 2:
        return False
    # Allow letters, spaces, hyphens, and apostrophes
    return bool(re.match(r"^[a-zA-Z\s\-']+$", name))

def parse_date(date_str, format='%Y-%m-%d'):
    """Parse date string with error handling"""
    try:
        return datetime.strptime(date_str, format).date()
    except (ValueError, TypeError, AttributeError):
        try:
            return parse(date_str).date()
        except:
            current_app.logger.warning(f'Failed to parse date: {date_str}')
            return None

def parse_datetime(datetime_str, format='%Y-%m-%d %H:%M:%S'):
    """Parse datetime string with error handling"""
    try:
        return datetime.strptime(datetime_str, format)
    except (ValueError, TypeError, AttributeError):
        try:
            return parse(datetime_str)
        except:
            current_app.logger.warning(f'Failed to parse datetime: {datetime_str}')
            return None

def validate_visit_type(visit_type):
    """Validate visit type against allowed values"""
    from backend.routes.visits import VISIT_TYPES  # Avoid circular import
    return visit_type.lower() in VISIT_TYPES

def generate_secure_hash(password):
    """Generate secure password hash"""
    return generate_password_hash(
        password,
        method='pbkdf2:sha256:600000',
        salt_length=16
    )