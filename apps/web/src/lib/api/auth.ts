import { apiRequest, clearCsrfToken, setCsrfToken } from "./client";
import type {
  AuthResponse,
  AuthSession,
  AuthUser,
  MessageResponse,
  SessionListResponse,
} from "./types";

export interface SignUpInput {
  email: string;
  password: string;
  full_name?: string | null;
}

export interface UpdateProfileInput {
  full_name?: string | null;
  timezone?: string;
  week_starts_on?: number;
}

export async function loginRequest(input: {
  email: string;
  password: string;
}): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    body: input,
  });
  setCsrfToken(response.csrf_token);
  return response;
}

export async function registerRequest(input: SignUpInput): Promise<AuthResponse> {
  const response = await apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    body: input,
  });
  setCsrfToken(response.csrf_token);
  return response;
}

export async function logoutRequest(): Promise<void> {
  await apiRequest<void>("/auth/logout", { method: "POST" });
  clearCsrfToken();
}

export async function forgotPasswordRequest(input: {
  email: string;
}): Promise<MessageResponse> {
  return apiRequest<MessageResponse>("/auth/forgot-password", {
    method: "POST",
    body: input,
  });
}

export async function resetPasswordRequest(input: {
  token: string;
  password: string;
}): Promise<MessageResponse> {
  const response = await apiRequest<MessageResponse>("/auth/reset-password", {
    method: "POST",
    body: input,
  });
  clearCsrfToken();
  return response;
}

export async function updateProfileRequest(
  input: UpdateProfileInput,
): Promise<AuthUser> {
  return apiRequest<AuthUser>("/auth/me", {
    method: "PATCH",
    body: input,
  });
}

export async function listSessionsRequest(): Promise<AuthSession[]> {
  const response = await apiRequest<SessionListResponse>("/auth/sessions");
  return response.sessions;
}

export async function revokeSessionRequest(sessionId: string): Promise<void> {
  await apiRequest<void>(`/auth/sessions/${encodeURIComponent(sessionId)}`, {
    method: "DELETE",
  });
}
