"""
Electronic Health Records (EHR) System
FHIR-compliant clinical data management with decision support
"""

from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import json
import uuid
from sqlalchemy import and_, or_, func
from backend.database import db
from backend.models import Client, Visit, Prescription, LabOrder, MedicalRecord, Staff

class ClinicalSeverity(Enum):
    """Clinical severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    """Clinical alert types"""
    DRUG_INTERACTION = "drug_interaction"
    ALLERGY = "allergy"
    VITAL_SIGNS = "vital_signs"
    LAB_CRITICAL = "lab_critical"
    CHRONIC_CONDITION = "chronic_condition"

@dataclass
class ClinicalAlert:
    """Clinical decision support alert"""
    id: str
    patient_id: str
    alert_type: AlertType
    severity: ClinicalSeverity
    title: str
    description: str
    recommendation: str
    triggered_by: str
    created_at: datetime
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None

@dataclass
class VitalSigns:
    """Patient vital signs record"""
    id: str
    patient_id: str
    recorded_by: str
    recorded_at: datetime
    systolic_bp: Optional[int] = None
    diastolic_bp: Optional[int] = None
    heart_rate: Optional[int] = None
    temperature: Optional[float] = None  # Celsius
    respiratory_rate: Optional[int] = None
    oxygen_saturation: Optional[float] = None
    weight: Optional[float] = None  # kg
    height: Optional[float] = None  # cm
    bmi: Optional[float] = None
    pain_score: Optional[int] = None  # 0-10 scale

@dataclass
class ClinicalNote:
    """Clinical documentation note"""
    id: str
    patient_id: str
    visit_id: Optional[str]
    note_type: str  # progress, admission, discharge, consultation
    author_id: str
    created_at: datetime
    title: str
    content: str
    template_used: Optional[str] = None
    signed: bool = False
    signed_at: Optional[datetime] = None

class EHRSystem:
    """Comprehensive Electronic Health Records System"""
    
    @staticmethod
    def create_clinical_note(patient_id: str, author_id: str, note_type: str, 
                           title: str, content: str, visit_id: Optional[str] = None,
                           template_used: Optional[str] = None) -> ClinicalNote:
        """Create a new clinical note"""
        note = ClinicalNote(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            visit_id=visit_id,
            note_type=note_type,
            author_id=author_id,
            created_at=datetime.utcnow(),
            title=title,
            content=content,
            template_used=template_used
        )
        
        # Store in database (you'd implement actual storage)
        return note
    
    @staticmethod
    def record_vital_signs(patient_id: str, recorded_by: str, **vitals) -> VitalSigns:
        """Record patient vital signs"""
        # Calculate BMI if height and weight provided
        bmi = None
        if vitals.get('weight') and vitals.get('height'):
            height_m = vitals['height'] / 100  # Convert cm to m
            bmi = round(vitals['weight'] / (height_m ** 2), 1)
        
        vital_signs = VitalSigns(
            id=str(uuid.uuid4()),
            patient_id=patient_id,
            recorded_by=recorded_by,
            recorded_at=datetime.utcnow(),
            systolic_bp=vitals.get('systolic_bp'),
            diastolic_bp=vitals.get('diastolic_bp'),
            heart_rate=vitals.get('heart_rate'),
            temperature=vitals.get('temperature'),
            respiratory_rate=vitals.get('respiratory_rate'),
            oxygen_saturation=vitals.get('oxygen_saturation'),
            weight=vitals.get('weight'),
            height=vitals.get('height'),
            bmi=bmi,
            pain_score=vitals.get('pain_score')
        )
        
        # Check for critical vital signs and create alerts
        alerts = EHRSystem._check_vital_signs_alerts(vital_signs)
        for alert in alerts:
            EHRSystem._create_clinical_alert(alert)
        
        return vital_signs
    
    @staticmethod
    def _check_vital_signs_alerts(vitals: VitalSigns) -> List[ClinicalAlert]:
        """Check vital signs for critical values"""
        alerts = []
        
        # Blood pressure alerts
        if vitals.systolic_bp and vitals.diastolic_bp:
            if vitals.systolic_bp >= 180 or vitals.diastolic_bp >= 120:
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=vitals.patient_id,
                    alert_type=AlertType.VITAL_SIGNS,
                    severity=ClinicalSeverity.CRITICAL,
                    title="Hypertensive Crisis",
                    description=f"Critical BP: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg",
                    recommendation="Immediate medical attention required. Consider antihypertensive therapy.",
                    triggered_by=f"vital_signs_{vitals.id}",
                    created_at=datetime.utcnow()
                ))
            elif vitals.systolic_bp >= 140 or vitals.diastolic_bp >= 90:
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=vitals.patient_id,
                    alert_type=AlertType.VITAL_SIGNS,
                    severity=ClinicalSeverity.HIGH,
                    title="Hypertension",
                    description=f"Elevated BP: {vitals.systolic_bp}/{vitals.diastolic_bp} mmHg",
                    recommendation="Monitor closely. Consider lifestyle modifications and medication review.",
                    triggered_by=f"vital_signs_{vitals.id}",
                    created_at=datetime.utcnow()
                ))
        
        # Heart rate alerts
        if vitals.heart_rate:
            if vitals.heart_rate < 50:
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=vitals.patient_id,
                    alert_type=AlertType.VITAL_SIGNS,
                    severity=ClinicalSeverity.HIGH,
                    title="Bradycardia",
                    description=f"Low heart rate: {vitals.heart_rate} bpm",
                    recommendation="Assess for underlying causes. Consider ECG and cardiac evaluation.",
                    triggered_by=f"vital_signs_{vitals.id}",
                    created_at=datetime.utcnow()
                ))
            elif vitals.heart_rate > 120:
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=vitals.patient_id,
                    alert_type=AlertType.VITAL_SIGNS,
                    severity=ClinicalSeverity.HIGH,
                    title="Tachycardia",
                    description=f"High heart rate: {vitals.heart_rate} bpm",
                    recommendation="Assess for underlying causes. Monitor for arrhythmias.",
                    triggered_by=f"vital_signs_{vitals.id}",
                    created_at=datetime.utcnow()
                ))
        
        # Temperature alerts
        if vitals.temperature:
            if vitals.temperature >= 38.5:
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=vitals.patient_id,
                    alert_type=AlertType.VITAL_SIGNS,
                    severity=ClinicalSeverity.MODERATE,
                    title="Fever",
                    description=f"Elevated temperature: {vitals.temperature}°C",
                    recommendation="Investigate source of infection. Consider antipyretics.",
                    triggered_by=f"vital_signs_{vitals.id}",
                    created_at=datetime.utcnow()
                ))
        
        # Oxygen saturation alerts
        if vitals.oxygen_saturation:
            if vitals.oxygen_saturation < 90:
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=vitals.patient_id,
                    alert_type=AlertType.VITAL_SIGNS,
                    severity=ClinicalSeverity.CRITICAL,
                    title="Hypoxemia",
                    description=f"Low oxygen saturation: {vitals.oxygen_saturation}%",
                    recommendation="Immediate oxygen therapy required. Assess respiratory status.",
                    triggered_by=f"vital_signs_{vitals.id}",
                    created_at=datetime.utcnow()
                ))
        
        return alerts
    
    @staticmethod
    def check_drug_interactions(patient_id: str, new_medication: str) -> List[ClinicalAlert]:
        """Check for drug interactions with current medications"""
        # Get current active prescriptions
        current_meds = db.session.query(Prescription).filter(
            Prescription.client_id == patient_id,
            Prescription.status == 'active',
            or_(
                Prescription.end_date.is_(None),
                Prescription.end_date > datetime.utcnow().date()
            )
        ).all()
        
        alerts = []
        
        # Drug interaction database (simplified - in reality, use comprehensive drug database)
        interactions = {
            'warfarin': {
                'aspirin': {
                    'severity': ClinicalSeverity.HIGH,
                    'description': 'Increased bleeding risk',
                    'recommendation': 'Monitor INR closely. Consider alternative antiplatelet therapy.'
                },
                'metronidazole': {
                    'severity': ClinicalSeverity.HIGH,
                    'description': 'Enhanced anticoagulant effect',
                    'recommendation': 'Reduce warfarin dose. Monitor INR frequently.'
                }
            },
            'metformin': {
                'contrast_media': {
                    'severity': ClinicalSeverity.MODERATE,
                    'description': 'Risk of lactic acidosis',
                    'recommendation': 'Hold metformin 48h before and after contrast procedure.'
                }
            },
            'digoxin': {
                'amiodarone': {
                    'severity': ClinicalSeverity.HIGH,
                    'description': 'Increased digoxin levels',
                    'recommendation': 'Reduce digoxin dose by 50%. Monitor digoxin levels.'
                }
            }
        }
        
        new_med_lower = new_medication.lower()
        
        for prescription in current_meds:
            current_med = prescription.medication_name.lower()
            
            # Check both directions of interaction
            if (new_med_lower in interactions and 
                current_med in interactions[new_med_lower]):
                interaction = interactions[new_med_lower][current_med]
                
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    alert_type=AlertType.DRUG_INTERACTION,
                    severity=interaction['severity'],
                    title=f"Drug Interaction: {new_medication} + {prescription.medication_name}",
                    description=interaction['description'],
                    recommendation=interaction['recommendation'],
                    triggered_by=f"prescription_{prescription.id}",
                    created_at=datetime.utcnow()
                ))
            
            elif (current_med in interactions and 
                  new_med_lower in interactions[current_med]):
                interaction = interactions[current_med][new_med_lower]
                
                alerts.append(ClinicalAlert(
                    id=str(uuid.uuid4()),
                    patient_id=patient_id,
                    alert_type=AlertType.DRUG_INTERACTION,
                    severity=interaction['severity'],
                    title=f"Drug Interaction: {prescription.medication_name} + {new_medication}",
                    description=interaction['description'],
                    recommendation=interaction['recommendation'],
                    triggered_by=f"prescription_{prescription.id}",
                    created_at=datetime.utcnow()
                ))
        
        return alerts
    
    @staticmethod
    def generate_clinical_summary(patient_id: str, days: int = 30) -> Dict[str, Any]:
        """Generate comprehensive clinical summary for patient"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get patient info
        patient = db.session.query(Client).filter(Client.id == patient_id).first()
        if not patient:
            return {"error": "Patient not found"}
        
        # Recent visits
        recent_visits = db.session.query(Visit).filter(
            Visit.client_id == patient_id,
            Visit.visit_date.between(start_date, end_date)
        ).order_by(Visit.visit_date.desc()).limit(10).all()
        
        # Active prescriptions
        active_prescriptions = db.session.query(Prescription).filter(
            Prescription.client_id == patient_id,
            Prescription.status == 'active',
            or_(
                Prescription.end_date.is_(None),
                Prescription.end_date > datetime.utcnow().date()
            )
        ).all()
        
        # Recent lab results
        recent_labs = db.session.query(LabOrder).filter(
            LabOrder.client_id == patient_id,
            LabOrder.result_date.between(start_date, end_date),
            LabOrder.result_value.isnot(None)
        ).order_by(LabOrder.result_date.desc()).limit(20).all()
        
        # Active alerts
        active_alerts = []  # Would fetch from alerts storage
        
        # Calculate age
        age = None
        if patient.dob:
            age = (datetime.utcnow().date() - patient.dob).days // 365
        
        return {
            'patient_info': {
                'id': patient.id,
                'name': f"{patient.first_name} {patient.last_name}",
                'age': age,
                'gender': patient.gender,
                'dob': patient.dob.isoformat() if patient.dob else None,
                'phone': patient.phone,
                'email': patient.email
            },
            'recent_visits': [
                {
                    'id': visit.id,
                    'date': visit.visit_date.isoformat(),
                    'type': visit.visit_type,
                    'purpose': visit.purpose,
                    'diagnosis': visit.diagnosis,
                    'treatment': visit.treatment
                } for visit in recent_visits
            ],
            'active_medications': [
                {
                    'id': rx.id,
                    'medication': rx.medication_name,
                    'dosage': rx.dosage,
                    'frequency': rx.frequency,
                    'prescribed_date': rx.prescribed_date.isoformat(),
                    'end_date': rx.end_date.isoformat() if rx.end_date else None,
                    'dispensed': rx.dispensed
                } for rx in active_prescriptions
            ],
            'recent_lab_results': [
                {
                    'id': lab.id,
                    'test_name': lab.test.name if lab.test else 'Unknown',
                    'result_value': lab.result_value,
                    'result_date': lab.result_date.isoformat(),
                    'abnormal_flag': lab.abnormal_flag,
                    'normal_range': lab.test.normal_range if lab.test else None
                } for lab in recent_labs
            ],
            'active_alerts': active_alerts,
            'summary_period': f"{days} days",
            'generated_at': datetime.utcnow().isoformat()
        }
    
    @staticmethod
    def _create_clinical_alert(alert: ClinicalAlert) -> None:
        """Store clinical alert (implement actual storage)"""
        # In a real implementation, this would store to database
        # For now, we'll just log it
        print(f"Clinical Alert Created: {alert.title} for patient {alert.patient_id}")
    
    @staticmethod
    def get_patient_timeline(patient_id: str, start_date: date = None, 
                           end_date: date = None) -> List[Dict[str, Any]]:
        """Get chronological timeline of patient events"""
        if not start_date:
            start_date = datetime.utcnow().date() - timedelta(days=365)
        if not end_date:
            end_date = datetime.utcnow().date()
        
        timeline_events = []
        
        # Visits
        visits = db.session.query(Visit).filter(
            Visit.client_id == patient_id,
            func.date(Visit.visit_date).between(start_date, end_date)
        ).all()
        
        for visit in visits:
            timeline_events.append({
                'date': visit.visit_date.date(),
                'time': visit.visit_date.time(),
                'type': 'visit',
                'title': f"{visit.visit_type.title()} Visit",
                'description': visit.purpose,
                'details': {
                    'diagnosis': visit.diagnosis,
                    'treatment': visit.treatment,
                    'notes': visit.notes
                }
            })
        
        # Prescriptions
        prescriptions = db.session.query(Prescription).filter(
            Prescription.client_id == patient_id,
            func.date(Prescription.prescribed_date).between(start_date, end_date)
        ).all()
        
        for rx in prescriptions:
            timeline_events.append({
                'date': rx.prescribed_date.date(),
                'time': rx.prescribed_date.time() if hasattr(rx.prescribed_date, 'time') else None,
                'type': 'prescription',
                'title': f"Prescribed {rx.medication_name}",
                'description': f"{rx.dosage}, {rx.frequency}",
                'details': {
                    'duration': rx.duration,
                    'quantity': rx.quantity,
                    'instructions': rx.instructions,
                    'dispensed': rx.dispensed
                }
            })
        
        # Lab orders
        lab_orders = db.session.query(LabOrder).filter(
            LabOrder.client_id == patient_id,
            func.date(LabOrder.created_at).between(start_date, end_date)
        ).all()
        
        for lab in lab_orders:
            timeline_events.append({
                'date': lab.created_at.date(),
                'time': lab.created_at.time(),
                'type': 'lab_order',
                'title': f"Lab Test: {lab.test.name if lab.test else 'Unknown'}",
                'description': lab.clinical_notes or "Lab test ordered",
                'details': {
                    'status': lab.status,
                    'priority': lab.priority,
                    'result_value': lab.result_value,
                    'result_date': lab.result_date.isoformat() if lab.result_date else None,
                    'abnormal_flag': lab.abnormal_flag
                }
            })
        
        # Sort by date and time
        timeline_events.sort(key=lambda x: (x['date'], x['time'] or datetime.min.time()), reverse=True)
        
        return timeline_events

