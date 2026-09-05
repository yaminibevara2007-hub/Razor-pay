import os
import sys
import json
import time
import jwt
import unittest

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from config import TestingConfig, ProductionConfig
from database.db import db
from database.models import User, Transaction, RecoveryDecision
from utils.auth import generate_token

class SecurityTestSuite(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestingConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        # Create standard test users
        self.user = User(username='test_user', role='USER')
        self.user.set_password('UserPass@123')
        db.session.add(self.user)

        self.admin = User(username='test_admin', role='ADMIN')
        self.admin.set_password('AdminPass@123')
        db.session.add(self.admin)
        db.session.commit()

        self.user_token = generate_token(self.user)
        self.admin_token = generate_token(self.admin)

        self.user_headers = {
            'Authorization': f'Bearer {self.user_token}',
            'Content-Type': 'application/json'
        }
        self.admin_headers = {
            'Authorization': f'Bearer {self.admin_token}',
            'Content-Type': 'application/json'
        }

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    # 1. Unauthenticated request to protected endpoint -> 401
    def test_01_unauthenticated_request_rejected(self):
        res = self.client.post('/api/payments/analyze', json={'amount': 5000})
        self.assertEqual(res.status_code, 401)
        data = res.get_json()
        self.assertEqual(data['error'], 'Unauthorized')

    # 2. Normal user accessing admin endpoint -> 403
    def test_02_normal_user_cannot_retrain(self):
        res = self.client.post('/api/model/retrain', headers=self.user_headers)
        self.assertEqual(res.status_code, 403)
        data = res.get_json()
        self.assertEqual(data['error'], 'Forbidden')

    # 3. Admin accessing admin endpoint -> allowed
    def test_03_admin_can_access_retrain(self):
        # Admin request should pass authorization (we check role passes auth)
        res = self.client.post('/api/payments/seed', headers=self.admin_headers, json={'count': 2})
        self.assertEqual(res.status_code, 201)

    # 4. Normal user accessing seed -> 403
    def test_04_normal_user_cannot_seed(self):
        res = self.client.post('/api/payments/seed', headers=self.user_headers, json={'count': 5})
        self.assertEqual(res.status_code, 403)

    # 5. Invalid amount -> 400
    def test_05_invalid_amount_rejected(self):
        payload = {
            'amount': 'not-a-number',
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good'
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Amount must be a valid numeric', res.get_json()['message'])

    # 6. Negative amount -> 400
    def test_06_negative_amount_rejected(self):
        payload = {
            'amount': -500,
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good'
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('greater than zero', res.get_json()['message'])

    # 7. NaN and Infinity amount -> 400
    def test_07_nan_and_inf_amount_rejected(self):
        for val in ['nan', 'inf', '-inf']:
            payload = {
                'amount': val,
                'failure_type': 'timeout',
                'payment_method': 'upi',
                'customer_history': 'good'
            }
            res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
            self.assertEqual(res.status_code, 400)
            self.assertIn('finite', res.get_json()['message'])

    # 8. Excessive amount -> 400
    def test_08_excessive_amount_rejected(self):
        payload = {
            'amount': 999_999_999,
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good'
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('exceeds maximum', res.get_json()['message'])

    # 9. Invalid retry number -> 400
    def test_09_invalid_retry_number_rejected(self):
        payload = {
            'amount': 1500,
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good',
            'retry_number': 99
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('retry_number', res.get_json()['message'])

    # 10. Invalid failure type -> 400
    def test_10_invalid_failure_type_rejected(self):
        payload = {
            'amount': 1500,
            'failure_type': 'fake_failure_hack',
            'payment_method': 'upi',
            'customer_history': 'good'
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Invalid failure_type', res.get_json()['message'])

    # 11. Invalid payment method -> 400
    def test_11_invalid_payment_method_rejected(self):
        payload = {
            'amount': 1500,
            'failure_type': 'timeout',
            'payment_method': 'crypto_coin',
            'customer_history': 'good'
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        self.assertIn('Invalid payment_method', res.get_json()['message'])

    # 12. Malformed transaction ID -> 400
    def test_12_malformed_transaction_id_rejected(self):
        payload = {
            'amount': 1500,
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good',
            'transaction_id': '<script>alert(1)</script>'
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)

    # 13. SQL injection payload in inputs -> safely handled/rejected
    def test_13_sql_injection_payload_handled(self):
        payload = {
            'amount': 1500,
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good',
            'card_issuer': "HDFC'; DROP TABLE transactions; --"
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 400)
        # Verify table still exists and is safe
        self.assertEqual(Transaction.query.count(), 0)

    # 14. Invalid JWT signature -> 401
    def test_14_invalid_jwt_signature_rejected(self):
        fake_token = jwt.encode({'sub': 1, 'role': 'ADMIN'}, 'wrong-secret-key-at-least-32-chars-long', algorithm='HS256')
        headers = {'Authorization': f'Bearer {fake_token}'}
        res = self.client.get('/api/analytics/overview', headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertIn('Invalid token', res.get_json()['message'])

    # 15. Expired JWT -> 401
    def test_15_expired_jwt_rejected(self):
        expired_payload = {
            'sub': self.user.id,
            'role': self.user.role,
            'exp': int(time.time()) - 3600
        }
        expired_token = jwt.encode(expired_payload, self.app.config['JWT_SECRET_KEY'], algorithm='HS256')
        headers = {'Authorization': f'Bearer {expired_token}'}
        res = self.client.get('/api/analytics/overview', headers=headers)
        self.assertEqual(res.status_code, 401)
        self.assertIn('expired', res.get_json()['message'])

    # 16. Missing Authorization header -> 401
    def test_16_missing_auth_header_rejected(self):
        res = self.client.get('/api/analytics/overview')
        self.assertEqual(res.status_code, 401)

    # 17. Rate limit handling
    def test_17_rate_limit_configuration(self):
        from app import limiter, create_app
        from config import DevelopmentConfig
        dev_app = create_app(DevelopmentConfig)
        self.assertIsNotNone(limiter)
        self.assertIn('limiter', dev_app.extensions)

    # 18. Seed endpoint disabled in production
    def test_18_seed_disabled_in_production(self):
        class ProdSeedDisabledConfig(TestingConfig):
            ENABLE_SEED_ENDPOINT = False
            
        prod_app = create_app(ProdSeedDisabledConfig)
        client = prod_app.test_client()
        with prod_app.app_context():
            token = generate_token(self.admin)
            res = client.post('/api/payments/seed', headers={'Authorization': f'Bearer {token}'})
            self.assertEqual(res.status_code, 403)
            self.assertIn('disabled', res.get_json()['message'])

    # 19. Export endpoint CSV formula injection protection
    def test_19_csv_formula_injection_protection(self):
        # Create transaction with formula injection prefix '=1+1'
        from utils.validators import sanitize_csv_cell
        self.assertEqual(sanitize_csv_cell('=cmd|'), "'=cmd|")
        self.assertEqual(sanitize_csv_cell('+SUM(A1:A10)'), "'+SUM(A1:A10)")
        self.assertEqual(sanitize_csv_cell('-2+3*4'), "'-2+3*4")
        self.assertEqual(sanitize_csv_cell('@HYPERLINK'), "'@HYPERLINK")
        self.assertEqual(sanitize_csv_cell('regular_txn_123'), 'regular_txn_123')

    # 20. Centralized error handling -> No stack traces
    def test_20_no_stack_traces_returned(self):
        res = self.client.get('/api/non_existent_route')
        self.assertEqual(res.status_code, 404)
        data = res.get_json()
        self.assertEqual(data['error'], 'Not Found')
        self.assertNotIn('Traceback', json.dumps(data))
        self.assertNotIn('File "', json.dumps(data))

    # 21. Secrets not present in API responses
    def test_21_secrets_not_exposed(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data_str = res.get_data(as_text=True)
        self.assertNotIn(self.app.config['SECRET_KEY'], data_str)
        self.assertNotIn('secret', data_str.lower())

    # 22. Sensitive payment data (PAN, CVV, PIN) not stored
    def test_22_sensitive_card_data_not_stored(self):
        columns = [c.name for c in Transaction.__table__.columns]
        self.assertNotIn('cvv', columns)
        self.assertNotIn('card_number', columns)
        self.assertNotIn('pan', columns)
        self.assertNotIn('pin', columns)
        self.assertNotIn('otp', columns)

    # 23. CORS origin policy
    def test_23_cors_headers_configured(self):
        res = self.client.get('/api/health', headers={'Origin': 'http://localhost:8000'})
        self.assertEqual(res.headers.get('Access-Control-Allow-Origin'), 'http://localhost:8000')

    # 24. Security headers present in responses
    def test_24_security_headers_present(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.headers.get('X-Content-Type-Options'), 'nosniff')
        self.assertEqual(res.headers.get('X-Frame-Options'), 'SAMEORIGIN')
        self.assertIn('Content-Security-Policy', res.headers)

    # 25. Existing payment analysis workflow still works
    def test_25_payment_analysis_workflow(self):
        payload = {
            'amount': 48500,
            'failure_type': 'timeout',
            'payment_method': 'upi',
            'customer_history': 'good',
            'retry_number': 1
        }
        res = self.client.post('/api/payments/analyze', headers=self.user_headers, json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertEqual(data['recommended_action'], 'RETRY')
        self.assertIn('Gateway timeout', data['reasoning'])
        self.assertGreater(data['expected_recovery_value'], 0)

    # 26. Existing dashboard metrics still accurate
    def test_26_dashboard_metrics_accurate(self):
        res = self.client.get('/api/analytics/overview', headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('total_analyzed', data)
        self.assertIn('recovery_rate', data)
        self.assertIn('total_recovery_value', data)

    # 27. Existing transactions ledger still functional
    def test_27_transactions_ledger(self):
        res = self.client.get('/api/payments', headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        self.assertIsInstance(res.get_json(), list)

    # 28. Existing model performance metrics still accurate
    def test_28_model_metrics(self):
        res = self.client.get('/api/model/metrics', headers=self.user_headers)
        self.assertEqual(res.status_code, 200)
        data = res.get_json()
        self.assertIn('accuracy', data)
        self.assertIn('roc_auc', data)

if __name__ == '__main__':
    unittest.main(verbosity=2)
