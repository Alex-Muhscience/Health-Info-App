from flask import Blueprint, jsonify, request
from backend import db
from backend.models import (
    Client, Program, Visit, Appointment, ClientProgram, Staff, Department,
    MedicalRecord, VitalSigns, Prescription, LabTest, LabOrder, Inventory,
    Bed, Admission, Billing, BillingItem, InsuranceProvider, User
)
from decimal import Decimal
from datetime import datetime, timedelta
from sqlalchemy import func, and_

system_bp = Blueprint('system', __name__)


@system_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get comprehensive system statistics and metrics for dashboard"""
    try:
        # Time calculations
        now = datetime.utcnow()
        today = now.date()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)
        
        # Basic counts
        total_clients = Client.query.filter_by(is_active=True).count()
        total_staff = Staff.query.filter_by(is_active=True).count()
        total_departments = Department.query.filter_by(is_active=True).count()
        
        # Appointments
        total_appointments = Appointment.query.count()
        todays_appointments = Appointment.query.filter(
            func.date(Appointment.date) == today
        ).count()
        
        # Admissions
        active_admissions = Admission.query.filter_by(status='active').count()
        
        # Lab results
        pending_lab_results = LabOrder.query.filter(
            LabOrder.status.in_(['ordered', 'collected', 'processing'])
        ).count()
        
        # Prescriptions
        active_prescriptions = Prescription.query.filter_by(
            status='active', dispensed=False
        ).count()
        
        # Billing
        pending_bills = Billing.query.filter(
            Billing.status.in_(['pending', 'partially_paid'])
        ).count()
        
        # Inventory - low stock alerts
        low_stock_items = Inventory.query.filter(
            Inventory.quantity_in_stock <= Inventory.minimum_stock_level,
            Inventory.is_active == True
        ).count()
        
        # Emergency cases (appointments with high priority)
        emergency_cases = Appointment.query.filter(
            Appointment.priority == 'high',
            Appointment.status == 'scheduled',
            Appointment.date >= now
        ).count()
        
        # Monthly revenue calculation
        current_month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_revenue = db.session.query(
            func.coalesce(func.sum(Billing.paid_amount), 0)
        ).filter(
            Billing.created_at >= current_month_start,
            Billing.status.in_(['paid', 'partially_paid'])
        ).scalar() or 0
        
        # Recent activity counts
        recent_visits = Visit.query.filter(
            Visit.visit_date >= last_7_days
        ).count()
        
        new_clients_this_month = Client.query.filter(
            Client.created_at >= current_month_start,
            Client.is_active == True
        ).count()
        
        # Comprehensive dashboard stats
        dashboard_stats = {
            # Main metrics
            "total_clients": total_clients,
            "todays_appointments": todays_appointments,
            "active_admissions": active_admissions,
            "pending_lab_results": pending_lab_results,
            "active_staff": total_staff,
            "active_prescriptions": active_prescriptions,
            "pending_bills": pending_bills,
            "low_stock_alerts": low_stock_items,
            "emergency_cases": emergency_cases,
            "monthly_revenue": float(monthly_revenue),
            
            # Additional metrics
            "total_appointments": total_appointments,
            "total_departments": total_departments,
            "recent_visits": recent_visits,
            "new_clients_this_month": new_clients_this_month,
            
            # Legacy compatibility
            "total_programs": Program.query.filter_by(is_active=True).count(),
            "visits_last_7_days": recent_visits,
            "upcoming_appointments": Appointment.query.filter(
                Appointment.date >= now,
                Appointment.date <= now + timedelta(days=7),
                Appointment.status == 'scheduled'
            ).count()
        }
        
        return jsonify(dashboard_stats), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@system_bp.route('/appointments', methods=['GET'])
def get_appointments():
    """Get appointments with optional filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        per_page = int(request.args.get('per_page', 10))
        page = int(request.args.get('page', 1))

        # Build query
        query = Appointment.query

        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Appointment.date >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Appointment.date <= end_dt)

        # Order by date descending
        query = query.order_by(Appointment.date.desc())

        # Paginate
        appointments = query.limit(per_page).offset((page - 1) * per_page).all()

        # Format response
        data = []
        for appointment in appointments:
            # Get client name if available
            client_name = "Unknown"
            if appointment.client:
                client_name = f"{appointment.client.first_name} {appointment.client.last_name}"

            data.append({
                "id": appointment.id,
                "date": appointment.date.isoformat() if appointment.date else None,
                "client_id": appointment.client_id,
                "client_name": client_name,
                "reason": appointment.reason or "General appointment",
                "status": appointment.status or "scheduled",
                "created_at": appointment.created_at.isoformat() if appointment.created_at else None
            })

        total = query.count()

        return jsonify({
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@system_bp.route('/visits', methods=['GET'])
def get_visits():
    """Get visits with optional filtering"""
    try:
        # Get query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        per_page = int(request.args.get('per_page', 10))
        page = int(request.args.get('page', 1))

        # Build query
        query = Visit.query

        # Apply date filters
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            query = query.filter(Visit.visit_date >= start_dt)
        
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            query = query.filter(Visit.visit_date <= end_dt)

        # Order by visit date descending
        query = query.order_by(Visit.visit_date.desc())

        # Paginate
        visits = query.limit(per_page).offset((page - 1) * per_page).all()

        # Format response
        data = []
        for visit in visits:
            # Get client name if available
            client_name = "Unknown"
            if visit.client:
                client_name = f"{visit.client.first_name} {visit.client.last_name}"

            data.append({
                "id": visit.id,
                "visit_date": visit.visit_date.isoformat() if visit.visit_date else None,
                "client_id": visit.client_id,
                "client_name": client_name,
                "purpose": visit.purpose or "General visit",
                "visit_type": getattr(visit, 'visit_type', 'consultation'),
                "created_at": visit.created_at.isoformat() if visit.created_at else None
            })

        total = query.count()

        return jsonify({
            "data": data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@system_bp.route('/health', methods=['GET'])
def health_check():
    """System health check endpoint"""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "database": "connected"
        }), 200
    except Exception as e:
        return jsonify({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat(),
            "database": "disconnected"
        }), 500