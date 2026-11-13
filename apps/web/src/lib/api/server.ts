import { cache } from "react";
import { cookies } from "next/headers";

import { env } from "@/lib/env";
import type { AuthUser } from "./types";

const SESSION_COOKIE = process.env.SESSION_COOKIE_NAME ?? "auv_session";
const CSRF_COOKIE = process.env.CSRF_COOKIE_NAME ?? "auv_csrf";
const CSRF_HEADER = process.env.CSRF_HEADER_NAME ?? "X-CSRF-Token";
const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

function serverApiBaseUrl() {
  return (process.env.API_INTERNAL_URL ?? env.apiBaseUrl).replace(/\/$/, "");
}

function serverWebOrigin() {
  const origin =
    process.env.WEB_APP_URL ??
    process.env.NEXT_PUBLIC_WEB_URL ??
    "http://localhost:3000";
  return origin.replace(/\/$/, "");
}

async function forwardedCookieHeader() {
  const cookieStore = await cookies();
  return cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");
}

/**
 * Server-side JSON request that forwards the browser's HttpOnly session and
 * CSRF cookies. Server Components cannot rely on `credentials: "include"`,
 * so workspace data must travel through this helper.
 */
export async function serverApiRequest<T>(
  path: string,
  init: { method?: string; body?: unknown } = {},
): Promise<T> {
  const method = (init.method ?? "GET").toUpperCase();
  const cookieStore = await cookies();
  const headers: Record<string, string> = {
    Accept: "application/json",
    Cookie: await forwardedCookieHeader(),
  };

  if (init.body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (UNSAFE_METHODS.has(method)) {
    const csrf = cookieStore.get(CSRF_COOKIE)?.value;
    if (csrf) headers[CSRF_HEADER] = csrf;
    headers.Origin = serverWebOrigin();
    headers.Referer = `${serverWebOrigin()}/`;
  }

  const response = await fetch(`${serverApiBaseUrl()}${path}`, {
    method,
    headers,
    body: init.body === undefined ? undefined : JSON.stringify(init.body),
    cache: "no-store",
  });

  if (!response.ok) {
    let detail = "";
    try {
      detail = (await response.text()).slice(0, 500);
    } catch {
      detail = "unreadable body";
    }
    console.error(
      `[auvyren] server API ${method} ${path} failed: ${response.status} ${detail}`,
    );
    throw new Error(`The Auvyren API returned ${response.status} for ${path}.`);
  }
  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}

/**
 * Resolve the current user directly from the API during a server render.
 * The HttpOnly session cookie is forwarded as-is; no token reaches the client.
 */
export const getServerUser = cache(async (): Promise<AuthUser | null> => {
  const cookieStore = await cookies();
  if (!cookieStore.has(SESSION_COOKIE)) return null;

  const response = await fetch(`${serverApiBaseUrl()}/auth/me`, {
    headers: {
      Accept: "application/json",
      Cookie: await forwardedCookieHeader(),
    },
    cache: "no-store",
  });

  if (response.status === 401 || response.status === 403) {
    return null;
  }
  if (!response.ok) {
    throw new Error("The Auvyren API could not verify this session.");
  }

  return (await response.json()) as AuthUser;
});
