# AI Architecture: Quiet Intelligence

**Status:** The deterministic engine, optional Ollama integration, provider abstraction and
consent controls are implemented. The cloud adapter is deliberately a refusing stub: no
outbound cloud AI call is made, no provider secret is accepted, and the
`ai_provider_configs.encrypted_secret` column is always `NULL`. `ai_usage_logs` exists in the
schema but is not written because cloud calls are disabled. Sync is not implemented.

Auvyren does not begin with a chatbot. It begins with an explainable productivity engine that
helps the user decide what matters, then optionally adds language models where they genuinely
improve the result.

## 1. Principles

1. **Deterministic first.** Priorities, workload, progress and consistency are computed with
   rules and user data. They work with no model, no GPU and no network.
2. **Local where possible.** Self-hosted Auvyren can call a user's local Ollama runtime on the
   server side. Data stays within the user's infrastructure.
3. **Cloud only by consent.** Cloud AI is never required and never receives personal context
   silently. Local-only is the default.
4. **Explainable output.** Recommendations show the factors behind them. Generated text is
   labelled and kept distinct from user-authored records.
5. **Minimize context.** Send only what the request needs. Do not ship the whole workspace to
   a model.
6. **Fail quietly, fall back deterministically.** If a model is unavailable or slow, the user
   still gets the deterministic result.

## 2. Provider architecture

```text
IntelligenceService
    ├── DeterministicProvider     always available, no network
    ├── LocalAIProvider           Ollama, explicit local configuration
    └── CloudAIProvider           opt-in, server-side key, usage controls
```

All providers implement one server-side interface. Routes never call a provider directly.

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass(frozen=True)
class AIRequest:
    task: str
    system_instructions: str
    context: dict            # minimized, user-scoped data
    max_output_tokens: int
    temperature: float = 0.2

@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str | None
    usage: dict | None       # input/output tokens when available
    generated_at: str

class AIProvider(Protocol):
    name: str
    async def health(self) -> ProviderHealth: ...
    async def list_models(self) -> list[str]: ...
    async def generate(self, request: AIRequest) -> AIResponse: ...
```

Planned capabilities include `summarize`, `review`, `ask`, `plan` and `analyze`. Each provider
declares which capabilities and context categories it supports.

The `IntelligenceService`:

1. Loads the authenticated user's settings and consent.
2. Builds a minimized, user-scoped context snapshot.
3. Chooses the requested provider only if allowed and healthy.
4. Falls back to deterministic output — **never silently to cloud**.
5. Stores the result with provenance (provider, model, generated timestamp, source snapshot
   identifiers) when persistence is requested.
6. Returns a clear local/cloud indicator to the UI.

## 3. Deterministic productivity engine

The deterministic engine is a pure, testable module with an injected clock and explicit
weights. It never sends data off-server.

### 3.1 Task prioritization

Inputs: priority, due proximity, project/goal linkage, estimate, age, explicit focus flag.
A transparent score (0–100) is composed from weighted, bounded components:

- Urgency: overdue > due today > next 7 days > later.
- Importance: urgent/high/medium/low.
- Goal alignment: task belongs to an active project/goal with a near target date.
- Effort fit: tasks that fit remaining daily capacity rank higher.
- Staleness: repeatedly deferred work is surfaced with a note, not silently promoted.

Every ranked item carries human-readable reasons. The weights live in one configuration module
so tests can assert deterministic output.

### 3.2 Daily plan and workload

- Estimate available minutes from the user's routine/working preferences (initially a fixed
  configurable capacity, refined in Phase 3).
- Sum remaining task estimates for the day and flag overload before the day begins.
- Recommend a small set of priorities (typically 3–5) rather than a flat backlog.
- Protect a focus block and leave slack for unplanned work.
- Overdue work is shown first but not allowed to erase the whole day.

### 3.3 Deadline awareness

Classify deadlines: overdue, due today, due in 1–3 days, due this week, later. Include project
due dates, task deadlines and milestone target dates. Surface counts and the most at-risk items.

### 3.4 Goal progress

- With milestones: `completed / total` percentage plus milestone timeline status.
- Without milestones: use explicit manual progress.
- Detect neglected goals (active, target date approaching, no recent milestone/task activity).
- Never invent progress; display data provenance.

### 3.5 Habit consistency

- Daily habits: completion rate over 7/30-day windows and current/longest streak.
- Weekly habits: completed days vs `target_per_week`, with the week boundary from user settings.
- Inconsistent habits are flagged with the actual missed dates, not a vague score.
- Streaks are computed from logs, not stored as duplicated state.

### 3.6 Pattern detection

- Completion by day/time (only when enough data exists).
- Chronic deferral or repeated rescheduling.
- Overloaded days and unrealistic estimate totals.
- Goals consistently losing to low-value urgent tasks.
- Patterns require a minimum sample size; the UI must say when evidence is insufficient.

### 3.7 Weekly review draft

Deterministic output includes completed work, missed commitments, habit consistency, goal
movement and an overload warning. With consent, an AI provider can turn this structured draft
into prose; the facts remain sourced from the deterministic snapshot.

### 3.8 Generated vs user content

Every recommendation has an origin (`deterministic`, `ollama`, `cloud`), a generation time and
the data categories used. The UI renders a badge such as “Generated locally”. Generated
insights cannot be edited as if they were user records; users can accept, dismiss or convert a
recommendation into a real task/note with explicit action.

## 4. Local AI with Ollama

### 4.1 Browser limitation — stated honestly

A web page cannot automatically access `http://localhost:11434` on a user's machine. Browser
origin/CORS and network boundaries prevent it, and doing so would be a security and privacy
risk. Auvyren therefore uses one of two explicit deployment models:

