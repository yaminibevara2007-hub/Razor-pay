import os
import secrets
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

# Load environment variables from .env if present
env_path = os.path.join(PROJECT_ROOT, '.env')
if os.path.exists(env_path):
    load_dotenv(env_path)

class BaseConfig:
    """Base application configuration with secure defaults"""
    # In Vercel serverless functions, only /tmp is writable
    if os.environ.get('VERCEL'):
        INSTANCE_DIR = '/tmp/instance'
    else:
        INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
        
    try:
        os.makedirs(INSTANCE_DIR, exist_ok=True)
    except OSError:
        pass
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'payments.db').replace('\\', '/')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    
    # Models and Data directories
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    try:
        os.makedirs(MODELS_DIR, exist_ok=True)
    except OSError:
        pass
    MODEL_PATH = os.path.join(MODELS_DIR, 'recovery_model.pkl')
    SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')
    
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    try:
        os.makedirs(DATA_DIR, exist_ok=True)
    except OSError:
        pass
    
    # CORS Origin Whitelist (comma-separated origins)
    _raw_origins = os.environ.get(
        'FRONTEND_ORIGIN', 
        'http://localhost:8000,http://127.0.0.1:8000,http://localhost:3000,http://127.0.0.1:3000'
    )
    FRONTEND_ORIGINS = [origin.strip() for origin in _raw_origins.split(',') if origin.strip()]
    if os.environ.get('VERCEL_URL'):
        FRONTEND_ORIGINS.append(f"https://{os.environ.get('VERCEL_URL')}")
    
    # Rate Limiting
    RATELIMIT_DEFAULT = os.environ.get('RATELIMIT_DEFAULT', '120 per minute')
    RATELIMIT_STORAGE_URI = os.environ.get('RATELIMIT_STORAGE_URI', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'

class DevelopmentConfig(BaseConfig):
    """Development environment configuration"""
    DEBUG = True
    TESTING = False
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-insecure-secret-key-replace-in-production')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', SECRET_KEY)
    ENABLE_SEED_ENDPOINT = os.environ.get('ENABLE_SEED_ENDPOINT', 'true').lower() in ('true', '1', 'yes')

class ProductionConfig(BaseConfig):
    """Hardened production environment configuration"""
    DEBUG = False
    TESTING = False
    ENABLE_SEED_ENDPOINT = os.environ.get('ENABLE_SEED_ENDPOINT', 'false').lower() in ('true', '1', 'yes')
    
    # Secrets must be explicitly supplied in production
    SECRET_KEY = os.environ.get('SECRET_KEY')
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    
    def __init__(self):
        if not self.SECRET_KEY or self.SECRET_KEY == 'dev-insecure-secret-key-replace-in-production':
            raise ValueError("CRITICAL: Production mode requires a strong, unique SECRET_KEY environment variable.")
        if not self.JWT_SECRET_KEY:
            raise ValueError("CRITICAL: Production mode requires a strong, unique JWT_SECRET_KEY environment variable.")

from sqlalchemy.pool import StaticPool

class TestingConfig(BaseConfig):
    """Isolated testing environment configuration"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SQLALCHEMY_ENGINE_OPTIONS = {
        'poolclass': StaticPool,
        'connect_args': {'check_same_thread': False}
    }
    SECRET_KEY = 'test-secret-key-for-automated-tests-at-least-32-chars-long'
    JWT_SECRET_KEY = 'test-jwt-secret-key-for-automated-tests-at-least-32-chars-long'
    ENABLE_SEED_ENDPOINT = True
    RATELIMIT_ENABLED = False

# Mapping for environment selection
config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig
}

# Default export
Config = DevelopmentConfig if os.environ.get('FLASK_ENV') != 'production' else ProductionConfig
