import { cache } from "react";
import { cookies } from "next/headers";

import { env } from "@/lib/env";
import type { AuthUser } from "./types";

const SESSION_COOKIE = process.env.AUV_SESSION_COOKIE_NAME ?? "auv_session";

function serverApiBaseUrl() {
  return (process.env.API_INTERNAL_URL ?? env.apiBaseUrl).replace(/\/$/, "");
}

/**
 * Resolve the current user directly from the API during a server render.
 * The HttpOnly session cookie is forwarded as-is; no token reaches the client.
 */
export const getServerUser = cache(async (): Promise<AuthUser | null> => {
  const cookieStore = await cookies();
  if (!cookieStore.has(SESSION_COOKIE)) return null;

  const cookieHeader = cookieStore
    .getAll()
    .map(({ name, value }) => `${name}=${value}`)
    .join("; ");

  const response = await fetch(`${serverApiBaseUrl()}/auth/me`, {
    headers: {
      Accept: "application/json",
      Cookie: cookieHeader,
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
