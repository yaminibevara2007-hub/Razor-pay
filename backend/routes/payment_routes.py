from flask import Blueprint, request, jsonify
from database.db import db
from database.models import Transaction, RecoveryDecision
from services.payment_service import analyze_payment, seed_sample_transactions

bp = Blueprint('payments', __name__, url_prefix='/api/payments')

@bp.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze a failed payment and make recovery decision
    
    Request payload:
    {
        "amount": 5000,
        "failure_type": "soft_decline",
        "payment_method": "card",
        "customer_history": "good",
        "card_issuer": "HDFC",
        "retry_number": 1,
        "time_since_failure_hours": 2
    }
    """
    try:
        data = request.get_json(force=True, silent=False)
        if not data:
            return jsonify({'error': 'No input data provided'}), 400
            
        required = ['amount', 'failure_type', 'payment_method', 'customer_history']
        missing = [f for f in required if f not in data or data[f] == '']
        if missing:
            return jsonify({'error': f'Missing required fields: {", ".join(missing)}'}), 400
            
        # Amount validation
        try:
            data['amount'] = float(data['amount'])
            if data['amount'] <= 0:
                return jsonify({'error': 'Amount must be greater than zero'}), 400
        except ValueError:
            return jsonify({'error': 'Amount must be a valid number'}), 400
            
        result = analyze_payment(data)
        return jsonify(result), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/<transaction_id>', methods=['GET'])
def get_transaction(transaction_id):
    """Get single transaction and its recovery decision"""
    transaction = Transaction.query.filter_by(transaction_id=transaction_id).first()
    if not transaction:
        return jsonify({'error': f'Transaction {transaction_id} not found'}), 404
        
    decision = RecoveryDecision.query.filter_by(transaction_id=transaction_id).first()
    
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
def list_transactions():
    """List recent transactions with their recovery decisions"""
    limit = request.args.get('limit', 50, type=int)
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
def seed():
    """Generate sample transaction records for instant testing"""
    try:
        data = request.get_json(silent=True) or {}
        count = int(data.get('count', 25))
        created = seed_sample_transactions(count=count)
        return jsonify({
            'message': f'Successfully generated {created} sample transactions',
            'count': created
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
