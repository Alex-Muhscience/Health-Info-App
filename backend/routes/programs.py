from flask import Blueprint, request, jsonify
from backend.models import Program
from backend import db
from backend.schemas import program_schema, programs_schema
from backend.utils.auth import token_required

programs_bp = Blueprint('programs', __name__)


@programs_bp.route('/', methods=['GET', 'POST'])
@token_required
def handle_programs(current_user):
    if request.method == 'GET':
        programs = Program.query.all()
        return jsonify(programs_schema.dump(programs))

    elif request.method == 'POST':
        data = request.get_json()

        if not data or not data.get('name'):
            return jsonify({'message': 'Program name is required!'}), 400

        new_program = Program(
            name=data['name'],
            description=data.get('description'),
            is_active=data.get('is_active', True)
        )

        db.session.add(new_program)
        db.session.commit()

        return jsonify({
            'message': 'Program created successfully!',
            'program': program_schema.dump(new_program)
        }), 201


@programs_bp.route('/<program_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def handle_program(current_user, program_id):
    program = Program.query.get_or_404(program_id)

    if request.method == 'GET':
        return jsonify(program_schema.dump(program))

    elif request.method == 'PUT':
        data = request.get_json()

        if not data:
            return jsonify({'message': 'No data provided!'}), 400

        program.name = data.get('name', program.name)
        program.description = data.get('description', program.description)
        program.is_active = data.get('is_active', program.is_active)

        db.session.commit()

        return jsonify({
            'message': 'Program updated successfully!',
            'program': program_schema.dump(program)
        })

    elif request.method == 'DELETE':
        db.session.delete(program)
        db.session.commit()

        return jsonify({'message': 'Program deleted successfully!'}), 200