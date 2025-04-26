from datetime import datetime, timedelta
from flask import Blueprint, jsonify, current_app
from sqlalchemy import func, and_
from backend import db
from backend.models import Client, Program, ClientProgram
from backend.utils import limiter
from backend.utils.auth import token_required, admin_required
from backend.utils.limiter import RateLimiter

system_bp = Blueprint('system', __name__, url_prefix='/api')


@system_bp.route('/health', methods=['GET'])
@RateLimiter.limit(10 )
def health_check():
    """
    System health check endpoint
    ---
    tags:
      - System
    responses:
      200:
        description: System status
        schema:
          type: object
          properties:
            status:
              type: string
            database:
              type: boolean
            timestamp:
              type: string
    """
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        db_status = True
    except Exception:
        db_status = False

    return jsonify({
        'status': 'healthy',
        'database': db_status,
        'timestamp': datetime.utcnow().isoformat(),
        'version': current_app.config.get('APP_VERSION', '1.0.0')
    })


@system_bp.route('/stats', methods=['GET'])
@token_required
def get_system_stats(current_user):
    """
    Get system statistics
    ---
    tags:
      - System
    security:
      - BearerAuth: []
    responses:
      200:
        description: System statistics
        schema:
          type: object
          properties:
            total_clients:
              type: integer
            active_programs:
              type: integer
            client_growth:
              type: number
            recent_activity:
              type: object
    """
    # Calculate time periods
    now = datetime.utcnow()
    today = now.date()
    thirty_days_ago = now - timedelta(days=30)
    sixty_days_ago = now - timedelta(days=60)

    # Client statistics
    total_clients = Client.query.count()

    # New clients in last 30 days
    new_clients = Client.query.filter(
        Client.created_at >= thirty_days_ago
    ).count()

    # Client growth calculation
    previous_period_clients = Client.query.filter(
        and_(
            Client.created_at >= sixty_days_ago,
            Client.created_at < thirty_days_ago
        )
    ).count()

    client_growth = 0
    if previous_period_clients > 0:
        client_growth = round(
            ((new_clients - previous_period_clients) / previous_period_clients) * 100,
            1
        )

    # Program statistics
    active_programs = Program.query.filter_by(is_active=True).count()

    # Program enrollment stats
    program_stats = db.session.query(
        Program.name,
        func.count(ClientProgram.id).label('enrollments')
    ).join(
        ClientProgram,
        Program.id == ClientProgram.program_id,
        isouter=True
    ).filter(
        Program.is_active == True
    ).group_by(
        Program.name
    ).all()

    # Today's activity
    todays_registrations = Client.query.filter(
        func.date(Client.created_at) == today
    ).count()

    todays_enrollments = ClientProgram.query.filter(
        func.date(ClientProgram.enrollment_date) == today
    ).count()

    return jsonify({
        'total_clients': total_clients,
        'active_programs': active_programs,
        'client_growth': client_growth,
        'program_distribution': [
            {'name': name, 'enrollments': count}
            for name, count in program_stats
        ],
        'recent_activity': {
            'registrations': todays_registrations,
            'enrollments': todays_enrollments
        },
        'time_period': {
            'start': thirty_days_ago.isoformat(),
            'end': now.isoformat()
        }
    })


@system_bp.route('/config', methods=['GET'])
@token_required
@admin_required
def get_system_config(current_user):
    """
    Get system configuration (admin only)
    ---
    tags:
      - System
    security:
      - BearerAuth: []
    responses:
      200:
        description: System configuration
      403:
        description: Forbidden
    """
    return jsonify({
        'settings': {
            'max_file_size': current_app.config.get('MAX_FILE_SIZE'),
            'allowed_extensions': current_app.config.get('ALLOWED_EXTENSIONS'),
            'maintenance_mode': current_app.config.get('MAINTENANCE_MODE', False)
        }
    })