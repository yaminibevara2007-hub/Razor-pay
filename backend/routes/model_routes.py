from datetime import datetime
from flask import Blueprint, jsonify
from database.db import db
from database.models import ModelMetrics
from ml.model_trainer import train_model, get_latest_metrics

bp = Blueprint('model', __name__, url_prefix='/api/model')

@bp.route('/metrics', methods=['GET'])
def metrics():
    """Get latest ML model performance metrics"""
    latest = ModelMetrics.query.order_by(ModelMetrics.metric_date.desc()).first()
    
    if not latest:
        # Fallback to defaults or seed an initial metric record
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
def retrain():
    """Trigger model retraining with fresh synthetic distribution"""
    try:
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
        return jsonify({'error': f'Model retraining failed: {str(e)}'}), 500
