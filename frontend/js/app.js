// Smart Payment Retry Engine - Main Application Logic

document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initAnalyzerForm();
    initPresets();
    loadDashboard();
    startDashboardPolling();
});

// ==========================================
// Toast Notification System
// ==========================================
function showToast(message, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
        <span class="toast-icon">${type === 'success' ? '✓' : type === 'error' ? '✕' : 'ℹ'}</span>
        <span class="toast-message">${message}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add('fade-out');
        setTimeout(() => toast.remove(), 400);
    }, 3500);
}

// ==========================================
// TAB NAVIGATION
// ==========================================
function initTabs() {
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const tabName = this.dataset.tab;
            switchTab(tabName);
        });
    });
}

function switchTab(tabName) {
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });

    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tabName) {
            btn.classList.add('active');
        }
    });

    const activeTab = document.getElementById(tabName);
    if (activeTab) {
        activeTab.classList.add('active');
    }

    if (tabName === 'dashboard') {
        loadDashboard();
        startDashboardPolling();
    } else {
        stopDashboardPolling();
        if (tabName === 'transactions') {
            loadTransactions();
        } else if (tabName === 'model') {
            loadModelMetrics();
        }
    }
}

// ==========================================
// DASHBOARD
// ==========================================
let dashboardPollInterval = null;

function startDashboardPolling() {
    stopDashboardPolling();
    // Poll every 20 seconds only when on dashboard tab
    dashboardPollInterval = setInterval(() => {
        const activeTab = document.querySelector('.tab.active');
        if (activeTab && activeTab.id === 'dashboard') {
            loadDashboard(true);
        }
    }, 20000);
}

function stopDashboardPolling() {
    if (dashboardPollInterval) {
        clearInterval(dashboardPollInterval);
        dashboardPollInterval = null;
    }
}

async function refreshDashboardManual() {
    const btn = document.getElementById('refresh-dashboard-btn');
    const originalText = btn ? btn.innerHTML : '';
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Fetching Live Data...';
    }
    try {
        await loadDashboard();
        showToast('Dashboard synchronized with database', 'info');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = originalText;
        }
    }
}

async function loadDashboard(isSilent = false) {
    try {
        const [overview, comparison] = await Promise.all([
            API.getOverview(),
            API.getComparison()
        ]);

        const totalAnalyzed = overview.total_analyzed || 0;

        // Update KPI metrics directly from real database records
        document.getElementById('total-analyzed').textContent = totalAnalyzed.toLocaleString();
        document.getElementById('recovery-rate').textContent = (overview.recovery_rate || 0).toFixed(1) + '%';
        document.getElementById('recovered-value').textContent = '₹' + formatNumber(overview.total_recovery_value || 0);
        document.getElementById('avg-probability').textContent = ((overview.average_recovery_probability || 0) * 100).toFixed(0) + '%';

        // Update comparison stats
        const improvementTag = document.getElementById('rate-improvement-badge');
        if (improvementTag) {
            const diff = comparison?.improvement?.better_recovery_rate || 0;
            improvementTag.textContent = (diff >= 0 ? `+${diff.toFixed(1)}%` : `${diff.toFixed(1)}%`) + ' vs Baseline';
        }

        const savedCostsTag = document.getElementById('saved-retries-count');
        if (savedCostsTag) {
            const retriesSaved = comparison?.improvement?.fewer_unnecessary_retries || 0;
            savedCostsTag.textContent = `${retriesSaved} retries saved`;
        }

        // Render charts with real database numbers
        updateComparisonChart(comparison);
        updateDecisionsChart(overview);

        // Update Live indicator timestamp
        const liveText = document.getElementById('live-indicator-text');
        const liveDot = document.getElementById('live-dot');
        const lastUpdated = document.getElementById('last-updated-time');
        if (liveText) liveText.textContent = 'LIVE';
        if (liveDot) liveDot.style.backgroundColor = '#31A24C';
        if (lastUpdated) {
            const now = new Date();
            lastUpdated.textContent = 'Last updated: ' + now.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit', second: '2-digit', hour12: true });
        }
    } catch (error) {
        console.error('Error loading dashboard:', error);
        const liveText = document.getElementById('live-indicator-text');
        const liveDot = document.getElementById('live-dot');
        if (liveText) liveText.textContent = 'OFFLINE';
        if (liveDot) liveDot.style.backgroundColor = '#E74C3C';
        if (!isSilent) {
            showToast('Failed to load dashboard metrics: ' + error.message, 'error');
        }
    }
}

