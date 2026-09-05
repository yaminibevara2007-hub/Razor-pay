# Security Policy & Architecture

## 1. Overview & Security Philosophy
The **Smart Payment Retry Engine** is designed as a mission-critical financial decision support system. Because failed payment recovery operates in close proximity to payment settlement pipelines, strict defensive-engineering standards are enforced across the entire stack:
- **Defense in Depth:** Validation, authentication, and authorization are verified at every layer.
- **Zero Cardholder Data (PCI DSS Alignment):** The engine operates exclusively on non-sensitive payment metadata. Cardholder PAN, CVV, PIN, and OTP are strictly forbidden from entering the system.
- **Least Privilege:** Public users cannot trigger administrative operations such as model retraining or synthetic seeding.
- **Fail Securely:** Any malformed input, missing credential, or unhandled condition defaults to rejecting the operation without exposing server internals.

---

## 2. Authentication Architecture
- **Standard:** JSON Web Tokens (JWT) adhering to RFC 7519.
- **Algorithm:** HMAC-SHA256 (`HS256`) signed with an environment-configured `JWT_SECRET_KEY` (minimum 32 characters in production).
- **Claims Structure:**
  - `sub`: Unique Subject Identifier (User ID as string)
  - `username`: Account handle
  - `role`: Role string (`USER` or `ADMIN`)
  - `iat`: Timestamp of issuance
  - `exp`: Timestamp of expiration (default 24 hours, configurable via `JWT_EXPIRATION_HOURS`)
- **Transport:** HTTP Authorization Header using the standard Bearer scheme:
  ```http
  Authorization: Bearer <token>
  ```
- **Storage:** Frontend clients store access tokens in `sessionStorage` or transient in-memory state; tokens are never persisted in unencrypted permanent disk cookies.

---

## 3. Role-Based Access Control (RBAC)
The engine enforces two distinct authorization levels:

| Role | Permitted Endpoints | Blocked Endpoints |
|---|---|---|
| **`USER`** | `/api/payments/analyze`, `/api/payments` (GET), `/api/analytics/*`, `/api/model/metrics` | `/api/model/retrain`, `/api/payments/seed` |
| **`ADMIN`** | All endpoints including `/api/model/retrain` and `/api/payments/seed` | None |

- **Retrain Protection:** Model retraining (`/api/model/retrain`) is restricted to the `ADMIN` role and enforced via a non-blocking thread lock to prevent resource exhaustion or DoS attacks.
- **Seed Protection:** The test seeding endpoint (`/api/payments/seed`) is restricted to `ADMIN` and can be completely toggled off via `ENABLE_SEED_ENDPOINT=False` in production environments.
- **Audit Logging:** Administrative actions (retraining, seeding) are recorded in the `admin_audit_logs` database table with timestamp, admin ID, IP address, and status.

---

## 4. Input Validation & Data Sanitization
All incoming JSON payloads undergo strict schema and value validation in `backend/utils/validators.py`:
- **Amount (`amount`):**
  - Must be a finite numeric value (`math.isnan()` and `math.isinf()` checks).
  - Must be strictly positive: `$0.01 \le \text{amount} \le \$10,000,000.00`.
- **Failure Types (`failure_type`):**
  - Whitelist-enforced: `network_error`, `insufficient_funds`, `timeout`, `bank_downtime`, `card_expired`, `fraud_suspected`, `duplicate`, `system_error`.
- **Payment Methods (`payment_method`):**
  - Whitelist-enforced: `card`, `upi`, `netbanking`, `wallet`.
- **Customer History (`customer_history`):**
  - Whitelist-enforced: `good`, `average`, `poor`, `new`.
- **Retry Number (`retry_number`):**
  - Valid integer bounded between `1` and `10`.
- **Time Since Failure (`time_since_failure_hours`):**
  - Non-negative integer or float bounded between `0` and `720` (30 days maximum).
- **Transaction ID Format (`transaction_id`):**
  - Validated with regex `^[a-zA-Z0-9_\-]{8,64}$` to eliminate path traversal and formatting exploits.

---

## 5. Defense Against Common Vulnerabilities

### 5.1 SQL Injection
- The application uses **SQLAlchemy ORM** parameterized queries exclusively.
- Raw SQL string formatting or concatenated queries are strictly prohibited across all models, queries, and migrations.

### 5.2 Cross-Site Scripting (XSS) & Content Sniffing
- Strict HTTP Security Headers are injected into every HTTP response via `backend/utils/security_headers.py`:
  - `Content-Security-Policy: default-src 'self'; ...`
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: SAMEORIGIN`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`

### 5.3 Cross-Origin Resource Sharing (CORS)
- CORS is restricted to authorized frontend origins (e.g. `http://localhost:8000`, `http://127.0.0.1:8000`) defined via `FRONTEND_ORIGINS`.
- Wildcard `*` origins are rejected in production configurations.

### 5.4 CSV Formula Injection (Spreadsheet Macro Defense)
- Exported transaction CSV records are sanitized before stream generation.
- Any string cell starting with unsafe formula triggers (`=`, `+`, `-`, `@`) is escaped with a leading single quote (`'`), neutralizing potential remote code execution or formula evaluation in Microsoft Excel and Google Sheets.

### 5.5 Information Disclosure & Error Sanitization
- Centralized error handlers capture HTTP `400`, `401`, `403`, `404`, `429`, and `500` errors.
- Internal Python stack traces, absolute server file paths, and database schema errors are never returned to clients; clean, standardized JSON error messages are returned instead.
- Debug mode (`DEBUG = False`) is enforced in production environments.

### 5.6 Rate Limiting & DoS Mitigation
- The engine implements **Flask-Limiter** with IP-based memory tracking:
  - Standard API Endpoints: `120 per minute`
  - Authentication Endpoints: `10 per minute`
  - Resource-Intensive ML Retrain: `2 per minute`

---

## 6. Sensitive Cardholder Data Policy
The Smart Payment Retry Engine is an **intelligent retry decision and prediction service**, not a payment gateway. 

> **Strict Zero-Storage Policy:**
> - The application NEVER accepts, stores, transmits, or logs Primary Account Numbers (PANs), CVVs, Card PINs, or One-Time Passwords (OTPs).
> - Logging filters (`backend/utils/logger.py`) automatically detect and redact sensitive patterns (passwords, auth tokens, and 13-19 digit card numbers).

---

## 7. Reporting Security Vulnerabilities
If you discover a potential security vulnerability within this project:
1. Do **NOT** file a public GitHub issue.
2. Email your findings with reproduction steps to the security team or maintainer.
3. Include an impact assessment and detailed proof-of-concept.
4. We aim to acknowledge receipt within 24 hours and provide an advisory / patch timeline.
