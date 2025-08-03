"""
Telemedicine & Video Consultation System
Comprehensive virtual care platform with WebRTC, remote monitoring, and consultation management
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import uuid
from sqlalchemy import and_, or_, func
from backend.database import db
from backend.models import Appointment, Client, Staff, Visit
import asyncio
import secrets
import logging

# Configure telemedicine logger
telemedicine_logger = logging.getLogger('telemedicine')

class ConsultationType(Enum):
    """Types of virtual consultations"""
    VIDEO_CALL = "video_call"
    AUDIO_CALL = "audio_call"
    CHAT_ONLY = "chat_only"
    SCREEN_SHARE = "screen_share"
    GROUP_CONSULTATION = "group_consultation"

class ConsultationStatus(Enum):
    """Consultation session status"""
    SCHEDULED = "scheduled"
    WAITING = "waiting"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"
    TECHNICAL_ISSUES = "technical_issues"

class ConnectionQuality(Enum):
    """Connection quality indicators"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    DISCONNECTED = "disconnected"

@dataclass
class VirtualConsultation:
    """Virtual consultation session"""
    id: str
    appointment_id: str
    patient_id: str
    provider_id: str
    consultation_type: ConsultationType
    status: ConsultationStatus
    scheduled_time: datetime
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    room_id: Optional[str] = None
    access_token: Optional[str] = None
    recording_enabled: bool = False
    recording_url: Optional[str] = None
    chat_transcript: List[Dict[str, Any]] = field(default_factory=list)
    technical_notes: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ParticipantSession:
    """Individual participant session data"""
    user_id: str
    consultation_id: str
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None
    connection_quality: ConnectionQuality = ConnectionQuality.GOOD
    audio_enabled: bool = True
    video_enabled: bool = True
    screen_sharing: bool = False
    technical_issues: List[str] = field(default_factory=list)
    session_token: Optional[str] = None

@dataclass
class RemoteVitalSigns:
    """Remote vital signs monitoring data"""
    id: str
    patient_id: str
    consultation_id: Optional[str]
    device_type: str  # smartphone, wearable, bp_monitor, etc.
    measurement_type: str  # heart_rate, blood_pressure, temperature, etc.
    value: float
    unit: str
    timestamp: datetime
    device_id: Optional[str] = None
    accuracy_score: Optional[float] = None
    verified_by_provider: bool = False

