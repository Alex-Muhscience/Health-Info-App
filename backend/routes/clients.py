from datetime import datetime

from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_

from backend import db
from backend.models import Client, ClientProgram, Program
from backend.schemas import (
    client_schema,
    clients_schema,
    client_programs_schema,
    programs_schema
)
from backend.utils.auth import token_required
from backend.utils.pagination import paginate_query
from backend.utils.validators import Validators

clients_bp = Blueprint('clients', __name__, url_prefix='/api/clients')


@clients_bp.route('/', methods=['GET', 'POST'])
@token_required
def clients(current_user):
    if request.method == 'GET':
        """
        Get all clients with optional search and pagination
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: query
            in: query
            type: string
            required: false
            description: Search term
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
          - name: active_only
            in: query
            type: boolean
            required: false
            default: true
        responses:
          200:
            description: List of clients
            schema:
              type: object
              properties:
                clients:
                  type: array
                  items:
                    $ref: '#/definitions/Client'
                total:
                  type: integer
                pages:
                  type: integer
                current_page:
                  type: integer
        """
        search = request.args.get('query', '').strip()
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        query = Client.query

        if active_only:
            query = query.filter(Client.is_active == True)

        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Client.first_name.ilike(search_term),
                    Client.last_name.ilike(search_term),
                    Client.phone.ilike(search_term),
                    Client.email.ilike(search_term),
                    Client.notes.ilike(search_term)
                )
            )

        return paginate_query(
            query,
            clients_schema,
            page=request.args.get('page', 1, type=int),
            per_page=request.args.get('per_page', 20, type=int)
        )

    elif request.method == 'POST':
        """
        Create a new client
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/ClientCreate'
        responses:
          201:
            description: Client created
            schema:
              $ref: '#/definitions/Client'
          400:
            description: Invalid input
        """
        data = request.get_json()

        # Validate required fields
        validation = Validators.validate_user_data(data)
        if not validation['valid']:
            return jsonify({'errors': validation['errors']}), 400

        # Additional validation
        if 'email' in data and not Validators.validate_email(data['email']):
            return jsonify({'message': 'Invalid email format'}), 400

        if not Validators.validate_phone(data['phone']):
            return jsonify({'message': 'Invalid phone number'}), 400

        # Create new client
        new_client = Client(
            first_name=data['first_name'],
            last_name=data['last_name'],
            dob=datetime.strptime(data['dob'], '%Y-%m-%d').date(),
            gender=data['gender'],
            phone=data['phone'],
            email=data.get('email'),
            address=data.get('address'),
            emergency_contact_name=data.get('emergency_contact_name'),
            emergency_contact_phone=data.get('emergency_contact_phone'),
            notes=data.get('notes'),
            created_by=current_user.id
        )

        db.session.add(new_client)
        db.session.commit()

        return jsonify({
            'message': 'Client created successfully',
            'client': client_schema.dump(new_client)
        }), 201


@clients_bp.route('/<int:client_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def client_detail(current_user, client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'GET':
        """
        Get client details
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: client_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Client details
            schema:
              $ref: '#/definitions/Client'
          404:
            description: Client not found
        """
        return jsonify(client_schema.dump(client))

    elif request.method == 'PUT':
        """
        Update client details
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: client_id
            in: path
            type: integer
            required: true
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/ClientUpdate'
        responses:
          200:
            description: Client updated
            schema:
              $ref: '#/definitions/Client'
          400:
            description: Invalid input
          404:
            description: Client not found
        """
        data = request.get_json()

        # Validate input
        if 'email' in data and data['email'] and not Validators.validate_email(data['email']):
            return jsonify({'message': 'Invalid email format'}), 400

        if 'phone' in data and not Validators.validate_phone(data['phone']):
            return jsonify({'message': 'Invalid phone number'}), 400

        # Update fields
        updateable_fields = [
            'first_name', 'last_name', 'dob', 'gender',
            'phone', 'email', 'address', 'emergency_contact_name',
            'emergency_contact_phone', 'notes', 'is_active'
        ]

        for field in updateable_fields:
            if field in data:
                if field == 'dob':
                    setattr(client, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                else:
                    setattr(client, field, data[field])

        client.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Client updated successfully',
            'client': client_schema.dump(client)
        })

    elif request.method == 'DELETE':
        """
        Delete a client (soft delete)
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: client_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: Client deactivated
          403:
            description: Forbidden
          404:
            description: Client not found
        """
        if current_user.role != 'admin':
            return jsonify({'message': 'Admin access required'}), 403

        client.is_active = False
        client.deactivated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Client deactivated successfully'})


@clients_bp.route('/<int:client_id>/programs', methods=['GET', 'POST'])
@token_required
def client_programs(current_user, client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'GET':
        """
        Get programs for a client
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: client_id
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
            description: List of programs
            schema:
              type: array
              items:
                $ref: '#/definitions/Program'
          404:
            description: Client not found
        """
        active_only = request.args.get('active_only', 'true').lower() == 'true'

        query = Program.query.join(ClientProgram).filter(
            ClientProgram.client_id == client_id
        )

        if active_only:
            query = query.filter(
                and_(
                    Program.is_active == True,
                    ClientProgram.status == 'active'
                )
            )

        programs = query.all()
        return jsonify(programs_schema.dump(programs))

    elif request.method == 'POST':
        """
        Enroll client in programs
        ---
        tags:
          - Clients
        security:
          - BearerAuth: []
        parameters:
          - name: client_id
            in: path
            type: integer
            required: true
          - name: body
            in: body
            required: true
            schema:
              type: object
              properties:
                program_ids:
                  type: array
                  items:
                    type: integer
                enrollment_date:
                  type: string
                  format: date
                status:
                  type: string
                  enum: [active, completed, cancelled]
                  default: active
                notes:
                  type: string
        responses:
          201:
            description: Enrollment successful
            schema:
              type: object
              properties:
                message:
                  type: string
                enrollments:
                  type: array
                  items:
                    $ref: '#/definitions/ClientProgram'
          400:
            description: Invalid input
          404:
            description: Client or program not found
        """
        data = request.get_json()

        if not data or not data.get('program_ids'):
            return jsonify({'message': 'Program IDs are required'}), 400

        programs = Program.query.filter(
            Program.id.in_(data['program_ids']),
            Program.is_active == True
        ).all()

        if len(programs) != len(data['program_ids']):
            return jsonify({'message': 'One or more programs not found or inactive'}), 404

        enrollments = []
        for program in programs:
            enrollment = ClientProgram(
                client_id=client_id,
                program_id=program.id,
                enrollment_date=datetime.strptime(
                    data.get('enrollment_date'),
                    '%Y-%m-%d'
                ).date() if data.get('enrollment_date') else datetime.utcnow().date(),
                status=data.get('status', 'active'),
                notes=data.get('notes'),
                enrolled_by=current_user.id
            )
            db.session.add(enrollment)
            enrollments.append(enrollment)

        db.session.commit()

        return jsonify({
            'message': f'Enrolled in {len(programs)} program(s)',
            'enrollments': client_programs_schema.dump(enrollments)
        }), 201