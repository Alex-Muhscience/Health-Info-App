from flask import Blueprint, jsonify
from backend import db
from backend.models import Client, Program, Visit, Appointment, ClientProgram
from datetime import datetime, timedelta
from sqlalchemy import func

system_bp = Blueprint('system', __name__)


@system_bp.route('/stats', methods=['GET'])
def get_stats():
    """Get system statistics and metrics"""
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