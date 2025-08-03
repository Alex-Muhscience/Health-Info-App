from backend import ma
from backend.models import User, Client, Program, ClientProgram, Visit, Appointment
from marshmallow import fields, validate, ValidationError


# Custom Validators
def validate_visit_type(value):
    """Custom validator for visit types."""
    from backend.models import Visit
    if value not in Visit.VISIT_TYPES:
        raise ValidationError(f"Invalid visit type: {value}. Valid types are: {', '.join(Visit.VISIT_TYPES)}.")


class UserSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing/deserializing User objects."""
    class Meta:
        model = User
        load_instance = True
        exclude = ("password",)

    role = fields.String(validate=validate.OneOf(User.ROLES))
    email = fields.Email(required=True)
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ClientSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing/deserializing Client objects."""
    class Meta:
        model = Client
        include_fk = True
        load_instance = True

    gender = fields.String(validate=validate.OneOf(Client.GENDERS))
    email = fields.Email()
    phone = fields.String(validate=validate.Length(min=7, max=20))
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ProgramSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing/deserializing Program objects."""
    class Meta:
        model = Program
        load_instance = True

    name = fields.String(required=True, validate=validate.Length(min=2, max=100))
    is_active = fields.Boolean(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)


class ClientProgramSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing/deserializing ClientProgram objects."""
    class Meta:
        model = ClientProgram
        include_fk = True
        load_instance = True

    status = fields.String(validate=validate.OneOf(ClientProgram.STATUSES))
    progress = fields.Integer(validate=validate.Range(min=0, max=100))
    enrollment_date = fields.Date(dump_only=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    program = ma.Nested(ProgramSchema)
    client = ma.Nested(ClientSchema)


class VisitSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing/deserializing Visit objects."""
    class Meta:
        model = Visit
        include_fk = True
        load_instance = True

    visit_type = fields.String(validate=validate_visit_type)  # Use custom validator
    visit_date = fields.DateTime(required=True)
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    client = ma.Nested(ClientSchema)
    user = ma.Nested(UserSchema)


class AppointmentSchema(ma.SQLAlchemyAutoSchema):
    """Schema for serializing/deserializing Appointment objects."""
    class Meta:
        model = Appointment
        include_fk = True
        load_instance = True

    status = fields.String(validate=validate.OneOf(Appointment.STATUSES))
    date = fields.DateTime(required=True)
    duration_minutes = fields.Integer(
        validate=validate.Range(min=15, max=240),
        load_default=30
    )
    created_at = fields.DateTime(dump_only=True)
    updated_at = fields.DateTime(dump_only=True)

    client = ma.Nested(ClientSchema)


# Initialize serializers
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