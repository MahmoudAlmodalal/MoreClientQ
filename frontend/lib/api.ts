/**
 * Centralized API client and authentication helpers for the frontend.
 * Works on both Client and Server Components.
 */

// Helper to decode JWT on the client or server
export function decodeJwt(token: string) {
  try {
    const base64Url = token.split(".")[1];
    const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
    const jsonPayload = decodeURIComponent(
      atob(base64)
        .split("")
        .map((c) => "%" + ("00" + c.charCodeAt(0).toString(16)).slice(-2))
        .join("")
    );
    return JSON.parse(jsonPayload);
  } catch {
    return null;
  }
}

// Client-side cookie helpers
export function setCookie(name: string, value: string, days = 7) {
  if (typeof document === "undefined") return;
  const expires = new Date();
  expires.setTime(expires.getTime() + days * 24 * 60 * 60 * 1000);
  document.cookie = `${name}=${value};expires=${expires.toUTCString()};path=/;SameSite=Lax;Secure`;
}

export function getCookie(name: string): string | null {
  if (typeof document === "undefined") return null;
  const nameEQ = name + "=";
  const ca = document.cookie.split(";");
  for (let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) === " ") c = c.substring(1, c.length);
    if (c.indexOf(nameEQ) === 0) return c.substring(nameEQ.length, c.length);
  }
  return null;
}

export function eraseCookie(name: string) {
  setCookie(name, "", -1);
}

// Dynamically determine the base API URL
export function getApiBaseUrl(): string {
  if (typeof window === "undefined") {
    // Server-side
    const backendUrl = process.env.BACKEND_URL || "http://backend:8000";
    return backendUrl.replace(/\/+$/, "") + "/api/v1";
  } else {
    // Client-side
    // Check if we have NEXT_PUBLIC_API_URL env variable
    let publicUrl = process.env.NEXT_PUBLIC_API_URL || "";
    if (!publicUrl) {
      // Fallback: request same host on port 8000 or relative if proxying
      const protocol = window.location.protocol;
      const hostname = window.location.hostname;
      publicUrl = `${protocol}//${hostname}:8000/api/v1`;
    }
    // Clean up trailing slashes and normalize
    publicUrl = publicUrl.replace(/\/+$/, "");
    if (!publicUrl.endsWith("/v1") && !publicUrl.endsWith("/api/v1")) {
      publicUrl = publicUrl.endsWith("/api") ? `${publicUrl}/v1` : `${publicUrl}/api/v1`;
    }
    return publicUrl;
  }
}

interface FetchOptions extends RequestInit {
  token?: string;
  tenantId?: string;
}

// Fetch wrapper that handles baseUrl, authentication headers, and multi-tenancy
export async function fetchApi(path: string, options: FetchOptions = {}) {
  const baseUrl = getApiBaseUrl();
  const url = `${baseUrl}${path.startsWith("/") ? path : "/" + path}`;

  const headers = new Headers(options.headers || {});
  if (!headers.has("Content-Type") && !(options.body instanceof FormData)) {
    headers.set("Content-Type", "application/json");
  }

  // Retrieve auth token (check option or read from cookie)
  const token = options.token || getCookie("access_token");
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
    
    // Inject X-Tenant-ID from token if not already explicitly provided
    if (!headers.has("X-Tenant-ID")) {
      const claims = decodeJwt(token);
      if (claims && claims.tenant_id) {
        headers.set("X-Tenant-ID", claims.tenant_id);
      }
    }
  }

  // Inject explicit X-Tenant-ID if provided in options
  if (options.tenantId) {
    headers.set("X-Tenant-ID", options.tenantId);
  }

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorMessage = "An error occurred";
    try {
      const errorData = await response.json();
      errorMessage = errorData.detail || errorData.message || errorMessage;
    } catch {
      // Use default error message if JSON parsing fails
    }
    throw new Error(errorMessage);
  }

  return response.json();
}
