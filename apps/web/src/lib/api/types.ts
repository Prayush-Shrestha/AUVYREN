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

// Intelligence types

export interface TaskScoreResponse {
  task_id: string;
  title: string;
  score: number;
  reasons: string[];
}

export interface TaskPrioritizeResponse {
  prioritized: TaskScoreResponse[];
}

export interface DailyPlanResponse {
  date: string;
  available_minutes: number;
  estimated_remaining_minutes: number;
  overload: boolean;
  priorities: TaskScoreResponse[];
  focus_block_minutes: number;
  slack_minutes: number;
}

export interface DeadlineItemResponse {
  kind: "task" | "goal" | "milestone";
  id: string;
  title: string;
  due: string;
  classification: string;
}

export interface DeadlineAwarenessResponse {
  items: DeadlineItemResponse[];
}

export interface GoalProgressResponse {
  goal_id: string;
  title: string;
  progress: number;
  milestone_count: number;
  completed_milestone_count: number;
  is_neglected: boolean;
}

export interface HabitConsistencyResponse {
  habit_id: string;
  name: string;
  schedule: string;
  streak: number;
  completions_7d: number;
  completions_30d: number;
  completion_rate_7d: number;
  completion_rate_30d: number;
  missed_dates_7d: string[];
  is_inconsistent: boolean;
}

export interface PatternResponse {
  kind: string;
  description: string;
  evidence: string;
  confidence: "low" | "medium" | "high";
}

export interface WeeklyReviewDraftResponse {
  week_start: string;
  completed_count: number;
  missed_count: number;
  habit_consistency_summary: string;
  goal_movement_summary: string;
  overload_warning: string | null;
  priorities_next_week: string[];
}

export interface BriefingResponse {
  date: string;
  daily_plan: DailyPlanResponse | null;
  deadlines: DeadlineItemResponse[];
  goal_progress: GoalProgressResponse[];
  habit_consistency: HabitConsistencyResponse[];
  patterns: PatternResponse[];
}

export interface AskRequest {
  question: string;
  provider: string;
  model?: string | null;
}

export interface AskResponse {
  answer: string;
  provider: string;
  model: string | null;
  usage: Record<string, unknown> | null;
  generated_at: string;
}

export interface ProviderInfoResponse {
  name: string;
  healthy: boolean;
  detail: string;
  models: string[];
}

export interface ProviderConfigureRequest {
  provider: string;
  base_url: string;
  model: string;
}

export interface ProviderConfigureResponse {
  provider: string;
  base_url: string;
  model: string;
  healthy: boolean;
  detail: string;
  secret_hash: string | null;
}

export interface ProviderSecretResponse {
  secret_hash: string | null;
}
