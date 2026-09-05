import io
import csv
from flask import Blueprint, jsonify, Response
from services.analytics_service import (
    calculate_overview,
    calculate_baseline_comparison,
    calculate_by_failure_type
)
from database.models import Transaction, RecoveryDecision
from utils.auth import jwt_required
from utils.validators import sanitize_csv_cell

bp = Blueprint('analytics', __name__, url_prefix='/api/analytics')

@bp.route('/overview', methods=['GET'])
@jwt_required
def overview():
    """Get aggregate recovery engine KPIs"""
    data = calculate_overview()
    return jsonify(data), 200

@bp.route('/comparison', methods=['GET'])
@jwt_required
def comparison():
    """Get comparative analysis between naive baseline and AI model"""
    data = calculate_baseline_comparison()
    return jsonify(data), 200

@bp.route('/by-failure-type', methods=['GET'])
@jwt_required
def by_failure_type():
    """Get metrics broken down by failure type"""
    data = calculate_by_failure_type()
    return jsonify(data), 200

@bp.route('/export', methods=['GET'])
@jwt_required
def export_report():
    """
    Download transactions and recovery decisions report as CSV
    Hardened against Formula / CSV Injection attacks.
    """
    transactions = Transaction.query.order_by(Transaction.created_at.desc()).limit(1000).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Transaction ID', 'Merchant ID', 'Amount (INR)', 'Failure Type',
        'Payment Method', 'Card Issuer', 'Customer History', 'Retry #',
        'Hours Since Failure', 'Recovery Probability', 'Recommended Action',
        'Expected Recovery Value', 'Decision Reasoning', 'Outcome', 'Timestamp'
    ])
    
    for txn in transactions:
        dec = RecoveryDecision.query.filter_by(transaction_id=txn.transaction_id).first()
        writer.writerow([
            sanitize_csv_cell(txn.transaction_id),
            sanitize_csv_cell(txn.merchant_id),
            txn.amount,
            sanitize_csv_cell(txn.failure_type),
            sanitize_csv_cell(txn.payment_method or ''),
            sanitize_csv_cell(txn.card_issuer or ''),
            sanitize_csv_cell(txn.customer_history or ''),
            txn.retry_number,
            txn.time_since_failure_hours,
            round(dec.predicted_recovery_prob, 4) if dec and dec.predicted_recovery_prob is not None else '',
            sanitize_csv_cell(dec.recommended_action if dec else ''),
            round(dec.expected_recovery_value, 2) if dec and dec.expected_recovery_value is not None else '',
            sanitize_csv_cell(dec.decision_reasoning if dec else ''),
            sanitize_csv_cell(dec.actual_outcome if dec else ''),
            txn.created_at.isoformat() if txn.created_at else ''
        ])
        
    output.seek(0)
    response = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={
            'Content-Disposition': 'attachment; filename="recovery_report.csv"',
            'X-Content-Type-Options': 'nosniff'
        }
    )
    return response
