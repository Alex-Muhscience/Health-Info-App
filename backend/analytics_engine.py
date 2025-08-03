"""
Advanced Analytics Engine for Healthcare Management System
Provides comprehensive insights, predictive analytics, and operational intelligence
"""

from datetime import datetime, timedelta
from sqlalchemy import func, text, and_, or_
from backend.database import db
from backend.models import (
    Client, Appointment, Visit, Prescription, LabOrder, 
    Admission, Department, Staff, Billing, Inventory
)
import pandas as pd
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import json

@dataclass
class AnalyticsResult:
    """Structured analytics result"""
    metric_name: str
    value: float
    trend: str  # 'up', 'down', 'stable'
    period: str
    comparison_value: Optional[float] = None
    metadata: Dict = None

class AdvancedAnalytics:
    """Advanced analytics engine for healthcare insights"""
    
    @staticmethod
    def get_patient_flow_analytics(days: int = 30) -> Dict:
        """Analyze patient flow patterns"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Daily patient visits
        daily_visits = db.session.query(
            func.date(Visit.visit_date).label('date'),
            func.count(Visit.id).label('count')
        ).filter(
            Visit.visit_date.between(start_date, end_date)
        ).group_by(func.date(Visit.visit_date)).all()
        
        # Peak hours analysis
        hourly_visits = db.session.query(
            func.extract('hour', Visit.visit_date).label('hour'),
            func.count(Visit.id).label('count')
        ).filter(
            Visit.visit_date.between(start_date, end_date)
        ).group_by(func.extract('hour', Visit.visit_date)).all()
        
        # Visit type distribution
        visit_types = db.session.query(
            Visit.visit_type,
            func.count(Visit.id).label('count')
        ).filter(
            Visit.visit_date.between(start_date, end_date)
        ).group_by(Visit.visit_type).all()
        
        return {
            'daily_visits': [{'date': str(d.date), 'count': d.count} for d in daily_visits],
            'peak_hours': [{'hour': int(h.hour), 'count': h.count} for h in hourly_visits],
            'visit_distribution': [{'type': v.visit_type, 'count': v.count} for v in visit_types],
            'period': f"{days} days",
            'total_visits': sum([v.count for v in daily_visits])
        }
    
    @staticmethod
    def get_revenue_analytics(days: int = 30) -> Dict:
        """Comprehensive revenue analysis"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Daily revenue
        daily_revenue = db.session.query(
            func.date(Billing.created_at).label('date'),
            func.sum(Billing.total_amount).label('revenue')
        ).filter(
            Billing.created_at.between(start_date, end_date),
            Billing.status == 'paid'
        ).group_by(func.date(Billing.created_at)).all()
        
        # Revenue by service type
        service_revenue = db.session.query(
            Billing.service_type,
            func.sum(Billing.total_amount).label('revenue'),
            func.count(Billing.id).label('transactions')
        ).filter(
            Billing.created_at.between(start_date, end_date),
            Billing.status == 'paid'
        ).group_by(Billing.service_type).all()
        
        # Outstanding payments
        outstanding = db.session.query(
            func.sum(Billing.total_amount).label('amount'),
            func.count(Billing.id).label('count')
        ).filter(
            Billing.status.in_(['pending', 'overdue'])
        ).first()
        
        total_revenue = sum([r.revenue or 0 for r in daily_revenue])
        
        return {
            'daily_revenue': [{'date': str(r.date), 'revenue': float(r.revenue or 0)} for r in daily_revenue],
            'service_breakdown': [
                {
                    'service': s.service_type,
                    'revenue': float(s.revenue or 0),
                    'transactions': s.transactions
                } for s in service_revenue
            ],
            'outstanding_payments': {
                'amount': float(outstanding.amount or 0),
                'count': outstanding.count or 0
            },
            'total_revenue': total_revenue,
            'period': f"{days} days"
        }
    
    @staticmethod
    def get_clinical_quality_metrics(days: int = 30) -> Dict:
        """Calculate clinical quality indicators"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Average length of stay for admissions
        avg_los = db.session.query(
            func.avg(
                func.extract('day', Admission.discharge_date - Admission.admission_date)
            ).label('avg_los')
        ).filter(
            Admission.admission_date.between(start_date, end_date),
            Admission.discharge_date.isnot(None)
        ).scalar()
        
        # Readmission rates (within 30 days)
        readmissions = db.session.query(
            func.count(Admission.id).label('readmissions')
        ).filter(
            and_(
                Admission.admission_date.between(start_date, end_date),
                Admission.id.in_(
                    db.session.query(Admission.id).filter(
                        Admission.client_id.in_(
                            db.session.query(Admission.client_id).filter(
                                Admission.discharge_date.between(
                                    start_date - timedelta(days=30), 
                                    start_date
                                )
                            )
                        )
                    )
                )
            )
        ).scalar()
        
        # Lab turnaround times
        lab_turnaround = db.session.query(
            func.avg(
                func.extract('hour', LabOrder.result_date - LabOrder.created_at)
            ).label('avg_turnaround')
        ).filter(
            LabOrder.created_at.between(start_date, end_date),
            LabOrder.result_date.isnot(None)
        ).scalar()
        
        # Prescription adherence (estimating based on refills)
        prescription_metrics = db.session.query(
            func.count(Prescription.id).label('total_prescriptions'),
            func.count(
                func.nullif(Prescription.dispensed, False)
            ).label('dispensed_prescriptions')
        ).filter(
            Prescription.prescribed_date.between(start_date, end_date)
        ).first()
        
        adherence_rate = 0
        if prescription_metrics.total_prescriptions > 0:
            adherence_rate = (prescription_metrics.dispensed_prescriptions / 
                            prescription_metrics.total_prescriptions) * 100
        
        return {
            'average_length_of_stay': round(avg_los or 0, 2),
            'readmission_rate': readmissions or 0,
            'lab_turnaround_hours': round(lab_turnaround or 0, 2),
            'prescription_adherence_rate': round(adherence_rate, 2),
            'period': f"{days} days"
        }
    
    @staticmethod
    def get_operational_efficiency_metrics() -> Dict:
        """Calculate operational efficiency indicators"""
        
        # Bed occupancy rate
        total_beds = db.session.query(func.count(Bed.id)).filter(
            Bed.status == 'available'
        ).scalar()
        
        occupied_beds = db.session.query(func.count(Admission.id)).filter(
            Admission.discharge_date.is_(None)
        ).scalar()
        
        occupancy_rate = (occupied_beds / total_beds * 100) if total_beds > 0 else 0
        
        # Staff utilization by department
        staff_utilization = db.session.query(
            Department.name,
            func.count(Staff.id).label('staff_count'),
            func.count(Appointment.id).label('appointments_today')
        ).join(Staff, Department.id == Staff.department_id
        ).outerjoin(
            Appointment, 
            and_(
                Staff.id == Appointment.doctor_id,
                func.date(Appointment.date) == func.current_date()
            )
        ).group_by(Department.name).all()
        
        # Equipment/Inventory status
        low_stock_items = db.session.query(
            func.count(Inventory.id)
        ).filter(
            Inventory.quantity_in_stock <= Inventory.minimum_stock_level,
            Inventory.is_active == True
        ).scalar()
        
        total_inventory_items = db.session.query(
            func.count(Inventory.id)
        ).filter(Inventory.is_active == True).scalar()
        
        return {
            'bed_occupancy_rate': round(occupancy_rate, 2),
            'department_utilization': [
                {
                    'department': d.name,
                    'staff_count': d.staff_count,
                    'daily_appointments': d.appointments_today or 0
                } for d in staff_utilization
            ],
            'inventory_status': {
                'low_stock_items': low_stock_items or 0,
                'total_items': total_inventory_items or 0,
                'stock_adequacy_rate': round(
                    ((total_inventory_items - low_stock_items) / total_inventory_items * 100)
                    if total_inventory_items > 0 else 0, 2
                )
            }
        }
    
    @staticmethod
    def get_predictive_insights(days: int = 90) -> Dict:
        """Generate predictive healthcare insights"""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Predict high-risk patients based on visit frequency
        high_risk_patients = db.session.query(
            Client.id,
            Client.first_name,
            Client.last_name,
            func.count(Visit.id).label('visit_count'),
            func.count(
                func.distinct(Visit.visit_type)
            ).label('visit_type_variety')
        ).join(Visit, Client.id == Visit.client_id
        ).filter(
            Visit.visit_date.between(start_date, end_date)
        ).group_by(Client.id, Client.first_name, Client.last_name
        ).having(func.count(Visit.id) > 5  # More than 5 visits in period
        ).order_by(func.count(Visit.id).desc()).limit(20).all()
        
        # Resource demand forecasting
        weekly_visits = db.session.query(
            func.extract('week', Visit.visit_date).label('week'),
            func.count(Visit.id).label('count')
        ).filter(
            Visit.visit_date.between(start_date, end_date)
        ).group_by(func.extract('week', Visit.visit_date)).all()
        
        # Calculate trend for next period prediction
        if len(weekly_visits) >= 4:
            recent_avg = sum([v.count for v in weekly_visits[-4:]]) / 4
            previous_avg = sum([v.count for v in weekly_visits[-8:-4]]) / 4 if len(weekly_visits) >= 8 else recent_avg
            trend_percentage = ((recent_avg - previous_avg) / previous_avg * 100) if previous_avg > 0 else 0
        else:
            trend_percentage = 0
            recent_avg = 0
        
        return {
            'high_risk_patients': [
                {
                    'patient_id': p.id,
                    'name': f"{p.first_name} {p.last_name}",
                    'visit_count': p.visit_count,
                    'visit_variety': p.visit_type_variety
                } for p in high_risk_patients
            ],
            'demand_forecast': {
                'current_weekly_average': round(recent_avg, 1),
                'trend_percentage': round(trend_percentage, 2),
                'predicted_next_week': round(recent_avg * (1 + trend_percentage/100), 1)
            },
            'recommendations': AdvancedAnalytics._generate_recommendations(
                high_risk_patients, trend_percentage
            )
        }
    
    @staticmethod
    def _generate_recommendations(high_risk_patients, trend_percentage) -> List[str]:
        """Generate actionable recommendations based on analytics"""
        recommendations = []
        
        if len(high_risk_patients) > 10:
            recommendations.append(
                "Consider implementing a care management program for high-frequency patients"
            )
        
        if trend_percentage > 15:
            recommendations.append(
                "Significant increase in demand detected. Consider staff scheduling adjustments"
            )
        elif trend_percentage < -15:
            recommendations.append(
                "Decreasing demand trend. Opportunity to focus on preventive care programs"
            )
        
        recommendations.extend([
            "Review inventory levels for high-demand items",
            "Analyze peak hours to optimize appointment scheduling",
            "Consider telemedicine options for routine follow-ups"
        ])
        
        return recommendations
    
    @staticmethod
    def generate_comprehensive_report(days: int = 30) -> Dict:
        """Generate a comprehensive analytics report"""
        return {
            'report_date': datetime.utcnow().isoformat(),
            'period': f"{days} days",
            'patient_flow': AdvancedAnalytics.get_patient_flow_analytics(days),
            'revenue': AdvancedAnalytics.get_revenue_analytics(days),
            'clinical_quality': AdvancedAnalytics.get_clinical_quality_metrics(days),
            'operational_efficiency': AdvancedAnalytics.get_operational_efficiency_metrics(),
            'predictive_insights': AdvancedAnalytics.get_predictive_insights(days * 3)
        }
