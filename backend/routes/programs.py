from flask import Blueprint, request, jsonify
from backend import db
from backend.models import Program, ClientProgram, Client
from backend.schemas import program_schema, programs_schema, client_programs_schema
from backend.utils.auth import token_required, roles_required
from backend.utils.helpers import validate_name
from datetime import datetime

programs_bp = Blueprint('programs', __name__)


@programs_bp.route('/', methods=['GET'])
@token_required
def get_programs(current_user):
    """Get all active programs with optional filters"""
    active_only = request.args.get('active_only', 'true').lower() == 'true'
    search = request.args.get('search', '').strip()

    query = Program.query

    if active_only:
        query = query.filter_by(is_active=True)

    if search:
        query = query.filter(Program.name.ilike(f'%{search}%'))

    programs = query.order_by(Program.name).all()
    return jsonify(programs_schema.dump(programs)), 200


@programs_bp.route('/', methods=['POST'])
@roles_required(['admin', 'doctor'])
def create_program(current_user):
    """Create a new health program"""
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({'error': 'Program name is required'}), 400

    if not validate_name(data['name']):
        return jsonify({'error': 'Invalid program name'}), 400

    if Program.query.filter(Program.name.ilike(data['name'])).first():
        return jsonify({'error': 'Program with similar name already exists'}), 409

    try:
        new_program = Program(
            name=data['name'].strip(),
            description=data.get('description', '').strip(),
            duration_days=data.get('duration_days'),
            is_active=data.get('is_active', True)
        )

        db.session.add(new_program)
        db.session.commit()

        return jsonify({
            'message': 'Program created successfully',
            'program': program_schema.dump(new_program)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@programs_bp.route('/<program_id>', methods=['GET'])
@token_required
def get_program(current_user, program_id):
    """Get program details"""
    program = Program.query.get_or_404(program_id)
    return jsonify(program_schema.dump(program)), 200


@programs_bp.route('/<program_id>', methods=['PUT'])
@roles_required(['admin', 'doctor'])
def update_program(current_user, program_id):
    """Update program information"""
    program = Program.query.get_or_404(program_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        if 'name' in data:
            if not validate_name(data['name']):
                return jsonify({'error': 'Invalid program name'}), 400
            if Program.query.filter(
                    Program.name.ilike(data['name']),
                    Program.id != program_id
            ).first():
                return jsonify({'error': 'Program with similar name already exists'}), 409
            program.name = data['name'].strip()

        if 'description' in data:
            program.description = data['description'].strip()

        if 'duration_days' in data:
            program.duration_days = data['duration_days']

        if 'is_active' in data:
            program.is_active = bool(data['is_active'])
            if not program.is_active:
                # Deactivate all enrollments when program is deactivated
                ClientProgram.query.filter_by(program_id=program_id).update(
                    {'status': 'inactive'}
                )

        db.session.commit()

        return jsonify({
            'message': 'Program updated successfully',
            'program': program_schema.dump(program)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@programs_bp.route('/<program_id>/enrollments', methods=['GET'])
@roles_required(['admin', 'doctor', 'nurse'])
def get_program_enrollments(current_user, program_id):
    """Get all enrollments for a specific program"""
    status = request.args.get('status')
    active_only = request.args.get('active_only', 'true').lower() == 'true'

    query = ClientProgram.query.filter_by(program_id=program_id)

    if status:
        query = query.filter_by(status=status.lower())

    if active_only:
        query = query.join(Client).filter(Client.is_active == True)

    enrollments = query.all()
    return jsonify(client_programs_schema.dump(enrollments)), 200