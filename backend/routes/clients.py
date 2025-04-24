from flask import Blueprint, request, jsonify
from backend.models import Client
from backend import db
from backend.schemas import client_schema, clients_schema
from backend.utils.auth import token_required
from datetime import datetime

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/', methods=['GET', 'POST'])
@token_required
def handle_clients(current_user):
    if request.method == 'GET':
        search_query = request.args.get('query', '')

        if search_query:
            clients = Client.query.filter(
                (Client.first_name.ilike(f'%{search_query}%')) |
                (Client.last_name.ilike(f'%{search_query}%')) |
                (Client.phone.ilike(f'%{search_query}%')) |
                (Client.email.ilike(f'%{search_query}%'))
            ).all()
        else:
            clients = Client.query.all()

        return jsonify(clients_schema.dump(clients))

    elif request.method == 'POST':
        data = request.get_json()

        required_fields = ['first_name', 'last_name', 'dob', 'gender', 'phone']
        if not all(field in data for field in required_fields):
            return jsonify({'message': 'Missing required fields!'}), 400

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
            notes=data.get('notes')
        )

        db.session.add(new_client)
        db.session.commit()

        return jsonify({
            'message': 'Client created successfully!',
            'client': client_schema.dump(new_client)
        }), 201


@clients_bp.route('/<client_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def handle_client(current_user, client_id):
    client = Client.query.get_or_404(client_id)

    if request.method == 'GET':
        return jsonify(client_schema.dump(client))

    elif request.method == 'PUT':
        data = request.get_json()

        if not data:
            return jsonify({'message': 'No data provided!'}), 400

        client.first_name = data.get('first_name', client.first_name)
        client.last_name = data.get('last_name', client.last_name)
        if data.get('dob'):
            client.dob = datetime.strptime(data['dob'], '%Y-%m-%d').date()
        client.gender = data.get('gender', client.gender)
        client.phone = data.get('phone', client.phone)
        client.email = data.get('email', client.email)
        client.address = data.get('address', client.address)
        client.emergency_contact_name = data.get('emergency_contact_name', client.emergency_contact_name)
        client.emergency_contact_phone = data.get('emergency_contact_phone', client.emergency_contact_phone)
        client.notes = data.get('notes', client.notes)

        db.session.commit()

        return jsonify({
            'message': 'Client updated successfully!',
            'client': client_schema.dump(client)
        })

    elif request.method == 'DELETE':
        db.session.delete(client)
        db.session.commit()

        return jsonify({'message': 'Client deleted successfully!'}), 200


@clients_bp.route('/<client_id>/enroll', methods=['POST'])
@token_required
def enroll_client(current_user, client_id):
    data = request.get_json()

    if not data or not data.get('program_ids'):
        return jsonify({'message': 'Program IDs are required!'}), 400

    from backend.models import Program, ClientProgram

    programs = Program.query.filter(Program.id.in_(data['program_ids'])).all()

    if len(programs) != len(data['program_ids']):
        return jsonify({'message': 'One or more programs not found!'}), 404

    enrollments = []
    for program in programs:
        enrollment = ClientProgram(
            client_id=client_id,
            program_id=program.id,
            enrollment_date=datetime.strptime(data.get('enrollment_date'), '%Y-%m-%d').date() if data.get(
                'enrollment_date') else datetime.utcnow().date(),
            status=data.get('status', 'active'),
            notes=data.get('notes')
        )
        db.session.add(enrollment)
        enrollments.append(enrollment)

    db.session.commit()

    from backend.schemas import client_programs_schema

    return jsonify({
        'message': f'Client enrolled in {len(programs)} program(s) successfully!',
        'enrollments': client_programs_schema.dump(enrollments)
    }), 201