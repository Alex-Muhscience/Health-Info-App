from datetime import datetime, timedelta

from flask import Blueprint, request, jsonify
from sqlalchemy import or_, and_

from backend import db
from backend.models import Visit, Client, Program
from backend.schemas import (
    visit_schema,
    visits_schema,
    client_schema,
    program_schema,
    user_schema
)
from backend.utils.auth import token_required, practitioner_required
from backend.utils.helpers import DateUtils
from backend.utils.pagination import paginate_query
from backend.utils.validators import Validators

visits_bp = Blueprint('visits', __name__, url_prefix='/api/visits')


@visits_bp.route('/', methods=['GET'])
@token_required
def get_visits(current_user):
    """
    Get visits with filtering options
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: client_id
        in: query
        type: integer
        required: false
      - name: program_id
        in: query
        type: integer
        required: false
      - name: practitioner_id
        in: query
        type: integer
        required: false
      - name: date_range
        in: query
        type: string
        required: false
        description: Date range in format 'YYYY-MM-DD,YYYY-MM-DD'
      - name: status
        in: query
        type: string
        enum: [scheduled, completed, cancelled, no_show]
        required: false
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
        description: List of visits
        schema:
          type: object
          properties:
            visits:
              type: array
              items:
                $ref: '#/definitions/Visit'
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
    """
    # Build query with filters
    query = Visit.query

    # Client filter
    if 'client_id' in request.args:
        query = query.filter(Visit.client_id == request.args['client_id'])

    # Program filter
    if 'program_id' in request.args:
        query = query.filter(Visit.program_id == request.args['program_id'])

    # Practitioner filter
    if 'practitioner_id' in request.args:
        query = query.filter(Visit.created_by == request.args['practitioner_id'])

    # Date range filter
    if 'date_range' in request.args:
        start_date, end_date = DateUtils.parse_date_range(request.args['date_range'])
        query = query.filter(
            and_(
                Visit.visit_date >= start_date,
                Visit.visit_date <= end_date
            )
        )

    # Status filter
    if 'status' in request.args:
        query = query.filter(Visit.status == request.args['status'])

    # For non-admins, only show their own visits or their client's visits
    if current_user.role not in ['admin', 'practitioner']:
        query = query.filter(
            or_(
                Visit.client_id.in_(
                    [c.id for c in current_user.clients]
                ),
                Visit.created_by == current_user.id
            )
        )

    # Order by visit date (newest first)
    query = query.order_by(Visit.visit_date.desc())

    return paginate_query(
        query,
        visits_schema,
        per_page=request.args.get('per_page', 20, type=int)
    )


@visits_bp.route('/<int:visit_id>', methods=['GET'])
@token_required
def get_visit(current_user, visit_id):
    """
    Get visit details
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: visit_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Visit details
        schema:
          allOf:
            - $ref: '#/definitions/Visit'
            - type: object
              properties:
                client:
                  $ref: '#/definitions/Client'
                program:
                  $ref: '#/definitions/Program'
                practitioner:
                  $ref: '#/definitions/User'
      403:
        description: Forbidden
      404:
        description: Visit not found
    """
    visit = Visit.query.get_or_404(visit_id)

    # Authorization check
    if current_user.role not in ['admin', 'practitioner'] and \
            visit.client_id not in [c.id for c in current_user.clients] and \
            visit.created_by != current_user.id:
        return jsonify({'message': 'Access denied'}), 403

    visit_data = visit_schema.dump(visit)

    # Include related data
    visit_data['client'] = client_schema.dump(visit.client)
    if visit.program:
        visit_data['program'] = program_schema.dump(visit.program)
    visit_data['practitioner'] = user_schema.dump(visit.practitioner)

    return jsonify(visit_data)


@visits_bp.route('/', methods=['POST'])
@token_required
@practitioner_required
def create_visit(current_user):
    """
    Create a new visit
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/VisitCreate'
    responses:
      201:
        description: Visit created
        schema:
          $ref: '#/definitions/Visit'
      400:
        description: Invalid input
    """
    data = request.get_json()

    validation = Validators.validate_visit_data(data)
    if not validation['valid']:
        return jsonify({'errors': validation['errors']}), 400

    # Check client exists
    client = Client.query.get(data['client_id'])
    if not client:
        return jsonify({'message': 'Client not found'}), 404

    # Check program exists if specified
    program = None
    if 'program_id' in data:
        program = Program.query.get(data['program_id'])
        if not program:
            return jsonify({'message': 'Program not found'}), 404

    new_visit = Visit(
        client_id=data['client_id'],
        program_id=data.get('program_id'),
        visit_date=datetime.strptime(data['visit_date'], '%Y-%m-%d %H:%M:%S'),
        purpose=data['purpose'],
        status=data.get('status', 'scheduled'),
        diagnosis=data.get('diagnosis'),
        treatment=data.get('treatment'),
        notes=data.get('notes'),
        created_by=current_user.id
    )

    db.session.add(new_visit)
    db.session.commit()

    return jsonify({
        'message': 'Visit created successfully',
        'visit': visit_schema.dump(new_visit)
    }), 201


