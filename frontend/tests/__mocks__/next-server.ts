/**
 * Lightweight mock of `next/server` for Jest unit tests.
 *
 * We only need the parts of NextResponse that the middleware uses:
 *  - NextResponse.next({ request: { headers } })
 *  - NextResponse.rewrite(url)
 *
 * NextRequest is not imported in tests directly; the tests create plain objects
 * that satisfy the shape the middleware reads.
 */

export class NextResponse {
  public type: "next" | "rewrite";
  public rewriteUrl?: { pathname: string };
  public requestHeaders?: Headers;

  private constructor(
    type: "next" | "rewrite",
    opts?: { rewriteUrl?: { pathname: string }; requestHeaders?: Headers }
  ) {
    this.type = type;
    this.rewriteUrl = opts?.rewriteUrl;
    this.requestHeaders = opts?.requestHeaders;
  }

  static next(options?: { request?: { headers?: Headers } }): NextResponse {
    return new NextResponse("next", {
      requestHeaders: options?.request?.headers,
    });
  }

  static rewrite(url: { pathname: string }): NextResponse {
    return new NextResponse("rewrite", { rewriteUrl: url });
  }
}

export class NextRequest {
  nextUrl: { pathname: string; clone(): { pathname: string } };
  headers: { get(name: string): string | null };

  constructor(
    url: string,
    init?: { headers?: Record<string, string> }
  ) {
    this.nextUrl = {
      pathname: new URL(url).pathname,
      clone() {
        return { pathname: new URL(url).pathname };
      },
    };
    const _headers = init?.headers ?? {};
    this.headers = {
      get(name: string) {
        return _headers[name] ?? null;
      },
    };
  }
}
