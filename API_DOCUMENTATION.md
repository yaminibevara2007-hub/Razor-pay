# Smart Payment Retry Engine — REST API Documentation

The Smart Payment Retry Engine exposes a clean, RESTful JSON API for analyzing failed payments, retrieving aggregate analytics, exploring transaction logs, and inspecting or retraining the machine learning model.

**Base URL:** `http://localhost:5000`

---

## 1. Payment Endpoints

### 1.1 Analyze Failed Payment
Analyzes a failed payment in real-time, queries the XGBoost model for recovery probability, calculates expected economic value, determines the optimal recommendation (`RETRY`, `CUSTOMER_ACTION`, or `STOP`), and persists the transaction in the database.

- **Method:** `POST`
- **Path:** `/api/payments/analyze`
- **Headers:** `Content-Type: application/json`

#### Request Body
```json
{
  "amount": 5000.00,
  "failure_type": "soft_decline",
  "payment_method": "card",
  "customer_history": "good",
  "card_issuer": "HDFC",
  "retry_number": 1,
  "time_since_failure_hours": 2,
  "merchant_id": "MERCHANT_001"
}
```

#### Field Descriptions
| Field | Type | Required | Allowed Values / Format | Description |
| :--- | :--- | :--- | :--- | :--- |
| `amount` | Float | Yes | Positive number | Transaction amount in INR |
| `failure_type` | String | Yes | `soft_decline`, `hard_decline`, `timeout`, `duplicate` | Primary gateway error category |
| `payment_method` | String | Yes | `card`, `upi`, `netbanking` | Payment rail used |
| `customer_history` | String | Yes | `good`, `medium`, `bad` | Customer reliability rating |
| `card_issuer` | String | No | e.g. `HDFC`, `ICICI`, `SBI`, `Axis` | Card issuing bank |
| `retry_number` | Integer | No | `1` to `5` (Default: 1) | Current retry count |
| `time_since_failure_hours` | Integer | No | `0` to `168` (Default: 0) | Hours since initial failure |

#### Response (`200 OK`)
```json
{
  "transaction_id": "txn_9a8543c0bb",
  "amount": 5000.0,
  "failure_type": "soft_decline",
  "payment_method": "card",
  "customer_history": "good",
  "card_issuer": "HDFC",
  "predicted_recovery_probability": 0.685,
  "recommended_action": "RETRY",
  "expected_recovery_value": 3415.00,
  "confidence": "High",
  "reasoning": "High confidence (68.5%) in transient failure recovery. Expected recovery value is ₹3,415.00 against ₹10 retry cost."
}
```

---

### 1.2 Get Transaction Details
Retrieve a specific transaction and its associated recovery decision by ID.

- **Method:** `GET`
- **Path:** `/api/payments/<transaction_id>`

#### Response (`200 OK`)
```json
{
  "transaction_id": "txn_9a8543c0bb",
  "merchant_id": "MERCHANT_001",
  "amount": 5000.0,
  "currency": "INR",
  "failure_type": "soft_decline",
  "payment_method": "card",
  "card_issuer": "HDFC",
  "customer_history": "good",
  "retry_number": 1,
  "time_since_failure_hours": 2,
  "decision": {
    "action": "RETRY",
    "probability": 0.685,
    "expected_value": 3415.0,
    "reasoning": "High confidence (68.5%) in transient failure recovery...",
    "actual_outcome": "success"
  },
  "timestamp": "2026-09-05T10:04:53.000000"
}
```

---

### 1.3 List Transactions
List recent transactions and recovery decisions.

- **Method:** `GET`
- **Path:** `/api/payments?limit=50`

#### Query Parameters
- `limit` (optional, integer): Number of transactions to return (default: 50).

#### Response (`200 OK`)
```json
[
  {
    "transaction_id": "txn_9a8543c0bb",
    "merchant_id": "MERCH_103",
    "amount": 5000.0,
    "currency": "INR",
    "failure_type": "soft_decline",
    "payment_method": "card",
    "card_issuer": "HDFC",
    "customer_history": "good",
    "action": "RETRY",
    "probability": 0.685,
    "expected_value": 3415.0,
    "actual_outcome": "success",
    "timestamp": "2026-09-05T10:04:53.000000"
  }
]
```

