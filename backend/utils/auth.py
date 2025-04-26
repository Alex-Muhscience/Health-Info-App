from datetime import datetime
from functools import wraps
from typing import Callable, Optional

import jwt
from flask import request, jsonify, current_app, g

from backend.models import User


def token_required(roles: Optional[list] = None, allow_expired: bool = False):
    """
    JWT token authentication decorator with optional role-based access control

    Args:
        roles: List of allowed roles (None for any authenticated user)
        allow_expired: Whether to allow expired tokens (for refresh scenarios)
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated(*args, **kwargs):
            token = None

            # Check for token in multiple locations
            if 'x-access-token' in request.headers:
                token = request.headers['x-access-token']
            elif 'Authorization' in request.headers:
                auth_header = request.headers.get('Authorization')
                if auth_header and auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]
            elif request.args.get('token'):
                token = request.args.get('token')

            if not token:
                return jsonify({
                    'error': 'authentication_required',
                    'message': 'Authorization token is missing'
                }), 401

            try:
                # Decode token with options
                decode_options = {'verify_exp': not allow_expired}
                data = jwt.decode(
                    token,
                    current_app.config['JWT_SECRET_KEY'],
                    algorithms=['HS256'],
                    options=decode_options
                )

                # Get current user and store in Flask's g context
                current_user = User.query.filter_by(id=data['id']).first()
                if not current_user:
                    return jsonify({
                        'error': 'user_not_found',
                        'message': 'User associated with this token no longer exists'
                    }), 401

                # Store user in context for downstream use
                g.current_user = current_user

                # Check roles if specified
                if roles and current_user.role not in roles:
                    return jsonify({
                        'error': 'unauthorized',
                        'message': 'You do not have permission to access this resource'
                    }), 403

            except jwt.ExpiredSignatureError:
                return jsonify({
                    'error': 'token_expired',
                    'message': 'Token has expired'
                }), 401
            except jwt.InvalidTokenError:
                return jsonify({
                    'error': 'invalid_token',
                    'message': 'Token is invalid'
                }), 401
            except Exception as e:
                current_app.logger.error(f"Token validation error: {str(e)}")
                return jsonify({
                    'error': 'token_validation_failed',
                    'message': 'Failed to validate token'
                }), 401

            return f(current_user, *args, **kwargs)

        return decorated

    return decorator


def admin_required(f: Callable):
    """
    Decorator that requires admin role
    """
    return token_required(roles=['admin'])(f)


def practitioner_required(f: Callable):
    """
    Decorator that requires practitioner role
    """
    return token_required(roles=['practitioner', 'admin'])(f)


def public_optional(f: Callable):
    """
    Decorator that makes authentication optional
    If user is authenticated, passes user to route, otherwise passes None
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            # Try normal token authentication
            return token_required()(f)(*args, **kwargs)
        except:
            # If authentication fails, call with None
            return f(None, *args, **kwargs)

    return decorated


def fresh_token_required(f: Callable):
    """
    Decorator that requires a fresh token (recently issued)
    Typically used for sensitive operations like password changes
    """

    @wraps(f)
    def decorated(*args, **kwargs):
        # Get token from request
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith("Bearer "):
            return jsonify({
                'error': 'invalid_token',
                'message': 'Fresh token required'
            }), 401

        token = auth_header.split(" ")[1]

        try:
            # Decode without verification to check freshness
            data = jwt.decode(token, options={'verify_signature': False})

            # Check if token was issued more than 15 minutes ago
            issued_at = datetime.fromtimestamp(data['iat'])
            if (datetime.utcnow() - issued_at).total_seconds() > 900:  # 15 minutes
                return jsonify({
                    'error': 'stale_token',
                    'message': 'Fresh token required for this operation'
                }), 401

            # Now verify properly
            return token_required()(f)(*args, **kwargs)

        except Exception as e:
            return jsonify({
                'error': 'token_validation_failed',
                'message': 'Failed to validate token freshness'
            }), 401

    return decorated


def scopes_required(*required_scopes: str):
    """
    Decorator that checks for specific JWT scopes
    """

    def decorator(f: Callable):
        @wraps(f)
        def decorated(*args, **kwargs):
            # Get token from request
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith("Bearer "):
                return jsonify({
                    'error': 'invalid_token',
                    'message': 'Token with scopes required'
                }), 401

            token = auth_header.split(" ")[1]

            try:
                # Decode without verification to check scopes
                data = jwt.decode(token, options={'verify_signature': False})

                # Check if token has all required scopes
                token_scopes = data.get('scopes', [])
                if not all(scope in token_scopes for scope in required_scopes):
                    return jsonify({
                        'error': 'insufficient_scopes',
                        'message': f'Required scopes: {", ".join(required_scopes)}'
                    }), 403

                # Now verify properly
                return token_required()(f)(*args, **kwargs)

            except Exception as e:
                return jsonify({
                    'error': 'token_validation_failed',
                    'message': 'Failed to validate token scopes'
                }), 401

        return decorated

    return decorator