# Research: Adaptive Machine Learning Retry Architecture

## 1. System Philosophy

The **Smart Payment Retry Engine** shifts payment recovery from a static, rule-based process to an **adaptive, real-time machine learning decision pipeline**.

Instead of treating all failed payments identically, the engine extracts multivariate signals from the transaction context, predicts the precise conditional recovery probability $P(\text{recovery} \mid \vec{x})$, calculates the expected economic value of recovery, and routes the transaction to the optimal action:

```
[Failed Transaction Event]
            │
            ▼
 [Feature Extraction & Scaling]
  • Amount & Currency
  • Failure Type (Categorical)
  • Payment Method (Card, UPI, Netbanking)
  • Customer History Rating (Good, Medium, Bad)
  • Retry Attempt Number
  • Elapsed Time Since Failure
  • Card Issuer / Routing Bank
            │
            ▼
[XGBoost Probability Predictor] ──> Returns P(recovery) ∈ [0, 1]
            │
            ▼
 [Economic Decision Engine]
  • Expected Value: (P × Amount) - Retry Cost
  • Policy Evaluation:
      - If P > 0.60 ──> RETRY
      - If 0.40 < P <= 0.60 and EV > 0 ──> CUSTOMER_ACTION
      - If P <= 0.40 or EV <= 0 ──> STOP
            │
            ▼
 [Execution & Audit Logging]
  • SQLite Persistence
  • Executive KPI Dashboards
```

## 2. Machine Learning Pipeline Specification

### Algorithm Selection: Gradient Boosted Trees (XGBoost)
We selected **XGBoost (eXtreme Gradient Boosting)** over deep neural networks and logistic regression for several technical reasons:
1. **Heterogeneous Tabular Data:** Payment records consist of a mix of numerical quantities (transaction amount, elapsed hours, retry attempts) and categorical attributes (failure reason, payment rail, customer tier). Decision trees naturally handle non-linear tabular interactions without requiring heavy dimensionality expansion.
2. **Probability Calibration:** XGBoost with logistic loss objective (`eval_metric='logloss'`) provides well-calibrated posterior probabilities essential for calculating accurate expected economic value.
3. **Sub-Millisecond Inference:** Payment checkout flows require ultra-low latency. The compiled tree model evaluates inference in `< 5ms`, making it production-ready for real-time checkout loops.

### Feature Engineering
The feature extractor encodes categorical signals deterministically:
- `amount` (float): Continuous monetary quantity.
- `failure_type` (encoded int): soft_decline (0), hard_decline (1), timeout (2), duplicate (3).
- `payment_method` (encoded int): card (0), upi (1), netbanking (2).
- `customer_history` (encoded int): bad (0), medium (1), good (2).
- `retry_number` (int): Monotonically decreasing success propensity on subsequent attempts.
- `time_since_failure_hours` (int): Temporal freshness of the transaction attempt.
- `card_issuer` (binary int): Availability of verified issuer routing metadata.

Features are standardized via `StandardScaler` fitted on the training split to ensure consistent numeric magnitude.

## 3. Heuristic Safeguard Fallback
To ensure high system reliability even during cold starts or model file updates, the engine includes an automated rule-based fallback that safely handles predictions using domain-grounded heuristics.
