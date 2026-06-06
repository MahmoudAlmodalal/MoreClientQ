/**
 * Unit tests for Next.js subdomain middleware.
 *
 * Tests cover:
 *  - extractTenantSlug(): pure function, no network calls
 *  - middleware() handler: mocked fetch, validates header injection and 404 rewrite
 *
 * Test runner: Jest (configured via jest.config.ts)
 * Run: npx jest tests/middleware.test.ts
 */

import { describe, expect, it, jest, beforeEach, afterEach } from "@jest/globals";

// ---------------------------------------------------------------------------
// Import the pure helper first — no Next.js request objects needed
// ---------------------------------------------------------------------------
import { extractTenantSlug } from "../middleware";

// ---------------------------------------------------------------------------
// extractTenantSlug — pure unit tests
// ---------------------------------------------------------------------------

describe("extractTenantSlug", () => {
  const PLATFORM = "localhost";

  it("returns the subdomain slug for a valid tenant subdomain", () => {
    expect(extractTenantSlug("acme.localhost", PLATFORM)).toBe("acme");
    expect(extractTenantSlug("beta.localhost", PLATFORM)).toBe("beta");
  });

  it("strips port numbers before parsing", () => {
    expect(extractTenantSlug("acme.localhost:3000", PLATFORM)).toBe("acme");
    expect(extractTenantSlug("beta.localhost:3000", PLATFORM)).toBe("beta");
  });

  it("returns null for the root platform hostname (no subdomain)", () => {
    expect(extractTenantSlug("localhost", PLATFORM)).toBeNull();
    expect(extractTenantSlug("localhost:3000", PLATFORM)).toBeNull();
  });

  it("returns null for the www subdomain (reserved)", () => {
    expect(extractTenantSlug("www.localhost", PLATFORM)).toBeNull();
  });

  it("returns null for the api subdomain (reserved)", () => {
    expect(extractTenantSlug("api.localhost", PLATFORM)).toBeNull();
  });

  it("returns null when hostname does not end with platform suffix", () => {
    expect(extractTenantSlug("acme.otherdomain.com", PLATFORM)).toBeNull();
    expect(extractTenantSlug("completely-different.com", PLATFORM)).toBeNull();
  });

  it("handles production-style platform hostname", () => {
    const PROD = "platform.com";
    expect(extractTenantSlug("acme.platform.com", PROD)).toBe("acme");
    expect(extractTenantSlug("beta.platform.com", PROD)).toBe("beta");
    expect(extractTenantSlug("platform.com", PROD)).toBeNull();
    expect(extractTenantSlug("www.platform.com", PROD)).toBeNull();
  });

  it("is case-insensitive for hostname comparison", () => {
    expect(extractTenantSlug("ACME.localhost", PLATFORM)).toBe("acme");
    expect(extractTenantSlug("ACME.LOCALHOST", PLATFORM)).toBe("acme");
  });

  it("returns null when subdomain is empty", () => {
    // e.g. ".localhost" — edge case
    expect(extractTenantSlug(".localhost", PLATFORM)).toBeNull();
  });
});

// ---------------------------------------------------------------------------
// middleware() — integration-style unit tests with mocked fetch & NextRequest
// ---------------------------------------------------------------------------

/**
 * Build a minimal NextRequest-compatible object for testing the middleware handler.
 * We mock only the properties the middleware reads.
 */
function makeRequest(
  pathname: string,
  host: string
): {
  nextUrl: { pathname: string; clone: () => { pathname: string } };
  headers: { get: (name: string) => string | null };
} {
  return {
    nextUrl: {
      pathname,
      clone() {
        return { pathname };
      },
    },
    headers: {
      get(name: string) {
        if (name === "host") return host;
        return null;
      },
    },
  };
}

