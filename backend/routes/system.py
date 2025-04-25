# Create a new file called system.py in your backend routes folder
from datetime import datetime, timedelta

from flask import Blueprint, jsonify

from backend import db
from backend.models import Client, Program
from backend.utils.auth import token_required

system_bp = Blueprint('system', __name__, url_prefix='/api')


@system_bp.route('/stats', methods=['GET'])
@token_required
def get_system_stats(current_user):
    # Get total clients
    total_clients = Client.query.count()

    # Get active programs
    active_programs = Program.query.filter_by(is_active=True).count()
    program_names = [p.name for p in Program.query.filter_by(is_active=True).all()]

    # Calculate client growth (last 30 days vs previous 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    sixty_days_ago = datetime.now() - timedelta(days=60)

    recent_clients = Client.query.filter(Client.created_at >= thirty_days_ago).count()
    previous_clients = Client.query.filter(
        Client.created_at >= sixty_days_ago,
        Client.created_at < thirty_days_ago
    ).count()

    client_growth = 0
    if previous_clients > 0:
        client_growth = round((recent_clients - previous_clients) / previous_clients * 100, 1)

    # Get today's enrollments and registrations
    today = datetime.now().date()
    recent_enrollments = 0  # You'll need to implement this based on your enrollment model
    recent_registrations = Client.query.filter(
        db.func.date(Client.created_at) == today
    ).count()

    return jsonify({
        'total_clients': total_clients,
        'active_programs': active_programs,
        'program_names': program_names,
        'client_growth': client_growth,
        'recent_enrollments': recent_enrollments,
        'recent_registrations': recent_registrations
    })


@system_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})
