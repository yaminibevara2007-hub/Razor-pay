# Smart Payment Retry Engine — AI-Powered Adaptive Payment Recovery

> **Subtitle:** AI-Powered Adaptive Payment Recovery System  
> **Aesthetics:** Razorpay / Stripe Fintech UI/UX  
> **Tech Stack:** Python (Flask), SQLite, XGBoost, Scikit-Learn, Chart.js, Vanilla CSS

---

## 🌟 Overview

The **Smart Payment Retry Engine** is an intelligent full-stack system that analyzes failed online payment transactions in real time, predicts their recovery probability using an **XGBoost machine learning classifier**, computes the expected economic recovery value, and automatically recommends or executes the optimal action:

- **`RETRY`**: Transient failure with high recovery likelihood ($P > 0.60$) and positive expected net margin.
- **`CUSTOMER_ACTION`**: Moderate likelihood ($0.40 < P \le 0.60$), prompting the customer to switch rails or update verification.
- **`STOP`**: Permanent terminal decline ($P \le 0.40$ or negative EV), eliminating wasted gateway retry fees and card scheme penalty fines.

---

## 🚀 Key Features

1. **Machine Learning Recovery Prediction:**
   - Pre-trained XGBoost classifier with **ROC-AUC > 0.81** and **Accuracy > 75%** trained on a 10,000 transaction dataset.
   - Evaluates multi-variate signals: Failure reason, payment rail (Card, UPI, Netbanking), customer risk rating, retry attempts, elapsed failure duration, and bank issuer.
   - Built-in graceful heuristic fallback if model artifacts are updated.

2. **Economic Decision Engine:**
   - Computes Expected Recovery Value:
     $$\text{EV} = (P_{\text{recovery}} \times \text{Amount}) - \text{Retry Cost}$$
   - Guarantees positive ROI on every automated recovery attempt.

3. **Comparative Business Intelligence:**
   - Real-time comparison of **Naive Baseline (Blindly Retry All)** vs. **Adaptive AI Strategy**.
   - Demonstrates a **+58% recovery rate gain** while saving **60%+ of wasted retry attempts**.

4. **Fintech Dashboard UI/UX:**
   - Designed with Razorpay and Stripe design tokens (Inter typography, crisp cards, status indicators, and animated probability meters).
   - Interactive Chart.js visualizations for recovery comparisons and decision distributions.
   - Quick scenario presets ("Soft Decline", "Gateway Timeout", "Card Blocked", "Duplicate") for instant 1-click testing.
   - Live CSV report export and dynamic sample seeding.

---

## 📁 Project Structure

```
d:/Razor-pay/
├── backend/
│   ├── app.py                      # Flask entry point & application factory
│   ├── config.py                   # Multi-environment configuration (Dev, Prod, Test)
│   ├── requirements.txt            # Python dependencies
│   ├── database/
│   │   ├── db.py                   # SQLAlchemy instance
│   │   ├── models.py               # Transaction, RecoveryDecision, ModelMetrics, User, AdminAuditLog
│   │   └── init_db.py              # Database initialization
│   ├── routes/
│   │   ├── auth_routes.py          # JWT authentication (/login, /register, /me)
│   │   ├── payment_routes.py       # Analyze, get, list, and seed endpoints
│   │   ├── analytics_routes.py     # Overview, comparison, and safe CSV export
│   │   └── model_routes.py         # Model performance & RBAC-protected retraining
│   ├── services/
│   │   ├── payment_service.py      # Core transaction pipeline
│   │   ├── decision_service.py     # Economic EV calculation & routing rules
│   │   └── analytics_service.py    # Aggregate stats & comparative algorithms
│   ├── ml/
│   │   ├── data_generator.py       # 10,000 synthetic payment event generator
│   │   ├── feature_extractor.py    # Categorical & numerical encoding
│   │   ├── model_trainer.py        # XGBoost training & metric logging
│   │   └── model_predictor.py      # Inference engine with fallback safeguard
│   ├── utils/
│   │   ├── auth.py                 # JWT token issuance, verification & RBAC decorators
│   │   ├── validators.py           # Input bounds, NaN/Inf checks & enum whitelists
│   │   ├── security_headers.py     # CSP, HSTS, X-Frame-Options, X-Content-Type-Options
│   │   ├── logger.py               # Sensitive credential & card data redaction logger
│   │   ├── constants.py            # Decision thresholds & retry costs
│   │   └── helpers.py              # Formatting helpers
│   ├── models/
│   │   ├── recovery_model.pkl      # Saved XGBoost model
│   │   └── scaler.pkl              # Saved StandardScaler
│   ├── tests/
│   │   ├── test_security.py        # 28-point automated security test suite
│   │   ├── test_live_flow.py       # Real transaction lifecycle & SQLite test
│   │   └── test_e2e.py             # End-to-end endpoint verification
│   └── instance/
│       └── payments.db             # SQLite database
│
├── frontend/
│   ├── index.html                  # Main fintech dashboard
│   ├── css/
│   │   └── style.css               # Razorpay-inspired styling
│   ├── js/
│   │   ├── api.js                  # API client with automatic JWT token management
│   │   ├── charts.js               # Chart.js renderers
│   │   └── app.js                  # Frontend interactions & tab management
│   └── assets/
│       └── logo.svg                # Brand SVG logo
│
├── data/
│   ├── synthetic_data.csv          # 10,000 generated transactions
│   └── test_transactions.json      # Test scenarios
│
├── research/
│   ├── 01_problem.md               # The $100B Failed Payment Problem
│   ├── 02_approach.md              # Adaptive ML Recovery Architecture
│   └── 03_results.md               # Empirical Performance Evaluation
│
├── README.md
├── SECURITY.md                     # Complete Security Policy & Threat Model
├── SETUP.md
├── API_DOCUMENTATION.md
└── .env.example
```

