from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.models import MedicalRecord, VitalSigns, Client, Visit, User
from backend.utils.helpers import handle_validation_error
from backend.utils.auth import role_required
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

medical_records_bp = Blueprint('medical_records', __name__)


@medical_records_bp.route('/medical-records', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_all_medical_records():
    """Get all medical records with optional filtering."""
    try:
        client_id = request.args.get('client_id')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        query = MedicalRecord.query
        
        if client_id:
            query = query.filter_by(client_id=client_id)
        
        records = query.order_by(MedicalRecord.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for record in records.items:
            record_data = {
                'id': record.id,
                'client_id': record.client_id,
                'client_name': f"{record.client.first_name} {record.client.last_name}" if record.client else None,
                'visit_id': record.visit_id,
                'chief_complaint': record.chief_complaint,
                'history_present_illness': record.history_present_illness,
                'assessment': record.assessment,
                'plan': record.plan,
                'created_by': record.created_by,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            }
            result.append(record_data)
        
        return jsonify(result), 200
    
    except Exception as e:
        logger.error(f"Error fetching medical records: {str(e)}")
        return jsonify({'error': 'Failed to fetch medical records'}), 500


@medical_records_bp.route('/clients/<client_id>/medical-records', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_client_medical_records(client_id):
    """Get all medical records for a specific client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 10)), 100)
        
        records = MedicalRecord.query.filter_by(client_id=client_id)\
            .order_by(MedicalRecord.created_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for record in records.items:
            record_data = {
                'id': record.id,
                'visit_id': record.visit_id,
                'chief_complaint': record.chief_complaint,
                'history_present_illness': record.history_present_illness,
                'past_medical_history': record.past_medical_history,
                'family_history': record.family_history,
                'social_history': record.social_history,
                'allergies': record.allergies,
                'current_medications': record.current_medications,
                'physical_examination': record.physical_examination,
                'assessment': record.assessment,
                'plan': record.plan,
                'created_by': record.created_by,
                'created_at': record.created_at.isoformat(),
                'updated_at': record.updated_at.isoformat()
            }
            result.append(record_data)
        
        return jsonify({
            'medical_records': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            },
            'pagination': {
                'page': records.page,
                'pages': records.pages,
                'per_page': records.per_page,
                'total': records.total,
                'has_next': records.has_next,
                'has_prev': records.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching medical records for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch medical records'}), 500


@medical_records_bp.route('/medical-records', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def create_medical_record():
    """Create a new medical record."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        if not data.get('client_id'):
            return jsonify({'error': 'Client ID is required'}), 400
        
        # Verify client exists
        client = Client.query.get_or_404(data['client_id'])
        
        # Create medical record
        record = MedicalRecord(
            client_id=data['client_id'],
            visit_id=data.get('visit_id'),
            chief_complaint=data.get('chief_complaint'),
            history_present_illness=data.get('history_present_illness'),
            past_medical_history=data.get('past_medical_history'),
            family_history=data.get('family_history'),
            social_history=data.get('social_history'),
            allergies=data.get('allergies'),
            current_medications=data.get('current_medications'),
            physical_examination=data.get('physical_examination'),
            assessment=data.get('assessment'),
            plan=data.get('plan'),
            created_by=current_user
        )
        
        db.session.add(record)
        db.session.commit()
        
        logger.info(f"Created medical record for client {client.first_name} {client.last_name}")
        
        return jsonify({
            'message': 'Medical record created successfully',
            'record': {
                'id': record.id,
                'client_id': record.client_id,
                'created_at': record.created_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating medical record: {str(e)}")
        return jsonify({'error': 'Failed to create medical record'}), 500


@medical_records_bp.route('/medical-records/<record_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_medical_record(record_id):
    """Get a specific medical record by ID."""
    try:
        record = MedicalRecord.query.get_or_404(record_id)
        
        return jsonify({
            'id': record.id,
            'client_id': record.client_id,
            'client_name': f"{record.client.first_name} {record.client.last_name}" if record.client else None,
            'visit_id': record.visit_id,
            'chief_complaint': record.chief_complaint,
            'history_present_illness': record.history_present_illness,
            'past_medical_history': record.past_medical_history,
            'family_history': record.family_history,
            'social_history': record.social_history,
            'allergies': record.allergies,
            'current_medications': record.current_medications,
            'physical_examination': record.physical_examination,
            'assessment': record.assessment,
            'plan': record.plan,
            'created_by': record.created_by,
            'created_at': record.created_at.isoformat(),
            'updated_at': record.updated_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching medical record {record_id}: {str(e)}")
        return jsonify({'error': 'Medical record not found'}), 404


@medical_records_bp.route('/medical-records/<record_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def update_medical_record(record_id):
    """Update a medical record."""
    try:
        record = MedicalRecord.query.get_or_404(record_id)
        data = request.get_json()
        
        # Update fields
        if 'chief_complaint' in data:
            record.chief_complaint = data['chief_complaint']
        if 'history_present_illness' in data:
            record.history_present_illness = data['history_present_illness']
        if 'past_medical_history' in data:
            record.past_medical_history = data['past_medical_history']
        if 'family_history' in data:
            record.family_history = data['family_history']
        if 'social_history' in data:
            record.social_history = data['social_history']
        if 'allergies' in data:
            record.allergies = data['allergies']
        if 'current_medications' in data:
            record.current_medications = data['current_medications']
        if 'physical_examination' in data:
            record.physical_examination = data['physical_examination']
        if 'assessment' in data:
            record.assessment = data['assessment']
        if 'plan' in data:
            record.plan = data['plan']
        
        db.session.commit()
        
        logger.info(f"Updated medical record {record_id}")
        
        return jsonify({
            'message': 'Medical record updated successfully',
            'record': {
                'id': record.id,
                'client_id': record.client_id,
                'updated_at': record.updated_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating medical record {record_id}: {str(e)}")
        return jsonify({'error': 'Failed to update medical record'}), 500


# Vital Signs Routes
@medical_records_bp.route('/clients/<client_id>/vital-signs', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_client_vital_signs(client_id):
    """Get all vital signs for a specific client."""
    try:
        # Verify client exists
        client = Client.query.get_or_404(client_id)
        
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        vitals = VitalSigns.query.filter_by(client_id=client_id)\
            .order_by(VitalSigns.recorded_at.desc())\
            .paginate(page=page, per_page=per_page, error_out=False)
        
        result = []
        for vital in vitals.items:
            vital_data = {
                'id': vital.id,
                'visit_id': vital.visit_id,
                'recorded_at': vital.recorded_at.isoformat(),
                'temperature': vital.temperature,
                'blood_pressure_systolic': vital.blood_pressure_systolic,
                'blood_pressure_diastolic': vital.blood_pressure_diastolic,
                'heart_rate': vital.heart_rate,
                'respiratory_rate': vital.respiratory_rate,
                'oxygen_saturation': vital.oxygen_saturation,
                'height': vital.height,
                'weight': vital.weight,
                'bmi': vital.bmi,
                'notes': vital.notes,
                'recorded_by': vital.recorded_by,
                'created_at': vital.created_at.isoformat()
            }
            result.append(vital_data)
        
        return jsonify({
            'vital_signs': result,
            'client': {
                'id': client.id,
                'name': f"{client.first_name} {client.last_name}"
            },
            'pagination': {
                'page': vitals.page,
                'pages': vitals.pages,
                'per_page': vitals.per_page,
                'total': vitals.total,
                'has_next': vitals.has_next,
                'has_prev': vitals.has_prev
            }
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching vital signs for client {client_id}: {str(e)}")
        return jsonify({'error': 'Failed to fetch vital signs'}), 500


@medical_records_bp.route('/vital-signs', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def create_vital_signs():
    """Create new vital signs record."""
    try:
        data = request.get_json()
        current_user = get_jwt_identity()
        
        # Validate required fields
        if not data.get('client_id'):
            return jsonify({'error': 'Client ID is required'}), 400
        
        # Verify client exists
        client = Client.query.get_or_404(data['client_id'])
        
        # Calculate BMI if height and weight are provided
        bmi = None
        if data.get('height') and data.get('weight'):
            height_m = float(data['height']) / 100  # Convert cm to m
            weight_kg = float(data['weight'])
            bmi = round(weight_kg / (height_m ** 2), 2)
        
        # Create vital signs record
        vital = VitalSigns(
            client_id=data['client_id'],
            visit_id=data.get('visit_id'),
            recorded_at=datetime.strptime(data['recorded_at'], '%Y-%m-%dT%H:%M:%S') if data.get('recorded_at') else datetime.utcnow(),
            temperature=data.get('temperature'),
            blood_pressure_systolic=data.get('blood_pressure_systolic'),
            blood_pressure_diastolic=data.get('blood_pressure_diastolic'),
            heart_rate=data.get('heart_rate'),
            respiratory_rate=data.get('respiratory_rate'),
            oxygen_saturation=data.get('oxygen_saturation'),
            height=data.get('height'),
            weight=data.get('weight'),
            bmi=bmi,
            notes=data.get('notes'),
            recorded_by=current_user
        )
        
        db.session.add(vital)
        db.session.commit()
        
        logger.info(f"Created vital signs record for client {client.first_name} {client.last_name}")
        
        return jsonify({
            'message': 'Vital signs recorded successfully',
            'vital_signs': {
                'id': vital.id,
                'client_id': vital.client_id,
                'bmi': vital.bmi,
                'recorded_at': vital.recorded_at.isoformat()
            }
        }), 201
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating vital signs: {str(e)}")
        return jsonify({'error': 'Failed to record vital signs'}), 500


@medical_records_bp.route('/vital-signs/<vital_id>', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_vital_signs(vital_id):
    """Get specific vital signs record by ID."""
    try:
        vital = VitalSigns.query.get_or_404(vital_id)
        
        return jsonify({
            'id': vital.id,
            'client_id': vital.client_id,
            'client_name': f"{vital.client.first_name} {vital.client.last_name}" if vital.client else None,
            'visit_id': vital.visit_id,
            'recorded_at': vital.recorded_at.isoformat(),
            'temperature': vital.temperature,
            'blood_pressure_systolic': vital.blood_pressure_systolic,
            'blood_pressure_diastolic': vital.blood_pressure_diastolic,
            'heart_rate': vital.heart_rate,
            'respiratory_rate': vital.respiratory_rate,
            'oxygen_saturation': vital.oxygen_saturation,
            'height': vital.height,
            'weight': vital.weight,
            'bmi': vital.bmi,
            'notes': vital.notes,
            'recorded_by': vital.recorded_by,
            'created_at': vital.created_at.isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error fetching vital signs {vital_id}: {str(e)}")
        return jsonify({'error': 'Vital signs record not found'}), 404


@medical_records_bp.route('/vital-signs/<vital_id>', methods=['PUT'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def update_vital_signs(vital_id):
    """Update vital signs record."""
    try:
        vital = VitalSigns.query.get_or_404(vital_id)
        data = request.get_json()
        
        # Update fields
        if 'temperature' in data:
            vital.temperature = data['temperature']
        if 'blood_pressure_systolic' in data:
            vital.blood_pressure_systolic = data['blood_pressure_systolic']
        if 'blood_pressure_diastolic' in data:
            vital.blood_pressure_diastolic = data['blood_pressure_diastolic']
        if 'heart_rate' in data:
            vital.heart_rate = data['heart_rate']
        if 'respiratory_rate' in data:
            vital.respiratory_rate = data['respiratory_rate']
        if 'oxygen_saturation' in data:
            vital.oxygen_saturation = data['oxygen_saturation']
        if 'height' in data:
            vital.height = data['height']
        if 'weight' in data:
            vital.weight = data['weight']
        if 'notes' in data:
            vital.notes = data['notes']
        
        # Recalculate BMI if height or weight changed
        if vital.height and vital.weight:
            height_m = float(vital.height) / 100  # Convert cm to m
            weight_kg = float(vital.weight)
            vital.bmi = round(weight_kg / (height_m ** 2), 2)
        
        db.session.commit()
        
        logger.info(f"Updated vital signs record {vital_id}")
        
        return jsonify({
            'message': 'Vital signs updated successfully',
            'vital_signs': {
                'id': vital.id,
                'client_id': vital.client_id,
                'bmi': vital.bmi,
                'recorded_at': vital.recorded_at.isoformat()
            }
        }), 200
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating vital signs {vital_id}: {str(e)}")
        return jsonify({'error': 'Failed to update vital signs'}), 500
