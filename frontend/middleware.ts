/**
 * Next.js Edge Middleware — Subdomain-Based Tenant Resolution
 *
 * Runs on every request before page rendering. Responsibilities:
 *  1. Extract the tenant slug from the subdomain (e.g., `acme` from `acme.localhost`).
 *  2. Skip resolution for the root platform domain and public static assets.
 *  3. Call the backend resolve endpoint (with Redis cache-aside) to validate the slug.
 *  4. On success: forward the resolved X-Tenant-ID and X-Tenant-Slug headers downstream.
 *  5. On failure (unknown slug): rewrite to the /404 page.
 */

import { NextRequest, NextResponse } from "next/server";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Backend internal API base URL. Reads from env at build/runtime. */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/**
 * Shared secret that identifies this Next.js service to the backend.
 * Must match `settings.INTERNAL_SECRET` in the FastAPI config.
 */
const INTERNAL_SECRET =
  process.env.INTERNAL_SECRET ?? "internal-service-secret";

/**
 * The base hostname for the platform (without leading dot).
 * Subdomains take the form `<slug>.<PLATFORM_HOSTNAME>`.
 * e.g. "localhost" in local dev or "platform.com" in production.
 */
const PLATFORM_HOSTNAME =
  process.env.NEXT_PUBLIC_PLATFORM_HOSTNAME ?? "localhost";

/**
 * URL prefixes that should always bypass tenant resolution.
 * Includes Next.js internals, static files, favicon, and health checks.
 */
const BYPASS_PREFIXES = [
  "/_next/",
  "/api/",
  "/favicon.ico",
  "/_vercel/",
  "/__nextjs_",
];

// ---------------------------------------------------------------------------
// Helper: extract slug from hostname
// ---------------------------------------------------------------------------

/**
 * Parse a tenant slug from the request hostname.
 *
 * Returns `null` if the request is for the root platform domain (no subdomain)
 * or for hostnames that don't carry a subdomain (e.g., "localhost" bare, "www").
 *
 * @example
 * extractTenantSlug("acme.localhost", "localhost")   → "acme"
 * extractTenantSlug("localhost", "localhost")         → null
 * extractTenantSlug("acme.platform.com", "platform.com") → "acme"
 * extractTenantSlug("platform.com", "platform.com")  → null
 */
export function extractTenantSlug(
  hostname: string,
  platformHostname: string
): string | null {
  // Strip port if present (e.g., "acme.localhost:3000" → "acme.localhost")
  const host = hostname.split(":")[0];

  // Normalise both to lower-case for comparison
  const lowerHost = host.toLowerCase();
  const lowerPlatform = platformHostname.toLowerCase();

  // Exact match → root domain, no subdomain
  if (lowerHost === lowerPlatform) return null;

  // Must end with ".<platformHostname>" to be a proper subdomain
  const suffix = `.${lowerPlatform}`;
  if (!lowerHost.endsWith(suffix)) return null;

  // Extract the leftmost label as the slug
  const subdomain = lowerHost.slice(0, lowerHost.length - suffix.length);

  // Reject obviously invalid or reserved subdomains
  if (!subdomain || subdomain === "www" || subdomain === "api") return null;

  return subdomain;
}

// ---------------------------------------------------------------------------
// Helper: call backend resolve endpoint
// ---------------------------------------------------------------------------

interface ResolveResult {
  tenant_id: string;
  slug: string;
  is_active: boolean;
}

/**
 * Calls `GET /api/v1/tenants/resolve/{slug}` on the backend.
 *
 * The backend implements a Redis cache-aside lookup, so this call is typically
 * served from Redis in < 5ms without hitting Postgres.
 *
 * Returns `null` if the slug is unknown, inactive, or the backend is unreachable.
 */
async function resolveTenantSlug(slug: string): Promise<ResolveResult | null> {
  try {
    const url = `${API_BASE_URL}/tenants/resolve/${encodeURIComponent(slug)}`;
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "X-Internal-Secret": INTERNAL_SECRET,
        "Content-Type": "application/json",
      },
      // Edge runtime: no persistent connections; keep timeout tight
      // `next: { revalidate: 0 }` disables data cache for fresh validation
      next: { revalidate: 0 },
    });

    if (!response.ok) {
      return null;
    }

    const data: ResolveResult = await response.json();
    return data;
  } catch {
    // Network error or backend unavailable — fail closed (deny tenant access)
    return null;
  }
}

// ---------------------------------------------------------------------------
// Middleware
// ---------------------------------------------------------------------------

export async function middleware(request: NextRequest): Promise<NextResponse> {
  const { pathname } = request.nextUrl;
  const hostname = request.headers.get("host") ?? "";

  // 1. Bypass: static assets and Next.js internals
  if (BYPASS_PREFIXES.some((prefix) => pathname.startsWith(prefix))) {
    return NextResponse.next();
  }

  // 2. Extract slug from subdomain
  const slug = extractTenantSlug(hostname, PLATFORM_HOSTNAME);

  // 3. No subdomain → root platform request, pass through without tenant context
  if (!slug) {
    return NextResponse.next();
  }

  // 4. Validate slug against backend (Redis-backed)
  const resolved = await resolveTenantSlug(slug);

  if (!resolved || !resolved.is_active) {
    // Unknown or inactive slug → redirect to 404
    const notFoundUrl = request.nextUrl.clone();
    notFoundUrl.pathname = "/404";
    return NextResponse.rewrite(notFoundUrl);
  }

  // 5. Inject resolved tenant context into request headers for downstream use
  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("X-Tenant-ID", resolved.tenant_id);
  requestHeaders.set("X-Tenant-Slug", resolved.slug);

  return NextResponse.next({
    request: { headers: requestHeaders },
  });
}

// ---------------------------------------------------------------------------
// Matcher config
// ---------------------------------------------------------------------------

/**
 * Apply this middleware to all routes except Next.js internal static paths.
 * The BYPASS_PREFIXES check inside the handler provides a secondary guard.
 */
export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - _next/static  (Next.js static files)
     * - _next/image   (Next.js image optimisation)
     * - favicon.ico
     */
    "/((?!_next/static|_next/image|favicon\\.ico).*)",
  ],
};
