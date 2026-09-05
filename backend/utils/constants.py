# Business & Decision Thresholds
RETRY_COST_INR = 10.0  # Cost per retry attempt in INR

# Decision Probability Thresholds
HIGH_CONFIDENCE_THRESHOLD = 0.60
MEDIUM_CONFIDENCE_THRESHOLD = 0.40

# Action Types
ACTION_RETRY = 'RETRY'
ACTION_CUSTOMER_ACTION = 'CUSTOMER_ACTION'
ACTION_STOP = 'STOP'

# Supported Categories
FAILURE_TYPES = ['soft_decline', 'hard_decline', 'timeout', 'duplicate']
PAYMENT_METHODS = ['card', 'upi', 'netbanking']
CUSTOMER_HISTORIES = ['good', 'medium', 'bad']
CARD_ISSUERS = ['HDFC', 'ICICI', 'SBI', 'Axis', 'Kotak', 'None']
DEFAULT_GATEWAY = 'razorpay'
