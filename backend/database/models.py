from datetime import datetime
from database.db import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    merchant_id = db.Column(db.String(100), nullable=False, default='TEST_MERCHANT')
    amount = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), default='INR')
    failure_type = db.Column(db.String(50), nullable=False)  # "timeout", "soft_decline", "hard_decline", "duplicate"
    payment_method = db.Column(db.String(50))                 # "card", "upi", "netbanking"
    card_issuer = db.Column(db.String(100))
    customer_history = db.Column(db.String(50))              # "good", "medium", "bad"
    retry_number = db.Column(db.Integer, default=1)
    time_since_failure_hours = db.Column(db.Integer, default=0)
    gateway = db.Column(db.String(100), default='razorpay')
    is_recoverable = db.Column(db.Boolean, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    decisions = db.relationship('RecoveryDecision', backref='transaction', lazy=True, cascade="all, delete-orphan")

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'merchant_id': self.merchant_id,
            'amount': self.amount,
            'currency': self.currency,
            'failure_type': self.failure_type,
            'payment_method': self.payment_method,
            'card_issuer': self.card_issuer,
            'customer_history': self.customer_history,
            'retry_number': self.retry_number,
            'time_since_failure_hours': self.time_since_failure_hours,
            'gateway': self.gateway,
            'is_recoverable': self.is_recoverable,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class RecoveryDecision(db.Model):
    __tablename__ = 'recovery_decisions'
    
    id = db.Column(db.Integer, primary_key=True)
    transaction_id = db.Column(db.String(100), db.ForeignKey('transactions.transaction_id'), nullable=False, index=True)
    predicted_recovery_prob = db.Column(db.Float)        # 0.0 to 1.0
    recommended_action = db.Column(db.String(50))              # "RETRY", "STOP", "CUSTOMER_ACTION"
    expected_recovery_value = db.Column(db.Float)
    decision_reasoning = db.Column(db.Text)              # Why we made this decision
    executed = db.Column(db.Boolean, default=False)
    actual_outcome = db.Column(db.String(50), nullable=True)  # "success", "failed", "stopped"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'transaction_id': self.transaction_id,
            'predicted_recovery_prob': self.predicted_recovery_prob,
            'recommended_action': self.recommended_action,
            'expected_recovery_value': self.expected_recovery_value,
            'decision_reasoning': self.decision_reasoning,
            'executed': self.executed,
            'actual_outcome': self.actual_outcome,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class ModelMetrics(db.Model):
    __tablename__ = 'model_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    metric_date = db.Column(db.DateTime, default=datetime.utcnow)
    accuracy = db.Column(db.Float)
    precision = db.Column(db.Float)
    recall = db.Column(db.Float)
    f1_score = db.Column(db.Float)
    roc_auc = db.Column(db.Float)
    total_predictions = db.Column(db.Integer, default=0)
    correct_predictions = db.Column(db.Integer, default=0)

    def to_dict(self):
        return {
            'id': self.id,
            'metric_date': self.metric_date.isoformat() if self.metric_date else None,
            'accuracy': self.accuracy,
            'precision': self.precision,
            'recall': self.recall,
            'f1_score': self.f1_score,
            'roc_auc': self.roc_auc,
            'total_predictions': self.total_predictions,
            'correct_predictions': self.correct_predictions
        }

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='USER')  # 'USER' or 'ADMIN'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class AdminAuditLog(db.Model):
    __tablename__ = 'admin_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    user_id = db.Column(db.Integer, nullable=True)
    username = db.Column(db.String(80), nullable=True)
    action = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'SUCCESS', 'FAILED', 'REJECTED'
    ip_address = db.Column(db.String(45), nullable=True)
    details = db.Column(db.Text, nullable=True)

    def to_dict(self):
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'username': self.username,
            'action': self.action,
            'status': self.status,
            'ip_address': self.ip_address,
            'details': self.details
        }

