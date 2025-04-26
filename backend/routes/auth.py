from flask import Blueprint, request, jsonify, current_app
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from backend.models import User
from backend import db
from backend.schemas import user_schema
from backend.utils.validators import Validators

from backend.utils.auth import token_required

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
            password:
              type: string
            role:
              type: string
              enum: [user, admin]
              default: user
    responses:
      201:
        description: User created
      400:
        description: Invalid input
      409:
        description: User already exists
    """
    data = request.get_json()

    # Validation
    if not data or not all(k in data for k in ['username', 'email', 'password']):
        return jsonify({'message': 'Missing required fields'}), 400

    if not Validators.validate_email(data['email']):
        return jsonify({'message': 'Invalid email format'}), 400

    if not Validators.validate_password(data['password']):
        return jsonify(
            {'message': 'Password must be at least 8 characters with uppercase, lowercase, and numbers'}), 400

    # Check for existing user
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists'}), 409

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists'}), 409

    # Create user
    hashed_password = generate_password_hash(
        data['password'],
        method='pbkdf2:sha256',
        salt_length=16
    )

    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        role=data.get('role', 'user')
    )

    db.session.add(new_user)
    db.session.commit()

    # Generate token
    token = jwt.encode({
        'id': new_user.id,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config.get('JWT_EXPIRATION_HOURS', 1))
    }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'User created successfully',
        'token': token,
        'user': user_schema.dump(new_user)
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user
    ---
    tags:
      - Authentication
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            password:
              type: string
    responses:
      200:
        description: Login successful
      400:
        description: Invalid input
      401:
        description: Invalid credentials
      404:
        description: User not found
    """
    data = request.get_json()

    if not data or not all(k in data for k in ['username', 'password']):
        return jsonify({'message': 'Username and password required'}), 400

    user = User.query.filter_by(username=data['username']).first()
    if not user:
        return jsonify({'message': 'Invalid credentials'}), 401  # Don't reveal user existence

    if not check_password_hash(user.password, data['password']):
        return jsonify({'message': 'Invalid credentials'}), 401

    token = jwt.encode({
        'id': user.id,
        'role': user.role,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config.get('JWT_EXPIRATION_HOURS', 1))
    }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'token': token,
        'user': user_schema.dump(user),
        'expires_in': current_app.config.get('JWT_EXPIRATION_HOURS', 1) * 3600
    })


@auth_bp.route('/refresh', methods=['POST'])
@token_required
def refresh_token(current_user):
    """
    Refresh JWT token
    ---
    tags:
      - Authentication
    security:
      - BearerAuth: []
    responses:
      200:
        description: New token generated
      401:
        description: Unauthorized
    """
    token = jwt.encode({
        'id': current_user.id,
        'role': current_user.role,
        'exp': datetime.utcnow() + timedelta(hours=current_app.config.get('JWT_EXPIRATION_HOURS', 1))
    }, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'token': token,
        'expires_in': current_app.config.get('JWT_EXPIRATION_HOURS', 1) * 3600
    })