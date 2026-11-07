import { env } from "@/lib/env";
import type { CsrfResponse, ProblemDetails } from "./types";

export const AUTH_EXPIRED_EVENT = "auvyren:auth-expired";

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);
const NO_AUTH_EXPIRY_EVENT = new Set([
  "/auth/login",
  "/auth/register",
  "/auth/forgot-password",
  "/auth/reset-password",
]);

let csrfToken: string | null = null;
let csrfPromise: Promise<string> | null = null;

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly detail: string;
  readonly requestId?: string;
  readonly fieldErrors?: Record<string, string>;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title);
    this.name = "ApiError";
    this.status = problem.status;
    this.code = problem.code;
    this.detail = problem.detail || problem.title;
    this.requestId = problem.request_id;
    this.fieldErrors = problem.errors?.reduce<Record<string, string>>((result, issue) => {
      result[issue.field.replace(/^body\./, "")] = issue.message;
      return result;
    }, {});
  }
}

type ApiRequestInit = Omit<RequestInit, "body"> & {
  body?: unknown;
};

export function setCsrfToken(token: string | null) {
  csrfToken = token;
  csrfPromise = null;
}

export function clearCsrfToken() {
  setCsrfToken(null);
}

export async function ensureCsrfToken(force = false): Promise<string> {
  if (typeof window === "undefined") {
    throw new Error("CSRF bootstrap requires a browser session");
  }
  if (csrfToken && !force) return csrfToken;
  if (csrfPromise && !force) return csrfPromise;

  if (force) {
    csrfToken = null;
    csrfPromise = null;
  }

  csrfPromise = (async () => {
    const response = await fetch(`${env.apiBaseUrl}/auth/csrf`, {
      method: "GET",
      credentials: "include",
      headers: { Accept: "application/json" },
      cache: "no-store",
    });

    if (!response.ok) {
      throw await toApiError(response, "/auth/csrf");
    }

    const payload = (await response.json()) as CsrfResponse;
    csrfToken = payload.csrf_token;
    return payload.csrf_token;
  })();

  try {
    return await csrfPromise;
  } finally {
    csrfPromise = null;
  }
}

async function toApiError(response: Response, path: string): Promise<ApiError> {
  let problem: ProblemDetails;
  try {
    problem = (await response.json()) as ProblemDetails;
  } catch {
    problem = {
      type: "https://auvyren.app/problems/unexpected_response",
      title: "Unexpected response",
      status: response.status,
      detail: "The server returned an unexpected response.",
      instance: path,
      code: "unexpected_response",
    };
  }
  return new ApiError(problem);
}

/**
 * Typed JSON client for the Auvyren API.
 * Cookies stay HttpOnly; the non-secret CSRF token is held in memory only.
 */
export async function apiRequest<T>(
  path: string,
  init: ApiRequestInit = {},
): Promise<T> {
  return request<T>(path, init, false);
}

async function request<T>(
  path: string,
  init: ApiRequestInit,
  retried: boolean,
): Promise<T> {
  const { body, headers, ...rest } = init;
  const method = (rest.method ?? "GET").toUpperCase();
  const unsafe = UNSAFE_METHODS.has(method);
  const hasBody = body !== undefined;

  const callerHeaders = new Headers(headers);
  const hasCallerCsrf = callerHeaders.has("X-CSRF-Token");
  if (unsafe && !hasCallerCsrf) {
    callerHeaders.set("X-CSRF-Token", await ensureCsrfToken());
  }

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...Object.fromEntries(callerHeaders.entries()),
    },
    body: hasBody ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
    const error = await toApiError(response, path);

    if (
      unsafe &&
      !retried &&
      error.status === 403 &&
      error.code === "csrf_validation_failed" &&
      !hasCallerCsrf &&
      typeof window !== "undefined"
    ) {
      await ensureCsrfToken(true);
      return request<T>(path, init, true);
    }

    if (
      error.status === 401 &&
      !NO_AUTH_EXPIRY_EVENT.has(path) &&
      typeof window !== "undefined"
    ) {
      window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT));
    }

    throw error;
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
