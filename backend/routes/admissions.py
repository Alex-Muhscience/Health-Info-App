from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import Admission, Bed, Client, Staff, Department, Billing, BillingItem
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

admissions_bp = Blueprint('admissions', __name__)


# Admissions Routes
@admissions_bp.route('/admissions', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_admissions():
    """Get admissions with filtering options."""
    try:
        client_id = request.args.get('client_id')
        status = request.args.get('status')
        admission_type = request.args.get('admission_type')
        date_from = request.args.get('date_from')
        date_to = request.args.get('date_to')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Admission.query
        
        if client_id:
            query = query.filter(Admission.client_id == client_id)
        if status:
            query = query.filter(Admission.status == status)
        if admission_type:
            query = query.filter(Admission.admission_type == admission_type)
        if date_from:
            query = query.filter(Admission.admission_date >= datetime.strptime(date_from, '%Y-%m-%d'))
        if date_to:
            query = query.filter(Admission.admission_date <= datetime.strptime(date_to, '%Y-%m-%d'))
        
        admissions = query.order_by(Admission.admission_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for admission in admissions.items:
            admission_data = {
                'id': admission.id,
                'client_id': admission.client_id,
                'client_name': f"{admission.client.first_name} {admission.client.last_name}" if admission.client else None,
                'bed_id': admission.bed_id,
                'bed_number': admission.bed.bed_number if admission.bed else None,
                'attending_doctor_id': admission.attending_doctor_id,
                'attending_doctor_name': f"{admission.attending_doctor.first_name} {admission.attending_doctor.last_name}" if admission.attending_doctor else None,
                'admission_date': admission.admission_date.isoformat(),
                'discharge_date': admission.discharge_date.isoformat() if admission.discharge_date else None,
                'admission_type': admission.admission_type,
                'status': admission.status,
                'reason': admission.reason,
                'diagnosis': admission.diagnosis,
                'total_cost': float(admission.total_cost) if admission.total_cost else None,
                'created_at': admission.created_at.isoformat()
            }
            result.append(admission_data)
        
        return jsonify({
            'admissions': result,
            'pagination': {
                'page': admissions.page,
                'pages': admissions.pages,
                'per_page': admissions.per_page,
                'total': admissions.total,
                'has_next': admissions.has_next,
                'has_prev': admissions.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching admissions: {str(e)}")
        return jsonify({'error': 'Failed to fetch admissions'}), 500


@admissions_bp.route('/admissions', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def create_admission():
    """Create a new admission."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        required_fields = ['client_id', 'attending_doctor_id', 'admission_type', 'reason']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Verify client and doctor exist
        client = Client.query.get_or_404(data['client_id'])
        doctor = Staff.query.get_or_404(data['attending_doctor_id'])
        
        # Check if client has active admission
        active_admission = Admission.query.filter_by(
            client_id=data['client_id'],
            status='active'
        ).first()
        
        if active_admission:
            return jsonify({'error': 'Client already has an active admission'}), 400
        
        # If bed is specified, verify it's available
        bed = None
        if data.get('bed_id'):
            bed = Bed.query.get_or_404(data['bed_id'])
            if bed.status != 'available':
                return jsonify({'error': 'Selected bed is not available'}), 400
        
        # Create admission
        admission = Admission(
            client_id=data['client_id'],
            bed_id=data.get('bed_id'),
            attending_doctor_id=data['attending_doctor_id'],
            admission_type=data['admission_type'],
            reason=data['reason'],
            diagnosis=data.get('diagnosis'),
            created_by=current_user
        )
        
        db.session.add(admission)
        
        # Update bed status if assigned
        if bed:
            bed.status = 'occupied'
        
        db.session.commit()
        
        logger.info(f"Created admission for client {client.first_name} {client.last_name}")
        
        return jsonify({
            'message': 'Admission created successfully',
            'admission': {
                'id': admission.id,
                'client_id': admission.client_id,
                'status': admission.status,
                'admission_date': admission.admission_date.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating admission: {str(e)}")
        return jsonify({'error': 'Failed to create admission'}), 500


@admissions_bp.route('/admissions/<admission_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_admission(admission_id):
    """Get a specific admission by ID."""
    try:
        admission = Admission.query.get_or_404(admission_id)
        
        return jsonify({
            'id': admission.id,
            'client_id': admission.client_id,
            'client_name': f"{admission.client.first_name} {admission.client.last_name}" if admission.client else None,
            'bed_id': admission.bed_id,
            'bed_number': admission.bed.bed_number if admission.bed else None,
            'bed_type': admission.bed.bed_type if admission.bed else None,
            'room_number': admission.bed.room_number if admission.bed else None,
            'attending_doctor_id': admission.attending_doctor_id,
            'attending_doctor_name': f"{admission.attending_doctor.first_name} {admission.attending_doctor.last_name}" if admission.attending_doctor else None,
            'admission_date': admission.admission_date.isoformat(),
            'discharge_date': admission.discharge_date.isoformat() if admission.discharge_date else None,
            'admission_type': admission.admission_type,
            'status': admission.status,
            'reason': admission.reason,
            'diagnosis': admission.diagnosis,
            'discharge_summary': admission.discharge_summary,
            'total_cost': float(admission.total_cost) if admission.total_cost else None,
            'created_by': admission.created_by,
            'created_at': admission.created_at.isoformat(),
            'updated_at': admission.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching admission {admission_id}: {str(e)}")
        return jsonify({'error': 'Admission not found'}), 404


@admissions_bp.route('/admissions/<admission_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def update_admission(admission_id):
    """Update an admission."""
    try:
        admission = Admission.query.get_or_404(admission_id)
        data = request.get_json()
        
        # Update fields
        if 'bed_id' in data:
            # If changing bed, update bed statuses
            if admission.bed_id != data['bed_id']:
                # Make old bed available
                if admission.bed:
                    admission.bed.status = 'available'
                
                # Check new bed availability
                if data['bed_id']:
                    new_bed = Bed.query.get_or_404(data['bed_id'])
                    if new_bed.status != 'available':
                        return jsonify({'error': 'Selected bed is not available'}), 400
                    new_bed.status = 'occupied'
                
                admission.bed_id = data['bed_id']
        
        if 'attending_doctor_id' in data:
            admission.attending_doctor_id = data['attending_doctor_id']
        if 'admission_type' in data:
            admission.admission_type = data['admission_type']
        if 'reason' in data:
            admission.reason = data['reason']
        if 'diagnosis' in data:
            admission.diagnosis = data['diagnosis']
        if 'discharge_summary' in data:
            admission.discharge_summary = data['discharge_summary']
        if 'total_cost' in data:
            admission.total_cost = data['total_cost']
        
        # Handle discharge
        if 'status' in data and data['status'] == 'discharged' and admission.status == 'active':
            admission.status = 'discharged'
            admission.discharge_date = datetime.utcnow()
            
            # Make bed available
            if admission.bed:
                admission.bed.status = 'available'
        elif 'status' in data:
            admission.status = data['status']
        
        db.session.commit()
        
        logger.info(f"Updated admission {admission_id}")
        
        return jsonify({
            'message': 'Admission updated successfully',
            'admission': {
                'id': admission.id,
                'status': admission.status,
                'discharge_date': admission.discharge_date.isoformat() if admission.discharge_date else None,
                'updated_at': admission.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating admission {admission_id}: {str(e)}")
        return jsonify({'error': 'Failed to update admission'}), 500


@admissions_bp.route('/admissions/<admission_id>/discharge', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor'])
def discharge_admission(admission_id):
    """Discharge a patient."""
    try:
        admission = Admission.query.get_or_404(admission_id)
        data = request.get_json()
        
        if admission.status != 'active':
            return jsonify({'error': 'Only active admissions can be discharged'}), 400
        
        # Update admission
        admission.status = 'discharged'
        admission.discharge_date = datetime.utcnow()
        admission.discharge_summary = data.get('discharge_summary', '')
        
        # Make bed available
        if admission.bed:
            admission.bed.status = 'available'
        
        db.session.commit()
        
        logger.info(f"Discharged admission {admission_id}")
        
        return jsonify({
            'message': 'Patient discharged successfully',
            'admission': {
                'id': admission.id,
                'status': admission.status,
                'discharge_date': admission.discharge_date.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error discharging admission {admission_id}: {str(e)}")
        return jsonify({'error': 'Failed to discharge patient'}), 500


# Bed Management Routes
@admissions_bp.route('/beds', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_beds():
    """Get beds with filtering options."""
    try:
        department_id = request.args.get('department_id')
        bed_type = request.args.get('bed_type')
        status = request.args.get('status')
        is_active = request.args.get('is_active', 'true').lower() == 'true'
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Bed.query.filter_by(is_active=is_active)
        
        if department_id:
            query = query.filter(Bed.department_id == department_id)
        if bed_type:
            query = query.filter(Bed.bed_type == bed_type)
        if status:
            query = query.filter(Bed.status == status)
        
        beds = query.order_by(Bed.bed_number).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        result = []
        for bed in beds.items:
            bed_data = {
                'id': bed.id,
                'bed_number': bed.bed_number,
                'department_id': bed.department_id,
                'department_name': bed.department.name if bed.department else None,
                'room_number': bed.room_number,
                'bed_type': bed.bed_type,
                'status': bed.status,
                'daily_rate': float(bed.daily_rate) if bed.daily_rate else None,
                'is_active': bed.is_active,
                'created_at': bed.created_at.isoformat()
            }
            result.append(bed_data)
        
        return jsonify({
            'beds': result,
            'pagination': {
                'page': beds.page,
                'pages': beds.pages,
                'per_page': beds.per_page,
                'total': beds.total,
                'has_next': beds.has_next,
                'has_prev': beds.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching beds: {str(e)}")
        return jsonify({'error': 'Failed to fetch beds'}), 500


@admissions_bp.route('/beds', methods=['POST'])
@jwt_required()
@role_required(['admin'])
def create_bed():
    """Create a new bed."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['bed_number', 'department_id', 'bed_type']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Check if bed number already exists
        if Bed.query.filter_by(bed_number=data['bed_number']).first():
            return jsonify({'error': 'Bed number already exists'}), 400
        
        # Verify department exists
        department = Department.query.get_or_404(data['department_id'])
        
        # Create bed
        bed = Bed(
            bed_number=data['bed_number'],
            department_id=data['department_id'],
            room_number=data.get('room_number'),
            bed_type=data['bed_type'],
            daily_rate=data.get('daily_rate')
        )
        
        db.session.add(bed)
        db.session.commit()
        
        logger.info(f"Created bed: {bed.bed_number}")
        
        return jsonify({
            'message': 'Bed created successfully',
            'bed': {
                'id': bed.id,
                'bed_number': bed.bed_number,
                'bed_type': bed.bed_type,
                'status': bed.status
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating bed: {str(e)}")
        return jsonify({'error': 'Failed to create bed'}), 500


@admissions_bp.route('/beds/<bed_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin'])
def update_bed(bed_id):
    """Update a bed."""
    try:
        bed = Bed.query.get_or_404(bed_id)
        data = request.get_json()
        
        # Update fields
        if 'room_number' in data:
            bed.room_number = data['room_number']
        if 'bed_type' in data:
            bed.bed_type = data['bed_type']
        if 'status' in data:
            bed.status = data['status']
        if 'daily_rate' in data:
            bed.daily_rate = data['daily_rate']
        if 'is_active' in data:
            bed.is_active = data['is_active']
        
        db.session.commit()
        
        logger.info(f"Updated bed: {bed.bed_number}")
        
        return jsonify({
            'message': 'Bed updated successfully',
            'bed': {
                'id': bed.id,
                'bed_number': bed.bed_number,
                'status': bed.status,
                'updated_at': bed.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating bed {bed_id}: {str(e)}")
        return jsonify({'error': 'Failed to update bed'}), 500


@admissions_bp.route('/clients/<client_id>/admissions', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_client_admissions(client_id):
    """Get all admissions for a specific client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        admissions = Admission.query.filter_by(client_id=client_id)\
            .order_by(Admission.admission_date.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for admission in admissions.items:
            admission_data = {
                'id': admission.id,
                'admission_date': admission.admission_date.isoformat(),
                'discharge_date': admission.discharge_date.isoformat() if admission.discharge_date else None,
                'admission_type': admission.admission_type,
                'status': admission.status,
                'reason': admission.reason,
                'diagnosis': admission.diagnosis,
                'bed_number': admission.bed.bed_number if admission.bed else None,
                'attending_doctor_name': f"{admission.attending_doctor.first_name} {admission.attending_doctor.last_name}" if admission.attending_doctor else None
            }
            result.append(admission_data)
        
        return jsonify({
            'admissions': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            },
            'pagination': {
                'page': admissions.page,
                'pages': admissions.pages,
                'per_page': admissions.per_page,
                'total': admissions.total,
                'has_next': admissions.has_next,
                'has_prev': admissions.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching admissions for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch admissions'}), 500


@admissions_bp.route('/admissions/statistics', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor'])
def get_admission_statistics():
    """Get admission statistics."""
    try:
        # Current admissions by status
        status_counts = {}
        for status in Admission.STATUSES:
            count = Admission.query.filter_by(status=status).count()
            status_counts[status] = count
        
        # Bed occupancy
        total_beds = Bed.query.filter_by(is_active=True).count()
        occupied_beds = Bed.query.filter_by(status='occupied', is_active=True).count()
        available_beds = Bed.query.filter_by(status='available', is_active=True).count()
        
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        
        # Today's admissions
        today = datetime.utcnow().date()
        today_admissions = Admission.query.filter(
            db.func.date(Admission.admission_date) == today
        ).count()
        
        # Today's discharges
        today_discharges = Admission.query.filter(
            db.func.date(Admission.discharge_date) == today
        ).count()
        
        return jsonify({
            'status_counts': status_counts,
            'bed_occupancy': {
                'total_beds': total_beds,
                'occupied_beds': occupied_beds,
                'available_beds': available_beds,
                'occupancy_rate': round(occupancy_rate, 2)
            },
            'today': {
                'admissions': today_admissions,
                'discharges': today_discharges
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching admission statistics: {str(e)}")
        return jsonify({'error': 'Failed to fetch admission statistics'}), 500


@admissions_bp.route('/beds/types', methods=['GET'])
@jwt_required()
def get_bed_types():
    """Get all bed types."""
    return jsonify({
        'bed_types': [
            {'value': bed_type, 'label': bed_type.replace('_', ' ').title()}
            for bed_type in Bed.TYPES
        ]
    }), 200


@admissions_bp.route('/beds/statuses', methods=['GET'])
@jwt_required()
def get_bed_statuses():
    """Get all bed statuses."""
    return jsonify({
        'statuses': [
            {'value': status, 'label': status.replace('_', ' ').title()}
            for status in Bed.STATUSES
        ]
    }), 200


@admissions_bp.route('/admissions/types', methods=['GET'])
@jwt_required()
def get_admission_types():
    """Get all admission types."""
    return jsonify({
        'admission_types': [
            {'value': admission_type, 'label': admission_type.replace('_', ' ').title()}
            for admission_type in Admission.ADMISSION_TYPES
        ]
    }), 200


@admissions_bp.route('/admissions/statuses', methods=['GET'])
@jwt_required()
def get_admission_statuses():
    """Get all admission statuses."""
    return jsonify({
        'statuses': [
            {'value': status, 'label': status.replace('_', ' ').title()}
            for status in Admission.STATUSES
        ]
    }), 200
