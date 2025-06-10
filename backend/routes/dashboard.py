from flask import Blueprint, jsonify, request
from backend import db
from backend.models import Client, Program, Visit, Appointment, ClientProgram
from datetime import datetime, timedelta
from sqlalchemy import func, and_

system_bp = Blueprint('system', __name__)


@system_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics and metrics"""
    try:
        # Calculate totals
        total_clients = Client.query.filter_by(is_active=True).count()
        total_programs = Program.query.filter_by(is_active=True).count()

        # Time-based calculations
        now = datetime.utcnow()
        last_30_days = now - timedelta(days=30)
        last_7_days = now - timedelta(days=7)

        # Recent activity
        new_clients = Client.query.filter(
            Client.created_at >= last_30_days,
            Client.is_active == True
        ).count()

        recent_visits = Visit.query.filter(
            Visit.visit_date >= last_7_days
        ).count()

        upcoming_appointments = Appointment.query.filter(
            Appointment.date >= now,
            Appointment.date <= now + timedelta(days=7),
            Appointment.status == 'scheduled'
        ).count()

        # Program enrollment stats
        popular_program = db.session.query(
            Program.name,
            func.count(ClientProgram.id).label('enrollments')
        ).join(ClientProgram).group_by(Program.id).order_by(
            func.count(ClientProgram.id).desc()
        ).first()

        stats = {
            "total_clients": total_clients,
            "active_programs": total_programs,
            "new_clients_last_30_days": new_clients,
            "visits_last_7_days": recent_visits,
            "upcoming_appointments": upcoming_appointments,
            "most_popular_program": {
                "name": popular_program[0] if popular_program else None,
                "enrollments": popular_program[1] if popular_program else 0
            }
        }

        return jsonify(stats), 200
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