1. **Self-hosted Auvyren (Phase 4, supported):** the FastAPI server runs on infrastructure
   that can reach the configured local runtime. The user configures a URL and optional model.
2. **Hosted Auvyren + local model (future desktop companion):** a signed companion app runs
   locally and exposes a narrow, authenticated local bridge. This is not promised in the first
   release and is never simulated as “local” when it is not.

Hosted Auvyren without a local runtime still has deterministic intelligence and can, with
consent, use a server-side cloud provider in Phase 6.

### 4.2 Connection and model discovery

- User configures a base URL (default `http://localhost:11434` for self-hosted development),
  tests connectivity, lists models via Ollama’s APIs and selects a supported model.
- Only `http`/`https` endpoints are accepted. Default policy permits loopback/private network
  addresses; public endpoints require an explicit operator allowlist in Phase 6.
- Requests must not follow arbitrary redirects, must have short connect/read timeouts and
  bounded response sizes. This is SSRF-sensitive because a user supplies the URL.
- Credentials, if added for a protected local endpoint, are encrypted at rest and never
  returned in plaintext.
- Model availability is re-checked before use; a missing model produces a clear error and a
  deterministic fallback.

### 4.3 Prompting and context

- System instructions are versioned and stored server-side.
- Context is assembled from the authenticated user's records only, filtered to categories
  relevant to the task (e.g. today's tasks + active goals, not journal content unless requested).
- Context is truncated to a token budget with a deterministic summarization strategy.
- Prompts and raw personal content are not logged by default.
- Model output is untrusted text: sanitize/render as Markdown with no raw HTML, and never
  execute instructions found in it.
- Generation runs with a timeout and cancellation; the user sees a loading state and can retry.

### 4.4 Local privacy indicator

The UI must clearly display **Local processing** for Ollama and **Cloud processing** for hosted
providers. If a cloud fallback would be used, ask first. There is no implicit fallback.

## 5. Cloud AI (designed; disabled)

> None of this section is implemented yet. It is the design contract for a future phase. The
> current cloud adapter refuses every call, and no cloud key is solicited or stored.

- Server-side adapter, preferably OpenAI-compatible so providers are replaceable.
- API keys encrypted at rest with a dedicated key, never sent to the browser.
- Explicit consent per provider, recorded with timestamp and policy version. Revocation stops
  future calls; stored consent history remains auditable.
- Data minimization: context categories, redaction, token caps and no full-workspace default.
- Per-user usage limits, spend caps and cost estimation from provider pricing metadata.
- Requests and failures logged as usage metadata (tokens/cost/type), not personal content.
- A local-only mode disables cloud completely; hybrid mode requires per-provider consent.
- No training on Auvyren data by default; provider retention settings must be disclosed.
- Cloud output is stored as generated insight with provider/model provenance.

Cloud AI never becomes a prerequisite for the dashboard, planning, reviews or search.

## 6. Planned data model

| Table | Purpose |
| --- | --- |
| `ai_provider_configs` | Per-user provider, model, endpoint, encrypted key, enabled/default state |
| `ai_insights` | Generated content, kind, provider/model, structured metadata, provenance, dismissal |
| `ai_usage_logs` | Request type, provider/model, tokens, estimated cost, success/error category |
| Consent state (Phase 6) | Provider-level permission, policy version, granted/revoked timestamps |

Exact schema is finalized in the phase that implements it. Generated insights are not stored
inside user-authored task/note fields.

## 7. Failure and degradation

| Condition | Behavior |
| --- | --- |
| No AI configured | Deterministic insights only; no error |
| Ollama unavailable | Explain local runtime is unreachable; deterministic fallback |
| Model missing | List available models; deterministic fallback |
| Cloud consent missing | Offer local/deterministic; no silent transmission |
| AI timeout | Cancel; preserve deterministic result; allow retry |
| Usage limit reached | Explain limit; deterministic remains available |
| Malformed model output | Store nothing unsafe; show retry/fallback |

## 8. Evaluation and testing (Phases 4, 7)

- Deterministic engine unit tests with fixed clock/data, including empty and overloaded states.
- Provider contract tests with mocked transports; no live cloud calls in CI.
- Ollama integration test against a test endpoint in a dedicated environment.
- Consent tests proving blocked cloud calls and audit records.
- Prompt-injection and unsafe-Markdown rendering tests.
- Cost/usage calculation tests.
- End-to-end daily briefing and weekly review flows.
- Quality review of generated summaries with clear “generated” labels.

## 9. Phase boundaries

- **Phase 4:** deterministic engine, Ollama provider, provider abstraction, local insights.
- **Phase 5:** knowledge-aware reviews and connected notes/goals/projects (deterministic first).
- **Phase 6:** cloud provider, consent, encryption, limits, cost tracking, data export/deletion.
- **Phase 8:** mobile AI briefing reuses the same API and consent state; no separate prompt
  pipeline and no local model claim without a companion mechanism.