class ClinicalDecisionSupport:
    """Clinical Decision Support System (CDSS)"""
    
    @staticmethod
    def get_care_recommendations(patient_id: str) -> List[Dict[str, Any]]:
        """Generate evidence-based care recommendations"""
        recommendations = []
        
        # Get patient data
        patient = db.session.query(Client).filter(Client.id == patient_id).first()
        if not patient:
            return recommendations
        
        # Age-based screening recommendations
        age = None
        if patient.dob:
            age = (datetime.utcnow().date() - patient.dob).days // 365
            
            if age >= 50:
                recommendations.append({
                    'type': 'screening',
                    'priority': 'routine',
                    'title': 'Colorectal Cancer Screening',
                    'description': 'Consider colonoscopy or FIT test for colorectal cancer screening',
                    'evidence_level': 'A',
                    'frequency': 'Every 10 years (colonoscopy) or annually (FIT)'
                })
            
            if age >= 65:
                recommendations.append({
                    'type': 'vaccination',
                    'priority': 'routine',
                    'title': 'Pneumococcal Vaccine',
                    'description': 'Administer pneumococcal vaccine for adults 65+',
                    'evidence_level': 'A',
                    'frequency': 'One-time (with booster considerations)'
                })
        
        # Gender-specific recommendations
        if patient.gender == 'female' and age and age >= 21:
            recommendations.append({
                'type': 'screening',
                'priority': 'routine',
                'title': 'Cervical Cancer Screening',
                'description': 'Pap smear and/or HPV testing for cervical cancer screening',
                'evidence_level': 'A',
                'frequency': 'Every 3 years (Pap) or every 5 years (Pap + HPV)'
            })
        
        # Check for overdue preventive care
        last_visit = db.session.query(Visit).filter(
            Visit.client_id == patient_id
        ).order_by(Visit.visit_date.desc()).first()
        
        if last_visit and (datetime.utcnow() - last_visit.visit_date).days > 365:
            recommendations.append({
                'type': 'follow_up',
                'priority': 'high',
                'title': 'Annual Wellness Visit',
                'description': 'Schedule annual wellness visit - last visit over 1 year ago',
                'evidence_level': 'B',
                'frequency': 'Annually'
            })
        
        return recommendations
