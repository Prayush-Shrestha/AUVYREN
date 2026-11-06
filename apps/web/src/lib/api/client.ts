import { env } from "@/lib/env";
import type { ProblemDetails } from "./types";

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly requestId?: string;
  readonly fieldErrors?: Record<string, string>;

  constructor(problem: ProblemDetails) {
    super(problem.detail || problem.title);
    this.name = "ApiError";
    this.status = problem.status;
    this.code = problem.code;
    this.requestId = problem.request_id;
    this.fieldErrors = problem.errors?.reduce<Record<string, string>>((result, issue) => {
      result[issue.field] = issue.message;
      return result;
    }, {});
  }
}

type ApiRequestInit = Omit<RequestInit, "body"> & {
  body?: unknown;
};

/**
 * Typed JSON client for the Auvyren API.
 * Session cookies are sent with every request; CSRF headers are added in Phase 2.
 */
export async function apiRequest<T>(
  path: string,
  init: ApiRequestInit = {},
): Promise<T> {
  const { body, headers, ...rest } = init;
  const hasBody = body !== undefined;

  const response = await fetch(`${env.apiBaseUrl}${path}`, {
    ...rest,
    credentials: "include",
    headers: {
      Accept: "application/json",
      ...(hasBody ? { "Content-Type": "application/json" } : {}),
      ...headers,
    },
    body: hasBody ? JSON.stringify(body) : undefined,
  });

  if (!response.ok) {
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
    throw new ApiError(problem);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return (await response.json()) as T;
}
