import uuid
import random
from datetime import datetime, timedelta
from database.db import db
from database.models import Transaction, RecoveryDecision
from ml.model_predictor import predict_recovery_probability
from services.decision_service import make_recovery_decision

def analyze_payment(data):
    """Analyze a failed payment transaction and persist records"""
    transaction_id = data.get('transaction_id') or f"txn_{uuid.uuid4().hex[:10]}"
    amount = float(data['amount'])
    failure_type = data['failure_type']
    payment_method = data['payment_method']
    customer_history = data['customer_history']
    card_issuer = data.get('card_issuer')
    retry_number = int(data.get('retry_number', 1))
    time_since_failure_hours = int(data.get('time_since_failure_hours', 0))
    merchant_id = data.get('merchant_id', 'MERCHANT_DEMO')
    gateway = data.get('gateway', 'razorpay')
    
    # Create transaction
    transaction = Transaction(
        transaction_id=transaction_id,
        merchant_id=merchant_id,
        amount=amount,
        failure_type=failure_type,
        payment_method=payment_method,
        card_issuer=card_issuer,
        customer_history=customer_history,
        retry_number=retry_number,
        time_since_failure_hours=time_since_failure_hours,
        gateway=gateway
    )
    db.session.add(transaction)
    
    # Predict ML probability
    recovery_prob = predict_recovery_probability({
        'amount': amount,
        'failure_type': failure_type,
        'payment_method': payment_method,
        'customer_history': customer_history,
        'retry_number': retry_number,
        'time_since_failure_hours': time_since_failure_hours,
        'card_issuer': card_issuer
    })
    
    # Make Decision
    decision_data = make_recovery_decision(transaction_id, recovery_prob, amount, failure_type=failure_type)
    
    # Store decision
    recovery_decision = RecoveryDecision(
        transaction_id=transaction_id,
        predicted_recovery_prob=recovery_prob,
        recommended_action=decision_data['action'],
        expected_recovery_value=decision_data['expected_value'],
        decision_reasoning=decision_data['reasoning'],
        executed=True,
        actual_outcome='success' if (decision_data['action'] == 'RETRY' and recovery_prob > 0.55) else ('stopped' if decision_data['action'] == 'STOP' else 'pending')
    )
    db.session.add(recovery_decision)
    db.session.commit()
    
    confidence = 'High' if recovery_prob > 0.70 else ('Medium' if recovery_prob > 0.40 else 'Low')
    
    return {
        'transaction_id': transaction_id,
        'amount': amount,
        'failure_type': failure_type,
        'payment_method': payment_method,
        'customer_history': customer_history,
        'card_issuer': card_issuer,
        'predicted_recovery_probability': round(recovery_prob, 3),
        'recommended_action': decision_data['action'],
        'expected_recovery_value': round(decision_data['expected_value'], 2),
        'reasoning': decision_data['reasoning'],
        'confidence': confidence
    }

def seed_sample_transactions(count=30):
    """Seed the database with diverse, realistic failure cases and ML recovery outcomes"""
    issuers = ['HDFC', 'ICICI', 'SBI', 'Axis', 'Kotak', None]
    methods = ['card', 'upi', 'netbanking']
    failures = ['soft_decline', 'hard_decline', 'timeout', 'duplicate']
    histories = ['good', 'medium', 'bad']
    
    created_count = 0
    now = datetime.utcnow()
    
    for i in range(count):
        txn_id = f"txn_{uuid.uuid4().hex[:10]}"
        failure = random.choices(failures, weights=[0.45, 0.20, 0.25, 0.10])[0]
        method = random.choices(methods, weights=[0.5, 0.35, 0.15])[0]
        history = random.choices(histories, weights=[0.35, 0.45, 0.20])[0]
        issuer = random.choice(issuers) if method == 'card' else None
        amount = round(random.uniform(250, 45000), 2)
        retry_no = random.randint(1, 3)
        hours_ago = random.randint(0, 48)
        created_time = now - timedelta(hours=hours_ago, minutes=random.randint(1, 59))
        
        # Calculate prediction
        features_dict = {
            'amount': amount,
            'failure_type': failure,
            'payment_method': method,
            'customer_history': history,
            'retry_number': retry_no,
            'time_since_failure_hours': hours_ago,
            'card_issuer': issuer
        }
        prob = predict_recovery_probability(features_dict)
        decision = make_recovery_decision(txn_id, prob, amount, failure_type=failure)
        
        # Outcome simulation based on decision & prob
        if decision['action'] == 'RETRY':
            # Soft decline or timeout has high chance of succeeding
            outcome = 'success' if (random.random() < prob) else 'failed'
        elif decision['action'] == 'STOP':
            outcome = 'stopped'
        else:
            outcome = 'success' if (random.random() < (prob * 0.7)) else 'pending'
            
        txn = Transaction(
            transaction_id=txn_id,
            merchant_id=f"MERCH_{random.randint(101, 109)}",
            amount=amount,
            currency='INR',
            failure_type=failure,
            payment_method=method,
            card_issuer=issuer,
            customer_history=history,
            retry_number=retry_no,
            time_since_failure_hours=hours_ago,
            gateway='razorpay',
            is_recoverable=True if outcome == 'success' else False,
            timestamp=created_time,
            created_at=created_time
        )
        db.session.add(txn)
        
        rec_dec = RecoveryDecision(
            transaction_id=txn_id,
            predicted_recovery_prob=prob,
            recommended_action=decision['action'],
            expected_recovery_value=decision['expected_value'],
            decision_reasoning=decision['reasoning'],
            executed=True,
            actual_outcome=outcome,
            created_at=created_time
        )
        db.session.add(rec_dec)
        created_count += 1
        
    db.session.commit()
    return created_count
