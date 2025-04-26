from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import func, and_, or_

from backend import db
from backend.models import Program, ClientProgram, Client
from backend.schemas import (
    program_schema,
    programs_schema,
    client_programs_schema,
    clients_schema
)
from backend.utils.auth import token_required
from backend.utils.pagination import paginate_query
from backend.utils.validators import Validators

programs_bp = Blueprint('programs', __name__, url_prefix='/api/programs')


@programs_bp.route('/', methods=['GET', 'POST'])
@token_required
def handle_programs(current_user):
    if request.method == 'GET':
        """
        Get all programs with filtering and pagination
        ---
        tags:
          - Programs
        security:
          - BearerAuth: []
        parameters:
          - name: active_only
            in: query
            type: boolean
            required: false
            default: true
          - name: page
            in: query
            type: integer
            required: false
            default: 1
          - name: per_page
            in: query
            type: integer
            required: false
            default: 20
          - name: search
            in: query
            type: string
            required: false
        responses:
          200:
            description: List of programs
            schema:
              type: object
              properties:
                programs:
                  type: array
                  items:
                    $ref: '#/definitions/Program'
                total:
                  type: integer
                pages:
                  type: integer
                current_page:
                  type: integer
        """
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        search = request.args.get('search', '').strip()

        query = Program.query

        if active_only:
            query = query.filter(Program.is_active == True)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Program.name.ilike(search_term),
                    Program.description.ilike(search_term)
                )
            )

        # Add enrollment count subquery
        enrollment_count = db.session.query(
            ClientProgram.program_id,
            func.count(ClientProgram.id).label('enrollment_count')
        ).group_by(ClientProgram.program_id).subquery()

        query = query.outerjoin(
            enrollment_count,
            Program.id == enrollment_count.c.program_id
        ).add_columns(
            enrollment_count.c.enrollment_count
        )

        return paginate_query(
            query,
            programs_schema,
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 20, type=int),
            extra_fields=['enrollment_count']
        )

    elif request.method == 'POST':
        """
        Create a new program
        ---
        tags:
          - Programs
        security:
          - BearerAuth: []
        parameters:
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/ProgramCreate'
        responses:
          201:
            description: Program created
            schema:
              $ref: '#/definitions/Program'
          400:
            description: Invalid input
        """
        data = request.get_json()

        validation = Validators.validate_program_data(data)
        if not validation['valid']:
            return jsonify({'errors': validation['errors']}), 400

        if Program.query.filter_by(name=data['name']).first():
            return jsonify({'message': 'Program with this name already exists'}), 409

        new_program = Program(
            name=data['name'],
            description=data.get('description', ''),
            is_active=data.get('is_active', True),
            duration_days=data.get('duration_days'),
            cost=data.get('cost'),
            created_by=current_user.id
        )

        db.session.add(new_program)
        db.session.commit()

        return jsonify({
            'message': 'Program created successfully',
            'program': program_schema.dump(new_program)
        }), 201


@programs_bp.route('/<int:program_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def handle_program(current_user, program_id):
    program = Program.query.get_or_404(program_id)

    if request.method == 'GET':
        """
        Get program details including enrolled clients
        ---
        tags:
          - Programs
        security:
          - BearerAuth: []
        parameters:
          - name: program_id
            in: path
            type: integer
            required: true
          - name: active_only
            in: query
            type: boolean
            required: false
            default: true
        responses:
          200:
            description: Program details
            schema:
              allOf:
                - $ref: '#/definitions/Program'
                - type: object
                  properties:
                    enrolled_clients:
                      type: array
                      items:
                        $ref: '#/definitions/Client'
                    enrollment_count:
                      type: integer
          404:
            description: Program not found
        """
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        program_data = program_schema.dump(program)

        # Get enrolled clients
        query = Client.query.join(ClientProgram).filter(
            ClientProgram.program_id == program_id
        )

        if active_only:
            query = query.filter(
                and_(
                    Client.is_active == True,
                    ClientProgram.status == 'active'
                )
            )

        clients = query.all()
        program_data['enrolled_clients'] = clients_schema.dump(clients)
        program_data['enrollment_count'] = len(clients)

        return jsonify(program_data)

    elif request.method == 'PUT':
        """
        Update program details
        ---
        tags:
          - Programs
        security:
          - BearerAuth: []
        parameters:
          - name: program_id
            in: path
            type: integer
            required: true
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/ProgramUpdate'
        responses:
          200:
            description: Program updated
            schema:
              $ref: '#/definitions/Program'
          400:
            description: Invalid input
          404:
            description: Program not found
        """
        data = request.get_json()

        if 'name' in data and data['name'] != program.name:
            if Program.query.filter_by(name=data['name']).first():
                return jsonify({'message': 'Program name already exists'}), 409

        updateable_fields = [
            'name', 'description', 'is_active',
            'duration_days', 'cost'
        ]

        for field in updateable_fields:
            if field in data:
                setattr(program, field, data[field])

        program.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Program updated successfully',
            'program': program_schema.dump(program)
        })

    elif request.method == 'DELETE':
        """
        Deactivate a program (soft delete)
        ---
        tags:
          - Programs
        security:
          - BearerAuth: []
        parameters:
          - name: program_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Program deactivated
          403:
            description: Forbidden
          404:
            description: Program not found
        """
        if current_user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403

        # Check for active enrollments
        active_enrollments = ClientProgram.query.filter(
            and_(
                ClientProgram.program_id == program_id,
                ClientProgram.status == 'active'
            )
        ).count()

        if active_enrollments > 0:
            return jsonify({
                'message': f'Cannot deactivate - {active_enrollments} active enrollments',
                'active_enrollments': active_enrollments
            }), 400

        program.is_active = False
        program.deactivated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Program deactivated successfully'})


@programs_bp.route('/<int:program_id>/enrollments', methods=['GET'])
@token_required
def program_enrollments(current_user, program_id):
    """
    Get enrollment details for a program
    ---
    tags:
      - Programs
    security:
      - BearerAuth: []
    parameters:
      - name: program_id
        in: path
        type: integer
        required: true
      - name: status
        in: query
        type: string
        enum: [active, completed, cancelled, all]
        required: false
        default: active
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: per_page
        in: query
        type: integer
        required: false
        default: 20
    responses:
      200:
        description: List of enrollments
        schema:
          type: object
          properties:
            enrollments:
              type: array
              items:
                $ref: '#/definitions/ClientProgram'
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      404:
        description: Program not found
    """
    status = request.args.get('status', 'active')

    query = ClientProgram.query.filter(
        ClientProgram.program_id == program_id
    )

    if status != 'all':
        query = query.filter(ClientProgram.status == status)

    return paginate_query(
        query,
        client_programs_schema,
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 20, type=int)
    )