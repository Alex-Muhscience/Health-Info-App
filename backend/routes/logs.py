from urllib import request

from flask import Blueprint, jsonify
from sqlalchemy import or_, and_, func, extract
from datetime import datetime, timedelta
from backend.models import ActivityLog, User
from backend import db
from backend.schemas import activity_logs_schema
from backend.utils.auth import admin_required
from backend.utils.pagination import paginate_query
from backend.utils.helpers import DateUtils

logs_bp = Blueprint('logs', __name__, url_prefix='/api/logs')


@logs_bp.route('/', methods=['GET'])
@admin_required
def get_activity_logs(current_user):
    """
    Get system activity logs
    ---
    tags:
      - Logs
    security:
      - BearerAuth: []
    parameters:
      - name: action
        in: query
        type: string
        required: false
      - name: user_id
        in: query
        type: integer
        required: false
      - name: entity_type
        in: query
        type: string
        required: false
      - name: entity_id
        in: query
        type: integer
        required: false
      - name: date_range
        in: query
        type: string
        required: false
        description: Date range in format 'YYYY-MM-DD,YYYY-MM-DD'
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: per_page
        in: query
        type: integer
        required: false
        default: 50
    responses:
      200:
        description: Activity logs
        schema:
          type: object
          properties:
            logs:
              type: array
              items:
                $ref: '#/definitions/ActivityLog'
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      403:
        description: Forbidden
    """
    query = ActivityLog.query

    # Action filter
    from urllib import request
    if 'action' in request.args:
        query = query.filter(ActivityLog.action == request.args['action'])

    # User filter
    if 'user_id' in request.args:
        query = query.filter(ActivityLog.user_id == request.args['user_id'])

    # Entity filter
    if 'entity_type' in request.args and 'entity_id' in request.args:
        query = query.filter(
            and_(
                ActivityLog.entity_type == request.args['entity_type'],
                ActivityLog.entity_id == request.args['entity_id']
            )
        )

    # Date range filter
    if 'date_range' in request.args:
        start_date, end_date = DateUtils.parse_date_range(request.args['date_range'])
        query = query.filter(
            and_(
                ActivityLog.timestamp >= start_date,
                ActivityLog.timestamp <= end_date
            )
        )

    return paginate_query(
        query.order_by(ActivityLog.timestamp.desc()),
        activity_logs_schema,
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 50, type=int)
    )


@logs_bp.route('/summary', methods=['GET'])
@admin_required
def get_log_summary(current_user):
    """
    Get activity log summary
    ---
    tags:
      - Logs
    security:
      - BearerAuth: []
    parameters:
      - name: days
        in: query
        type: integer
        required: false
        default: 7
    responses:
      200:
        description: Activity summary
        schema:
          $ref: '#/definitions/ActivitySummary'
      403:
        description: Forbidden
    """
    days = request.args.get('days', 7, type=int)
    cutoff_date = datetime.utcnow() - timedelta(days=days)

    # Top actions
    top_actions = db.session.query(
        ActivityLog.action,
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= cutoff_date
    ).group_by(
        ActivityLog.action
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(5).all()

    # Top users
    top_users = db.session.query(
        User.username,
        func.count(ActivityLog.id).label('count')
    ).join(
        ActivityLog,
        User.id == ActivityLog.user_id
    ).filter(
        ActivityLog.timestamp >= cutoff_date
    ).group_by(
        User.username
    ).order_by(
        func.count(ActivityLog.id).desc()
    ).limit(5).all()

    # Activity by hour
    activity_by_hour = db.session.query(
        extract('hour', ActivityLog.timestamp).label('hour'),
        func.count(ActivityLog.id).label('count')
    ).filter(
        ActivityLog.timestamp >= cutoff_date
    ).group_by(
        'hour'
    ).order_by(
        'hour'
    ).all()

    return jsonify({
        'top_actions': [
            {'action': action, 'count': count}
            for action, count in top_actions
        ],
        'top_users': [
            {'username': username, 'count': count}
            for username, count in top_users
        ],
        'activity_by_hour': [
            {'hour': hour, 'count': count}
            for hour, count in activity_by_hour
        ],
        'time_period': {
            'start': cutoff_date.isoformat(),
            'end': datetime.utcnow().isoformat(),
            'days': days
        }
    })