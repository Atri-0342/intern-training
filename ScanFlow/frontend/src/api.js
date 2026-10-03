const BASE_URL = '';

let authToken = null;
let unauthorizedHandler = null;

export function setAuthToken(token) {
    authToken = token;
}

export function clearAuthToken() {
    authToken = null;
}

export function setUnauthorizedHandler(handler) {
    unauthorizedHandler = handler;
}

export async function apiFetch(path, options = {}) {
    const url = `${BASE_URL}${path}`;

    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
    };

    if (authToken) {
        headers.Authorization = `Bearer ${authToken}`;
    }

    const response = await fetch(url, { ...options, headers });

    let data = null;
    try {
        data = await response.json();
    } catch {
        // No JSON body — fine for 204, or a non-JSON error page.
    }

    if (response.status === 401) {
        clearAuthToken();
        if (unauthorizedHandler) unauthorizedHandler();
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        throw new Error(
            data?.error?.message ||
            `Request failed with status ${response.status}`
        );
    }

    return data;
}