// ==========================================
// ANALYZER FORM
// ==========================================
function initAnalyzerForm() {
    const form = document.getElementById('analyzeForm');
    if (!form) return;

    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = form.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner"></span> Analyzing with ML Engine...';

        const formData = new FormData(form);
        const payload = Object.fromEntries(formData);
        
        // Data casting
        payload.amount = parseFloat(payload.amount);
        payload.retry_number = parseInt(payload.retry_number || 1, 10);
        payload.time_since_failure_hours = parseInt(payload.time_since_failure_hours || 0, 10);

        try {
            const result = await API.analyzePayment(payload);
            displayAnalysisResult(result);
            showToast('Payment analyzed & persisted to database', 'success');
            // Background refresh dashboard so next view is immediately synced
            loadDashboard(true);
        } catch (error) {
            console.error('Analysis error:', error);
            showToast('Error analyzing payment: ' + error.message, 'error');
        } finally {
            submitBtn.disabled = false;
            submitBtn.textContent = originalText;
        }
    });
}

function displayAnalysisResult(result) {
    const resultsDiv = document.getElementById('analysisResults');
    if (!resultsDiv) return;

    document.getElementById('result-txn-id').textContent = result.transaction_id;
    document.getElementById('result-amount').textContent = '₹' + formatNumber(result.amount);
    
    const prob = result.predicted_recovery_probability;
    const probPct = (prob * 100).toFixed(1);
    document.getElementById('result-probability').textContent = probPct + '%';

    // Probability bar fill
    const barFill = document.getElementById('result-probability-bar');
    barFill.style.width = probPct + '%';
    if (prob > 0.60) {
        barFill.style.background = 'linear-gradient(90deg, #0052CC, #31A24C)';
    } else if (prob > 0.40) {
        barFill.style.background = 'linear-gradient(90deg, #F79646, #FFAB00)';
    } else {
        barFill.style.background = 'linear-gradient(90deg, #E74C3C, #FF5630)';
    }

    // Action badge
    const actionBadge = document.getElementById('result-action');
    actionBadge.textContent = result.recommended_action.replace('_', ' ');
    actionBadge.className = 'result-value action-badge ' + result.recommended_action.toLowerCase().replace('_', '-');

    // Expected recovery value
    document.getElementById('result-expected-value').textContent = '₹' + formatNumber(result.expected_recovery_value);

    // Confidence badge
    const confidenceBadge = document.getElementById('result-confidence');
    confidenceBadge.textContent = result.confidence + ' Confidence';
    confidenceBadge.className = 'result-value confidence-badge ' + result.confidence.toLowerCase();

    // Reasoning
    document.getElementById('result-reasoning').textContent = result.reasoning;

    // Unhide and scroll
    resultsDiv.classList.remove('hidden');
    resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

// Preset Quick-Fill buttons for testing
function initPresets() {
    const presets = {
        'soft': {
            amount: 6500,
            failure_type: 'soft_decline',
            payment_method: 'card',
            customer_history: 'good',
            retry_number: 1,
            time_since_failure_hours: 1,
            card_issuer: 'HDFC'
        },
        'timeout': {
            amount: 2800,
            failure_type: 'timeout',
            payment_method: 'upi',
            customer_history: 'good',
            retry_number: 1,
            time_since_failure_hours: 0,
            card_issuer: ''
        },
        'hard': {
            amount: 4500,
            failure_type: 'hard_decline',
            payment_method: 'card',
            customer_history: 'bad',
            retry_number: 2,
            time_since_failure_hours: 24,
            card_issuer: 'SBI'
        },
        'duplicate': {
            amount: 15000,
            failure_type: 'duplicate',
            payment_method: 'netbanking',
            customer_history: 'medium',
            retry_number: 1,
            time_since_failure_hours: 0,
            card_issuer: ''
        }
    };

    document.querySelectorAll('.preset-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const key = btn.dataset.preset;
            const data = presets[key];
            if (!data) return;

            const form = document.getElementById('analyzeForm');
            for (const [name, val] of Object.entries(data)) {
                const field = form.elements[name];
                if (field) field.value = val;
            }
            showToast(`Loaded preset: ${btn.textContent}`, 'info');
        });
    });
}