@visits_bp.route('/<int:visit_id>', methods=['PUT'])
@token_required
def update_visit(current_user, visit_id):
    """
    Update visit details
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: visit_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/VisitUpdate'
    responses:
      200:
        description: Visit updated
        schema:
          $ref: '#/definitions/Visit'
      400:
        description: Invalid input
      403:
        description: Forbidden
      404:
        description: Visit not found
    """
    visit = Visit.query.get_or_404(visit_id)

    # Authorization check
    if current_user.role not in ['admin', 'practitioner'] and \
            visit.created_by != current_user.id:
        return jsonify({'message': 'Access denied'}), 403

    data = request.get_json()

    updateable_fields = [
        'program_id', 'visit_date', 'purpose', 'status',
        'diagnosis', 'treatment', 'notes'
    ]

    for field in updateable_fields:
        if field in data:
            if field == 'visit_date':
                setattr(visit, field, datetime.strptime(data[field], '%Y-%m-%d %H:%M:%S'))
            else:
                setattr(visit, field, data[field])

    visit.updated_at = datetime.utcnow()
    db.session.commit()

    return jsonify({
        'message': 'Visit updated successfully',
        'visit': visit_schema.dump(visit)
    })


@visits_bp.route('/<int:visit_id>', methods=['DELETE'])
@token_required
@practitioner_required
def delete_visit(current_user, visit_id):
    """
    Delete a visit
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: visit_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Visit deleted
      403:
        description: Forbidden
      404:
        description: Visit not found
    """
    visit = Visit.query.get_or_404(visit_id)

    # Only allow deletion by admin, practitioner who created it, or practitioner assigned to client
    if current_user.role != 'admin' and \
            visit.created_by != current_user.id and \
            current_user.id not in [p.id for p in visit.client.practitioners]:
        return jsonify({'message': 'Access denied'}), 403

    db.session.delete(visit)
    db.session.commit()

    return jsonify({'message': 'Visit deleted successfully'})


@visits_bp.route('/upcoming', methods=['GET'])
@token_required
def get_upcoming_visits(current_user):
    """
    Get upcoming visits
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: days_ahead
        in: query
        type: integer
        required: false
        default: 7
      - name: client_id
        in: query
        type: integer
        required: false
    responses:
      200:
        description: List of upcoming visits
        schema:
          type: array
          items:
            $ref: '#/definitions/Visit'
    """
    days_ahead = request.args.get('days_ahead', 7, type=int)
    now = datetime.utcnow()
    end_date = now + timedelta(days=days_ahead)

    query = Visit.query.filter(
        and_(
            Visit.visit_date >= now,
            Visit.visit_date <= end_date,
            Visit.status == 'scheduled'
        )
    )

    # Filter by client if specified
    if 'client_id' in request.args:
        query = query.filter(Visit.client_id == request.args['client_id'])

    # For non-admins, only show their own visits or their client's visits
    if current_user.role not in ['admin', 'practitioner']:
        query = query.filter(
            or_(
                Visit.client_id.in_(
                    [c.id for c in current_user.clients]
                ),
                Visit.created_by == current_user.id
            )
        )

    visits = query.order_by(Visit.visit_date.asc()).all()

    return jsonify(visits_schema.dump(visits))


@visits_bp.route('/<int:visit_id>/complete', methods=['POST'])
@token_required
@practitioner_required
def complete_visit(current_user, visit_id):
    """
    Mark visit as completed
    ---
    tags:
      - Visits
    security:
      - BearerAuth: []
    parameters:
      - name: visit_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            diagnosis:
              type: string
            treatment:
              type: string
            notes:
              type: string
    responses:
      200:
        description: Visit completed
        schema:
          $ref: '#/definitions/Visit'
      400:
        description: Invalid status transition
      403:
        description: Forbidden
      404:
        description: Visit not found
    """
    visit = Visit.query.get_or_404(visit_id)

    # Authorization check
    if current_user.role != 'admin' and \
            visit.created_by != current_user.id and \
            current_user.id not in [p.id for p in visit.client.practitioners]:
        return jsonify({'message': 'Access denied'}), 403

    if visit.status != 'scheduled':
        return jsonify({'message': 'Only scheduled visits can be completed'}), 400

    data = request.get_json()

    visit.status = 'completed'
    visit.diagnosis = data.get('diagnosis', '')
    visit.treatment = data.get('treatment', '')
    visit.notes = data.get('notes', '')
    visit.updated_at = datetime.utcnow()

    db.session.commit()

    return jsonify({
        'message': 'Visit marked as completed',
        'visit': visit_schema.dump(visit)
    })