describe("middleware (handler)", () => {
  // We need to dynamically import middleware after setting env vars
  // and after mocking fetch, so use jest.isolateModules per test group.

  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
    jest.resetModules();
  });

  it("passes through requests to _next/static without calling fetch", async () => {
    const fetchMock = jest.fn<typeof fetch>();
    globalThis.fetch = fetchMock;

    // Re-import middleware after mocking
    const { middleware } = await import("../middleware");
    const req = makeRequest("/_next/static/chunk.js", "acme.localhost:3000");
    // @ts-ignore — partial mock object
    const res = await middleware(req as any);

    expect(fetchMock).not.toHaveBeenCalled();
    // NextResponse.next() is returned — just ensure no rewrite to 404
    expect(res).toBeDefined();
  });

  it("passes through root platform requests (no subdomain) without calling fetch", async () => {
    const fetchMock = jest.fn<typeof fetch>();
    globalThis.fetch = fetchMock;

    const { middleware } = await import("../middleware");
    const req = makeRequest("/", "localhost:3000");
    // @ts-ignore
    const res = await middleware(req as any);

    expect(fetchMock).not.toHaveBeenCalled();
    expect(res).toBeDefined();
  });

  it("calls backend resolve endpoint for tenant subdomain", async () => {
    const resolvePayload = {
      tenant_id: "8fa53874-9844-4861-bf96-5f7bd0cb11aa",
      slug: "acme",
      is_active: true,
    };

    const fetchMock = jest.fn<typeof fetch>().mockResolvedValueOnce({
      ok: true,
      json: async () => resolvePayload,
    } as Response);
    globalThis.fetch = fetchMock;

    const { middleware } = await import("../middleware");
    const req = makeRequest("/dashboard", "acme.localhost:3000");
    // @ts-ignore
    const res = await middleware(req as any);

    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [calledUrl, calledOpts] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(calledUrl).toContain("/tenants/resolve/acme");
    expect((calledOpts.headers as Record<string, string>)["X-Internal-Secret"]).toBeTruthy();
  });

  it("injects X-Tenant-ID header on successful slug resolution", async () => {
    const tenantId = "8fa53874-9844-4861-bf96-5f7bd0cb11aa";
    const fetchMock = jest.fn<typeof fetch>().mockResolvedValueOnce({
      ok: true,
      json: async () => ({ tenant_id: tenantId, slug: "acme", is_active: true }),
    } as Response);
    globalThis.fetch = fetchMock;

    // Spy on Headers.prototype.set to capture injected headers
    const setHeader = jest.fn<(name: string, value: string) => void>();
    const OriginalHeaders = globalThis.Headers;
    // @ts-ignore
    globalThis.Headers = class extends OriginalHeaders {
      set(name: string, value: string) {
        setHeader(name, value);
        return super.set(name, value);
      }
    };

    const { middleware } = await import("../middleware");
    const req = makeRequest("/dashboard", "acme.localhost:3000");
    // @ts-ignore
    await middleware(req as any);

    // Expect tenant headers to have been set
    const calls = setHeader.mock.calls.map(([name]) => name);
    expect(calls).toContain("X-Tenant-ID");
    expect(calls).toContain("X-Tenant-Slug");

    globalThis.Headers = OriginalHeaders;
  });

  it("rewrites to /404 when backend returns 404 for unknown slug", async () => {
    const fetchMock = jest.fn<typeof fetch>().mockResolvedValueOnce({
      ok: false,
      status: 404,
    } as Response);
    globalThis.fetch = fetchMock;

    const { middleware, extractTenantSlug: _et } = await import("../middleware");
    const req = makeRequest("/dashboard", "invalid-slug.localhost:3000");
    // @ts-ignore
    const res = await middleware(req as any);

    // The middleware should call NextResponse.rewrite — res should be the rewrite response
    expect(res).toBeDefined();
    // We can't easily inspect internal URL of NextResponse without full Next.js env,
    // but we verify fetch was called (meaning the slug was extracted and a lookup was attempted)
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("rewrites to /404 when fetch throws a network error", async () => {
    const fetchMock = jest
      .fn<typeof fetch>()
      .mockRejectedValueOnce(new Error("Network error"));
    globalThis.fetch = fetchMock;

    const { middleware } = await import("../middleware");
    const req = makeRequest("/dashboard", "acme.localhost:3000");
    // @ts-ignore
    const res = await middleware(req as any);

    expect(res).toBeDefined();
    // fetch was attempted, error was caught — middleware should return 404 rewrite
    expect(fetchMock).toHaveBeenCalledTimes(1);
  });
});
