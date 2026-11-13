import {
  expect,
  request as playwrightRequest,
  type BrowserContext,
} from "@playwright/test";

export const WEB_ORIGIN = "http://localhost:3000";
export const API_ORIGIN = "http://localhost:8000";
export const API_BASE_URL = `${API_ORIGIN}/api/v1`;
export const PASSWORD = "correct horse battery staple";

let counter = 0;

export function uniqueEmail(prefix = "e2e") {
  counter += 1;
  return `${prefix}-${Date.now()}-${counter}@e2e.auvyren.app`;
}

/**
 * Registers a real account through the API without touching a browser
 * context. Use this when a test needs credentials but must start signed out.
 */
export async function registerAccount({
  prefix = "journey",
  fullName = "E2E Tester",
} = {}): Promise<{ email: string; password: string }> {
  const email = uniqueEmail(prefix);
  const api = await playwrightRequest.newContext({
    baseURL: API_ORIGIN,
    extraHTTPHeaders: { Origin: WEB_ORIGIN, Referer: `${WEB_ORIGIN}/` },
  });

  try {
    const csrfResponse = await api.get("/api/v1/auth/csrf");
    expect(csrfResponse.ok()).toBeTruthy();
    const { csrf_token: csrfToken } = await csrfResponse.json();

    const register = await api.post("/api/v1/auth/register", {
      data: { email, password: PASSWORD, full_name: fullName },
      headers: { "X-CSRF-Token": csrfToken },
    });
    expect(register.status()).toBe(201);
    return { email, password: PASSWORD };
  } finally {
    await api.dispose();
  }
}

/**
 * Creates a real account and installs its HttpOnly session cookie into the
 * browser context. Used for journeys that are not about sign-in itself.
 */
export async function createAccount(
  context: BrowserContext,
  options: { prefix?: string; fullName?: string } = {},
): Promise<{ email: string; password: string }> {
  const credentials = await registerAccount(options);
  const { email } = credentials;

  const api = await playwrightRequest.newContext({
    baseURL: API_ORIGIN,
    extraHTTPHeaders: { Origin: WEB_ORIGIN, Referer: `${WEB_ORIGIN}/` },
  });

  try {
    const csrfResponse = await api.get("/api/v1/auth/csrf");
    expect(csrfResponse.ok()).toBeTruthy();
    const { csrf_token: csrfToken } = await csrfResponse.json();
    const login = await api.post("/api/v1/auth/login", {
      data: credentials,
      headers: { "X-CSRF-Token": csrfToken },
    });
    expect(login.status(), `Could not sign in ${email}`).toBe(200);

    const state = await api.storageState();
    await context.addCookies(state.cookies);
    return credentials;
  } finally {
    await api.dispose();
  }
}

/** Creates a note from inside the authenticated browser context. */
export async function createNote(
  context: BrowserContext,
  input: { title: string; content?: string; tags?: string; kind?: string },
): Promise<{ id: string; title: string }> {
  const csrfResponse = await context.request.get(`${API_BASE_URL}/auth/csrf`, {
    headers: { Origin: WEB_ORIGIN, Referer: `${WEB_ORIGIN}/` },
  });
  expect(csrfResponse.ok()).toBeTruthy();
  const { csrf_token: csrfToken } = await csrfResponse.json();

  const response = await context.request.post(`${API_BASE_URL}/knowledge`, {
    data: input,
    headers: {
      "X-CSRF-Token": csrfToken,
      Origin: WEB_ORIGIN,
      Referer: `${WEB_ORIGIN}/`,
    },
  });
  expect(response.status()).toBe(201);
  return response.json();
}
