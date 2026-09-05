import urllib.request
import json
import sqlite3
import os

BASE = 'http://localhost:5005/api'

def run_tests():
    print("=== Starting Smart Payment Retry Engine Verification ===")
    
    # 1. Fetch initial overview
    req = urllib.request.urlopen(f'{BASE}/analytics/overview')
    initial_overview = json.loads(req.read().decode())
    print("Initial Overview:", initial_overview)
    
    # TEST 1: Analyze ₹48,500 Gateway Timeout UPI
    payload_1 = {
        'amount': 48500,
        'failure_type': 'timeout',
        'payment_method': 'upi',
        'customer_history': 'good',
        'retry_number': 1,
        'time_since_failure_hours': 1,
        'card_issuer': 'HDFC'
    }
    data = json.dumps(payload_1).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/payments/analyze', data=data, headers={'Content-Type': 'application/json'})
    res_1 = json.loads(urllib.request.urlopen(req).read().decode())
    print("\n--- TEST 1: INR 48,500 Timeout (UPI, Good) ---")
    print(json.dumps(res_1, indent=2))
    assert res_1['recommended_action'] == 'RETRY', f"Expected RETRY, got {res_1['recommended_action']}"
    assert "Gateway timeout" in res_1['reasoning'], f"Expected Timeout reasoning, got {res_1['reasoning']}"
    assert res_1['expected_recovery_value'] > 0, "Expected recovery value must be > 0"
    
    # Verify transaction in transactions ledger endpoint
    req = urllib.request.urlopen(f'{BASE}/payments?limit=5')
    recent_txns = json.loads(req.read().decode())
    found_1 = next((t for t in recent_txns if t['transaction_id'] == res_1['transaction_id']), None)
    assert found_1 is not None, "TEST 1 transaction not found in ledger!"
    print(f"Ledger record verified: {found_1['transaction_id']} | INR {found_1['amount']} | {found_1['action']} | Method: {found_1['payment_method']}")
    
    # Verify overview updated
    req = urllib.request.urlopen(f'{BASE}/analytics/overview')
    updated_overview_1 = json.loads(req.read().decode())
    print("Updated Overview after TEST 1:", updated_overview_1)
    assert updated_overview_1['total_analyzed'] == initial_overview['total_analyzed'] + 1, "Total analyzed did not increment by 1"
    assert updated_overview_1['retry_recommended'] == initial_overview['retry_recommended'] + 1, "Retry count did not increment by 1"
    
    # TEST 2: Analyze INR 5,000 Duplicate Transaction Card
    payload_2 = {
        'amount': 5000,
        'failure_type': 'duplicate',
        'payment_method': 'card',
        'customer_history': 'good',
        'retry_number': 1,
        'time_since_failure_hours': 1,
        'card_issuer': 'HDFC'
    }
    data = json.dumps(payload_2).encode('utf-8')
    req = urllib.request.Request(f'{BASE}/payments/analyze', data=data, headers={'Content-Type': 'application/json'})
    res_2 = json.loads(urllib.request.urlopen(req).read().decode())
    print("\n--- TEST 2: INR 5,000 Duplicate (Card, Good) ---")
    print(json.dumps(res_2, indent=2))
    assert res_2['recommended_action'] == 'STOP', f"Expected STOP, got {res_2['recommended_action']}"
    assert res_2['expected_recovery_value'] == 0.0, f"Expected 0.0 EV for STOP, got {res_2['expected_recovery_value']}"
    assert "Duplicate transaction" in res_2['reasoning'], f"Expected Duplicate reasoning, got {res_2['reasoning']}"
    
    # Check overview updated
    req = urllib.request.urlopen(f'{BASE}/analytics/overview')
    updated_overview_2 = json.loads(req.read().decode())
    print("Updated Overview after TEST 2:", updated_overview_2)
    assert updated_overview_2['total_analyzed'] == updated_overview_1['total_analyzed'] + 1, "Total analyzed did not increment"
    assert updated_overview_2['stop_recommended'] == updated_overview_1['stop_recommended'] + 1, "STOP count did not increment"
    
    # TEST 3 & 4: Direct SQLite persistence verification
    db_path = os.path.join(os.path.dirname(__file__), 'backend', 'instance', 'payments.db')
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("SELECT transaction_id, amount, failure_type, payment_method FROM transactions WHERE transaction_id IN (?, ?)", (res_1['transaction_id'], res_2['transaction_id']))
    db_rows = cur.fetchall()
    conn.close()
    assert len(db_rows) == 2, f"Expected 2 rows in SQLite, found {len(db_rows)}"
    print("\n--- TEST 3 & 4: SQLite Persistence Verified ---")
    for r in db_rows:
        print(f"Persisted in SQLite: ID={r[0]}, Amount=INR {r[1]}, Failure={r[2]}, Method={r[3]}")
        
    print("\nALL TEST 1, TEST 2, TEST 3 & TEST 4 VERIFICATIONS PASSED SUCCESSFULLY!")

if __name__ == '__main__':
    run_tests()
