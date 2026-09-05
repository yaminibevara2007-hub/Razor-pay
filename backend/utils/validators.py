import re
import math

ALLOWED_FAILURE_TYPES = {'soft_decline', 'hard_decline', 'timeout', 'duplicate'}
ALLOWED_PAYMENT_METHODS = {'card', 'upi', 'netbanking'}
ALLOWED_CUSTOMER_HISTORIES = {'good', 'medium', 'bad'}
ALLOWED_CURRENCIES = {'INR', 'USD', 'EUR'}
IDENTIFIER_REGEX = re.compile(r'^[a-zA-Z0-9_\-]{1,64}$')

MAX_TRANSACTION_AMOUNT = 10_000_000.0  # 10 Million INR
MAX_RETRY_NUMBER = 10
MAX_HOURS_SINCE_FAILURE = 720  # 30 days

def validate_payment_analysis_payload(data):
    """
    Validate input payload for /api/payments/analyze.
    Returns (is_valid: bool, validated_data_or_error_msg: dict/str)
    """
    if not isinstance(data, dict):
        return False, "Request body must be a JSON object"
        
    required_fields = ['amount', 'failure_type', 'payment_method', 'customer_history']
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == '':
            return False, f"Missing required field: '{field}'"
            
    # 1. Amount validation
    try:
        raw_amount = float(data['amount'])
        if math.isnan(raw_amount) or math.isinf(raw_amount):
            return False, "Amount must be a finite numeric value"
        if raw_amount <= 0:
            return False, "Amount must be greater than zero"
        if raw_amount > MAX_TRANSACTION_AMOUNT:
            return False, f"Amount exceeds maximum allowed limit (₹{MAX_TRANSACTION_AMOUNT:,.0f})"
    except (ValueError, TypeError):
        return False, "Amount must be a valid numeric value"
        
    # 2. Failure type validation
    failure_type = str(data['failure_type']).strip().lower()
    if failure_type not in ALLOWED_FAILURE_TYPES:
        return False, f"Invalid failure_type '{failure_type}'. Allowed values: {', '.join(sorted(ALLOWED_FAILURE_TYPES))}"
        
    # 3. Payment method validation
    payment_method = str(data['payment_method']).strip().lower()
    if payment_method not in ALLOWED_PAYMENT_METHODS:
        return False, f"Invalid payment_method '{payment_method}'. Allowed values: {', '.join(sorted(ALLOWED_PAYMENT_METHODS))}"
        
    # 4. Customer history validation
    customer_history = str(data['customer_history']).strip().lower()
    if customer_history not in ALLOWED_CUSTOMER_HISTORIES:
        return False, f"Invalid customer_history '{customer_history}'. Allowed values: {', '.join(sorted(ALLOWED_CUSTOMER_HISTORIES))}"
        
    # 5. Retry number validation
    try:
        retry_number = int(data.get('retry_number', 1))
        if retry_number < 1 or retry_number > MAX_RETRY_NUMBER:
            return False, f"retry_number must be an integer between 1 and {MAX_RETRY_NUMBER}"
    except (ValueError, TypeError):
        return False, "retry_number must be an integer"
        
    # 6. Time since failure validation
    try:
        hours = float(data.get('time_since_failure_hours', 0))
        if math.isnan(hours) or math.isinf(hours) or hours < 0 or hours > MAX_HOURS_SINCE_FAILURE:
            return False, f"time_since_failure_hours must be a number between 0 and {MAX_HOURS_SINCE_FAILURE}"
        hours = int(hours)
    except (ValueError, TypeError):
        return False, "time_since_failure_hours must be a valid number"
        
    # 7. Card issuer validation (optional)
    card_issuer = data.get('card_issuer')
    if card_issuer:
        card_issuer = str(card_issuer).strip()
        if len(card_issuer) > 100:
            return False, "card_issuer exceeds maximum length of 100 characters"
        # Sanitize card issuer (only alphanumeric, dashes, spaces)
        if not re.match(r'^[a-zA-Z0-9\s_\-]{1,100}$', card_issuer):
            return False, "card_issuer contains invalid characters"
    else:
        card_issuer = None
        
    # 8. Transaction ID validation (optional, auto-generated if omitted)
    txn_id = data.get('transaction_id')
    if txn_id:
        txn_id = str(txn_id).strip()
        if not IDENTIFIER_REGEX.match(txn_id):
            return False, "transaction_id must be 1-64 characters alphanumeric, dashes, or underscores"
            
    # 9. Merchant ID validation (optional)
    merchant_id = data.get('merchant_id', 'MERCHANT_DEMO')
    if merchant_id:
        merchant_id = str(merchant_id).strip()
        if not IDENTIFIER_REGEX.match(merchant_id):
            return False, "merchant_id must be 1-64 characters alphanumeric, dashes, or underscores"

    # 10. Currency validation (optional)
    currency = str(data.get('currency', 'INR')).strip().upper()
    if currency not in ALLOWED_CURRENCIES:
        return False, f"Invalid currency '{currency}'. Supported currencies: {', '.join(sorted(ALLOWED_CURRENCIES))}"

    validated_data = {
        'amount': round(raw_amount, 2),
        'failure_type': failure_type,
        'payment_method': payment_method,
        'customer_history': customer_history,
        'retry_number': retry_number,
        'time_since_failure_hours': hours,
        'card_issuer': card_issuer,
        'transaction_id': txn_id,
        'merchant_id': merchant_id,
        'currency': currency,
        'gateway': 'razorpay'
    }
    return True, validated_data

def sanitize_csv_cell(val):
    """
    Prevent CSV / Formula Injection (CWE-1236).
    If cell begins with =, +, -, @, \t, or \r, escape with leading single quote.
    """
    if val is None:
        return ''
    val_str = str(val)
    if val_str and val_str[0] in ('=', '+', '-', '@', '\t', '\r'):
        return f"'{val_str}"
    return val_str

def sanitize_identifier(val, max_len=64):
    """Sanitize string identifier for safe lookup"""
    if not val:
        return None
    val_str = str(val).strip()
    if IDENTIFIER_REGEX.match(val_str) and len(val_str) <= max_len:
        return val_str
    return None
