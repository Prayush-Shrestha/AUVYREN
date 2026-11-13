import { NextRequest } from "next/server";
import { describe, expect, it } from "vitest";

import { proxy } from "@/proxy";

function request(path: string, init?: { cookie?: string; proto?: string }) {
  const headers = new Headers();
  if (init?.cookie) headers.set("cookie", init.cookie);
  if (init?.proto) headers.set("x-forwarded-proto", init.proto);
  return new NextRequest(`http://localhost:3000${path}`, { headers });
}

describe("proxy security boundary", () => {
  it("attaches a nonce-bound CSP and hardening headers", () => {
    const response = proxy(request("/"));
    const csp = response.headers.get("content-security-policy") ?? "";

    expect(csp).toContain("default-src 'self'");
    expect(csp).toMatch(/script-src 'self' 'nonce-[^']+' 'strict-dynamic'/);
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("connect-src 'self' http://localhost:8000");
    expect(response.headers.get("x-content-type-options")).toBe("nosniff");
    expect(response.headers.get("x-frame-options")).toBe("DENY");
    expect(response.headers.get("referrer-policy")).toBe(
      "strict-origin-when-cross-origin",
    );
    expect(response.headers.get("cross-origin-opener-policy")).toBe(
      "same-origin",
    );
  });

  it("uses a fresh nonce for each request", () => {
    const first = proxy(request("/")).headers.get("content-security-policy");
    const second = proxy(request("/")).headers.get("content-security-policy");
    expect(first).not.toBe(second);
  });

  it("redirects unauthenticated workspace requests to sign-in", () => {
    const response = proxy(request("/settings/profile"));

    expect(response.status).toBe(307);
    expect(response.headers.get("location")).toBe(
      "http://localhost:3000/sign-in?reason=signin_required&next=%2Fsettings%2Fprofile",
    );
    expect(response.headers.get("cache-control")).toBe("no-store");
    expect(response.headers.get("content-security-policy")).toBeTruthy();
  });

  it("guards every workspace route, not only settings", () => {
    for (const path of ["/dashboard", "/intelligence", "/notes", "/knowledge"]) {
      const response = proxy(request(path));
      expect(response.status, path).toBe(307);
      expect(response.headers.get("location"), path).toContain(
        `next=${encodeURIComponent(path)}`,
      );
    }
  });

  it("allows authenticated workspace requests through", () => {
    const response = proxy(
      request("/dashboard", { cookie: "auv_session=opaque-token" }),
    );

    expect(response.status).toBe(200);
    expect(
      response.headers.get("x-middleware-request-x-auvyren-pathname"),
    ).toBe("/dashboard");
  });

  it("adds transport security only for HTTPS requests", () => {
    const insecure = proxy(request("/", { proto: "http" }));
    expect(insecure.headers.get("strict-transport-security")).toBeNull();
    expect(insecure.headers.get("content-security-policy")).not.toContain(
      "upgrade-insecure-requests",
    );

    const secure = proxy(request("/", { proto: "https" }));
    expect(secure.headers.get("strict-transport-security")).toContain(
      "max-age=63072000",
    );
    expect(secure.headers.get("content-security-policy")).toContain(
      "upgrade-insecure-requests",
    );
  });

  it("leaves public pages reachable without a session", () => {
    const response = proxy(request("/sign-in"));
    expect(response.status).toBe(200);
    expect(response.headers.get("location")).toBeNull();
  });
});
