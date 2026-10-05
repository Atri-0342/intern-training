const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
    ...options.headers,
};

if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
}

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

    if (unauthorizedHandler) {
        unauthorizedHandler();
    }

    const error = new Error("Unauthorized");
    error.status = 401;

    throw error;
}


    if (!response.ok) {
    const error = new Error(
        data?.error?.message ||
        data?.detail ||
        `Request failed with status ${response.status}`
    );

    error.status = response.status;

    throw error;
}

    return data;
}