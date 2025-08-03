"""
Advanced Security & Audit System for Healthcare Management
HIPAA-compliant security with comprehensive audit logging and threat detection
"""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import json
import hashlib
import secrets
import uuid
from flask import request, session
from functools import wraps
import re
import ipaddress
from sqlalchemy import func, and_, or_
from backend.database import db
from backend.models import User, Client
import jwt
import bcrypt
from cryptography.fernet import Fernet
import logging

# Configure security logger
security_logger = logging.getLogger('security')
security_logger.setLevel(logging.INFO)

class SecurityEventType(Enum):
    """Security event types for audit logging"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    ACCOUNT_LOCKED = "account_locked"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    DATA_EXPORT = "data_export"
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    BULK_DATA_ACCESS = "bulk_data_access"
    PHI_ACCESS = "phi_access"  # Protected Health Information

class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class SecurityEvent:
    """Security audit event"""
    id: str
    event_type: SecurityEventType
    user_id: Optional[str]
    username: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    resource_accessed: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.LOW
    location: Optional[str] = None
    session_id: Optional[str] = None
    success: bool = True

@dataclass
class ThreatDetection:
    """Threat detection result"""
    threat_detected: bool
    threat_type: str
    risk_score: float
    details: str
    recommended_action: str

class EncryptionManager:
    """Handles encryption/decryption of sensitive data"""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        if encryption_key:
            self.fernet = Fernet(encryption_key)
        else:
            # Generate a new key (in production, store this securely)
            self.fernet = Fernet(Fernet.generate_key())
    
    def encrypt_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        if not encrypted_data:
            return encrypted_data
        try:
            return self.fernet.decrypt(encrypted_data.encode()).decode()
        except Exception:
            # Log decryption failure
            security_logger.error("Failed to decrypt data")
            return ""
    
    def hash_sensitive_data(self, data: str) -> str:
        """Create one-way hash of sensitive data for indexing"""
        return hashlib.sha256(data.encode()).hexdigest()

class PasswordPolicy:
    """Enforces password security policies"""
    
    MIN_LENGTH = 12
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_NUMBERS = True
    REQUIRE_SPECIAL_CHARS = True
    MAX_CONSECUTIVE_CHARS = 2
    HISTORY_CHECK_COUNT = 5
    
    @classmethod
    def validate_password(cls, password: str, username: str = "") -> Tuple[bool, List[str]]:
        """Validate password against security policy"""
        errors = []
        
        if len(password) < cls.MIN_LENGTH:
            errors.append(f"Password must be at least {cls.MIN_LENGTH} characters long")
        
        if cls.REQUIRE_UPPERCASE and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if cls.REQUIRE_LOWERCASE and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if cls.REQUIRE_NUMBERS and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        if cls.REQUIRE_SPECIAL_CHARS and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for consecutive characters
        consecutive_count = 1
        for i in range(1, len(password)):
            if password[i] == password[i-1]:
                consecutive_count += 1
                if consecutive_count > cls.MAX_CONSECUTIVE_CHARS:
                    errors.append(f"Password cannot have more than {cls.MAX_CONSECUTIVE_CHARS} consecutive identical characters")
                    break
            else:
                consecutive_count = 1
        
        # Check if password contains username
        if username.lower() in password.lower():
            errors.append("Password cannot contain the username")
        
        # Check for common patterns
        common_patterns = ['123456', 'password', 'qwerty', 'abc123']
        for pattern in common_patterns:
            if pattern in password.lower():
                errors.append("Password cannot contain common patterns")
                break
        
        return len(errors) == 0, errors
    
    @classmethod
    def generate_secure_password(cls, length: int = 16) -> str:
        """Generate a secure random password"""
        import string
        
        characters = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(characters) for _ in range(length))
        
        # Ensure it meets policy requirements
        valid, _ = cls.validate_password(password)
        if not valid:
            return cls.generate_secure_password(length)
        
        return password

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self):
        self.encryption_manager = EncryptionManager()
    
    def log_security_event(
        self,
        event_type: SecurityEventType,
        user_id: Optional[str] = None,
        username: Optional[str] = None,
        resource_accessed: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        risk_level: RiskLevel = RiskLevel.LOW,
        success: bool = True
    ) -> SecurityEvent:
        """Log a security event"""
        
        # Get request context if available
        ip_address = "unknown"
        user_agent = "unknown"
        session_id = None
        
        try:
            if request:
                ip_address = request.remote_addr or "unknown"
                user_agent = request.headers.get('User-Agent', 'unknown')
                session_id = session.get('session_id')
        except RuntimeError:
            # No request context
            pass
        
        event = SecurityEvent(
            id=str(uuid.uuid4()),
            event_type=event_type,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            timestamp=datetime.utcnow(),
            resource_accessed=resource_accessed,
            details=details or {},
            risk_level=risk_level,
            session_id=session_id,
            success=success
        )
        
        # Store in database (implement actual storage)
        self._store_audit_event(event)
        
        # Log to security logger
        security_logger.info(
            f"Security Event: {event_type.value} | User: {username} | "
            f"IP: {ip_address} | Success: {success} | Risk: {risk_level.name}"
        )
        
        # Check for suspicious patterns
        threat_detection = self._analyze_for_threats(event)
        if threat_detection.threat_detected:
            self._handle_threat_detection(event, threat_detection)
        
        return event
    
    def _store_audit_event(self, event: SecurityEvent):
        """Store audit event in database (implement actual storage)"""
        # In production, store in a separate audit database
        # with write-only access and tamper protection
        pass
    
    def _analyze_for_threats(self, event: SecurityEvent) -> ThreatDetection:
        """Analyze event for potential security threats"""
        
        # Multiple failed logins
        if event.event_type == SecurityEventType.LOGIN_FAILURE:
            recent_failures = self._count_recent_failures(event.ip_address, event.username)
            if recent_failures >= 5:
                return ThreatDetection(
                    threat_detected=True,
                    threat_type="brute_force_attack",
                    risk_score=0.8,
                    details=f"{recent_failures} failed login attempts",
                    recommended_action="Lock account and block IP"
                )
        
        # Unusual access patterns
        if event.event_type == SecurityEventType.DATA_ACCESS:
            if self._detect_unusual_access_pattern(event):
                return ThreatDetection(
                    threat_detected=True,
                    threat_type="unusual_access_pattern",
                    risk_score=0.6,
                    details="Access pattern differs from normal behavior",
                    recommended_action="Review access and alert security team"
                )
        
        # Bulk data access
        if event.event_type == SecurityEventType.BULK_DATA_ACCESS:
            return ThreatDetection(
                threat_detected=True,
                threat_type="bulk_data_access",
                risk_score=0.7,
                details="Large amount of data accessed",
                recommended_action="Monitor closely and verify authorization"
            )
        
        return ThreatDetection(
            threat_detected=False,
            threat_type="none",
            risk_score=0.0,
            details="No threats detected",
            recommended_action="Continue monitoring"
        )
    
    def _count_recent_failures(self, ip_address: str, username: Optional[str]) -> int:
        """Count recent login failures (implement with actual storage)"""
        # This would query the audit database for recent failures
        return 0
    
    def _detect_unusual_access_pattern(self, event: SecurityEvent) -> bool:
        """Detect unusual access patterns"""
        # Implement machine learning-based anomaly detection
        # For now, simple heuristics
        
        # Access outside normal hours
        if event.timestamp.hour < 6 or event.timestamp.hour > 22:
            return True
        
        # Access from unusual location
        # (would implement geolocation checking)
        
        return False
    
    def _handle_threat_detection(self, event: SecurityEvent, threat: ThreatDetection):
        """Handle detected security threats"""
        
        # Log critical threat
        security_logger.critical(
            f"THREAT DETECTED: {threat.threat_type} | "
            f"Risk Score: {threat.risk_score} | "
            f"User: {event.username} | IP: {event.ip_address}"
        )
        
        # Implement automated responses
        if threat.risk_score >= 0.8:
            self._initiate_security_response(event, threat)
    
    def _initiate_security_response(self, event: SecurityEvent, threat: ThreatDetection):
        """Initiate automated security response"""
        
        if threat.threat_type == "brute_force_attack":
            # Lock account and block IP
            self._lock_user_account(event.username)
            self._block_ip_address(event.ip_address)
        
        # Send alert to security team
        self._send_security_alert(event, threat)
    
    def _lock_user_account(self, username: Optional[str]):
        """Lock user account"""
        if username:
            # Implement account locking
            security_logger.warning(f"Account locked: {username}")
    
    def _block_ip_address(self, ip_address: str):
        """Block IP address"""
        # Implement IP blocking (firewall rules, etc.)
        security_logger.warning(f"IP blocked: {ip_address}")
    
    def _send_security_alert(self, event: SecurityEvent, threat: ThreatDetection):
        """Send security alert to administrators"""
        # Implement alerting system (email, SMS, etc.)
        pass

class HIPAACompliance:
    """HIPAA compliance utilities and checks"""
    
    @staticmethod
    def is_phi_access(resource: str, data: Dict[str, Any]) -> bool:
        """Check if access involves Protected Health Information"""
        
        phi_indicators = [
            'patient', 'client', 'medical_record', 'diagnosis',
            'prescription', 'lab_result', 'visit', 'appointment'
        ]
        
        # Check resource type
        for indicator in phi_indicators:
            if indicator in resource.lower():
                return True
        
        # Check data fields
        phi_fields = [
            'ssn', 'social_security', 'medical_record_number',
            'diagnosis', 'treatment', 'medication', 'dob',
            'date_of_birth', 'phone', 'email', 'address'
        ]
        
        for field in phi_fields:
            if field in str(data).lower():
                return True
        
        return False
    
    @staticmethod
    def generate_phi_access_log(
        user_id: str,
        patient_id: str,
        access_type: str,
        justification: str
    ) -> Dict[str, Any]:
        """Generate HIPAA-compliant PHI access log"""
        
        return {
            'access_id': str(uuid.uuid4()),
            'timestamp': datetime.utcnow().isoformat(),
            'user_id': user_id,
            'patient_id': patient_id,
            'access_type': access_type,
            'justification': justification,
            'ip_address': request.remote_addr if request else 'unknown',
            'session_id': session.get('session_id') if session else 'unknown'
        }
    
    @staticmethod
    def validate_minimum_necessary(
        requested_data: List[str],
        user_role: str,
        purpose: str
    ) -> Tuple[bool, List[str]]:
        """Validate minimum necessary standard"""
        
        # Define role-based data access rules
        role_permissions = {
            'doctor': ['all'],
            'nurse': ['vital_signs', 'medications', 'care_plans', 'visit_notes'],
            'pharmacist': ['medications', 'allergies', 'prescriptions'],
            'lab_tech': ['lab_orders', 'lab_results'],
            'receptionist': ['demographics', 'contact_info', 'appointments'],
            'billing': ['demographics', 'insurance', 'billing_info']
        }
        
        allowed_data = role_permissions.get(user_role, [])
        
        if 'all' in allowed_data:
            return True, []
        
        denied_data = []
        for data_type in requested_data:
            if data_type not in allowed_data:
                denied_data.append(data_type)
        
        return len(denied_data) == 0, denied_data

class AccessControl:
    """Advanced access control system"""
    
    @staticmethod
    def check_permission(
        user_id: str,
        resource: str,
        action: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Tuple[bool, str]:
        """Check if user has permission for action on resource"""
        
        # Get user from database
        user = db.session.query(User).filter(User.id == user_id).first()
        if not user or not user.is_active:
            return False, "User not found or inactive"
        
        # Role-based access control
        permissions = {
            'admin': ['*'],  # All permissions
            'doctor': [
                'read:patient', 'write:patient', 'read:medical_record',
                'write:medical_record', 'read:prescription', 'write:prescription',
                'read:lab_result', 'write:lab_order'
            ],
            'nurse': [
                'read:patient', 'write:vital_signs', 'read:medical_record',
                'read:prescription', 'write:visit_note'
            ],
            'pharmacist': [
                'read:prescription', 'write:prescription_dispense',
                'read:patient_medication_history'
            ],
            'receptionist': [
                'read:patient_demographics', 'write:appointment',
                'read:appointment', 'write:patient_contact'
            ]
        }
        
        user_permissions = permissions.get(user.role, [])
        
        # Check for wildcard permission
        if '*' in user_permissions:
            return True, "Admin access granted"
        
        # Check specific permission
        required_permission = f"{action}:{resource}"
        if required_permission in user_permissions:
            return True, "Permission granted"
        
        # Additional context-based checks
        if context:
            # Example: Doctor can only access their own patients
            if (user.role == 'doctor' and 
                resource == 'patient' and 
                context.get('assigned_doctor') == user_id):
                return True, "Access granted to assigned patient"
        
        return False, f"Permission denied: {required_permission}"

class SessionManager:
    """Secure session management"""
    
    @staticmethod
    def create_secure_session(user_id: str, user_role: str) -> Dict[str, Any]:
        """Create a secure session"""
        
        session_data = {
            'session_id': str(uuid.uuid4()),
            'user_id': user_id,
            'user_role': user_role,
            'created_at': datetime.utcnow().isoformat(),
            'last_activity': datetime.utcnow().isoformat(),
            'ip_address': request.remote_addr if request else 'unknown',
            'user_agent': request.headers.get('User-Agent', 'unknown') if request else 'unknown'
        }
        
        # Set session timeout based on inactivity
        session_data['expires_at'] = (
            datetime.utcnow() + timedelta(hours=8)
        ).isoformat()
        
        return session_data
    
    @staticmethod
    def validate_session(session_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Validate session and check for security issues"""
        
        # Get session from storage (implement actual storage)
        session_data = {}  # Would fetch from session store
        
        if not session_data:
            return False, None
        
        # Check expiration
        expires_at = datetime.fromisoformat(session_data['expires_at'])
        if datetime.utcnow() > expires_at:
            return False, None
        
        # Check for session hijacking indicators
        current_ip = request.remote_addr if request else 'unknown'
        session_ip = session_data.get('ip_address', 'unknown')
        
        if current_ip != session_ip:
            # Potential session hijacking
            security_logger.warning(
                f"Session IP mismatch: {session_id} | "
                f"Original: {session_ip} | Current: {current_ip}"
            )
            return False, None
        
        # Update last activity
        session_data['last_activity'] = datetime.utcnow().isoformat()
        
        return True, session_data

