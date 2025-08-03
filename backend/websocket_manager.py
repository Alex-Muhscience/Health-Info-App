"""
WebSocket Manager for Real-time Features
Provides real-time notifications, appointment updates, and system alerts
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from functools import wraps
import json
from datetime import datetime

socketio = SocketIO(cors_allowed_origins="*")

class NotificationManager:
    """Manages real-time notifications across the HMS"""
    
    @staticmethod
    def authenticated_only(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                verify_jwt_in_request()
                return f(*args, **kwargs)
            except Exception as e:
                emit('error', {'message': 'Authentication required'})
                return False
        return decorated

@socketio.on('connect')
@NotificationManager.authenticated_only
def handle_connect():
    """Handle client connection"""
    user_id = get_jwt_identity()
    join_room(f'user_{user_id}')
    emit('connected', {'message': 'Successfully connected to real-time updates'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    user_id = get_jwt_identity()
    if user_id:
        leave_room(f'user_{user_id}')

@socketio.on('join_department')
@NotificationManager.authenticated_only
def handle_join_department(data):
    """Join department room for department-specific notifications"""
    department_id = data.get('department_id')
    join_room(f'department_{department_id}')
    emit('joined_department', {'department_id': department_id})

class RealTimeNotifications:
    """Real-time notification system"""
    
    @staticmethod
    def notify_appointment_created(appointment_data):
        """Notify relevant users about new appointment"""
        socketio.emit('appointment_created', {
            'type': 'appointment',
            'action': 'created',
            'data': appointment_data,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'department_{appointment_data.get("department_id")}')
    
    @staticmethod
    def notify_lab_result_ready(lab_order_data):
        """Notify about lab results being ready"""
        socketio.emit('lab_result_ready', {
            'type': 'lab_result',
            'action': 'completed',
            'data': lab_order_data,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{lab_order_data.get("ordered_by")}')
    
    @staticmethod
    def notify_emergency_alert(alert_data):
        """Broadcast emergency alerts to all connected users"""
        socketio.emit('emergency_alert', {
            'type': 'emergency',
            'priority': 'high',
            'data': alert_data,
            'timestamp': datetime.utcnow().isoformat()
        }, broadcast=True)
    
    @staticmethod
    def notify_prescription_dispensed(prescription_data):
        """Notify about prescription being dispensed"""
        socketio.emit('prescription_dispensed', {
            'type': 'prescription',
            'action': 'dispensed',
            'data': prescription_data,
            'timestamp': datetime.utcnow().isoformat()
        }, room=f'user_{prescription_data.get("doctor_id")}')

# Integration with Flask app
def init_websocket(app):
    """Initialize WebSocket with Flask app"""
    socketio.init_app(app, cors_allowed_origins="*")
    return socketio
