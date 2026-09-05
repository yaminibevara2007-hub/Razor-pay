import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.constants import RETRY_COST_INR, ACTION_RETRY, ACTION_CUSTOMER_ACTION, ACTION_STOP

def make_recovery_decision(transaction_id, recovery_probability, amount, failure_type=None):
    """
    Make intelligent recovery decision based on ML predicted probability, failure category, and expected monetary value.
    
    Formula:
    Expected Value = (Recovery Probability * Transaction Amount) - Retry Cost (₹10)
    
    Decision Policy:
    - Failure == 'duplicate': STOP (Deterministic non-recoverable, P ~ 0)
    - Failure == 'hard_decline': STOP (Permanent card decline, avoid scheme penalties)
    - P(success) > 0.60 and Expected Value > 0: RETRY (Transient network/soft failure, high ROI)
    - 0.40 < P(success) <= 0.60 and Expected Value > 0: CUSTOMER_ACTION (Suggest re-auth or alt rail)
    - P(success) <= 0.40 or Expected Value <= 0: STOP (Low recovery likelihood, prevent wasted fees)
    """
    retry_cost = float(RETRY_COST_INR)
    raw_ev = (recovery_probability * float(amount)) - retry_cost
    
    # Category-specific overrides
    ft_lower = (failure_type or '').lower()
    
    if ft_lower == 'duplicate':
        action = ACTION_STOP
        expected_recovery_value = 0.0
        reasoning = "Duplicate transaction has very low recovery probability. Further retry is not recommended."
    elif ft_lower == 'hard_decline':
        action = ACTION_STOP
        expected_recovery_value = 0.0
        reasoning = f"Permanent card decline detected ({recovery_probability*100:.1f}% recovery probability). Halting retries to prevent card scheme penalties."
    elif recovery_probability > 0.60 and raw_ev > 0:
        action = ACTION_RETRY
        expected_recovery_value = max(0.0, raw_ev)
        if ft_lower == 'timeout':
            reasoning = "Gateway timeout appears transient and has a high predicted recovery probability. Retry is economically justified."
        else:
            reasoning = (
                f"Transient failure has high recovery probability ({recovery_probability*100:.1f}%). "
                f"Retry is economically justified with ₹{expected_recovery_value:.2f} expected net recovery value against ₹{retry_cost:.0f} retry cost."
            )
    elif recovery_probability > 0.40 and raw_ev > 0:
        action = ACTION_CUSTOMER_ACTION
        expected_recovery_value = max(0.0, raw_ev)
        reasoning = (
            f"Moderate recovery probability ({recovery_probability*100:.1f}%). "
            f"Recommend customer notification to re-authenticate or switch payment rail."
        )
    else:
        action = ACTION_STOP
        expected_recovery_value = 0.0
        reasoning = (
            f"Low recovery probability ({recovery_probability*100:.1f}%) or non-viable economic return (Expected Net Value <= ₹0). "
            f"Halting automated retries to avoid unnecessary gateway fees."
        )
    
    return {
        'action': action,
        'expected_value': round(expected_recovery_value, 2),
        'reasoning': reasoning
    }
