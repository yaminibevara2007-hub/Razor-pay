import re
from flask import Blueprint, request, jsonify, g
from database.db import db
from database.models import User
from utils.auth import generate_token, jwt_required

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

USERNAME_REGEX = re.compile(r'^[a-zA-Z0-9_\-\.]{3,30}$')

@bp.route('/register', methods=['POST'])
def register():
    """Register a new user account (defaults to USER role)"""
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    
    if not username or not password:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Both username and password are required'
        }), 400
        
    if not USERNAME_REGEX.match(username):
        return jsonify({
            'error': 'Validation Error',
            'message': 'Username must be 3-30 characters alphanumeric, dots, hyphens, or underscores'
        }), 400
        
    if len(password) < 8:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Password must be at least 8 characters long'
        }), 400
        
    existing = User.query.filter_by(username=username).first()
    if existing:
        return jsonify({
            'error': 'Conflict',
            'message': f"Username '{username}' is already registered"
        }), 409
        
    # First user can be promoted to ADMIN if no users exist, or explicit role if internal
    user_count = User.query.count()
    role = 'ADMIN' if user_count == 0 else 'USER'
    
    user = User(username=username, role=role)
    user.set_password(password)
    
    db.session.add(user)
    db.session.commit()
    
    token = generate_token(user)
    return jsonify({
        'message': 'User registered successfully',
        'token': token,
        'user': user.to_dict()
    }), 201

@bp.route('/login', methods=['POST'])
def login():
    """Authenticate with username and password, returning signed JWT token"""
    data = request.get_json(silent=True) or {}
    username = str(data.get('username', '')).strip()
    password = str(data.get('password', '')).strip()
    
    if not username or not password:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Both username and password are required'
        }), 400
        
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password) or not user.is_active:
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Invalid credentials'
        }), 401
        
    token = generate_token(user)
    return jsonify({
        'message': 'Authentication successful',
        'token': token,
        'user': user.to_dict()
    }), 200

@bp.route('/me', methods=['GET'])
@jwt_required
def me():
    """Inspect profile and role of currently authenticated user"""
    return jsonify({
        'user': g.current_user.to_dict()
    }), 200
