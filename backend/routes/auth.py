from flask import Blueprint, request, jsonify
from backend.models import User
from backend import db
from werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from backend.schemas import user_schema
from backend.utils.auth import token_required

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'message': 'Username, email and password are required!'}), 400

    if User.query.filter_by(username=data['username']).first():
        return jsonify({'message': 'Username already exists!'}), 400

    if User.query.filter_by(email=data['email']).first():
        return jsonify({'message': 'Email already exists!'}), 400

    hashed_password = generate_password_hash(data['password'], method='sha256')

    new_user = User(
        username=data['username'],
        email=data['email'],
        password=hashed_password,
        role=data.get('role', 'user')
    )

    db.session.add(new_user)
    db.session.commit()

    return jsonify({'message': 'User created successfully!'}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()

    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'message': 'Username and password are required!'}), 400

    user = User.query.filter_by(username=data['username']).first()

    if not user:
        return jsonify({'message': 'User not found!'}), 404

    if check_password_hash(user.password, data['password']):
        token = jwt.encode({
            'id': user.id,
            'exp': datetime.utcnow() + timedelta(hours=1)
        }, 'your-secret-key-here')

        return jsonify({
            'token': token,
            'user': user_schema.dump(user)
        }), 200

    return jsonify({'message': 'Invalid credentials!'}), 401