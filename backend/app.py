import os
import sys

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from flask import Flask, jsonify
from flask_cors import CORS
from config import Config
from database.db import db, init_db
from routes.payment_routes import bp as payment_bp
from routes.analytics_routes import bp as analytics_bp
from routes.model_routes import bp as model_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    
    # Initialize database tables
    with app.app_context():
        init_db()
        
    # Register blueprints
    app.register_blueprint(payment_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(model_bp)
    
    @app.route('/')
    def root():
        return jsonify({
            'name': 'Smart Payment Retry Engine API',
            'version': '1.0.0',
            'status': 'healthy',
            'endpoints': {
                'payments': '/api/payments',
                'analyze': '/api/payments/analyze',
                'analytics': '/api/analytics/overview',
                'comparison': '/api/analytics/comparison',
                'model_metrics': '/api/model/metrics'
            }
        })
        
    @app.route('/api/health')
    def health():
        return jsonify({'status': 'ok'})
        
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('PORT', 5005))
    print(f"Starting Smart Payment Retry Engine backend on http://localhost:{port}")
    app.run(debug=True, host='0.0.0.0', port=port)
