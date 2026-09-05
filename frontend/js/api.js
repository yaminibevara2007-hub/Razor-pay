// API Client configuration
const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:5005'
    : window.location.origin;

async function fetchAPI(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };

    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            let errorMsg = `Server error ${response.status}: ${response.statusText}`;
            try {
                const errData = await response.json();
                if (errData && errData.error) {
                    errorMsg = errData.error;
                }
            } catch (e) {
                // Not JSON
            }
            throw new Error(errorMsg);
        }

        return await response.json();
    } catch (error) {
        console.error(`[API Error] ${endpoint}:`, error);
        throw error;
    }
}

// Service helper methods
const API = {
    getOverview: () => fetchAPI('/api/analytics/overview'),
    getComparison: () => fetchAPI('/api/analytics/comparison'),
    getByFailureType: () => fetchAPI('/api/analytics/by-failure-type'),
    getTransactions: (limit = 50) => fetchAPI(`/api/payments?limit=${limit}`),
    getTransaction: (id) => fetchAPI(`/api/payments/${id}`),
    analyzePayment: (payload) => fetchAPI('/api/payments/analyze', {
        method: 'POST',
        body: JSON.stringify(payload)
    }),
    seedTransactions: (count = 25) => fetchAPI('/api/payments/seed', {
        method: 'POST',
        body: JSON.stringify({ count })
    }),
    getModelMetrics: () => fetchAPI('/api/model/metrics'),
    retrainModel: () => fetchAPI('/api/model/retrain', { method: 'POST' }),
    getReportExportUrl: () => `${API_BASE_URL}/api/analytics/export`
};
