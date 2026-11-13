import { expect, test } from "@playwright/test";

import { API_BASE_URL, WEB_ORIGIN, createAccount } from "./support";

test.describe("security boundary", () => {
  test("documents carry a nonce-bound CSP and hardening headers", async ({
    page,
  }) => {
    const response = await page.goto("/");
    expect(response).not.toBeNull();
    const headers = response!.headers();
    const csp = headers["content-security-policy"] ?? "";

    expect(csp).toMatch(
      /script-src 'self' 'nonce-[^']+' 'strict-dynamic'/,
    );
    expect(csp).toContain("default-src 'self'");
    expect(csp).toContain("object-src 'none'");
    expect(csp).toContain("base-uri 'self'");
    expect(csp).toContain("form-action 'self'");
    expect(csp).toContain("frame-ancestors 'none'");
    expect(csp).toContain("connect-src 'self' http://localhost:8000");

    expect(headers["x-content-type-options"]).toBe("nosniff");
    expect(headers["x-frame-options"]).toBe("DENY");
    expect(headers["referrer-policy"]).toBe("strict-origin-when-cross-origin");
    expect(headers["permissions-policy"]).toContain("camera=()");
    expect(headers["cross-origin-opener-policy"]).toBe("same-origin");
    expect(headers["cross-origin-resource-policy"]).toBe("same-origin");

    const nonce = csp.match(/'nonce-([^']+)'/)?.[1];
    expect(nonce).toBeTruthy();
    const scriptNonces = await page
      .locator("script[nonce]")
      .evaluateAll((scripts) =>
        scripts.map((script) => (script as HTMLScriptElement).nonce),
      );
    expect(scriptNonces.length).toBeGreaterThan(0);
    expect(scriptNonces).toContain(nonce);
  });

  test("every document request receives a fresh nonce", async ({ page }) => {
    const first = await page.goto("/");
    const second = await page.goto("/sign-in");

    const nonceOf = (response: Awaited<ReturnType<typeof page.goto>>) =>
      response?.headers()["content-security-policy"]?.match(
        /'nonce-([^']+)'/,
      )?.[1];

    const firstNonce = nonceOf(first);
    const secondNonce = nonceOf(second);
    expect(firstNonce).toBeTruthy();
    expect(secondNonce).toBeTruthy();
    expect(firstNonce).not.toBe(secondNonce);
  });

  test("HSTS is only asserted over HTTPS", async ({ page }) => {
    const response = await page.goto("/");
    expect(response?.headers()["strict-transport-security"]).toBeUndefined();
  });

  test("session cookies stay out of reach of document scripts", async ({
    page,
    context,
  }) => {
    await createAccount(context);
    await page.goto("/dashboard");

    const session = (await context.cookies()).find(
      (cookie) => cookie.name === "auv_session",
    );
    expect(session).toMatchObject({ httpOnly: true, sameSite: "Lax" });
    expect(await page.evaluate(() => document.cookie)).not.toContain(
      "auv_session",
    );
  });

  test("sign-out revokes the session on the server, not only in the browser", async ({
    page,
    context,
    request,
  }) => {
    await createAccount(context, { fullName: "Revocation Probe" });
    await page.goto("/dashboard");

    const session = (await context.cookies()).find(
      (cookie) => cookie.name === "auv_session",
    );
    expect(session).toBeTruthy();

    await page
      .getByRole("button", { name: /account menu for Revocation Probe/ })
      .click();
    await page.getByRole("menuitem", { name: "Sign out" }).click();
    await expect(page).toHaveURL(/\/sign-in\?reason=signed_out$/);

    const reuse = await request.get(`${API_BASE_URL}/auth/me`, {
      headers: {
        Cookie: `auv_session=${session!.value}`,
        Origin: WEB_ORIGIN,
      },
    });
    expect(reuse.status()).toBe(401);
    expect((await reuse.json()).code).toBe("not_authenticated");
  });

  test("the API rejects anonymous workspace calls", async ({ request }) => {
    const response = await request.get(`${API_BASE_URL}/auth/me`, {
      headers: { Origin: WEB_ORIGIN },
    });
    expect(response.status()).toBe(401);
    const problem = await response.json();
    expect(problem.code).toBe("not_authenticated");
    expect(problem.request_id).toBeTruthy();
  });

  test("health endpoints expose liveness without workspace data", async ({
    request,
  }) => {
    const response = await request.get("http://localhost:8000/health/live");
    expect(response.status()).toBe(200);
    const body = await response.json();
    expect(body.status).toBe("ok");
  });
});
