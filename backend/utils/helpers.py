def format_currency_inr(value):
    """Format value as INR currency string"""
    try:
        return f"₹{float(value):,.2f}"
    except (ValueError, TypeError):
        return "₹0.00"

def get_confidence_tier(probability):
    """Categorize recovery probability into confidence levels"""
    if probability > 0.70:
        return 'High'
    elif probability > 0.40:
        return 'Medium'
    return 'Low'