// ==========================================
// TRANSACTIONS
// ==========================================
async function loadTransactions() {
    const tbody = document.getElementById('transactionsBody');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 24px;"><span class="spinner"></span> Loading transactions...</td></tr>';

    try {
        const transactions = await API.getTransactions(50);
        tbody.innerHTML = '';

        if (!transactions || transactions.length === 0) {
            tbody.innerHTML = '<tr><td colspan="8" style="text-align: center; padding: 32px; color: var(--text-light);">No transactions recorded yet. Analyze a payment in Recovery Analyzer to populate the ledger.</td></tr>';
            return;
        }

        transactions.forEach(txn => {
            const probPct = ((txn.probability || 0) * 100).toFixed(0);
            const actionClass = (txn.action || 'PENDING').toLowerCase().replace('_', '-');
            const dateStr = txn.timestamp ? new Date(txn.timestamp).toLocaleString('en-IN', {
                month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
            }) : '-';

            const row = document.createElement('tr');
            row.innerHTML = `
                <td><code>${txn.transaction_id}</code></td>
                <td><strong>₹${formatNumber(txn.amount)}</strong></td>
                <td><span class="tag-pill tag-${txn.failure_type}">${formatFailureType(txn.failure_type)}</span></td>
                <td><span class="tag-pill tag-method">${formatPaymentMethod(txn.payment_method)}</span></td>
                <td>
                    <div class="table-prob-container">
                        <span class="table-prob-val">${probPct}%</span>
                        <div class="table-prob-bar"><div class="table-prob-fill" style="width: ${probPct}%;"></div></div>
                    </div>
                </td>
                <td><span class="action-badge ${actionClass}">${(txn.action || 'PENDING').replace('_', ' ')}</span></td>
                <td>₹${formatNumber(txn.expected_value || 0)}</td>
                <td style="color: var(--text-light); font-size: 13px;">${dateStr}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading transactions:', error);
        tbody.innerHTML = `<tr><td colspan="8" style="text-align: center; color: var(--danger); padding: 24px;">Failed to load transactions: ${error.message}</td></tr>`;
    }
}

function formatPaymentMethod(method) {
    const map = {
        'card': 'Card',
        'upi': 'UPI',
        'netbanking': 'NetBanking'
    };
    return map[method] || (method ? method.toUpperCase() : 'CARD');
}

function formatFailureType(type) {
    const map = {
        'soft_decline': 'Soft Decline',
        'hard_decline': 'Hard Decline',
        'timeout': 'Timeout',
        'duplicate': 'Duplicate'
    };
    return map[type] || type;
}

// ==========================================
// MODEL METRICS
// ==========================================
async function loadModelMetrics() {
    try {
        const metrics = await API.getModelMetrics();

        updateMetricDisplay('accuracy', metrics.accuracy);
        updateMetricDisplay('precision', metrics.precision);
        updateMetricDisplay('recall', metrics.recall);
        updateMetricDisplay('f1', metrics.f1_score);
        updateMetricDisplay('auc', metrics.roc_auc);

        const trainedDate = document.getElementById('model-trained-date');
        if (trainedDate && metrics.trained_at) {
            trainedDate.textContent = 'Trained at: ' + new Date(metrics.trained_at).toLocaleString('en-IN');
        }

        const totalPreds = document.getElementById('model-total-preds');
        if (totalPreds && metrics.total_predictions) {
            totalPreds.textContent = `${metrics.correct_predictions.toLocaleString()} / ${metrics.total_predictions.toLocaleString()} correct`;
        }
    } catch (error) {
        console.error('Error loading model metrics:', error);
        showToast('Failed to load ML metrics: ' + error.message, 'error');
    }
}

function updateMetricDisplay(metric, value) {
    const display = document.getElementById(`metric-${metric}`);
    const bar = document.getElementById(`metric-${metric}-bar`);

    if (display) {
        display.textContent = (value * 100).toFixed(1) + '%';
    }
    if (bar) {
        bar.style.width = (value * 100) + '%';
    }
}

async function retrainModel() {
    const btn = document.getElementById('retrain-btn');
    const originalText = btn ? btn.textContent : '';

    if (!confirm('Train a new XGBoost model on 10,000 synthetic payment recovery records?')) return;

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Retraining XGBoost Model...';
    }

    try {
        const result = await API.retrainModel();
        showToast('Model retrained successfully with updated weights!', 'success');
        await loadModelMetrics();
        await loadDashboard();
    } catch (error) {
        console.error('Retrain error:', error);
        showToast('Error retraining model: ' + error.message, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

// ==========================================
// GENERATE SAMPLE DATA & EXPORT
// ==========================================
async function generateSampleData() {
    const btn = document.getElementById('generate-sample-btn');
    const originalText = btn ? btn.textContent : '';

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<span class="spinner"></span> Seeding transactions...';
    }

    try {
        const res = await API.seedTransactions(25);
        showToast(`Generated ${res.count || 25} new sample transactions!`, 'success');
        await loadDashboard();
    } catch (error) {
        console.error('Error generating sample data:', error);
        showToast('Failed to seed transactions: ' + error.message, 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = originalText;
        }
    }
}

async function downloadReport() {
    showToast('Downloading transactions and decisions CSV...', 'info');
    try {
        const blob = await API.downloadReportBlob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'recovery_report.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        a.remove();
        showToast('CSV report downloaded successfully', 'success');
    } catch (e) {
        showToast('Failed to download report: ' + e.message, 'error');
    }
}

// ==========================================
// UTILITIES
// ==========================================
function formatNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '0';
    return Number(num).toLocaleString('en-IN', {
        maximumFractionDigits: 2,
        minimumFractionDigits: 0
    });
}
