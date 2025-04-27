from flask import Blueprint, request, jsonify
from backend import db
from backend.models import Visit, Client, User
from backend.schemas import visit_schema, visits_schema
from backend.utils.auth import token_required, roles_required
from backend.utils.helpers import parse_datetime, validate_visit_type
from datetime import datetime

visits_bp = Blueprint('visits', __name__)

VISIT_TYPES = [
    'consultation', 'follow_up', 'emergency',
    'vaccination', 'test', 'procedure', 'other'
]


@visits_bp.route('/', methods=['GET'])
@roles_required(['admin', 'doctor', 'nurse'])
def get_visits(current_user):
    """Get visits with filters"""
    client_id = request.args.get('client_id')
    visit_type = request.args.get('type')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Visit.query.join(Client).filter(Client.is_active == True)

    if client_id:
        query = query.filter(Visit.client_id == client_id)

    if visit_type and visit_type in VISIT_TYPES:
        query = query.filter(Visit.visit_type == visit_type)

    if start_date:
        try:
            start_date = parse_datetime(start_date)
            query = query.filter(Visit.visit_date >= start_date)
        except:
            return jsonify({'error': 'Invalid start date format'}), 400

    if end_date:
        try:
            end_date = parse_datetime(end_date)
            query = query.filter(Visit.visit_date <= end_date)
        except:
            return jsonify({'error': 'Invalid end date format'}), 400

    visits = query.order_by(Visit.visit_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'data': visits_schema.dump(visits.items),
        'total': visits.total,
        'pages': visits.pages,
        'current_page': visits.page
    }), 200


@visits_bp.route('/<client_id>', methods=['POST'])
@roles_required(['admin', 'doctor', 'nurse'])
def create_visit(current_user, client_id):
    """Create a new visit record"""
    client = Client.query.filter_by(id=client_id, is_active=True).first_or_404()
    data = request.get_json()

    required_fields = ['visit_date', 'purpose', 'type']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    if not validate_visit_type(data['type']):
        return jsonify({
            'error': f'Invalid visit type. Must be one of: {", ".join(VISIT_TYPES)}'
        }), 400

    try:
        visit_date = parse_datetime(data['visit_date'])
        if visit_date > datetime.utcnow():
            return jsonify({'error': 'Visit date cannot be in the future'}), 400

        new_visit = Visit(
            client_id=client_id,
            visit_date=visit_date,
            visit_type=data['type'].lower(),
            purpose=data['purpose'].strip(),
            diagnosis=data.get('diagnosis', '').strip(),
            treatment=data.get('treatment', '').strip(),
            notes=data.get('notes', '').strip(),
            created_by=current_user.id
        )

        db.session.add(new_visit)
        db.session.commit()

        return jsonify({
            'message': 'Visit recorded successfully',
            'visit': visit_schema.dump(new_visit)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


@visits_bp.route('/<visit_id>', methods=['GET'])
@roles_required(['admin', 'doctor', 'nurse'])
def get_visit(current_user, visit_id):
    """Get specific visit details"""
    visit = Visit.query.get_or_404(visit_id)
    return jsonify(visit_schema.dump(visit)), 200


@visits_bp.route('/<visit_id>', methods=['PUT'])
@roles_required(['admin', 'doctor'])
def update_visit(current_user, visit_id):
    """Update visit information"""
    visit = Visit.query.get_or_404(visit_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        if 'visit_date' in data:
            new_date = parse_datetime(data['visit_date'])
            if new_date > datetime.utcnow():
                return jsonify({'error': 'Visit date cannot be in the future'}), 400
            visit.visit_date = new_date

        if 'type' in data:
            if not validate_visit_type(data['type']):
                return jsonify({
                    'error': f'Invalid visit type. Must be one of: {", ".join(VISIT_TYPES)}'
                }), 400
            visit.visit_type = data['type'].lower()

        if 'purpose' in data:
            visit.purpose = data['purpose'].strip()

        if 'diagnosis' in data:
            visit.diagnosis = data['diagnosis'].strip()

        if 'treatment' in data:
            visit.treatment = data['treatment'].strip()

        if 'notes' in data:
            visit.notes = data['notes'].strip()

        db.session.commit()

        return jsonify({
            'message': 'Visit updated successfully',
            'visit': visit_schema.dump(visit)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400