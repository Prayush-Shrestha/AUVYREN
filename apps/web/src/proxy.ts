import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE = process.env.SESSION_COOKIE_NAME ?? "auv_session";
const PROTECTED_PREFIXES = [
  "/dashboard",
  "/settings",
  "/intelligence",
  "/notes",
  "/knowledge",
];

function isProtected(pathname: string) {
  return PROTECTED_PREFIXES.some(
    (prefix) => pathname === prefix || pathname.startsWith(`${prefix}/`),
  );
}

function apiOrigin() {
  const base =
    process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
  return new URL(base).origin;
}

function buildCsp(nonce: string, secure: boolean, development: boolean) {
  const directives = [
    "default-src 'self'",
    `script-src 'self' 'nonce-${nonce}' 'strict-dynamic'${
      development ? " 'unsafe-eval'" : ""
    }`,
    // React style attributes and the design catalogue's swatches require
    // inline styles; scripts remain nonce-bound and strict-dynamic.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' blob: data:",
    "font-src 'self' data:",
    `connect-src 'self' ${apiOrigin()}`,
    "worker-src 'self' blob:",
    "manifest-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    "frame-ancestors 'none'",
  ];
  if (secure) directives.push("upgrade-insecure-requests");
  return directives.join("; ");
}

function harden(
  response: NextResponse,
  { csp, secure }: { csp: string; secure: boolean },
) {
  response.headers.set("Content-Security-Policy", csp);
  response.headers.set("X-Content-Type-Options", "nosniff");
  response.headers.set("X-Frame-Options", "DENY");
  response.headers.set("Referrer-Policy", "strict-origin-when-cross-origin");
  response.headers.set(
    "Permissions-Policy",
    "camera=(), microphone=(), geolocation=(), browsing-topics=()",
  );
  response.headers.set("Cross-Origin-Opener-Policy", "same-origin");
  response.headers.set("Cross-Origin-Resource-Policy", "same-origin");
  response.headers.set("X-DNS-Prefetch-Control", "off");
  if (secure) {
    response.headers.set(
      "Strict-Transport-Security",
      "max-age=63072000; includeSubDomains; preload",
    );
  }
}

/**
 * Applies the browser security boundary and the optimistic navigation guard.
 * The API verifies every session and the workspace layout performs the
 * authoritative server-side check.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const nonce = btoa(crypto.randomUUID());
  const secure =
    request.nextUrl.protocol === "https:" ||
    request.headers.get("x-forwarded-proto") === "https";
  const csp = buildCsp(nonce, secure, process.env.NODE_ENV !== "production");

  if (isProtected(pathname) && !request.cookies.has(SESSION_COOKIE)) {
    const signIn = new URL("/sign-in", request.url);
    signIn.searchParams.set("reason", "signin_required");
    signIn.searchParams.set("next", `${pathname}${search}`);
    const redirect = NextResponse.redirect(signIn);
    redirect.headers.set("Cache-Control", "no-store");
    harden(redirect, { csp, secure });
    return redirect;
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-nonce", nonce);
  requestHeaders.set("Content-Security-Policy", csp);
  if (isProtected(pathname)) {
    requestHeaders.set("x-auvyren-pathname", `${pathname}${search}`);
  }

  const response = NextResponse.next({ request: { headers: requestHeaders } });
  harden(response, { csp, secure });
  return response;
}

export const config = {
  matcher: [
    /*
     * Render every page through the security boundary, but skip immutable
     * assets, metadata files, and router prefetches (which are not documents).
     */
    {
      source: "/((?!_next/static|_next/image|favicon.ico|icon.svg|.*\\..*).*)",
      missing: [
        { type: "header", key: "next-router-prefetch" },
        { type: "header", key: "purpose", value: "prefetch" },
      ],
    },
  ],
};
