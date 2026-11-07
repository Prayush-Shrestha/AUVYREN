export interface ProblemFieldIssue {
  field: string;
  message: string;
  type: string;
}

export interface ProblemDetails {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
  code: string;
  request_id?: string;
  errors?: ProblemFieldIssue[];
}

export interface UserSettings {
  timezone: string;
  week_starts_on: number;
}

export interface AuthUser {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  email_verified: boolean;
  last_login_at: string | null;
  created_at: string;
  settings: UserSettings;
}

export interface AuthResponse {
  user: AuthUser;
  csrf_token: string;
}

export interface CsrfResponse {
  csrf_token: string;
}

export interface MessageResponse {
  message: string;
}

export interface AuthSession {
  id: string;
  created_at: string;
  last_used_at: string | null;
  expires_at: string;
  user_agent: string | null;
  ip_address: string | null;
  current: boolean;
}

export interface SessionListResponse {
  sessions: AuthSession[];
}
