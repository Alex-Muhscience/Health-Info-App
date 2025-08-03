from flask import Blueprint, request, jsonify, current_app
from backend import db, jwt
from backend.models import User
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt as pyjwt
from flask_jwt_extended import create_access_token, create_refresh_token, get_jwt_identity, jwt_required
from backend.schemas import user_schema
from backend.utils.auth import token_required, admin_required
from backend.utils.helpers import validate_email, validate_password
from backend import limiter
import logging

auth_bp = Blueprint('auth', __name__)
logger = logging.getLogger(__name__)


@auth_bp.route('/register', methods=['POST'])
@admin_required
@limiter.limit("5 per minute")
def register(current_user):
    """Register a new user (admin only)"""
    try:
        data = request.get_json()

        # Validate input
        required_fields = ['username', 'email', 'password', 'role']
        if not all(field in data for field in required_fields):
            logger.warning("Missing required fields in registration")
            return jsonify({'error': 'Missing required fields'}), 400

        # Check for existing user
        if User.query.filter_by(username=data['username']).first():
            logger.warning(f"Username already exists: {data['username']}")
            return jsonify({'error': 'Username already exists'}), 409

        if User.query.filter_by(email=data['email']).first():
            logger.warning(f"Email already exists: {data['email']}")
            return jsonify({'error': 'Email already exists'}), 409

        if not validate_email(data['email']):
            logger.warning(f"Invalid email format: {data['email']}")
            return jsonify({'error': 'Invalid email format'}), 400

        if not validate_password(data['password']):
            logger.warning("Password validation failed")
            return jsonify({
                'error': 'Password must be 8+ chars with mix of letters, numbers and symbols'
            }), 400

        # Create new user
        hashed_password = generate_password_hash(
            data['password'],
            method=current_app.config['PASSWORD_HASH_SCHEME'],
            salt_length=current_app.config['PASSWORD_SALT_LENGTH']
        )

        new_user = User(
            username=data['username'],
            email=data['email'],
            password=hashed_password,
            role=data['role'].lower(),
            is_active=True
        )

        db.session.add(new_user)
        db.session.commit()

        logger.info(f"New user created: {data['username']}")
        return jsonify({
            'message': 'User created successfully',
            'user': user_schema.dump(new_user)
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"Registration failed: {str(e)}", exc_info=True)
        return jsonify({'error': 'User registration failed'}), 500




@auth_bp.route('/login', methods=['POST'])
@limiter.limit("10 per minute")
def login():
    try:
        data = request.get_json()
        if not data or not data.get('username') or not data.get('password'):
            return jsonify({'error': 'Username and password required'}), 400

        user = User.query.filter_by(username=data['username']).first()
        if not user or not check_password_hash(user.password, data['password']):
            return jsonify({'error': 'Invalid credentials'}), 401

        if not user.is_active:
            return jsonify({'error': 'Account disabled'}), 403

        # Use Flask-JWT-Extended's token creation
        access_token = create_access_token(
            identity=user.id,
            additional_claims={'role': user.role}
        )
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user_schema.dump(user)
        }), 200

    except Exception as e:
        logger.error(f"Login error: {str(e)}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500


@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    current_user = get_jwt_identity()
    new_token = create_access_token(
        identity=current_user,
        additional_claims={'role': User.query.get(current_user).role}
    )
    return jsonify(access_token=new_token), 200


@auth_bp.route('/me', methods=['GET'])
@token_required
def get_me(current_user):
    """Get current user profile"""
    try:
        return jsonify(user_schema.dump(current_user)), 200
    except Exception as e:
        logger.error(f"Failed to get user profile: {str(e)}", exc_info=True)
        return jsonify({'error': 'Failed to retrieve user profile'}), 500