class TelemedicineManager:
    """Core telemedicine platform management"""
    
    def __init__(self):
        self.active_consultations: Dict[str, VirtualConsultation] = {}
        self.participant_sessions: Dict[str, List[ParticipantSession]] = {}
        self.webrtc_config = self._get_webrtc_configuration()
    
    def schedule_virtual_consultation(
        self,
        patient_id: str,
        provider_id: str,
        scheduled_time: datetime,
        consultation_type: ConsultationType = ConsultationType.VIDEO_CALL,
        duration_minutes: int = 30,
        notes: Optional[str] = None
    ) -> Optional[VirtualConsultation]:
        """Schedule a new virtual consultation"""
        
        try:
            # Create appointment first
            appointment_id = self._create_telemedicine_appointment(
                patient_id, provider_id, scheduled_time, duration_minutes, notes
            )
            
            if not appointment_id:
                return None
            
            # Create virtual consultation
            consultation = VirtualConsultation(
                id=str(uuid.uuid4()),
                appointment_id=appointment_id,
                patient_id=patient_id,
                provider_id=provider_id,
                consultation_type=consultation_type,
                status=ConsultationStatus.SCHEDULED,
                scheduled_time=scheduled_time,
                room_id=self._generate_room_id(),
                access_token=self._generate_access_token()
            )
            
            # Store consultation
            self.active_consultations[consultation.id] = consultation
            
            # Send notifications
            self._send_consultation_notifications(consultation)
            
            telemedicine_logger.info(
                f"Virtual consultation scheduled: {consultation.id} for {scheduled_time}"
            )
            
            return consultation
            
        except Exception as e:
            telemedicine_logger.error(f"Error scheduling consultation: {e}")
            return None
    
    def start_consultation(
        self, 
        consultation_id: str, 
        user_id: str
    ) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """Start a virtual consultation session"""
        
        consultation = self.active_consultations.get(consultation_id)
        if not consultation:
            return False, "Consultation not found", None
        
        # Verify user permission
        if user_id not in [consultation.patient_id, consultation.provider_id]:
            return False, "Unauthorized access", None
        
        # Check if consultation is ready to start
        now = datetime.utcnow()
        if consultation.scheduled_time > now + timedelta(minutes=15):
            return False, "Consultation not yet available", None
        
        # Initialize consultation if not started
        if consultation.status == ConsultationStatus.SCHEDULED:
            consultation.status = ConsultationStatus.WAITING
            consultation.start_time = now
        
        # Create participant session
        participant = ParticipantSession(
            user_id=user_id,
            consultation_id=consultation_id,
            joined_at=now,
            session_token=self._generate_session_token(user_id, consultation_id)
        )
        
        if consultation_id not in self.participant_sessions:
            self.participant_sessions[consultation_id] = []
        
        self.participant_sessions[consultation_id].append(participant)
        
        # Prepare session data
        session_data = {
            'consultation_id': consultation_id,
            'room_id': consultation.room_id,
            'session_token': participant.session_token,
            'webrtc_config': self.webrtc_config,
            'consultation_type': consultation.consultation_type.value,
            'recording_enabled': consultation.recording_enabled,
            'participants': self._get_consultation_participants(consultation_id)
        }
        
        # Update consultation status if both participants joined
        participants = self.participant_sessions[consultation_id]
        if len(participants) >= 2:  # Patient and provider
            consultation.status = ConsultationStatus.IN_PROGRESS
        
        return True, "Session started successfully", session_data
    
    def end_consultation(
        self, 
        consultation_id: str, 
        user_id: str,
        completion_notes: Optional[str] = None
    ) -> Tuple[bool, str]:
        """End a virtual consultation"""
        
        consultation = self.active_consultations.get(consultation_id)
        if not consultation:
            return False, "Consultation not found"
        
        # Verify permission (provider can end, patient can leave)
        if user_id == consultation.provider_id:
            # Provider ending consultation
            consultation.status = ConsultationStatus.COMPLETED
            consultation.end_time = datetime.utcnow()
            
            # Update all participant sessions
            if consultation_id in self.participant_sessions:
                for participant in self.participant_sessions[consultation_id]:
                    if not participant.left_at:
                        participant.left_at = datetime.utcnow()
            
            # Create visit record
            self._create_consultation_visit_record(consultation, completion_notes)
            
            # Send follow-up notifications
            self._send_consultation_summary(consultation)
            
        elif user_id == consultation.patient_id:
            # Patient leaving consultation
            participants = self.participant_sessions.get(consultation_id, [])
            for participant in participants:
                if participant.user_id == user_id:
                    participant.left_at = datetime.utcnow()
                    break
        
        return True, "Consultation ended successfully"
    
    def send_chat_message(
        self,
        consultation_id: str,
        sender_id: str,
        message: str,
        message_type: str = "text"
    ) -> bool:
        """Send chat message during consultation"""
        
        consultation = self.active_consultations.get(consultation_id)
        if not consultation:
            return False
        
        # Verify sender is participant
        if sender_id not in [consultation.patient_id, consultation.provider_id]:
            return False
        
        # Add message to transcript
        chat_message = {
            'id': str(uuid.uuid4()),
            'sender_id': sender_id,
            'message': message,
            'message_type': message_type,
            'timestamp': datetime.utcnow().isoformat(),
            'delivered': False
        }
        
        consultation.chat_transcript.append(chat_message)
        
        # Broadcast message to other participants
        self._broadcast_chat_message(consultation_id, chat_message)
        
        return True
    
    def update_connection_quality(
        self,
        consultation_id: str,
        user_id: str,
        quality: ConnectionQuality,
        technical_issues: Optional[List[str]] = None
    ):
        """Update participant connection quality"""
        
        participants = self.participant_sessions.get(consultation_id, [])
        for participant in participants:
            if participant.user_id == user_id:
                participant.connection_quality = quality
                if technical_issues:
                    participant.technical_issues.extend(technical_issues)
                break
        
        # Log connection issues
        if quality in [ConnectionQuality.POOR, ConnectionQuality.DISCONNECTED]:
            telemedicine_logger.warning(
                f"Connection issues in consultation {consultation_id}: "
                f"User {user_id} has {quality.value} connection"
            )
    
    def record_remote_vital_signs(
        self,
        patient_id: str,
        device_type: str,
        measurement_type: str,
        value: float,
        unit: str,
        consultation_id: Optional[str] = None,
        device_id: Optional[str] = None
    ) -> RemoteVitalSigns:
        """Record vital signs from remote monitoring devices"""
        
        vital_signs = RemoteVitalSigns(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            consultation_id=consultation_id,
            device_type=device_type,
            measurement_type=measurement_type,
            value=value,
            unit=unit,
            timestamp=datetime.utcnow(),
            device_id=device_id,
            accuracy_score=self._calculate_measurement_accuracy(
                device_type, measurement_type, value
            )
        )
        
        # Store vital signs (implement actual storage)
        self._store_remote_vital_signs(vital_signs)
        
        # Alert if abnormal values detected
        if self._is_abnormal_vital_sign(measurement_type, value):
            self._send_vital_signs_alert(vital_signs)
        
        return vital_signs
    
    def get_consultation_analytics(
        self, 
        consultation_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get detailed consultation analytics"""
        
        consultation = self.active_consultations.get(consultation_id)
        if not consultation:
            return None
        
        participants = self.participant_sessions.get(consultation_id, [])
        
        # Calculate session metrics
        total_duration = 0
        if consultation.start_time and consultation.end_time:
            total_duration = (consultation.end_time - consultation.start_time).total_seconds() / 60
        
        # Connection quality analysis
        quality_scores = [p.connection_quality.value for p in participants]
        avg_quality = self._calculate_average_quality(quality_scores)
        
        # Technical issues summary
        all_issues = []
        for participant in participants:
            all_issues.extend(participant.technical_issues)
        
        return {
            'consultation_id': consultation_id,
            'duration_minutes': total_duration,
            'participants_count': len(participants),
            'average_connection_quality': avg_quality,
            'technical_issues_count': len(all_issues),
            'technical_issues': list(set(all_issues)),
            'chat_messages_count': len(consultation.chat_transcript),
            'recording_available': bool(consultation.recording_url),
            'completion_status': consultation.status.value,
            'patient_satisfaction': None  # Would implement post-consultation survey
        }
    
    def _create_telemedicine_appointment(
        self,
        patient_id: str,
        provider_id: str,
        scheduled_time: datetime,
        duration_minutes: int,
        notes: Optional[str]
    ) -> Optional[str]:
        """Create appointment for telemedicine consultation"""
        
        try:
            appointment = Appointment(
                id=str(uuid.uuid4()),
                client_id=patient_id,
                doctor_id=provider_id,
                date=scheduled_time,
                duration_minutes=duration_minutes,
                appointment_type='telemedicine',
                status='scheduled',
                reason='Virtual consultation',
                notes=notes or 'Telemedicine appointment',
                created_at=datetime.utcnow()
            )
            
            db.session.add(appointment)
            db.session.commit()
            
            return appointment.id
            
        except Exception as e:
            db.session.rollback()
            telemedicine_logger.error(f"Error creating telemedicine appointment: {e}")
            return None
    
    def _generate_room_id(self) -> str:
        """Generate unique room ID for consultation"""
        return f"room_{secrets.token_urlsafe(16)}"
    
    def _generate_access_token(self) -> str:
        """Generate access token for consultation"""
        return secrets.token_urlsafe(32)
    
    def _generate_session_token(self, user_id: str, consultation_id: str) -> str:
        """Generate session token for participant"""
        return secrets.token_urlsafe(24)
    
    def _get_webrtc_configuration(self) -> Dict[str, Any]:
        """Get WebRTC configuration for video calls"""
        return {
            'iceServers': [
                {'urls': 'stun:stun.l.google.com:19302'},
                {'urls': 'stun:stun1.l.google.com:19302'},
                # Add TURN servers for production
            ],
            'iceCandidatePoolSize': 10,
            'bundlePolicy': 'max-bundle',
            'rtcpMuxPolicy': 'require'
        }
    
    def _send_consultation_notifications(self, consultation: VirtualConsultation):
        """Send consultation scheduling notifications"""
        # Implement email/SMS notifications
        pass
    
    def _get_consultation_participants(self, consultation_id: str) -> List[Dict[str, Any]]:
        """Get current consultation participants"""
        participants = self.participant_sessions.get(consultation_id, [])
        return [
            {
                'user_id': p.user_id,
                'joined_at': p.joined_at.isoformat() if p.joined_at else None,
                'connection_quality': p.connection_quality.value,
                'audio_enabled': p.audio_enabled,
                'video_enabled': p.video_enabled
            } for p in participants if not p.left_at
        ]
    
    def _broadcast_chat_message(self, consultation_id: str, message: Dict[str, Any]):
        """Broadcast chat message to consultation participants"""
        # Implement WebSocket broadcasting
        pass
    
    def _create_consultation_visit_record(
        self, 
        consultation: VirtualConsultation, 
        notes: Optional[str]
    ):
        """Create visit record for completed consultation"""
        
        try:
            visit = Visit(
                id=str(uuid.uuid4()),
                client_id=consultation.patient_id,
                visit_date=consultation.start_time or consultation.scheduled_time,
                visit_type='telemedicine',
                purpose='Virtual consultation',
                diagnosis=notes or 'Telemedicine consultation completed',
                treatment='',
                notes=f"Virtual consultation via {consultation.consultation_type.value}",
                created_at=datetime.utcnow()
            )
            
            db.session.add(visit)
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            telemedicine_logger.error(f"Error creating visit record: {e}")
    
    def _send_consultation_summary(self, consultation: VirtualConsultation):
        """Send consultation summary to participants"""
        # Implement summary generation and delivery
        pass
    
    def _calculate_measurement_accuracy(
        self, 
        device_type: str, 
        measurement_type: str, 
        value: float
    ) -> float:
        """Calculate accuracy score for remote measurements"""
        
        # Device-specific accuracy factors
        accuracy_factors = {
            'smartphone': {
                'heart_rate': 0.85,
                'blood_pressure': 0.70,
                'temperature': 0.60
            },
            'wearable': {
                'heart_rate': 0.90,
                'steps': 0.95,
                'sleep': 0.80
            },
            'bp_monitor': {
                'blood_pressure': 0.95
            },
            'thermometer': {
                'temperature': 0.98
            }
        }
        
        return accuracy_factors.get(device_type, {}).get(measurement_type, 0.75)
    
    def _store_remote_vital_signs(self, vital_signs: RemoteVitalSigns):
        """Store remote vital signs data"""
        # Implement actual database storage
        pass
    
    def _is_abnormal_vital_sign(self, measurement_type: str, value: float) -> bool:
        """Check if vital sign value is abnormal"""
        
        abnormal_ranges = {
            'heart_rate': (50, 120),
            'systolic_bp': (90, 140),
            'diastolic_bp': (60, 90),
            'temperature': (36.1, 37.8),  # Celsius
            'oxygen_saturation': (95, 100)
        }
        
        range_values = abnormal_ranges.get(measurement_type)
        if range_values:
            min_val, max_val = range_values
            return value < min_val or value > max_val
        
        return False
    
    def _send_vital_signs_alert(self, vital_signs: RemoteVitalSigns):
        """Send alert for abnormal vital signs"""
        telemedicine_logger.warning(
            f"Abnormal vital sign detected: {vital_signs.measurement_type} = "
            f"{vital_signs.value} {vital_signs.unit} for patient {vital_signs.patient_id}"
        )
        # Implement alert system
    
    def _calculate_average_quality(self, quality_scores: List[str]) -> str:
        """Calculate average connection quality"""
        if not quality_scores:
            return "unknown"
        
        quality_values = {
            'excellent': 4,
            'good': 3,
            'fair': 2,
            'poor': 1,
            'disconnected': 0
        }
        
        avg_score = sum(quality_values.get(q, 0) for q in quality_scores) / len(quality_scores)
        
        if avg_score >= 3.5:
            return 'excellent'
        elif avg_score >= 2.5:
            return 'good'
        elif avg_score >= 1.5:
            return 'fair'
        else:
            return 'poor'

class VirtualWaitingRoom:
    """Virtual waiting room management"""
    
    def __init__(self):
        self.waiting_patients: Dict[str, Dict[str, Any]] = {}
    
    def add_patient_to_waiting_room(
        self,
        consultation_id: str,
        patient_id: str,
        estimated_wait_time: int = 15
    ):
        """Add patient to virtual waiting room"""
        
        self.waiting_patients[patient_id] = {
            'consultation_id': consultation_id,
            'joined_at': datetime.utcnow(),
            'estimated_wait_time': estimated_wait_time,
            'status': 'waiting',
            'position': len(self.waiting_patients) + 1
        }
    
    def update_wait_times(self):
        """Update estimated wait times for all waiting patients"""
        
        current_time = datetime.utcnow()
        
        for patient_id, wait_info in self.waiting_patients.items():
            elapsed_time = (current_time - wait_info['joined_at']).total_seconds() / 60
            wait_info['estimated_wait_time'] = max(0, wait_info['estimated_wait_time'] - elapsed_time)
    
    def remove_patient_from_waiting_room(self, patient_id: str):
        """Remove patient from waiting room"""
        if patient_id in self.waiting_patients:
            del self.waiting_patients[patient_id]
            self._update_queue_positions()
    
    def _update_queue_positions(self):
        """Update queue positions after patient removal"""
        for i, (patient_id, wait_info) in enumerate(self.waiting_patients.items()):
            wait_info['position'] = i + 1

# Global instances
telemedicine_manager = TelemedicineManager()
virtual_waiting_room = VirtualWaitingRoom()