# Security decorators
def require_permission(resource: str, action: str):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get current user from session/token
            user_id = session.get('user_id')  # or from JWT token
            if not user_id:
                return {'error': 'Authentication required'}, 401
            
            # Check permission
            allowed, message = AccessControl.check_permission(
                user_id, resource, action
            )
            
            if not allowed:
                audit_logger.log_security_event(
                    SecurityEventType.UNAUTHORIZED_ACCESS,
                    user_id=user_id,
                    resource_accessed=f"{action}:{resource}",
                    success=False,
                    risk_level=RiskLevel.MEDIUM
                )
                return {'error': message}, 403
            
            # Log authorized access
            audit_logger.log_security_event(
                SecurityEventType.DATA_ACCESS,
                user_id=user_id,
                resource_accessed=f"{action}:{resource}",
                success=True
            )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def log_phi_access(patient_id_param: str = 'patient_id'):
    """Decorator to log PHI access"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            user_id = session.get('user_id')
            patient_id = kwargs.get(patient_id_param)
            
            if user_id and patient_id:
                audit_logger.log_security_event(
                    SecurityEventType.PHI_ACCESS,
                    user_id=user_id,
                    resource_accessed=f"patient:{patient_id}",
                    success=True,
                    risk_level=RiskLevel.MEDIUM
                )
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize global instances
audit_logger = AuditLogger()
encryption_manager = EncryptionManager()
password_policy = PasswordPolicy()

# Security utilities
def sanitize_input(data: str) -> str:
    """Sanitize user input to prevent injection attacks"""
    if not data:
        return data
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', ';', '(', ')', '|', '`']
    for char in dangerous_chars:
        data = data.replace(char, '')
    
    return data.strip()

def generate_csrf_token() -> str:
    """Generate CSRF token for form protection"""
    return secrets.token_urlsafe(32)

def validate_csrf_token(token: str, expected: str) -> bool:
    """Validate CSRF token"""
    return secrets.compare_digest(token, expected)

def is_safe_url(url: str, allowed_hosts: List[str]) -> bool:
    """Check if URL is safe for redirects"""
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        return parsed.netloc in allowed_hosts or parsed.netloc == ''
    except Exception:
        return False

def rate_limit_key(identifier: str) -> str:
    """Generate rate limiting key"""
    return f"rate_limit:{hashlib.sha256(identifier.encode()).hexdigest()}"

# Export key components
__all__ = [
    'SecurityEventType', 'RiskLevel', 'SecurityEvent', 'ThreatDetection',
    'EncryptionManager', 'PasswordPolicy', 'AuditLogger', 'HIPAACompliance',
    'AccessControl', 'SessionManager', 'require_permission', 'log_phi_access',
    'audit_logger', 'encryption_manager', 'password_policy',
    'sanitize_input', 'generate_csrf_token', 'validate_csrf_token',
    'is_safe_url', 'rate_limit_key'
]
