import re
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
from email_validator import validate_email, EmailNotValidError
from flask import request
import phonenumbers
from marshmallow import ValidationError as MarshmallowValidationError
from werkzeug.datastructures import FileStorage
from pydantic import ValidationError as PydanticValidationError

from backend.schemas import UserSchema, ProgramSchema, VisitSchema


class Validators:
    """
    Comprehensive validation utilities for API inputs
    """

    # Common regex patterns
    USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_.-]{3,30}$')
    PASSWORD_REGEX = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$')
    NAME_REGEX = re.compile(r'^[a-zA-Z\s\'-]{2,50}$')
    ZIPCODE_REGEX = re.compile(r'^\d{5}(?:[-\s]\d{4})?$')

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, str]:
        """Validate email address format and deliverability"""
        try:
            v = validate_email(email, check_deliverability=False)
            return True, v.normalized
        except EmailNotValidError as e:
            return False, str(e)

    @staticmethod
    def validate_phone(phone: str, country_code: str = 'US') -> Tuple[bool, str]:
        """Validate phone number format"""
        try:
            p = phonenumbers.parse(phone, country_code)
            if not phonenumbers.is_valid_number(p):
                return False, "Invalid phone number"
            return True, phonenumbers.format_number(p, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            return False, "Invalid phone number format"

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, str]:
        """Validate password meets complexity requirements"""
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        if not Validators.PASSWORD_REGEX.match(password):
            return False, (
                "Password must contain at least one uppercase letter, "
                "one lowercase letter, one number and one special character"
            )
        return True, ""

    @staticmethod
    def validate_file(
            file: FileStorage,
            allowed_extensions: List[str],
            max_size: int = 16 * 1024 * 1024  # 16MB default
    ) -> Tuple[bool, str]:
        """Validate uploaded file"""
        if not file:
            return False, "No file provided"

        if file.content_length > max_size:
            return False, f"File too large. Max size is {max_size / 1024 / 1024}MB"

        if (not hasattr(file, 'filename') or
                not any(file.filename.lower().endswith(ext) for ext in allowed_extensions)):
            return False, f"Invalid file type. Allowed: {', '.join(allowed_extensions)}"

        return True, ""

    @staticmethod
    def validate_json(data: Dict, required_fields: Dict[str, type]) -> Tuple[bool, Dict[str, List[str]]]:
        """Validate JSON request body structure and types"""
        errors = {}

        # Check required fields
        for field, field_type in required_fields.items():
            if field not in data:
                errors.setdefault('missing', []).append(field)
            elif not isinstance(data[field], field_type):
                errors.setdefault('type_errors', []).append(
                    f"{field} should be {field_type.__name__}"
                )

        # Additional validation for specific field types
        if 'email' in data and 'email' not in errors.get('type_errors', []):
            is_valid, email_error = Validators.validate_email(data['email'])
            if not is_valid:
                errors.setdefault('validation_errors', []).append(f"email: {email_error}")

        if 'phone' in data and 'phone' not in errors.get('type_errors', []):
            is_valid, phone_error = Validators.validate_phone(data['phone'])
            if not is_valid:
                errors.setdefault('validation_errors', []).append(f"phone: {phone_error}")

        return len(errors) == 0, errors

    @staticmethod
    def validate_date(date_str: str, format: str = '%Y-%m-%d') -> Tuple[bool, Optional[datetime]]:
        """Validate date string format"""
        try:
            return True, datetime.strptime(date_str, format)
        except (ValueError, TypeError):
            return False, None

    @staticmethod
    def validate_pagination(page: int, per_page: int, max_per_page: int = 100) -> Tuple[bool, str]:
        """Validate pagination parameters"""
        if page < 1:
            return False, "Page must be greater than 0"
        if per_page < 1:
            return False, "Per page must be greater than 0"
        if per_page > max_per_page:
            return False, f"Per page cannot exceed {max_per_page}"
        return True, ""

    @staticmethod
    def validate_enum(value: Any, allowed_values: List[Any]) -> Tuple[bool, str]:
        """Validate value is in allowed set"""
        if value not in allowed_values:
            return False, f"Value must be one of: {', '.join(map(str, allowed_values))}"
        return True, ""

    @staticmethod
    def validate_request_content_type(content_type: str = 'application/json') -> Tuple[bool, str]:
        """Validate request content type"""
        if request.content_type != content_type:
            return False, f"Content-Type must be {content_type}"
        return True, ""

    @staticmethod
    def validate_user_data(user_data: dict) -> Tuple[Optional[Dict], Optional[str]]:
        """Validate user data using UserSchema"""
        try:
            validated_data = UserSchema(**user_data)
            return validated_data.dict(), None
        except (MarshmallowValidationError, PydanticValidationError) as e:
            return None, str(e)

    @staticmethod
    def validate_program_data(program_data: dict) -> Tuple[Optional[Dict], Optional[Dict[str, str]]]:
        """
        Validate program data structure and content
        """
        try:
            validated = ProgramSchema(**program_data)
            program_dict = validated.dict()

            # Additional business logic validation
            errors = {}

            if 'name' in program_dict:
                if len(program_dict['name']) > 100:
                    errors['name'] = "Name cannot exceed 100 characters"
                if len(program_dict['name']) < 3:
                    errors['name'] = "Name must be at least 3 characters"

            if 'description' in program_dict and len(program_dict['description']) > 2000:
                errors['description'] = "Description cannot exceed 2000 characters"

            if 'duration_weeks' in program_dict:
                if program_dict['duration_weeks'] < 1 or program_dict['duration_weeks'] > 104:
                    errors['duration_weeks'] = "Duration must be between 1 and 104 weeks"

            if 'cost' in program_dict and program_dict['cost'] < 0:
                errors['cost'] = "Cost cannot be negative"

            if errors:
                return None, errors

            return program_dict, None

        except (MarshmallowValidationError, PydanticValidationError) as e:
            if hasattr(e, 'errors'):
                return None, e.errors()
            return None, {'schema_error': str(e)}

    @staticmethod
    def validate_visit_data(visit_data: dict) -> Tuple[Optional[Dict], Optional[Dict[str, str]]]:
        """
        Validate visit data structure and content
        """
        try:
            validated = VisitSchema(**visit_data)
            visit_dict = validated.dict()

            # Additional business logic validation
            errors = {}

            if 'visit_date' in visit_dict:
                is_valid, _ = Validators.validate_date(visit_dict['visit_date'])
                if not is_valid:
                    errors['visit_date'] = "Invalid date format. Use YYYY-MM-DD"

            if 'status' in visit_dict:
                valid_statuses = ['scheduled', 'completed', 'canceled', 'no-show']
                if visit_dict['status'].lower() not in valid_statuses:
                    errors['status'] = f"Invalid status. Must be one of: {', '.join(valid_statuses)}"

            if 'duration_minutes' in visit_dict:
                if visit_dict['duration_minutes'] < 5 or visit_dict['duration_minutes'] > 240:
                    errors['duration_minutes'] = "Duration must be between 5 and 240 minutes"

            if 'purpose' in visit_dict:
                if len(visit_dict['purpose']) > 500:
                    errors['purpose'] = "Purpose cannot exceed 500 characters"
                if len(visit_dict['purpose']) < 10:
                    errors['purpose'] = "Purpose must be at least 10 characters"

            if errors:
                return None, errors

            return visit_dict, None

        except (MarshmallowValidationError, PydanticValidationError) as e:
            if hasattr(e, 'errors'):
                return None, e.errors()
            return None, {'schema_error': str(e)}