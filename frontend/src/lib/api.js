const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Make authenticated API request
 */
async function apiRequest(endpoint, options = {}) {
    const token = localStorage.getItem('access_token');

    const headers = {
        ...options.headers,
    };

    if (token) {
        headers['Authorization'] = `Bearer ${token}`;
    }

    // Don't set Content-Type for FormData
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${API_BASE}${endpoint}`, {
        ...options,
        headers,
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Request failed' }));
        throw new Error(error.detail || 'Request failed');
    }

    return response.json();
}

/**
 * Verify a document
 */
export async function verifyDocument(file, documentTypeHint = null) {
    const formData = new FormData();
    formData.append('file', file);

    if (documentTypeHint) {
        formData.append('document_type_hint', documentTypeHint);
    }

    return apiRequest('/api/v1/verify/process', {
        method: 'POST',
        body: formData,
    });
}

/**
 * Upscale a document image
 */
export async function upscaleDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    // Returns a Blob (image) not JSON
    const token = localStorage.getItem('access_token');
    const headers = {};
    if (token) headers['Authorization'] = `Bearer ${token}`;

    const response = await fetch(`${API_BASE}/api/v1/documents/upscale`, {
        method: 'POST',
        headers,
        body: formData,
    });

    if (!response.ok) {
        throw new Error('Upscaling failed');
    }

    return response.blob();
}

/**
 * Submit verification decision
 */
export async function submitDecision(requestId, decision, overrideReason = null) {
    return apiRequest('/api/v1/verify/decision', {
        method: 'POST',
        body: JSON.stringify({
            request_id: requestId,
            final_decision: decision,
            override_reason: overrideReason,
        }),
    });
}

/**
 * Get audit logs
 */
export async function getAuditLogs(page = 1, pageSize = 20) {
    return apiRequest(`/api/v1/audit/logs?page=${page}&page_size=${pageSize}`);
}

/**
 * Get current user profile
 */
export async function getCurrentUser() {
    return apiRequest('/api/v1/auth/me');
}
