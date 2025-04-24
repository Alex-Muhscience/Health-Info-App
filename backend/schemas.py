from backend import ma
from backend.models import User, Client, Program, ClientProgram, Visit


class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        exclude = ('password',)


class ClientSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Client
        include_fk = True


class ProgramSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Program


class ClientProgramSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = ClientProgram
        include_fk = True

    program = ma.Nested(ProgramSchema)


class VisitSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Visit
        include_fk = True


# Initialize schemas
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