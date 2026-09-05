import numpy as np

# Column order standard matching data_generator
FEATURE_COLUMNS = [
    'amount',
    'failure_type',
    'payment_method',
    'customer_history',
    'retry_number',
    'time_since_failure_hours',
    'card_issuer'
]

def extract_features(transaction_data):
    """
    Extract features from transaction dictionary for ML prediction.
    Returns: list of numeric features strictly in FEATURE_COLUMNS order.
    """
    # Encode failure type
    failure_type_map = {
        'soft_decline': 0,
        'hard_decline': 1,
        'timeout': 2,
        'duplicate': 3
    }
    failure_type_val = transaction_data.get('failure_type', 'duplicate')
    failure_type_encoded = failure_type_map.get(failure_type_val, 3)
    
    # Encode payment method
    payment_method_map = {
        'card': 0,
        'upi': 1,
        'netbanking': 2
    }
    payment_method_val = transaction_data.get('payment_method', 'card')
    payment_method_encoded = payment_method_map.get(payment_method_val, 0)
    
    # Encode customer history
    customer_history_map = {
        'bad': 0,
        'medium': 1,
        'good': 2
    }
    customer_history_val = transaction_data.get('customer_history', 'bad')
    customer_history_encoded = customer_history_map.get(customer_history_val, 0)
    
    # Card issuer flag
    card_issuer_val = transaction_data.get('card_issuer')
    has_issuer = 1 if card_issuer_val and str(card_issuer_val).strip() not in ['None', 'none', ''] else 0
    
    # Build feature vector in exact order:
    # 1. amount
    # 2. failure_type
    # 3. payment_method
    # 4. customer_history
    # 5. retry_number
    # 6. time_since_failure_hours
    # 7. card_issuer
    features = [
        float(transaction_data.get('amount', 0)),
        int(failure_type_encoded),
        int(payment_method_encoded),
        int(customer_history_encoded),
        int(transaction_data.get('retry_number', 1)),
        int(transaction_data.get('time_since_failure_hours', 0)),
        int(has_issuer)
    ]
    
    return features
