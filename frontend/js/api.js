// Smart Payment Retry Engine - Secure API Client
const API_BASE_URL = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
    ? 'http://localhost:5005'
    : window.location.origin;

let _userToken = null;
let _adminToken = null;

async function getAuthToken(role = 'USER') {
    if (role === 'ADMIN') {
        if (_adminToken) return _adminToken;
        try {
            const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username: 'demo_admin', password: 'Admin@12345' })
            });
            if (res.ok) {
                const data = await res.json();
                _adminToken = data.token;
                return _adminToken;
            }
        } catch (e) {
            console.warn('[Auth] Admin token fetch failed:', e);
        }
    }

    if (_userToken) return _userToken;

    // Check sessionStorage
    const cached = sessionStorage.getItem('retry_engine_token');
    if (cached) {
        _userToken = cached;
        return _userToken;
    }

    // Authenticate as standard demo user
    try {
        const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: 'demo_user', password: 'User@12345' })
        });
        if (res.ok) {
            const data = await res.json();
            _userToken = data.token;
            sessionStorage.setItem('retry_engine_token', _userToken);
            return _userToken;
        }
    } catch (e) {
        console.warn('[Auth] User token fetch failed:', e);
    }
    return null;
}

async function fetchAPI(endpoint, options = {}, role = 'USER') {
    const url = `${API_BASE_URL}${endpoint}`;
    const token = await getAuthToken(role);

    const defaultHeaders = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    };

    if (token) {
        defaultHeaders['Authorization'] = `Bearer ${token}`;
    }

    const config = {
        ...options,
        headers: {
            ...defaultHeaders,
            ...options.headers
        }
    };

    try {
        let response = await fetch(url, config);

        // If 401 Unauthorized, token might be expired; refresh token once and retry
        if (response.status === 401 && token) {
            sessionStorage.removeItem('retry_engine_token');
            _userToken = null;
            _adminToken = null;
            const freshToken = await getAuthToken(role);
            if (freshToken) {
                config.headers['Authorization'] = `Bearer ${freshToken}`;
                response = await fetch(url, config);
            }
        }
        
        if (!response.ok) {
            let errorMsg = `Server error ${response.status}: ${response.statusText}`;
            try {
                const errData = await response.json();
                if (errData) {
                    errorMsg = errData.message || errData.error || errorMsg;
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
    ensureAuthenticated: () => getAuthToken('USER'),
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
    }, 'ADMIN'),
    getModelMetrics: () => fetchAPI('/api/model/metrics'),
    retrainModel: () => fetchAPI('/api/model/retrain', { method: 'POST' }, 'ADMIN'),
    downloadReportBlob: async () => {
        const token = await getAuthToken('USER');
        const res = await fetch(`${API_BASE_URL}/api/analytics/export`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!res.ok) {
            let err = `Export failed (${res.status})`;
            try {
                const d = await res.json();
                err = d.message || err;
            } catch (e) {}
            throw new Error(err);
        }
        return await res.blob();
    },
    getReportExportUrl: () => `${API_BASE_URL}/api/analytics/export`
};
