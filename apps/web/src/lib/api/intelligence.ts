import { apiRequest } from "./client";
import type {
  AskRequest,
  AskResponse,
  BriefingResponse,
  DeadlineAwarenessResponse,
  GoalProgressResponse,
  HabitConsistencyResponse,
  PatternResponse,
  ProviderConfigureRequest,
  ProviderConfigureResponse,
  ProviderInfoResponse,
  ProviderSecretResponse,
  TaskPrioritizeResponse,
  WeeklyReviewDraftResponse,
} from "./types";

export async function prioritizeTasksRequest(): Promise<TaskPrioritizeResponse> {
  return apiRequest<TaskPrioritizeResponse>("/intelligence/prioritize");
}

export async function dailyPlanRequest(): Promise<BriefingResponse> {
  return apiRequest<BriefingResponse>("/intelligence/daily-plan");
}

export async function deadlinesRequest(): Promise<DeadlineAwarenessResponse> {
  return apiRequest<DeadlineAwarenessResponse>("/intelligence/deadlines");
}

export async function goalsProgressRequest(): Promise<GoalProgressResponse[]> {
  return apiRequest<GoalProgressResponse[]>("/intelligence/goals/progress");
}

export async function habitsConsistencyRequest(): Promise<
  HabitConsistencyResponse[]
> {
  return apiRequest<HabitConsistencyResponse[]>(
    "/intelligence/habits/consistency",
  );
}

export async function patternsRequest(): Promise<PatternResponse[]> {
  return apiRequest<PatternResponse[]>("/intelligence/patterns");
}

export async function briefingRequest(): Promise<BriefingResponse> {
  return apiRequest<BriefingResponse>("/intelligence/briefing");
}

export async function weeklyReviewRequest(): Promise<WeeklyReviewDraftResponse> {
  return apiRequest<WeeklyReviewDraftResponse>("/intelligence/weekly-review");
}

export async function askRequest(input: AskRequest): Promise<AskResponse> {
  return apiRequest<AskResponse>("/intelligence/ask", {
    method: "POST",
    body: input,
  });
}

export async function listProvidersRequest(): Promise<ProviderInfoResponse[]> {
  return apiRequest<ProviderInfoResponse[]>("/intelligence/providers");
}

export async function configureProviderRequest(
  input: ProviderConfigureRequest,
): Promise<ProviderConfigureResponse> {
  return apiRequest<ProviderConfigureResponse>(
    "/intelligence/providers/configure",
    { method: "POST", body: input },
  );
}

export async function providerSecretRequest(): Promise<ProviderSecretResponse> {
  return apiRequest<ProviderSecretResponse>("/intelligence/providers/secret");
}

export async function providerHealthRequest(
  providerName: string,
): Promise<ProviderInfoResponse> {
  return apiRequest<ProviderInfoResponse>(
    `/intelligence/providers/${encodeURIComponent(providerName)}/health`,
  );
}
