"""
Telemedicine API Routes
Virtual consultation and video call management endpoints
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from backend.database import db
from backend.telemedicine_system import telemedicine_manager, virtual_waiting_room, ConsultationType, ConsultationStatus
from backend.utils.auth import role_required
from backend.security_system import audit_logger, SecurityEventType, RiskLevel
from datetime import datetime, timedelta
import logging

# Configure telemedicine logger
telemedicine_logger = logging.getLogger('telemedicine')

telemedicine_bp = Blueprint('telemedicine', __name__)

@telemedicine_bp.route('/consultations/schedule', methods=['POST'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse', 'receptionist'])
def schedule_consultation():
    """Schedule a virtual consultation"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_id', 'provider_id', 'scheduled_time']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Parse consultation parameters
        patient_id = data['patient_id']
        provider_id = data['provider_id']
        scheduled_time = datetime.fromisoformat(data['scheduled_time'])
        consultation_type = ConsultationType(data.get('consultation_type', 'video_call'))
        duration_minutes = data.get('duration_minutes', 30)
        notes = data.get('notes')
        
        # Schedule consultation
        consultation = telemedicine_manager.schedule_virtual_consultation(
            patient_id=patient_id,
            provider_id=provider_id,
            scheduled_time=scheduled_time,
            consultation_type=consultation_type,
            duration_minutes=duration_minutes,
            notes=notes
        )
        
        if not consultation:
            return jsonify({
                'status': 'error',
                'message': 'Failed to schedule consultation'
            }), 500
        
        # Log consultation scheduling
        audit_logger.log_security_event(
            SecurityEventType.DATA_MODIFICATION,
            user_id=current_user,
            resource_accessed=f"telemedicine_consultation",
            details={'consultation_id': consultation.id, 'patient_id': patient_id}
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'consultation_id': consultation.id,
                'appointment_id': consultation.appointment_id,
                'room_id': consultation.room_id,
                'scheduled_time': consultation.scheduled_time.isoformat(),
                'consultation_type': consultation.consultation_type.value,
                'status': consultation.status.value,
                'access_instructions': {
                    'join_url': f"/telemedicine/join/{consultation.id}",
                    'join_time': "Available 15 minutes before scheduled time"
                }
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid data format: {str(e)}'
        }), 400
    except Exception as e:
        telemedicine_logger.error(f"Error scheduling consultation: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to schedule consultation'
        }), 500

