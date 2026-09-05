import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.constants import RETRY_COST_INR, ACTION_RETRY, ACTION_CUSTOMER_ACTION, ACTION_STOP

def make_recovery_decision(transaction_id, recovery_probability, amount):
    """
    Make intelligent recovery decision based on ML predicted probability and expected monetary value.
    
    Decision Policy:
    - P(success) > 0.60: RETRY (Gateway has high probability of succeeding on immediate retry)
    - 0.40 < P(success) <= 0.60 and Expected Value > 0: CUSTOMER_ACTION (Ask customer to verify details or select alt rail)
    - P(success) <= 0.40 or Expected Value <= 0: STOP (Low recovery likelihood, saves merchant retry fees and prevents churn)
    """
    retry_cost = RETRY_COST_INR
    expected_recovery_value = (recovery_probability * float(amount)) - retry_cost
    
    if recovery_probability > 0.60:
        action = ACTION_RETRY
        reasoning = (
            f"High confidence ({recovery_probability*100:.1f}%) in transient failure recovery. "
            f"Expected recovery value is ₹{expected_recovery_value:.2f} against ₹{retry_cost:.0f} retry cost."
        )
    elif recovery_probability > 0.40 and expected_recovery_value > 0:
        action = ACTION_CUSTOMER_ACTION
        reasoning = (
            f"Moderate recovery probability ({recovery_probability*100:.1f}%). "
            f"Recommend customer notification to re-authenticate or switch payment method."
        )
    else:
        action = ACTION_STOP
        reasoning = (
            f"Low recovery probability ({recovery_probability*100:.1f}%) or negative expected economic value. "
            f"Halting automated retries to avoid gateway penalty fees and card scheme churn."
        )
    
    return {
        'action': action,
        'expected_value': max(0.0, float(expected_recovery_value)),
        'reasoning': reasoning
    }
