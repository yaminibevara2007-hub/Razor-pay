import urllib.request
import json
import sys

def verify():
    print("=" * 60)
    print("  SMART PAYMENT RETRY ENGINE - COMPREHENSIVE STATUS CHECK")
    print("=" * 60)

    # 1. Backend API Checks (Port 5005)
    endpoints = [
        ('/api/health', 'GET'),
        ('/', 'GET'),
        ('/api/analytics/overview', 'GET'),
        ('/api/analytics/comparison', 'GET'),
        ('/api/analytics/by-failure-type', 'GET'),
        ('/api/payments?limit=5', 'GET'),
        ('/api/model/metrics', 'GET'),
        ('/api/analytics/export', 'GET')
    ]

    all_passed = True

    print("\n[1] Checking Backend Endpoints (http://localhost:5005):")
    for ep, method in endpoints:
        url = f'http://localhost:5005{ep}'
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=3) as r:
                print(f"  [PASS] {method} {ep} -> Status {r.status}")
        except Exception as e:
            print(f"  [FAIL] {method} {ep} -> {e}")
            all_passed = False

    # 2. Test Live Payment Prediction
    print("\n[2] Checking ML Prediction Engine:")
    try:
        payload = {
            'amount': 5000.0,
            'failure_type': 'soft_decline',
            'payment_method': 'card',
            'customer_history': 'good',
            'card_issuer': 'HDFC',
            'retry_number': 1,
            'time_since_failure_hours': 2
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            'http://localhost:5005/api/payments/analyze',
            data=data,
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            res = json.loads(r.read().decode('utf-8'))
            prob = res.get('predicted_recovery_probability')
            action = res.get('recommended_action')
            ev = res.get('expected_recovery_value')
            print(f"  [PASS] /api/payments/analyze -> Status {r.status}")
            print(f"         Prediction: P={prob} | Action: {action} | EV: INR {ev}")
    except Exception as e:
        print(f"  [FAIL] /api/payments/analyze -> {e}")
        all_passed = False

    # 3. Frontend Static Server Checks (Port 8000)
    print("\n[3] Checking Frontend Dashboard Assets (http://localhost:8000):")
    assets = [
        ('/', 'Dashboard HTML (index.html)'),
        ('/css/style.css', 'Fintech Stylesheet'),
        ('/js/api.js', 'API Client'),
        ('/js/charts.js', 'Chart.js Visualizer'),
        ('/js/app.js', 'Application Logic'),
        ('/assets/logo.svg', 'SVG Logo'),
        ('/favicon.ico', 'Favicon')
    ]

    for path, label in assets:
        url = f'http://localhost:8000{path}'
        try:
            with urllib.request.urlopen(url, timeout=3) as r:
                print(f"  [PASS] {label} ({path}) -> Status {r.status}")
        except Exception as e:
            print(f"  [FAIL] {label} ({path}) -> {e}")
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("  ALL SYSTEMS OPERATIONAL & WORKING EXCELLENTLY (100%)")
    else:
        print("  WARNING: SOME CHECKS FAILED - SEE LOGS ABOVE")
    print("=" * 60)

if __name__ == '__main__':
    verify()
