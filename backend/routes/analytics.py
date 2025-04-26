from datetime import datetime, timedelta

from flask import Blueprint, jsonify
from sqlalchemy import func, extract, and_

from backend import db
from backend.models import Client, Program, Visit, ClientProgram
from backend.schemas import (
    program_schema
)
from backend.utils.auth import token_required

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')


@analytics_bp.route('/overview', methods=['GET'])
@token_required
def get_dashboard_data(current_user):
    """
    Get dashboard overview metrics
    ---
    tags:
      - Analytics
    security:
      - BearerAuth: []
    responses:
      200:
        description: Dashboard metrics
        schema:
          $ref: '#/definitions/DashboardMetrics'
    """
    # Date ranges for analytics
    today = datetime.utcnow().date()
    last_30_days = today - timedelta(days=30)
    last_60_days = today - timedelta(days=60)
    current_year = today.year

    # Client analytics
    total_clients = Client.query.count()
    new_clients = Client.query.filter(Client.created_at >= last_30_days).count()

    # Client growth calculation
    previous_clients = Client.query.filter(
        and_(
            Client.created_at >= last_60_days,
            Client.created_at < last_30_days
        )
    ).count()

    client_growth = 0
    if previous_clients > 0:
        client_growth = round(((new_clients - previous_clients) / previous_clients) * 100, 1)

    # Program analytics
    active_programs = Program.query.filter_by(is_active=True).count()

    # Program distribution with enrollment counts
    program_dist = db.session.query(
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

    # Monthly client growth
    monthly_growth = db.session.query(
        extract('month', Client.created_at).label('month'),
        func.count(Client.id).label('count')
    ).filter(
        extract('year', Client.created_at) == current_year
    ).group_by(
        'month'
    ).order_by(
        'month'
    ).all()

    # Visit statistics
    completed_visits = Visit.query.filter(
        Visit.status == 'completed',
        func.date(Visit.visit_date) == today
    ).count()

    scheduled_visits = Visit.query.filter(
        Visit.status == 'scheduled',
        Visit.visit_date >= datetime.utcnow()
    ).count()

    return jsonify({
        'total_clients': total_clients,
        'new_clients': new_clients,
        'client_growth': client_growth,
        'active_programs': active_programs,
        'program_distribution': [
            {'name': name, 'enrollments': count}
            for name, count in program_dist
        ],
        'monthly_growth': [
            {'month': month, 'count': count}
            for month, count in monthly_growth
        ],
        'visits': {
            'completed_today': completed_visits,
            'upcoming': scheduled_visits
        },
        'time_period': {
            'start': last_30_days.isoformat(),
            'end': today.isoformat()
        }
    })


@analytics_bp.route('/programs/<int:program_id>', methods=['GET'])
@token_required
def program_analytics(current_user, program_id):
    """
    Get analytics for specific program
    ---
    tags:
      - Analytics
    security:
      - BearerAuth: []
    parameters:
      - name: program_id
        in: path
        type: integer
        required: true
    responses:
      200:
        description: Program analytics
        schema:
          $ref: '#/definitions/ProgramAnalytics'
      404:
        description: Program not found
    """
    program = Program.query.get_or_404(program_id)

    # Enrollment stats by month
    enrollments_by_month = db.session.query(
        extract('month', ClientProgram.enrollment_date).label('month'),
        func.count(ClientProgram.id).label('count')
    ).filter(
        ClientProgram.program_id == program_id
    ).group_by(
        'month'
    ).order_by(
        'month'
    ).all()

    # Completion rates
    total_enrollments = ClientProgram.query.filter_by(
        program_id=program_id
    ).count()

    completed_enrollments = ClientProgram.query.filter(
        and_(
            ClientProgram.program_id == program_id,
            ClientProgram.status == 'completed'
        )
    ).count()

    completion_rate = 0
    if total_enrollments > 0:
        completion_rate = round((completed_enrollments / total_enrollments) * 100, 1)

    # Active clients
    active_clients = ClientProgram.query.filter(
        and_(
            ClientProgram.program_id == program_id,
            ClientProgram.status == 'active'
        )
    ).count()

    return jsonify({
        'program': program_schema.dump(program),
        'enrollments_by_month': [
            {'month': month, 'count': count}
            for month, count in enrollments_by_month
        ],
        'completion_rate': completion_rate,
        'active_clients': active_clients,
        'total_enrollments': total_enrollments
    })


@analytics_bp.route('/clients/geographic', methods=['GET'])
@token_required
def client_geographic():
    """
    Get client geographic distribution
    ---
    tags:
      - Analytics
    security:
      - BearerAuth: []
    responses:
      200:
        description: Geographic distribution
        schema:
          type: array
          items:
            $ref: '#/definitions/GeographicDistribution'
    """
    # Requires Client model to have city, state, country fields
    geographic_dist = db.session.query(
        Client.state,
        Client.country,
        func.count(Client.id).label('count')
    ).filter(
        Client.state.isnot(None),
        Client.country.isnot(None)
    ).group_by(
        Client.state,
        Client.country
    ).all()

    return jsonify([
        {
            'state': state,
            'country': country,
            'count': count
        }
        for state, country, count in geographic_dist
    ])