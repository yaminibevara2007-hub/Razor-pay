import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(BASE_DIR, '..'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'smart-retry-engine-secret-key-2024')
    INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
    os.makedirs(INSTANCE_DIR, exist_ok=True)
    
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 
        f"sqlite:///{os.path.join(INSTANCE_DIR, 'payments.db').replace('\\', '/')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    
    MODELS_DIR = os.path.join(BASE_DIR, 'models')
    os.makedirs(MODELS_DIR, exist_ok=True)
    
    MODEL_PATH = os.path.join(MODELS_DIR, 'recovery_model.pkl')
    SCALER_PATH = os.path.join(MODELS_DIR, 'scaler.pkl')
    
    DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
    os.makedirs(DATA_DIR, exist_ok=True)
