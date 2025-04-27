from functools import wraps
from flask import request, jsonify, current_app
import jwt
from jwt import ExpiredSignatureError, InvalidTokenError
from backend.models import User
from backend import db
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def token_required(f):
    """Base token authentication decorator"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # Get token from header
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split()[1]

        if not token:
            logger.warning("Missing authentication token")
            return jsonify({'error': 'Authentication token is missing'}), 401

        try:
            # Decode token
            data = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=['HS256']
            )

            # Verify required claims
            required_claims = ['sub', 'exp', 'iat', 'role']
            if not all(claim in data for claim in required_claims):
                logger.warning(f"Missing required claims in token: {data}")
                return jsonify({'error': 'Invalid token claims'}), 401

            # Verify token expiration
            if datetime.utcnow() > datetime.fromtimestamp(data['exp']):
                raise ExpiredSignatureError("Token has expired")

            # Get user from database
            current_user = User.query.filter_by(
                id=data['sub'],
                is_active=True
            ).first()

            if not current_user:
                logger.warning(f"User not found for token: {data['sub']}")
                return jsonify({'error': 'User not found'}), 404

            # Verify role hasn't changed
            if current_user.role != data['role']:
                logger.warning(f"Role mismatch for user {current_user.id}")
                return jsonify({'error': 'Token invalid - role changed'}), 401

            # Attach user to request
            request.current_user = current_user

        except ExpiredSignatureError:
            logger.warning("Expired token attempt")
            return jsonify({'error': 'Token has expired'}), 401
        except InvalidTokenError as e:
            logger.warning(f"Invalid token: {str(e)}")
            return jsonify({'error': 'Invalid token'}), 401
        except Exception as e:
            logger.error(f"Token validation error: {str(e)}", exc_info=True)
            return jsonify({'error': 'Authentication failed'}), 401

        return f(request.current_user, *args, **kwargs)

    return decorated

def roles_required(*required_roles):
    """Role-based access control decorator"""
    def decorator(f):
        @wraps(f)
        @token_required
        def decorated(current_user, *args, **kwargs):
            if current_user.role not in required_roles:
                logger.warning(
                    f"Role violation: User {current_user.id} "
                    f"attempted {request.endpoint} (required: {required_roles})"
                )
                return jsonify({
                    'error': 'Insufficient permissions',
                    'required_roles': required_roles,
                    'your_role': current_user.role
                }), 403
            return f(current_user, *args, **kwargs)
        return decorated
    return decorator

def admin_required(f):
    """Convenience decorator for admin-only endpoints"""
    return roles_required('admin')(f)