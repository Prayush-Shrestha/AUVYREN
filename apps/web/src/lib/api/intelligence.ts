import { apiRequest } from "./client";
import type {
  AskRequest,
  AskResponse,
  BriefingResponse,
  DeadlineAwarenessResponse,
  GoalProgressResponse,
  HabitConsistencyResponse,
  KnowledgeSearchResponse,
  NoteCreate,
  NoteLinkCreate,
  NoteLinkResponse,
  NoteListResponse,
  NoteResponse,
  NoteUpdate,
  PatternResponse,
  ProviderConfigureRequest,
  ProviderConfigureResponse,
  ProviderInfoResponse,
  ProviderSecretResponse,
  TaskPrioritizeResponse,
  WeeklyReviewDraftResponse,
} from "./types";

export async function createNoteRequest(
  input: NoteCreate,
): Promise<NoteResponse> {
  return apiRequest<NoteResponse>("/knowledge", {
    method: "POST",
    body: input,
  });
}

export async function listNotesRequest({
  kind,
  source_type,
  include_deleted,
  limit,
  offset,
}: {
  kind?: string;
  source_type?: string;
  include_deleted?: boolean;
  limit?: number;
  offset?: number;
}): Promise<NoteListResponse> {
  const params = new URLSearchParams();
  if (kind) params.set("kind", kind);
  if (source_type) params.set("source_type", source_type);
  if (include_deleted) params.set("include_deleted", "true");
  if (limit) params.set("limit", String(limit));
  if (offset) params.set("offset", String(offset));
  const qs = params.toString();
  return apiRequest<NoteListResponse>(
    `/knowledge${qs ? "?" + qs : ""}`,
  );
}

export async function getNoteRequest(
  noteId: string,
): Promise<NoteResponse> {
  return apiRequest<NoteResponse>(`/knowledge/${noteId}`);
}

export async function updateNoteRequest(
  noteId: string,
  input: NoteUpdate,
): Promise<NoteResponse> {
  return apiRequest<NoteResponse>(`/knowledge/${noteId}`, {
    method: "PATCH",
    body: input,
  });
}

export async function deleteNoteRequest(
  noteId: string,
): Promise<void> {
  return apiRequest<void>(`/knowledge/${noteId}`, {
    method: "DELETE",
  });
}

export async function restoreNoteRequest(
  noteId: string,
): Promise<NoteResponse> {
  return apiRequest<NoteResponse>(`/knowledge/${noteId}/restore`, {
    method: "POST",
  });
}

export async function createNoteLinkRequest(
  noteId: string,
  input: NoteLinkCreate,
): Promise<NoteResponse> {
  return apiRequest<NoteResponse>(`/knowledge/${noteId}/links`, {
    method: "POST",
    body: input,
  });
}

export async function listNoteLinksRequest(
  noteId: string,
): Promise<NoteLinkResponse[]> {
  return apiRequest<NoteLinkResponse[]>(`/knowledge/${noteId}/links`);
}

export async function deleteNoteLinkRequest(
  linkId: string,
): Promise<void> {
  return apiRequest<void>(`/knowledge/links/${linkId}`, {
    method: "DELETE",
  });
}

export async function searchNotesRequest({
  q,
  kind,
  limit,
}: {
  q: string;
  kind?: string;
  limit?: number;
}): Promise<KnowledgeSearchResponse> {
  return apiRequest<KnowledgeSearchResponse>("/knowledge/search", {
    method: "POST",
    body: { q, kind, limit: limit ?? 50 },
  });
}

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