@telemedicine_bp.route('/consultations/<consultation_id>/join', methods=['POST'])
@jwt_required()
def join_consultation(consultation_id):
    """Join a virtual consultation"""
    try:
        current_user = get_jwt_identity()
        
        # Start consultation session
        success, message, session_data = telemedicine_manager.start_consultation(
            consultation_id, current_user
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # Add patient to virtual waiting room if needed
        if session_data and len(session_data.get('participants', [])) == 1:
            virtual_waiting_room.add_patient_to_waiting_room(
                consultation_id, current_user
            )
        
        # Log consultation access
        audit_logger.log_security_event(
            SecurityEventType.DATA_ACCESS,
            user_id=current_user,
            resource_accessed=f"telemedicine_session_{consultation_id}",
            risk_level=RiskLevel.MEDIUM
        )
        
        return jsonify({
            'status': 'success',
            'message': message,
            'data': session_data
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error joining consultation: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to join consultation'
        }), 500

@telemedicine_bp.route('/consultations/<consultation_id>/end', methods=['POST'])
@jwt_required()
def end_consultation(consultation_id):
    """End a virtual consultation"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json() or {}
        completion_notes = data.get('completion_notes')
        
        # End consultation
        success, message = telemedicine_manager.end_consultation(
            consultation_id, current_user, completion_notes
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': message
            }), 400
        
        # Remove from waiting room
        virtual_waiting_room.remove_patient_from_waiting_room(current_user)
        
        return jsonify({
            'status': 'success',
            'message': message
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error ending consultation: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to end consultation'
        }), 500

@telemedicine_bp.route('/consultations/<consultation_id>/chat', methods=['POST'])
@jwt_required()
def send_chat_message(consultation_id):
    """Send chat message during consultation"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        message = data.get('message')
        message_type = data.get('message_type', 'text')
        
        if not message:
            return jsonify({
                'status': 'error',
                'message': 'Message content is required'
            }), 400
        
        # Send message
        success = telemedicine_manager.send_chat_message(
            consultation_id, current_user, message, message_type
        )
        
        if not success:
            return jsonify({
                'status': 'error',
                'message': 'Failed to send message'
            }), 400
        
        return jsonify({
            'status': 'success',
            'message': 'Message sent successfully'
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error sending chat message: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to send message'
        }), 500

@telemedicine_bp.route('/consultations/<consultation_id>/connection-quality', methods=['PUT'])
@jwt_required()
def update_connection_quality(consultation_id):
    """Update connection quality metrics"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        from backend.telemedicine_system import ConnectionQuality
        
        quality = ConnectionQuality(data.get('quality', 'good'))
        technical_issues = data.get('technical_issues', [])
        
        telemedicine_manager.update_connection_quality(
            consultation_id, current_user, quality, technical_issues
        )
        
        return jsonify({
            'status': 'success',
            'message': 'Connection quality updated'
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error updating connection quality: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to update connection quality'
        }), 500

@telemedicine_bp.route('/consultations/<consultation_id>/analytics', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor'])
def get_consultation_analytics(consultation_id):
    """Get detailed consultation analytics"""
    try:
        current_user = get_jwt_identity()
        
        analytics = telemedicine_manager.get_consultation_analytics(consultation_id)
        
        if not analytics:
            return jsonify({
                'status': 'error',
                'message': 'Consultation not found'
            }), 404
        
        return jsonify({
            'status': 'success',
            'data': analytics
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error getting consultation analytics: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve analytics'
        }), 500

@telemedicine_bp.route('/vital-signs/remote', methods=['POST'])
@jwt_required()
def record_remote_vital_signs():
    """Record vital signs from remote monitoring devices"""
    try:
        current_user = get_jwt_identity()
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['patient_id', 'device_type', 'measurement_type', 'value', 'unit']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    'status': 'error',
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Record vital signs
        vital_signs = telemedicine_manager.record_remote_vital_signs(
            patient_id=data['patient_id'],
            device_type=data['device_type'],
            measurement_type=data['measurement_type'],
            value=float(data['value']),
            unit=data['unit'],
            consultation_id=data.get('consultation_id'),
            device_id=data.get('device_id')
        )
        
        return jsonify({
            'status': 'success',
            'data': {
                'vital_signs_id': vital_signs.id,
                'timestamp': vital_signs.timestamp.isoformat(),
                'accuracy_score': vital_signs.accuracy_score,
                'verified': vital_signs.verified_by_provider
            }
        }), 201
        
    except ValueError as e:
        return jsonify({
            'status': 'error',
            'message': f'Invalid value format: {str(e)}'
        }), 400
    except Exception as e:
        telemedicine_logger.error(f"Error recording vital signs: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to record vital signs'
        }), 500

@telemedicine_bp.route('/waiting-room/status', methods=['GET'])
@jwt_required()
def get_waiting_room_status():
    """Get virtual waiting room status"""
    try:
        current_user = get_jwt_identity()
        
        # Update wait times
        virtual_waiting_room.update_wait_times()
        
        # Get current status
        waiting_patients = virtual_waiting_room.waiting_patients
        
        # Filter based on user role (patients see only their info, providers see all)
        # This would require role checking logic
        
        return jsonify({
            'status': 'success',
            'data': {
                'total_waiting': len(waiting_patients),
                'patients': [
                    {
                        'patient_id': patient_id,
                        'position': info['position'],
                        'estimated_wait_time': info['estimated_wait_time'],
                        'status': info['status']
                    } for patient_id, info in waiting_patients.items()
                ]
            }
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error getting waiting room status: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to get waiting room status'
        }), 500

@telemedicine_bp.route('/consultations/active', methods=['GET'])
@jwt_required()
@role_required(['admin', 'doctor', 'nurse'])
def get_active_consultations():
    """Get list of active consultations"""
    try:
        current_user = get_jwt_identity()
        
        active_consultations = []
        for consultation_id, consultation in telemedicine_manager.active_consultations.items():
            if consultation.status in [ConsultationStatus.SCHEDULED, ConsultationStatus.WAITING, ConsultationStatus.IN_PROGRESS]:
                active_consultations.append({
                    'consultation_id': consultation.id,
                    'patient_id': consultation.patient_id,
                    'provider_id': consultation.provider_id,
                    'scheduled_time': consultation.scheduled_time.isoformat(),
                    'status': consultation.status.value,
                    'consultation_type': consultation.consultation_type.value,
                    'participants': len(telemedicine_manager.participant_sessions.get(consultation_id, []))
                })
        
        return jsonify({
            'status': 'success',
            'data': active_consultations
        }), 200
        
    except Exception as e:
        telemedicine_logger.error(f"Error getting active consultations: {e}")
        return jsonify({
            'status': 'error',
            'message': 'Failed to retrieve active consultations'
        }), 500
