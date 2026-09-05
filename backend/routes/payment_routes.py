from flask import Blueprint, request, jsonify, current_app
from database.db import db
from database.models import Transaction, RecoveryDecision
from services.payment_service import analyze_payment, seed_sample_transactions
from utils.validators import validate_payment_analysis_payload, sanitize_identifier
from utils.auth import jwt_required, admin_required, log_admin_action

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('/analyze', methods=['POST'])
@jwt_required
def analyze():
    """
    Analyze a failed payment and make recovery decision
    Requires authenticated user (USER or ADMIN)
    """
    try:
        raw_data = request.get_json(silent=True)
        if not raw_data:
            return jsonify({
                'error': 'Validation Error',
                'message': 'No JSON payload provided in request'
            }), 400
            
        is_valid, validated_or_err = validate_payment_analysis_payload(raw_data)
        if not is_valid:
            return jsonify({
                'error': 'Validation Error',
                'message': validated_or_err
            }), 400
            
        result = analyze_payment(validated_or_err)
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error analyzing payment: {e}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred while analyzing the payment transaction'
        }), 500

@bp.route('/<transaction_id>', methods=['GET'])
@jwt_required
def get_transaction(transaction_id):
    """Get single transaction and its recovery decision"""
    clean_id = sanitize_identifier(transaction_id)
    if not clean_id:
        return jsonify({
            'error': 'Validation Error',
            'message': 'Invalid transaction ID format'
        }), 400
        
    transaction = Transaction.query.filter_by(transaction_id=clean_id).first()
    if not transaction:
        return jsonify({
            'error': 'Not Found',
            'message': f"Transaction '{clean_id}' was not found"
        }), 404
        
    decision = RecoveryDecision.query.filter_by(transaction_id=clean_id).first()
    
    return jsonify({
        'transaction_id': transaction.transaction_id,
        'merchant_id': transaction.merchant_id,
        'amount': transaction.amount,
        'currency': transaction.currency,
        'failure_type': transaction.failure_type,
        'payment_method': transaction.payment_method,
        'card_issuer': transaction.card_issuer,
        'customer_history': transaction.customer_history,
        'retry_number': transaction.retry_number,
        'time_since_failure_hours': transaction.time_since_failure_hours,
        'decision': {
            'action': decision.recommended_action if decision else None,
            'probability': decision.predicted_recovery_prob if decision else None,
            'expected_value': decision.expected_recovery_value if decision else None,
            'reasoning': decision.decision_reasoning if decision else None,
            'actual_outcome': decision.actual_outcome if decision else None
        },
        'timestamp': transaction.created_at.isoformat() if transaction.created_at else None
    }), 200

@bp.route('', methods=['GET'])
@jwt_required
def list_transactions():
    """List recent transactions with their recovery decisions"""
    try:
        raw_limit = request.args.get('limit', 50)
        limit = int(raw_limit)
        limit = max(1, min(limit, 100))  # Clamp between 1 and 100
    except (ValueError, TypeError):
        limit = 50
        
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(limit).all()
    
    result = []
    for txn in transactions:
        decision = RecoveryDecision.query.filter_by(transaction_id=txn.transaction_id).first()
        result.append({
            'transaction_id': txn.transaction_id,
            'merchant_id': txn.merchant_id,
            'amount': txn.amount,
            'currency': txn.currency,
            'failure_type': txn.failure_type,
            'payment_method': txn.payment_method,
            'card_issuer': txn.card_issuer,
            'customer_history': txn.customer_history,
            'action': decision.recommended_action if decision else 'PENDING',
            'probability': round(decision.predicted_recovery_prob, 3) if decision and decision.predicted_recovery_prob is not None else 0.0,
            'expected_value': round(decision.expected_recovery_value, 2) if decision and decision.expected_recovery_value is not None else 0.0,
            'actual_outcome': decision.actual_outcome if decision else 'unknown',
            'timestamp': txn.created_at.isoformat() if txn.created_at else None
        })
        
    return jsonify(result), 200

@bp.route('/seed', methods=['POST'])
@admin_required
def seed():
    """
    Generate sample transaction records for testing
    Restricted to ADMIN role only. Disabled in production by default.
    """
    if not current_app.config.get('ENABLE_SEED_ENDPOINT', False):
        log_admin_action('/api/payments/seed', 'REJECTED', 'Seed endpoint disabled in configuration')
        return jsonify({
            'error': 'Forbidden',
            'message': 'Sample data seeding is disabled in this environment'
        }), 403
        
    try:
        data = request.get_json(silent=True) or {}
        try:
            count = int(data.get('count', 25))
            count = max(1, min(count, 50))  # Max 50 per batch
        except (ValueError, TypeError):
            count = 25
            
        created = seed_sample_transactions(count=count)
        log_admin_action('/api/payments/seed', 'SUCCESS', f"Seeded {created} sample transactions")
        return jsonify({
            'message': f"Successfully generated {created} sample transactions",
            'count': created
        }), 201
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error seeding transactions: {e}", exc_info=True)
        log_admin_action('/api/payments/seed', 'FAILED', str(e))
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'Failed to generate sample transaction batch'
        }), 500
