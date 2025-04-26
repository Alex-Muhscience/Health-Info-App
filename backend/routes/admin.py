from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import func, or_, and_
from datetime import datetime
from backend.models import User, Client, Program, Visit, ActivityLog, ClientProgram
from backend import db
from backend.schemas import (
    user_schema,
    users_schema,
    activity_logs_schema,
    SystemStatsSchema
)
from backend.utils.auth import admin_required
from backend.utils.validators import Validators
from backend.utils.pagination import paginate_query
from backend.utils.export import generate_user_report
from backend.utils.helpers import DateUtils


admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')


@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """
    Get all users with filtering options
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    parameters:
      - name: role
        in: query
        type: string
        enum: [admin, practitioner, client]
        required: false
      - name: active
        in: query
        type: boolean
        required: false
      - name: search
        in: query
        type: string
        required: false
      - name: page
        in: query
        type: integer
        required: false
        default: 1
      - name: per_page
        in: query
        type: integer
        required: false
        default: 20
    responses:
      200:
        description: List of users
        schema:
          type: object
          properties:
            users:
              type: array
              items:
                $ref: '#/definitions/User'
            total:
              type: integer
            pages:
              type: integer
            current_page:
              type: integer
      403:
        description: Forbidden
    """
    query = User.query

    # Role filter
    if 'role' in request.args:
        query = query.filter(User.role == request.args['role'])

    # Active status filter
    if 'active' in request.args:
        active = request.args['active'].lower() == 'true'
        query = query.filter(User.is_active == active)

    # Search filter
    if 'search' in request.args:
        search = f"%{request.args['search']}%"
        query = query.filter(
            or_(
                User.username.ilike(search),
                User.email.ilike(search),
                User.first_name.ilike(search),
                User.last_name.ilike(search)
            )
        )

    return paginate_query(
        query.order_by(User.created_at.desc()),
        users_schema,
        page=request.args.get('page', 1, type=int),
        per_page=request.args.get('per_page', 20, type=int)
    )


@admin_bp.route('/users/<int:user_id>', methods=['GET', 'PUT', 'DELETE'])
@admin_required
def manage_user(current_user, user_id):
    user = User.query.get_or_404(user_id)

    if request.method == 'GET':
        """
        Get user details
        ---
        tags:
          - Admin
        security:
          - BearerAuth: []
        parameters:
          - name: user_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: User details
            schema:
              $ref: '#/definitions/User'
          403:
            description: Forbidden
          404:
            description: User not found
        """
        return jsonify(user_schema.dump(user))

    elif request.method == 'PUT':
        """
        Update user details
        ---
        tags:
          - Admin
        security:
          - BearerAuth: []
        parameters:
          - name: user_id
            in: path
            type: integer
            required: true
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/UserUpdate'
        responses:
          200:
            description: User updated
            schema:
              $ref: '#/definitions/User'
          400:
            description: Invalid input
          403:
            description: Forbidden
          404:
            description: User not found
        """
        data = request.get_json()

        validation = Validators.validate_user_data(data, update=True)
        if not validation['valid']:
            return jsonify({'errors': validation['errors']}), 400

        # Prevent modifying own admin status
        if user.id == current_user.id and 'role' in data and data['role'] != 'admin':
            return jsonify({'message': 'Cannot modify your own admin status'}), 400

        updateable_fields = [
            'username', 'email', 'first_name', 'last_name',
            'role', 'is_active', 'phone', 'address'
        ]

        for field in updateable_fields:
            if field in data:
                setattr(user, field, data[field])

        user.updated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({
            'message': 'User updated successfully',
            'user': user_schema.dump(user)
        })

    elif request.method == 'DELETE':
        """
        Deactivate user (soft delete)
        ---
        tags:
          - Admin
        security:
          - BearerAuth: []
        parameters:
          - name: user_id
            in: path
            type: integer
            required: true
        responses:
          200:
            description: User deactivated
          403:
            description: Forbidden
          404:
            description: User not found
        """
        if user.id == current_user.id:
            return jsonify({'message': 'Cannot deactivate yourself'}), 400

        user.is_active = False
        user.deactivated_at = datetime.utcnow()
        db.session.commit()

        return jsonify({'message': 'User deactivated successfully'})


