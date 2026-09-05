import urllib.request
import json
import sys

BASE_URL = 'http://localhost:5005'

def get(endpoint):
    url = BASE_URL + endpoint
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def post(endpoint, payload):
    url = BASE_URL + endpoint
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )
    with urllib.request.urlopen(req) as resp:
        return resp.status, json.loads(resp.read().decode())

def run_all_tests():
    print("==================================================")
    print("  Smart Payment Retry Engine - E2E Verification  ")
    print("==================================================")

    # 1. Root & Health
    status, root = get('/')
    assert status == 200, f"Root failed with status {status}"
    print(f"[OK] Root endpoint online: {root['name']} (v{root['version']})")

    # 2. Payment Analyzer with test cases
    with open('data/test_transactions.json', 'r') as f:
        cases = json.load(f)

    print(f"\n[OK] Testing {len(cases)} payment failure scenarios:")
    for case in cases:
        status, res = post('/api/payments/analyze', case['payload'])
        assert status == 200, f"Analyze failed for {case['description']}"
        action = res['recommended_action']
        prob = res['predicted_recovery_probability']
        ev = res['expected_recovery_value']
        conf = res['confidence']
        print(f"   [{action}] P={prob:.3f} | EV=INR {ev:,.2f} | Conf={conf} | {case['description']}")

    # 3. Overview Analytics
    status, ov = get('/api/analytics/overview')
    assert status == 200
    print(f"\n[OK] Analytics Overview:")
    print(f"   Total Analyzed: {ov['total_analyzed']}")
    print(f"   Recovery Rate: {ov['recovery_rate']}%")
    print(f"   Recovered Value: INR {ov['total_recovery_value']:,.2f}")
    print(f"   Avg Recovery Prob: {ov['average_recovery_probability']*100:.1f}%")
    print(f"   Policy Breakdown: Retry={ov['retry_recommended']} | Stop={ov['stop_recommended']} | CustAction={ov['customer_action_recommended']}")

    # 4. Comparison
    status, comp = get('/api/analytics/comparison')
    assert status == 200
    print(f"\n[OK] Comparison Engine:")
    print(f"   Baseline Recovery: {comp['baseline']['recovery_rate']}%")
    print(f"   AI Model Recovery: {comp['ai_model']['recovery_rate']}%")
    print(f"   Efficiency Gain:   +{comp['improvement']['better_recovery_rate']}%")
    print(f"   Unnecessary Retries Saved: {comp['improvement']['fewer_unnecessary_retries']}")

    # 5. Model Metrics
    status, metrics = get('/api/model/metrics')
    assert status == 200
    print(f"\n[OK] Model Metrics:")
    print(f"   Accuracy:  {metrics['accuracy']*100:.2f}%")
    print(f"   Precision: {metrics['precision']*100:.2f}%")
    print(f"   Recall:    {metrics['recall']*100:.2f}%")
    print(f"   F1-Score:  {metrics['f1_score']*100:.2f}%")
    print(f"   ROC-AUC:   {metrics['roc_auc']:.4f}")

    # 6. CSV Export
    export_url = BASE_URL + '/api/analytics/export'
    with urllib.request.urlopen(export_url) as resp:
        csv_data = resp.read().decode('utf-8')
        lines = csv_data.strip().splitlines()
        print(f"\n[OK] CSV Export:")
        print(f"   Status: {resp.status}")
        print(f"   Total rows generated: {len(lines)}")
        print(f"   Header: {lines[0]}")

    print("\n==================================================")
    print("  ALL TESTS PASSED SUCCESSFULLY! (100% HEALTHY)   ")
    print("==================================================")

if __name__ == '__main__':
    run_all_tests()
