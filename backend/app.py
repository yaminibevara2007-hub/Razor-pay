import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import Config, config_by_name
from database.db import db, init_db
from database.models import User
from routes.payment_routes import bp as payment_bp
from routes.analytics_routes import bp as analytics_bp
from routes.model_routes import bp as model_bp
from routes.auth_routes import bp as auth_bp
from utils.security_headers import apply_security_headers
from utils.logger import setup_logger

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"
)

def create_app(config_class=Config):
    if isinstance(config_class, type):
        config_instance = config_class()
    else:
        config_instance = config_class

    app = Flask(__name__)
    app.config.from_object(config_instance)
    
    # Configure secure logging
    setup_logger(app)
    
    # Initialize database
    db.init_app(app)
    
    # Initialize rate limiter
    limiter.enabled = app.config.get('RATELIMIT_ENABLED', True)
    limiter.init_app(app)
    
    # Initialize CORS restricted to whitelisted origins
    allowed_origins = app.config.get('FRONTEND_ORIGINS', ['http://localhost:8000', 'http://127.0.0.1:8000'])
    CORS(app, resources={r"/api/*": {"origins": allowed_origins}}, supports_credentials=True)
    
    # Initialize database tables and provision default demo accounts
    with app.app_context():
        init_db()
        _provision_default_users(app)
        
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(model_bp)
    
    # Security headers on all responses
    @app.after_request
    def after_request_security(response):
        return apply_security_headers(response)
        
    # Root discovery endpoint
    @app.route('/')
    @app.route('/api')
    @app.route('/api/')
    def root():
        return jsonify({
            'name': 'Smart Payment Retry Engine API',
            'version': '1.0.0',
            'status': 'healthy',
            'endpoints': {
                'auth': '/api/auth/login',
                'payments': '/api/payments',
                'analyze': '/api/payments/analyze',
                'analytics': '/api/analytics/overview',
                'comparison': '/api/analytics/comparison',
                'model_metrics': '/api/model/metrics',
                'model_info': '/api/model/info'
            }
        })
        
    # Safe health check endpoint (never exposes secrets, credentials, or internal paths)
    @app.route('/api/health')
    @app.route('/health')
    def health():
        return jsonify({
            'status': 'healthy',
            'environment': 'production' if not app.debug else 'development'
        }), 200

    # Centralized JSON Error Handlers (prevent stack trace and server path leakage)
    @app.errorhandler(400)
    def handle_bad_request(e):
        return jsonify({
            'error': 'Bad Request',
            'message': getattr(e, 'description', 'Invalid request syntax or parameters')
        }), 400

    @app.errorhandler(401)
    def handle_unauthorized(e):
        return jsonify({
            'error': 'Unauthorized',
            'message': getattr(e, 'description', 'Authentication credentials are required')
        }), 401

    @app.errorhandler(403)
    def handle_forbidden(e):
        return jsonify({
            'error': 'Forbidden',
            'message': getattr(e, 'description', 'You do not have permission to access this resource')
        }), 403

    @app.errorhandler(404)
    def handle_not_found(e):
        return jsonify({
            'error': 'Not Found',
            'message': getattr(e, 'description', 'The requested resource was not found')
        }), 404

    @app.errorhandler(429)
    def handle_ratelimit_exceeded(e):
        return jsonify({
            'error': 'Too Many Requests',
            'message': 'Rate limit exceeded. Please slow down and retry later.'
        }), 429

    @app.errorhandler(500)
    def handle_server_error(e):
        app.logger.error(f"Internal server error: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected server error occurred. Please contact support.'
        }), 500
        
    return app

def _provision_default_users(app):
    """Seed initial demo user and admin accounts with hashed credentials if not already present"""
    try:
        demo_user = User.query.filter_by(username='demo_user').first()
        if not demo_user:
            u = User(username='demo_user', role='USER')
            u.set_password(os.environ.get('DEFAULT_USER_PASS', 'User@12345'))
            db.session.add(u)
            
        demo_admin = User.query.filter_by(username='demo_admin').first()
        if not demo_admin:
            a = User(username='demo_admin', role='ADMIN')
            a.set_password(os.environ.get('DEFAULT_ADMIN_PASS', 'Admin@12345'))
            db.session.add(a)
            
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to seed default accounts: {e}")

app = create_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    is_debug = app.config.get('DEBUG', False)
    print(f"Starting Smart Payment Retry Engine backend on http://localhost:{port} (Debug={is_debug})")
    app.run(debug=is_debug, host='0.0.0.0', port=port)
