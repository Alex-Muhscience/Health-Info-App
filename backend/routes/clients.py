from flask import Blueprint, request, jsonify
from backend import db
from backend.models import Client, ClientProgram, Program
from backend.schemas import client_schema, clients_schema, client_programs_schema
from backend.utils.auth import token_required, roles_required
from backend.utils.helpers import parse_date, validate_phone, validate_email
from datetime import datetime
from sqlalchemy import or_, and_

clients_bp = Blueprint('clients', __name__)


@clients_bp.route('/', methods=['GET'])
@roles_required('admin', 'doctor', 'nurse', 'receptionist')
def get_clients(current_user):
    """Get paginated list of clients with optional filters"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        search_query = request.args.get('query', '')
        gender = request.args.get('gender')
        active_only = request.args.get('active_only', 'true').lower() == 'true'
        min_age = request.args.get('min_age', type=int)
        max_age = request.args.get('max_age', type=int)

        query = Client.query

        # Apply filters
        if search_query:
            query = query.filter(or_(
                Client.first_name.ilike(f'%{search_query}%'),
                Client.last_name.ilike(f'%{search_query}%'),
                Client.phone.ilike(f'%{search_query}%'),
                Client.email.ilike(f'%{search_query}%')
            ))

        if gender and gender.lower() != 'all':
            query = query.filter_by(gender=gender.lower())

        if active_only:
            query = query.filter_by(is_active=True)

        if min_age or max_age:
            today = datetime.utcnow().date()
            if min_age:
                max_dob = today.replace(year=today.year - min_age)
                query = query.filter(Client.dob <= max_dob)
            if max_age:
                min_dob = today.replace(year=today.year - max_age - 1)
                query = query.filter(Client.dob > min_dob)

        # Order by creation date (newest first)
        query = query.order_by(Client.created_at.desc())

        # Pagination
        paginated_clients = query.paginate(page=page, per_page=per_page, error_out=False)

        # Calculate age for each client
        clients_data = []
        for client in paginated_clients.items:
            client_dict = client_schema.dump(client)
            if client.dob:
                age = (datetime.utcnow().date() - client.dob).days // 365
                client_dict['age'] = age
            else:
                client_dict['age'] = None
            clients_data.append(client_dict)

        return jsonify({
            'data': clients_data,
            'total': paginated_clients.total,
            'pages': paginated_clients.pages,
            'current_page': paginated_clients.page,
            'per_page': per_page
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/', methods=['POST'])
@roles_required('admin', 'doctor', 'nurse', 'receptionist')
def create_client(current_user):
    """Create a new client"""
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        required_fields = ['first_name', 'last_name', 'dob', 'gender', 'phone']
        missing_fields = [field for field in required_fields if not data.get(field)]
        
        if missing_fields:
            return jsonify({
                'error': f'Missing required fields: {", ".join(missing_fields)}'
            }), 400

        # Validate phone number
        if not validate_phone(data['phone']):
            return jsonify({'error': 'Invalid phone number format'}), 400

        # Validate email if provided
        if data.get('email') and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Check for duplicate phone number
        existing_client = Client.query.filter_by(phone=data['phone']).first()
        if existing_client:
            return jsonify({'error': 'A client with this phone number already exists'}), 409

        new_client = Client(
            first_name=data['first_name'].strip(),
            last_name=data['last_name'].strip(),
            dob=parse_date(data['dob']),
            gender=data['gender'].lower(),
            phone=data['phone'].strip(),
            email=data.get('email', '').strip().lower() if data.get('email') else None,
            address=data.get('address', '').strip() if data.get('address') else None,
            emergency_contact_name=data.get('emergency_contact_name', '').strip() if data.get('emergency_contact_name') else None,
            emergency_contact_phone=data.get('emergency_contact_phone', '').strip() if data.get('emergency_contact_phone') else None,
            notes=data.get('notes', '').strip() if data.get('notes') else None,
            created_at=datetime.utcnow(),
            is_active=True
        )

        db.session.add(new_client)
        db.session.commit()

        return jsonify({
            'message': 'Client created successfully',
            'client': client_schema.dump(new_client)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>', methods=['GET'])
@roles_required('admin', 'doctor', 'nurse')
def get_client(current_user, client_id):
    """Get client details by ID"""
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        client_data = client_schema.dump(client)
        
        # Calculate age
        if client.dob:
            age = (datetime.utcnow().date() - client.dob).days // 365
            client_data['age'] = age
        
        return jsonify(client_data), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>', methods=['PUT'])
@roles_required('admin', 'doctor', 'nurse')
def update_client(current_user, client_id):
    """Update client information"""
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate phone if being updated
        if 'phone' in data and data['phone']:
            if not validate_phone(data['phone']):
                return jsonify({'error': 'Invalid phone number format'}), 400
            
            # Check for duplicate phone (excluding current client)
            existing_client = Client.query.filter(
                Client.phone == data['phone'],
                Client.id != client_id
            ).first()
            if existing_client:
                return jsonify({'error': 'A client with this phone number already exists'}), 409

        # Validate email if being updated
        if 'email' in data and data['email'] and not validate_email(data['email']):
            return jsonify({'error': 'Invalid email format'}), 400

        # Update fields
        if 'first_name' in data:
            client.first_name = data['first_name'].strip()
        if 'last_name' in data:
            client.last_name = data['last_name'].strip()
        if 'dob' in data:
            client.dob = parse_date(data['dob'])
        if 'gender' in data:
            client.gender = data['gender'].lower()
        if 'phone' in data:
            client.phone = data['phone'].strip()
        if 'email' in data:
            client.email = data['email'].strip().lower() if data['email'] else None
        if 'is_active' in data:
            client.is_active = bool(data['is_active'])

        # Optional fields
        optional_fields = ['address', 'emergency_contact_name', 'emergency_contact_phone', 'notes']
        for field in optional_fields:
            if field in data:
                setattr(client, field, data[field].strip() if data[field] else None)

        client.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'Client updated successfully',
            'client': client_schema.dump(client)
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>', methods=['DELETE'])
@roles_required('admin')
def delete_client(current_user, client_id):
    """Deactivate a client (soft delete)"""
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        if not client.is_active:
            return jsonify({'error': 'Client is already deactivated'}), 400

        client.is_active = False
        client.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'Client deactivated successfully'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>/programs', methods=['GET'])
@roles_required('admin', 'doctor', 'nurse')
def get_client_programs(current_user, client_id):
    """Get programs for a specific client"""
    try:
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404

        status = request.args.get('status')
        query = ClientProgram.query.filter_by(client_id=client_id)

        if status:
            query = query.filter_by(status=status.lower())

        programs = query.all()
        return jsonify({
            'data': client_programs_schema.dump(programs),
            'total': len(programs)
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@clients_bp.route('/<client_id>/programs', methods=['POST'])
@roles_required('admin', 'doctor', 'nurse')
def enroll_client(current_user, client_id):
    """Enroll client in programs"""
    try:
        data = request.get_json()

        if not data or not data.get('program_ids'):
            return jsonify({'error': 'Program IDs are required'}), 400

        # Verify client exists
        client = Client.query.get(client_id)
        if not client:
            return jsonify({'error': 'Client not found'}), 404
        
        if not client.is_active:
            return jsonify({'error': 'Cannot enroll inactive client'}), 400

        # Get programs
        programs = Program.query.filter(
            Program.id.in_(data['program_ids']),
            Program.is_active == True
        ).all()

        if len(programs) != len(data['program_ids']):
            missing_ids = set(data['program_ids']) - {p.id for p in programs}
            return jsonify({
                'error': 'Some programs not found or inactive',
                'missing_ids': list(missing_ids)
            }), 404

        # Check for existing enrollments
        existing = ClientProgram.query.filter(
            ClientProgram.client_id == client_id,
            ClientProgram.program_id.in_(data['program_ids'])
        ).all()

        if existing:
            existing_ids = [e.program_id for e in existing]
            return jsonify({
                'error': 'Client already enrolled in some programs',
                'existing_programs': existing_ids
            }), 409

        # Create enrollments
        enrollments = []
        for program in programs:
            enrollment = ClientProgram(
                client_id=client_id,
                program_id=program.id,
                enrollment_date=datetime.utcnow().date(),
                status=data.get('status', 'active').lower(),
                notes=data.get('notes', '').strip() if data.get('notes') else None
            )
            db.session.add(enrollment)
            enrollments.append(enrollment)

        db.session.commit()
        return jsonify({
            'message': f'Client enrolled in {len(programs)} program(s)',
            'enrollments': client_programs_schema.dump(enrollments)
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500