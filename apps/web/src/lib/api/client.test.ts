import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import {
  ApiError,
  AUTH_EXPIRED_EVENT,
  apiRequest,
  clearCsrfToken,
  ensureCsrfToken,
  setCsrfToken,
} from "@/lib/api/client";
import { env } from "@/lib/env";

function jsonResponse(body: unknown, status = 200): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

function problem(
  status: number,
  code: string,
  detail = "Something went wrong",
  extra: Record<string, unknown> = {},
) {
  return {
    type: `https://auvyren.app/problems/${code}`,
    title: "Request failed",
    status,
    detail,
    instance: "/api/v1/test",
    code,
    request_id: "req-1",
    ...extra,
  };
}

const fetchMock = vi.fn<typeof fetch>();

beforeEach(() => {
  clearCsrfToken();
  fetchMock.mockReset();
});

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubFetch() {
  vi.stubGlobal("fetch", fetchMock);
}

describe("apiRequest", () => {
  it("sends JSON requests with cookies and no CSRF token for reads", async () => {
    stubFetch();
    fetchMock.mockResolvedValueOnce(jsonResponse({ ok: true }));

    const result = await apiRequest<{ ok: boolean }>("/tasks");

    expect(result).toEqual({ ok: true });
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe(`${env.apiBaseUrl}/tasks`);
    expect(init?.credentials).toBe("include");
    expect(init?.method).toBeUndefined();
    expect(new Headers(init?.headers).get("Accept")).toBe("application/json");
    expect(new Headers(init?.headers).get("X-CSRF-Token")).toBeNull();
  });

  it("bootstraps a CSRF token before unsafe requests", async () => {
    stubFetch();
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: "token-1" }))
      .mockResolvedValueOnce(jsonResponse({ id: "note-1" }, 201));

    await apiRequest("/knowledge", {
      method: "POST",
      body: { title: "A note" },
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(fetchMock.mock.calls[0][0]).toBe(`${env.apiBaseUrl}/auth/csrf`);
    const [, init] = fetchMock.mock.calls[1];
    expect(init?.method).toBe("POST");
    expect(init?.body).toBe(JSON.stringify({ title: "A note" }));
    expect(new Headers(init?.headers).get("X-CSRF-Token")).toBe("token-1");
    expect(new Headers(init?.headers).get("Content-Type")).toBe(
      "application/json",
    );
  });

  it("refreshes a stale CSRF token once and retries the request", async () => {
    stubFetch();
    setCsrfToken("stale-token");
    fetchMock
      .mockResolvedValueOnce(
        jsonResponse(problem(403, "csrf_validation_failed"), 403),
      )
      .mockResolvedValueOnce(jsonResponse({ csrf_token: "fresh-token" }))
      .mockResolvedValueOnce(jsonResponse({ ok: true }));

    const result = await apiRequest<{ ok: boolean }>("/tasks", {
      method: "POST",
      body: { title: "Task" },
    });

    expect(result).toEqual({ ok: true });
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock.mock.calls[0][0]).toBe(`${env.apiBaseUrl}/tasks`);
    expect(fetchMock.mock.calls[1][0]).toBe(`${env.apiBaseUrl}/auth/csrf`);
    expect(fetchMock.mock.calls[2][0]).toBe(`${env.apiBaseUrl}/tasks`);
    expect(
      new Headers(fetchMock.mock.calls[2][1]?.headers).get("X-CSRF-Token"),
    ).toBe("fresh-token");
  });

  it("does not retry a caller-supplied CSRF token", async () => {
    stubFetch();
    fetchMock.mockResolvedValueOnce(
      jsonResponse(problem(403, "csrf_validation_failed"), 403),
    );

    await expect(
      apiRequest("/tasks", {
        method: "POST",
        headers: { "X-CSRF-Token": "caller-token" },
      }),
    ).rejects.toBeInstanceOf(ApiError);

    expect(fetchMock).toHaveBeenCalledTimes(1);
  });

  it("returns undefined for 204 responses", async () => {
    stubFetch();
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: "token-1" }))
      .mockResolvedValueOnce(new Response(null, { status: 204 }));

    await expect(
      apiRequest("/tasks/1", { method: "DELETE" }),
    ).resolves.toBeUndefined();
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });

  it("maps problem details and field errors to ApiError", async () => {
    stubFetch();
    fetchMock.mockResolvedValueOnce(
      jsonResponse(
        problem(422, "validation_error", "Check the form", {
          errors: [
            { field: "body.email", message: "Enter a valid email.", type: "value_error" },
          ],
        }),
        422,
      ),
    );

    await expect(apiRequest("/auth/register", { method: "POST" })).rejects.toMatchObject({
      name: "ApiError",
      status: 422,
      code: "validation_error",
      detail: "Check the form",
      requestId: "req-1",
      fieldErrors: { email: "Enter a valid email." },
    });
  });

  it("falls back to a problem when the error body is not JSON", async () => {
    stubFetch();
    fetchMock.mockResolvedValueOnce(
      new Response("<html>bad gateway</html>", { status: 502 }),
    );

    await expect(apiRequest("/tasks")).rejects.toMatchObject({
      status: 502,
      code: "unexpected_response",
    });
  });

  it("announces an expired session for protected requests", async () => {
    stubFetch();
    fetchMock.mockResolvedValueOnce(jsonResponse(problem(401, "not_authenticated"), 401));
    const listener = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, listener);

    await expect(apiRequest("/tasks")).rejects.toBeInstanceOf(ApiError);
    expect(listener).toHaveBeenCalledTimes(1);

    window.removeEventListener(AUTH_EXPIRED_EVENT, listener);
  });

  it("does not announce an expired session for sign-in failures", async () => {
    stubFetch();
    fetchMock.mockResolvedValueOnce(jsonResponse(problem(401, "invalid_credentials"), 401));
    const listener = vi.fn();
    window.addEventListener(AUTH_EXPIRED_EVENT, listener);

    await expect(
      apiRequest("/auth/login", { method: "POST", body: {} }),
    ).rejects.toBeInstanceOf(ApiError);
    expect(listener).not.toHaveBeenCalled();

    window.removeEventListener(AUTH_EXPIRED_EVENT, listener);
  });

  it("caches and forces CSRF refreshes", async () => {
    stubFetch();
    fetchMock
      .mockResolvedValueOnce(jsonResponse({ csrf_token: "one" }))
      .mockResolvedValueOnce(jsonResponse({ csrf_token: "two" }));

    await expect(ensureCsrfToken()).resolves.toBe("one");
    await expect(ensureCsrfToken()).resolves.toBe("one");
    await expect(ensureCsrfToken(true)).resolves.toBe("two");
    expect(fetchMock).toHaveBeenCalledTimes(2);
  });
});
