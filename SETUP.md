# Setup Guide — Smart Payment Retry Engine

Complete guide to running the Smart Payment Retry Engine locally.

## Prerequisites

- **Python:** 3.9+ (Python 3.13 tested and supported)
- **pip:** Package installer for Python
- **Web Browser:** Modern browser (Chrome, Firefox, Edge, Safari)

---

## 1. Backend Setup

### Step 1: Install Dependencies
Open a terminal in the project root:

```bash
cd backend
pip install -r requirements.txt
```

*Dependencies installed:* `Flask`, `Flask-CORS`, `Flask-SQLAlchemy`, `SQLAlchemy`, `xgboost`, `scikit-learn`, `pandas`, `numpy`.

### Step 2: Generate Dataset & Train Model
Train the initial XGBoost model on 10,000 synthetic payment failure transactions:

```bash
python ml/model_trainer.py
```

This generates:
- Synthetic dataset: `data/synthetic_data.csv`
- Model pickle: `backend/models/recovery_model.pkl`
- Standard scaler: `backend/models/scaler.pkl`

### Step 3: Run the Backend Flask Server
From the `backend` directory or the project root:

```bash
python app.py
```

The Flask API will start on: **`http://localhost:5000`**

---

## 2. Frontend Setup

In a new terminal window, navigate to the `frontend` directory:

```bash
cd frontend
python -m http.server 8000
```

Open your browser and navigate to: **`http://localhost:8000`**

---

## 3. End-to-End Walkthrough in 5 Minutes

1. **Dashboard Tab:**
   - Observe live aggregated KPIs: Total Analyzed, Recovery Rate, Recovered Value (₹), and Average Recovery Probability.
   - Inspect the **Baseline vs AI Model** comparative bar chart and the **Decisions Distribution** doughnut chart.
   - Click **"Generate Sample Transactions"** to inject 25 new random failure events and watch the charts and KPIs update in real-time.
   - Click **"Export CSV Report"** to download the complete transaction audit log.

2. **Recovery Analyzer Tab:**
   - Click any preset button (e.g. *"Soft Decline (Card)"* or *"Gateway Timeout (UPI)"*) to auto-fill the form with realistic parameters.
   - Click **"Analyze & Predict Optimal Action"**.
   - Review the animated probability bar, the recommended action badge (`RETRY`, `CUSTOMER_ACTION`, `STOP`), expected recovery value, and human-readable reasoning.

3. **Transactions Tab:**
   - Browse the audit ledger of recent failed payment transactions, probabilities, actions, and timestamps.

4. **Model Performance Tab:**
   - Inspect the validation metrics: Accuracy, Precision, Recall, F1-Score, and ROC-AUC.
   - Click **"Retrain Model on Fresh Data"** to run a complete retraining loop on a new 10,000 sample distribution.

---

## Troubleshooting

- **Port 5000 in use?**
  Set `PORT=5001` or edit the port in `backend/app.py`.
- **Database reset?**
  Delete `backend/instance/payments.db` and restart the backend server; tables will be re-created automatically.
- **CORS Issues?**
  Flask-CORS is enabled on all `/api/*` endpoints.
