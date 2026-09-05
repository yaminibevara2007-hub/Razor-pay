from routes.payment_routes import bp as payment_bp
from routes.analytics_routes import bp as analytics_bp
from routes.model_routes import bp as model_bp

__all__ = ['payment_bp', 'analytics_bp', 'model_bp']
