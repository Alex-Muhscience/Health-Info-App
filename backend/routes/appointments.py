from flask import Blueprint, request, jsonify
from backend import db
from backend.models import Appointment, Client
from backend.schemas import appointment_schema, appointments_schema
from backend.utils.auth import token_required, roles_required
from backend.utils.helpers import parse_datetime, validate_phone
from datetime import datetime, timedelta

appointments_bp = Blueprint('appointments', __name__)


@appointments_bp.route('/', methods=['GET'])
@roles_required('admin', 'doctor', 'nurse', 'receptionist')
def get_appointments(current_user):
    """Get appointments with filters"""
    client_id = request.args.get('client_id')
    status = request.args.get('status')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = Appointment.query.join(Client).filter(Client.is_active == True)

    if client_id:
        query = query.filter(Appointment.client_id == client_id)

    if status:
        query = query.filter(Appointment.status == status.lower())

    if start_date:
        try:
            start_date = parse_datetime(start_date)
            query = query.filter(Appointment.date >= start_date)
        except:
            return jsonify({'error': 'Invalid start date format'}), 400

    if end_date:
        try:
            end_date = parse_datetime(end_date)
            query = query.filter(Appointment.date <= end_date)
        except:
            return jsonify({'error': 'Invalid end date format'}), 400

    appointments = query.order_by(Appointment.date.asc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'data': appointments_schema.dump(appointments.items),
        'total': appointments.total,
        'pages': appointments.pages,
        'current_page': appointments.page
    }), 200


@appointments_bp.route('/', methods=['POST'])
@roles_required('admin', 'doctor', 'nurse', 'receptionist')
def create_appointment(current_user):
    """Create a new appointment with conflict checking"""
    data = request.get_json()

    required_fields = ['client_id', 'date', 'reason']
    if not all(field in data for field in required_fields):
        return jsonify({'error': 'Missing required fields'}), 400

    client = Client.query.filter_by(id=data['client_id'], is_active=True).first_or_404()

    try:
        appointment_date = parse_datetime(data['date'])
        duration = timedelta(minutes=data.get('duration_minutes', 30))

        # Check for scheduling conflicts
        conflicting_appointments = Appointment.query.filter(
            Appointment.date.between(
                appointment_date - timedelta(minutes=29),
                appointment_date + duration + timedelta(minutes=29)
            ),
            Appointment.status != 'cancelled'
        ).count()

        if conflicting_appointments > 0:
            return jsonify({
                'error': 'Time slot conflicts with existing appointment',
                'available_slots': get_available_slots(appointment_date.date())
            }), 409

        new_appointment = Appointment(
            client_id=data['client_id'],
            date=appointment_date,
            duration_minutes=data.get('duration_minutes', 30),
            reason=data['reason'].strip(),
            status='scheduled',
            notes=data.get('notes', '').strip()
        )

        db.session.add(new_appointment)
        db.session.commit()

        return jsonify({
            'message': 'Appointment scheduled successfully',
            'appointment': appointment_schema.dump(new_appointment)
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400


def get_available_slots(date):
    """Helper function to find available time slots"""
    # Implementation would query existing appointments and calculate available slots
    return []


@appointments_bp.route('/<appointment_id>', methods=['GET'])
@roles_required('admin', 'doctor', 'nurse', 'receptionist')
def get_appointment(current_user, appointment_id):
    """Get appointment details"""
    appointment = Appointment.query.get_or_404(appointment_id)
    return jsonify(appointment_schema.dump(appointment)), 200


@appointments_bp.route('/<appointment_id>', methods=['PUT'])
@roles_required('admin', 'doctor', 'nurse', 'receptionist')
def update_appointment(current_user, appointment_id):
    """Update appointment information"""
    appointment = Appointment.query.get_or_404(appointment_id)
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data provided'}), 400

    try:
        if 'date' in data:
            new_date = parse_datetime(data['date'])
            if new_date < datetime.utcnow():
                return jsonify({'error': 'Cannot schedule appointment in the past'}), 400
            appointment.date = new_date

        if 'duration_minutes' in data:
            appointment.duration_minutes = data['duration_minutes']

        if 'reason' in data:
            appointment.reason = data['reason'].strip()

        if 'status' in data:
            appointment.status = data['status'].lower()

        if 'notes' in data:
            appointment.notes = data['notes'].strip()

        db.session.commit()

        return jsonify({
            'message': 'Appointment updated successfully',
            'appointment': appointment_schema.dump(appointment)
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 400