@admin_bp.route('/users/export', methods=['GET'])
@admin_required
def export_users(current_user):
    """
    Export user data to CSV
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    responses:
      200:
        description: CSV file
        schema:
          type: file
      403:
        description: Forbidden
    """
    users = User.query.all()
    return generate_user_report(users)


@admin_bp.route('/stats', methods=['GET'])
@admin_required
def system_statistics(current_user):
    """
    Get detailed system statistics
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    responses:
      200:
        description: System statistics
        schema:
          $ref: '#/definitions/SystemStats'
      403:
        description: Forbidden
    """
    stats = {
        'users': {
            'total': User.query.count(),
            'active': User.query.filter_by(is_active=True).count(),
            'by_role': dict(db.session.query(User.role, func.count(User.id))
                            .group_by(User.role).all())
        },
        'clients': {
            'total': Client.query.count(),
            'active': Client.query.filter_by(is_active=True).count(),
            'new_today': Client.query.filter(
                func.date(Client.created_at) == datetime.utcnow().date()
            ).count()
        },
        'programs': {
            'total': Program.query.count(),
            'active': Program.query.filter_by(is_active=True).count(),
            'popular': Program.query.join(ClientProgram)
            .group_by(Program.id)
            .order_by(func.count(ClientProgram.id).desc())
            .limit(3).all()
        },
        'visits': {
            'total': Visit.query.count(),
            'completed_today': Visit.query.filter(
                func.date(Visit.visit_date) == datetime.utcnow().date(),
                Visit.status == 'completed'
            ).count(),
            'upcoming': Visit.query.filter(
                Visit.visit_date > datetime.utcnow(),
                Visit.status == 'scheduled'
            ).count()
        }
    }

    return jsonify(SystemStatsSchema.dump(stats))


@admin_bp.route('/activity', methods=['GET'])
@admin_required
def activity_logs(current_user):
    """
    Get system activity logs
    ---
    tags:
      - Admin
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
    if 'action' in request.args:
        query = query.filter(ActivityLog.action == request.args['action'])

    # User filter
    if 'user_id' in request.args:
        query = query.filter(ActivityLog.user_id == request.args['user_id'])

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


@admin_bp.route('/config', methods=['GET', 'PUT'])
@admin_required
def system_config(current_user):
    if request.method == 'GET':
        """
        Get system configuration
        ---
        tags:
          - Admin
        security:
          - BearerAuth: []
        responses:
          200:
            description: System configuration
            schema:
              $ref: '#/definitions/SystemConfig'
          403:
            description: Forbidden
        """
        config = {
            'maintenance_mode': current_app.config.get('MAINTENANCE_MODE', False),
            'user_registration': current_app.config.get('ALLOW_USER_REGISTRATION', True),
            'password_policy': {
                'min_length': current_app.config.get('PASSWORD_MIN_LENGTH', 8),
                'require_upper': current_app.config.get('PASSWORD_REQUIRE_UPPER', True),
                'require_lower': current_app.config.get('PASSWORD_REQUIRE_LOWER', True),
                'require_number': current_app.config.get('PASSWORD_REQUIRE_NUMBER', True),
                'require_special': current_app.config.get('PASSWORD_REQUIRE_SPECIAL', True)
            }
        }
        return jsonify(config)

    elif request.method == 'PUT':
        """
        Update system configuration
        ---
        tags:
          - Admin
        security:
          - BearerAuth: []
        parameters:
          - name: body
            in: body
            required: true
            schema:
              $ref: '#/definitions/SystemConfigUpdate'
        responses:
          200:
            description: Configuration updated
          400:
            description: Invalid input
          403:
            description: Forbidden
        """
        data = request.get_json()

        # Update runtime config (persistent changes would need to be saved to database or config file)
        if 'maintenance_mode' in data:
            current_app.config['MAINTENANCE_MODE'] = bool(data['maintenance_mode'])
        if 'user_registration' in data:
            current_app.config['ALLOW_USER_REGISTRATION'] = bool(data['user_registration'])

        return jsonify({'message': 'Configuration updated successfully'})