---

### 1.4 Seed Sample Transactions
Populate the database with a batch of diverse test transactions.

- **Method:** `POST`
- **Path:** `/api/payments/seed`
- **Request Body:**
```json
{
  "count": 25
}
```
- **Response (`201 Created`):**
```json
{
  "message": "Successfully generated 25 sample transactions",
  "count": 25
}
```

---

## 2. Analytics Endpoints

### 2.1 Dashboard Overview
Get aggregate key performance indicators.

- **Method:** `GET`
- **Path:** `/api/analytics/overview`

#### Response (`200 OK`)
```json
{
  "total_analyzed": 36,
  "retry_recommended": 13,
  "stop_recommended": 10,
  "customer_action_recommended": 13,
  "successful_recoveries": 11,
  "recovery_rate": 30.56,
  "average_recovery_probability": 0.475,
  "total_recovery_value": 362519.46
}
```

---

### 2.2 Baseline vs. AI Comparison
Compare naive retry-all strategy against adaptive ML policy.

- **Method:** `GET`
- **Path:** `/api/analytics/comparison`

#### Response (`200 OK`)
```json
{
  "baseline": {
    "strategy": "Always retry once (Naive)",
    "retry_attempts": 36,
    "successful_recoveries": 4,
    "recovery_rate": 11.1
  },
  "ai_model": {
    "strategy": "Adaptive ML Retry (P > 0.5)",
    "retry_attempts": 13,
    "successful_recoveries": 9,
    "recovery_rate": 69.2
  },
  "improvement": {
    "better_recovery_rate": 58.1,
    "fewer_unnecessary_retries": 23,
    "estimated_cost_savings": 230.0
  }
}
```

---

### 2.3 Analytics by Failure Type
Breakdown metrics grouped by failure category.

- **Method:** `GET`
- **Path:** `/api/analytics/by-failure-type`

#### Response (`200 OK`)
```json
{
  "soft_decline": {
    "count": 18,
    "avg_recovery_probability": 0.508,
    "successful_recoveries": 5
  },
  "timeout": {
    "count": 11,
    "avg_recovery_probability": 0.666,
    "successful_recoveries": 6
  },
  "hard_decline": {
    "count": 6,
    "avg_recovery_probability": 0.109,
    "successful_recoveries": 0
  },
  "duplicate": {
    "count": 1,
    "avg_recovery_probability": 0.001,
    "successful_recoveries": 0
  }
}
```

---

### 2.4 Export CSV Report
Download all logged transactions and recovery decisions formatted as CSV.

- **Method:** `GET`
- **Path:** `/api/analytics/export`
- **Response:** `Content-Type: text/csv` file download (`recovery_report.csv`).

---

## 3. Machine Learning Model Endpoints

### 3.1 Model Performance Metrics
Retrieve current cross-validation scores and training metadata.

- **Method:** `GET`
- **Path:** `/api/model/metrics`

#### Response (`200 OK`)
```json
{
  "accuracy": 0.88,
  "precision": 0.85,
  "recall": 0.82,
  "f1_score": 0.835,
  "roc_auc": 0.91,
  "total_predictions": 2000,
  "correct_predictions": 1760,
  "trained_at": "2026-09-05T10:06:53.214906"
}
```

---

### 3.2 Retrain Model
Trigger retraining on a freshly generated synthetic dataset of 10,000 transactions and update pickled weights.

- **Method:** `POST`
- **Path:** `/api/model/retrain`

#### Response (`200 OK`)
```json
{
  "message": "Model retrained successfully and artifacts updated",
  "metrics": {
    "accuracy": 0.7495,
    "precision": 0.6916,
    "recall": 0.7141,
    "f1_score": 0.7027,
    "roc_auc": 0.8179,
    "total_predictions": 2000,
    "correct_predictions": 1499
  }
}
```
