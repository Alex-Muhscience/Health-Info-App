"""Data serialization and validation schemas for the Health App backend."""
from backend import ma
from backend.models import (
    User, Client, Program, ClientProgram,
    Visit, Appointment, FileUpload, ActivityLog
)
from pydantic import BaseModel, Field, validator, EmailStr, constr
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
import re


# Marshmallow Schemas ========================================================

class UserSchema(ma.SQLAlchemyAutoSchema):
    """User data serialization schema."""

    class Meta:
        model = User
        exclude = ("_password", "activity_logs")  # Exclude the actual password field
        load_instance = True
        dump_only = ("id", "role", "is_active", "last_login")


class ProgramSchema(ma.SQLAlchemyAutoSchema):
    """Program data serialization schema."""

    class Meta:
        model = Program
        load_instance = True


class ClientProgramSchema(ma.SQLAlchemyAutoSchema):
    """Client-Program association serialization schema."""
    program = ma.Nested(ProgramSchema)

    class Meta:
        model = ClientProgram
        include_fk = True
        load_instance = True


class VisitSchema(ma.SQLAlchemyAutoSchema):
    """Visit record serialization schema."""

    class Meta:
        model = Visit
        include_fk = True
        load_instance = True


class AppointmentSchema(ma.SQLAlchemyAutoSchema):
    """Appointment serialization schema."""

    class Meta:
        model = Appointment
        include_fk = True
        load_instance = True


class ClientSchema(ma.SQLAlchemyAutoSchema):
    """Client data serialization schema."""
    programs = ma.Nested(ClientProgramSchema, many=True)
    visits = ma.Nested(VisitSchema, many=True)
    appointments = ma.Nested(AppointmentSchema, many=True)

    class Meta:
        model = Client
        include_fk = True
        load_instance = True


class FileUploadSchema(ma.SQLAlchemyAutoSchema):
    """File upload serialization schema."""

    class Meta:
        model = FileUpload
        include_fk = True
        load_instance = True


class ActivityLogSchema(ma.SQLAlchemyAutoSchema):
    """Activity log serialization schema."""

    class Meta:
        model = ActivityLog
        include_fk = True
        load_instance = True


# Schema Instances ===========================================================

user_schema = UserSchema()
users_schema = UserSchema(many=True)

client_schema = ClientSchema()
clients_schema = ClientSchema(many=True)

program_schema = ProgramSchema()
programs_schema = ProgramSchema(many=True)

client_program_schema = ClientProgramSchema()
client_programs_schema = ClientProgramSchema(many=True)

visit_schema = VisitSchema()
visits_schema = VisitSchema(many=True)

appointment_schema = AppointmentSchema()
appointments_schema = AppointmentSchema(many=True)

file_upload_schema = FileUploadSchema()
file_uploads_schema = FileUploadSchema(many=True)

activity_log_schema = ActivityLogSchema()
activity_logs_schema = ActivityLogSchema(many=True)