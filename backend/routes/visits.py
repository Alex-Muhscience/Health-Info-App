from flask import Blueprint, request, jsonify
from backend.models import Visit
from backend import db
from backend.schemas import visit_schema, visits_schema
from backend.utils.auth import token_required
from datetime import datetime

visits_bp = Blueprint('visits', __name__)


@visits_bp.route('/client/<client_id>', methods=['GET', 'POST'])
@token_required
def handle_client_visits(current_user, client_id):
    if request.method == 'GET':
        visits = Visit.query.filter_by(client_id=client_id).all()
        return jsonify(visits_schema.dump(visits))

    elif request.method == 'POST':
        data = request.get_json()

        if not data or not data.get('purpose'):
            return jsonify({'message': 'Visit purpose is required!'}), 400

        new_visit = Visit(
            client_id=client_id,
            visit_date=datetime.strptime(data['visit_date'], '%Y-%m-%d %H:%M:%S') if data.get(
                'visit_date') else datetime.utcnow(),
            purpose=data['purpose'],
            diagnosis=data.get('diagnosis'),
            treatment=data.get('treatment'),
            notes=data.get('notes'),
            created_by=current_user.id
        )

        db.session.add(new_visit)
        db.session.commit()

        return jsonify({
            'message': 'Visit recorded successfully!',
            'visit': visit_schema.dump(new_visit)
        }), 201


@visits_bp.route('/<visit_id>', methods=['GET', 'PUT', 'DELETE'])
@token_required
def handle_visit(current_user, visit_id):
    visit = Visit.query.get_or_404(visit_id)

    if request.method == 'GET':
        return jsonify(visit_schema.dump(visit))

    elif request.method == 'PUT':
        data = request.get_json()

        if not data:
            return jsonify({'message': 'No data provided!'}), 400

        if data.get('visit_date'):
            visit.visit_date = datetime.strptime(data['visit_date'], '%Y-%m-%d %H:%M:%S')
        visit.purpose = data.get('purpose', visit.purpose)
        visit.diagnosis = data.get('diagnosis', visit.diagnosis)
        visit.treatment = data.get('treatment', visit.treatment)
        visit.notes = data.get('notes', visit.notes)

        db.session.commit()

        return jsonify({
            'message': 'Visit updated successfully!',
            'visit': visit_schema.dump(visit)
        })

    elif request.method == 'DELETE':
        db.session.delete(visit)
        db.session.commit()

        return jsonify({'message': 'Visit deleted successfully!'}), 200