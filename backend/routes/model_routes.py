import threading
from datetime import datetime
from flask import Blueprint, jsonify, current_app
from database.db import db
from database.models import ModelMetrics
from ml.model_trainer import train_model, get_latest_metrics
from utils.auth import jwt_required, admin_required, log_admin_action

bp = Blueprint('model', __name__, url_prefix='/api/model')

# Mutex lock to prevent simultaneous CPU-heavy model retraining
_retrain_lock = threading.Lock()

@bp.route('/metrics', methods=['GET'])
@jwt_required
def metrics():
    """Get latest ML model performance metrics"""
    latest = ModelMetrics.query.order_by(ModelMetrics.metric_date.desc()).first()
    
    if not latest:
        fallback = get_latest_metrics()
        seed_record = ModelMetrics(
            accuracy=fallback['accuracy'],
            precision=fallback['precision'],
            recall=fallback['recall'],
            f1_score=fallback['f1_score'],
            roc_auc=fallback['roc_auc'],
            total_predictions=fallback['total_predictions'],
            correct_predictions=fallback['correct_predictions']
        )
        db.session.add(seed_record)
        db.session.commit()
        latest = seed_record
        
    return jsonify({
        'accuracy': round(latest.accuracy, 4),
        'precision': round(latest.precision, 4),
        'recall': round(latest.recall, 4),
        'f1_score': round(latest.f1_score, 4),
        'roc_auc': round(latest.roc_auc, 4),
        'total_predictions': latest.total_predictions,
        'correct_predictions': latest.correct_predictions,
        'trained_at': latest.metric_date.isoformat() if latest.metric_date else datetime.utcnow().isoformat()
    }), 200

@bp.route('/info', methods=['GET'])
@jwt_required
def info():
    """Get model metadata and pipeline information"""
    return jsonify({
        'model_name': 'XGBoost Adaptive Payment Recovery Classifier',
        'algorithm': 'Gradient Boosted Decision Trees',
        'version': '2.0+',
        'features': [
            'amount', 'failure_type', 'payment_method', 'customer_history',
            'retry_number', 'time_since_failure_hours', 'card_issuer'
        ],
        'target': 'is_recoverable',
        'status': 'active'
    }), 200

@bp.route('/retrain', methods=['POST'])
@admin_required
def retrain():
    """
    Trigger model retraining with fresh synthetic distribution
    Restricted to ADMIN role. Thread-safe concurrency locked.
    """
    acquired = _retrain_lock.acquire(blocking=False)
    if not acquired:
        log_admin_action('/api/model/retrain', 'REJECTED', 'Retraining already in progress')
        return jsonify({
            'error': 'Conflict',
            'message': 'A model retraining job is already in progress. Please wait until it completes.'
        }), 409
        
    try:
        current_app.logger.info("Starting authorized model retraining job...")
        results = train_model(n_samples=10000)
        
        # Save metrics to database
        metric_record = ModelMetrics(
            accuracy=results['accuracy'],
            precision=results['precision'],
            recall=results['recall'],
            f1_score=results['f1'],
            roc_auc=results['roc_auc'],
            total_predictions=results['total'],
            correct_predictions=results['correct']
        )
        db.session.add(metric_record)
        db.session.commit()
        
        log_admin_action(
            '/api/model/retrain', 
            'SUCCESS', 
            f"Trained XGBoost model. Accuracy: {results['accuracy']:.4f}, ROC-AUC: {results['roc_auc']:.4f}"
        )
        
        return jsonify({
            'message': 'Model retrained successfully and artifacts updated',
            'metrics': {
                'accuracy': round(results['accuracy'], 4),
                'precision': round(results['precision'], 4),
                'recall': round(results['recall'], 4),
                'f1_score': round(results['f1'], 4),
                'roc_auc': round(results['roc_auc'], 4),
                'total_predictions': results['total'],
                'correct_predictions': results['correct']
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Model retraining failed: {e}", exc_info=True)
        log_admin_action('/api/model/retrain', 'FAILED', str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Model retraining failed due to an internal computational error'
        }), 500
    finally:
        _retrain_lock.release()
