import os
import sys
import pickle
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config
from ml.feature_extractor import extract_features

_cached_model = None
_cached_scaler = None

def load_model_and_scaler(force_reload=False):
    """Load model and scaler from disk, with caching"""
    global _cached_model, _cached_scaler
    
    if _cached_model is not None and _cached_scaler is not None and not force_reload:
        return _cached_model, _cached_scaler
    
    model_path = Config.MODEL_PATH
    scaler_path = Config.SCALER_PATH
    
    if os.path.exists(model_path) and os.path.exists(scaler_path):
        try:
            with open(model_path, 'rb') as f:
                _cached_model = pickle.load(f)
            with open(scaler_path, 'rb') as f:
                _cached_scaler = pickle.load(f)
            return _cached_model, _cached_scaler
        except Exception as e:
            print(f"[ModelPredictor] Warning loading model files: {e}")
            return None, None
    return None, None

def predict_recovery_probability(transaction_data):
    """
    Predict recovery probability for a failed payment.
    Returns: float between 0.0 and 1.0
    """
    model, scaler = load_model_and_scaler()
    
    if model is None or scaler is None:
        return fallback_prediction(transaction_data)
        
    try:
        import pandas as pd
        from ml.feature_extractor import FEATURE_COLUMNS
        features = extract_features(transaction_data)
        features_df = pd.DataFrame([features], columns=FEATURE_COLUMNS)
        features_scaled = scaler.transform(features_df)
        proba = model.predict_proba(features_scaled)[0][1]
        return float(np.clip(proba, 0.0, 1.0))
    except Exception as e:
        print(f"[ModelPredictor] Prediction error: {e}. Using fallback prediction.")
        return fallback_prediction(transaction_data)

def fallback_prediction(data):
    """Fallback heuristic prediction when model is not yet loaded"""
    failure_type = data.get('failure_type', 'unknown')
    customer_history = data.get('customer_history', 'bad')
    
    base_prob = {
        'soft_decline': 0.65,
        'timeout': 0.75,
        'hard_decline': 0.15,
        'duplicate': 0.0
    }.get(failure_type, 0.30)
    
    if customer_history == 'good':
        base_prob += 0.10
    elif customer_history == 'bad':
        base_prob -= 0.10
        
    return float(np.clip(base_prob, 0.0, 1.0))