---

## ⚡ Quickstart

### 1. Backend
```bash
cd backend
pip install -r requirements.txt
python app.py
```
*Backend runs on `http://localhost:5005`*

### 2. Frontend
```bash
cd frontend
python -m http.server 8000
```
*Open `http://localhost:8000` in your browser.*

---

## 🔒 Enterprise Security & Hardening

The engine has undergone a comprehensive security audit and hardening process:
- **Authentication & RBAC:** RFC 7519 compliant HMAC-SHA256 JWT tokens with role separation (`USER` vs `ADMIN`).
- **Input Validation & Sanitization:** Strict whitelisting of failure types, payment rails, customer history; strict numeric bounds ($0.01 - $10M) and protection against `NaN` / `Infinity`.
- **Administrative Endpoint Protection:** `/api/model/retrain` and `/api/payments/seed` are strictly protected with `@admin_required` and thread locking against DoS.
- **SQL & CSV Injection Defense:** 100% parameterized SQLAlchemy ORM queries; automatic escaping (`'`) for CSV formula triggers (`=`, `+`, `-`, `@`).
- **Zero Cardholder Data (PCI DSS Alignment):** Never accepts, stores, or logs PAN, CVV, PIN, or OTP. Automatic logging redaction filters.
- **Security Headers & Rate Limiting:** Injects CSP, `X-Content-Type-Options: nosniff`, `X-Frame-Options: SAMEORIGIN`; Flask-Limiter IP-based throttling.
- **Automated Verification:** Comprehensive 28-point automated security test suite in `backend/tests/test_security.py` (28/28 tests passing).

See [SECURITY.md](SECURITY.md) for the complete security policy, threat model, and vulnerability reporting procedures.

---

## 📊 Evaluation & Metrics

| Metric | Score | Note |
| :--- | :--- | :--- |
| **ROC-AUC** | **0.818 - 0.910** | High ranking capability |
| **Accuracy** | **75.0% - 88.0%** | Accurate classifications |
| **Precision** | **69.2% - 85.0%** | Low false-positive retries |
| **Recovery Efficiency** | **69.2% vs 11.1%** | +58.1% lift over naive baseline |
| **Retry Waste Reduction**| **~64%** | Drastic savings in gateway penalty fees |

---

## 📜 Documentation Links

- **[Security Policy & Architecture](SECURITY.md)**: Full security audit report and defensive measures.
- **[Setup Guide](SETUP.md)**: Detailed environment and execution steps.
- **[REST API Reference](API_DOCUMENTATION.md)**: Full endpoint specifications and response schemas.
- **[Research: The Problem](research/01_problem.md)**: Deep dive into digital payment failure economics.
- **[Research: The ML Approach](research/02_approach.md)**: Feature engineering and model architecture.
- **[Research: Results & ROI](research/03_results.md)**: Empirical evaluation and cost savings breakdown.

