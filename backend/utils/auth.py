import datetime
from functools import wraps
import jwt
from flask import request, jsonify, g, current_app
from database.db import db
from database.models import User, AdminAuditLog

def get_jwt_secret():
    return current_app.config.get('JWT_SECRET_KEY') or current_app.config.get('SECRET_KEY')

def generate_token(user, expires_in_seconds=86400):
    """Generate signed JWT token for user with role and expiration"""
    now = datetime.datetime.now(datetime.timezone.utc)
    payload = {
        'sub': str(user.id),
        'username': user.username,
        'role': user.role,
        'iat': now,
        'exp': now + datetime.timedelta(seconds=expires_in_seconds)
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm='HS256')

def decode_token(token):
    """Decode and cryptographically verify JWT token signature and expiration"""
    try:
        payload = jwt.decode(token, get_jwt_secret(), algorithms=['HS256'])
        return True, payload
    except jwt.ExpiredSignatureError:
        return False, "Token has expired"
    except jwt.InvalidTokenError:
        return False, "Invalid token signature or malformed token"

class AuthenticatedUser:
    """Lightweight user representation from verified cryptographically-signed JWT claims"""
    def __init__(self, user_id, username, role):
        self.id = user_id
        self.username = username
        self.role = role
        self.is_active = True

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active
        }

def jwt_required(f):
    """Decorator to require a valid JWT Bearer token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Missing Authorization header'
            }), 401
            
        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != 'bearer':
            return jsonify({
                'error': 'Unauthorized',
                'message': 'Authorization header format must be Bearer <token>'
            }), 401
            
        token = parts[1]
        valid, result = decode_token(token)
        if not valid:
            return jsonify({
                'error': 'Unauthorized',
                'message': result
            }), 401
            
        user = None
        try:
            sub_val = result.get('sub')
            user_id = int(sub_val) if sub_val and str(sub_val).isdigit() else sub_val
            user = db.session.get(User, user_id)
        except Exception:
            pass

        if not user:
            user = AuthenticatedUser(
                user_id=result.get('sub'),
                username=result.get('username', 'user'),
                role=result.get('role', 'USER')
            )
        elif not user.is_active:
            return jsonify({
                'error': 'Unauthorized',
                'message': 'User account is deactivated'
            }), 401
            
        g.current_user = user
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    """Decorator to require authenticated user with role == ADMIN"""
    @wraps(f)
    @jwt_required
    def decorated_function(*args, **kwargs):
        user = getattr(g, 'current_user', None)
        if not user or user.role != 'ADMIN':
            # Log unauthorized admin access attempt
            log_admin_action(
                action=request.path,
                status='REJECTED',
                details=f"User '{user.username if user else 'anonymous'}' attempted admin action without ADMIN role"
            )
            return jsonify({
                'error': 'Forbidden',
                'message': 'Administrator privileges required for this operation'
            }), 403
        return f(*args, **kwargs)
    return decorated_function

def log_admin_action(action, status, details=None):
    """Audit logging helper for administrative actions"""
    try:
        user = getattr(g, 'current_user', None)
        client_ip = request.headers.get('X-Forwarded-For', request.remote_addr)
        if client_ip and ',' in client_ip:
            client_ip = client_ip.split(',')[0].strip()
            
        audit_entry = AdminAuditLog(
            user_id=user.id if user else None,
            username=user.username if user else 'anonymous',
            action=action,
            status=status,
            ip_address=client_ip,
            details=details
        )
        db.session.add(audit_entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Failed to record admin audit log: {e}")
