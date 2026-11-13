# API Architecture

**Base path:** `/api/v1` for product resources
**Operational health:** `/health/live`, `/health/ready`
**Interactive docs:** `/docs` (development; can be disabled)
**OpenAPI:** `/openapi.json`

The API is the only authority for data access and user scoping. The frontend never talks
directly to PostgreSQL or AI providers.

## 1. Operational and meta endpoints

Product endpoints are grouped under `/api/v1` (auth, tasks, projects, goals, habits,
routines, calendar, intelligence, knowledge, privacy). The OpenAPI schema is the source of
truth when docs are enabled. The stable operational surface is:

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/` | Service metadata and docs link |
| `GET` | `/health/live` | Process liveness; no database dependency |
| `GET` | `/health/ready` | Readiness; verifies PostgreSQL with `SELECT 1` |
| `GET` | `/api/v1/meta` | Versioned API metadata |
| `GET` | `/docs` | Swagger UI, when docs are enabled |
| `GET` | `/openapi.json` | OpenAPI schema, when docs are enabled |

Health responses:

```json
{
  "status": "ok",
  "service": "Auvyren API",
  "version": "0.1.0",
  "database": "ok"
}
```

## 2. Conventions

### Transport

- HTTPS in production; JSON request/response bodies.
- `Content-Type: application/json` for request bodies.
- Timestamps are ISO 8601 UTC strings with offsets, e.g. `2026-11-06T14:30:00Z`.
- Calendar-day values are ISO dates, e.g. `2026-11-06`, interpreted in the user's timezone.
- Field names are `snake_case` across the API and database.
- IDs are UUID strings.
- Enumerations are lowercase strings. Clients must tolerate unknown values only where
  explicitly documented.

### Status codes

| Code | Use |
| --- | --- |
| `200` | Successful read/update |
| `201` | Resource created; `Location` header where useful |
| `204` | Successful delete/no content |
| `400` | Malformed request |
| `401` | Missing/expired session |
| `403` | Authenticated but not allowed |
| `404` | Missing resource **or** resource owned by another user |
| `409` | Conflict, duplicate or stale version |
| `422` | Field validation failure |
| `429` | Rate limit exceeded |
| `503` | Readiness/dependency failure |

### Request IDs and errors

Every response includes `X-Request-ID`. A well-formed client value is echoed; otherwise the
server generates one.

Errors use [RFC 9457](https://www.rfc-editor.org/rfc/rfc9457) problem details with
`application/problem+json`:

```json
{
  "type": "https://auvyren.app/problems/request_validation_failed",
  "title": "Request validation failed",
  "status": 422,
  "detail": "One or more fields are invalid.",
  "instance": "/api/v1/tasks",
  "code": "request_validation_failed",
  "request_id": "f9a5d57f4b0a4e25888a3a57e4ec7b9e",
  "errors": [
    {
      "field": "body.title",
      "message": "Field required",
      "type": "missing"
    }
  ]
}
```

The `code` is stable for client branching. The `detail` is human-readable and safe to show.
Unknown internal errors return a generic message; diagnostics live in server logs.

### Authentication and CSRF

- Browser sessions use an HttpOnly cookie.
- Mutating requests require the session-bound CSRF header.
- The frontend obtains the CSRF token from the readable CSRF cookie and sends it as
  `X-CSRF-Token`.
- `401` drives the web app to sign-in; `403` is a genuine authorization failure.
- All resource queries are scoped to the authenticated user. Cross-user access returns `404`
  to avoid existence leakage.

Exact session behavior and controls are in [security](security.md).

### Pagination

Collection endpoints use offset pagination by default:

```json
{
  "items": [],
  "total": 0,
  "limit": 50,
  "offset": 0
}
```

Rules:

- `limit` default 50, maximum 100.
- `offset` minimum 0.
- Collections are ordered deterministically (requested sort, then `id`).
- Cursor pagination will be introduced for sync/change feeds in Phase 6, not forced onto
  ordinary lists.

### Filtering, sorting and search

- Explicit filter parameters only; no arbitrary SQL expressions.
- Example: `GET /api/v1/tasks?status=todo&priority=high&project_id=...&planned_for=2026-11-06`.
- Sort fields are whitelisted per endpoint; default is deterministic.
- Search uses a `q` parameter and is case-insensitive; implementation may use `ILIKE`,
  trigram or full-text indexes without changing the contract.
- Unknown query parameters are rejected in development/contract tests and ignored in forward
  compatibility scenarios only if explicitly documented (default: reject via strict models).

### Mutations and idempotency

- `POST` creates; `PATCH` partially updates; `PUT` replaces only where stated; `DELETE`
  removes or soft-deletes according to the resource.
- Completion/reopen are explicit action endpoints rather than ambiguous field toggles.
- Phase 6 adds `Idempotency-Key` support to sensitive creates and sync writes. Phase 0 does
  not claim it.
- Concurrent edits will use an explicit version/conflict token in Phase 6; clients must not
  assume silent last-write-wins.

### Rate limiting

Planned for Phase 2/6:

- Authentication: per IP and per normalized email, low threshold, progressive delay.
- Forgot-password: per account and IP; always generic response.
- AI endpoints: per user, with provider-specific and daily limits.
- General API: reasonable per-session limits with `429` and `Retry-After`.

Rate-limit headers and limits are not yet implemented.

## 3. Endpoint map by phase

This is a contract outline, not a claim of implementation. Names may be refined in the phase
plan, but resource boundaries and ownership rules are fixed.

### Phase 2 — Authentication and profile

| Method | Path | Purpose |
| --- | --- | --- |
| `POST` | `/auth/register` | Create account; sets initial session |
| `POST` | `/auth/login` | Verify credentials; rotate/create session |
| `POST` | `/auth/logout` | Revoke current session; clear cookies |
| `GET` | `/auth/me` | Current user + settings |
| `PATCH` | `/users/me` | Update display name/email with validation |
| `PATCH` | `/settings` | Timezone, week start |
| `POST` | `/auth/password/forgot` | Send generic reset link |
| `POST` | `/auth/password/reset` | Consume one-time token |
| `GET` | `/auth/sessions` | List active sessions |
| `DELETE` | `/auth/sessions/{id}` | Revoke a session |

### Phase 3 — Productivity

| Resource | Endpoints |
| --- | --- |
| Dashboard | `GET /dashboard/today` |
| Tasks | `GET/POST /tasks`, `GET/PATCH/DELETE /tasks/{id}`, `POST /tasks/{id}/complete`, `POST /tasks/{id}/reopen` |
| Projects | `GET/POST /projects`, `GET/PATCH/DELETE /projects/{id}` |
| Goals | `GET/POST /goals`, `GET/PATCH/DELETE /goals/{id}`, `GET/POST /goals/{id}/milestones`, `PATCH/DELETE /milestones/{id}` |
| Habits | `GET/POST /habits`, `PATCH/DELETE /habits/{id}`, `PUT/DELETE /habits/{id}/logs/{date}` |
| Routines | `GET/POST /routines`, `GET/PATCH/DELETE /routines/{id}`, step CRUD |
| Calendar | `GET /calendar?start=…&end=…&view=month|week|day`, event CRUD |

Goal progress is returned as a computed value, not a client-maintained duplicate.

### Phase 4 — Intelligence

| Method | Path | Purpose |
| --- | --- | --- |
| `GET/PUT` | `/ai/settings` | Local/cloud mode and consent state |
| `GET` | `/ai/providers` | Available/configured providers and health |
| `POST` | `/ai/providers/local/test` | Validate local Ollama endpoint/models |
| `GET` | `/ai/insights` | Stored generated insights with provenance |
| `POST` | `/ai/insights/daily` | Deterministic daily briefing |
| `POST` | `/ai/insights/weekly` | Weekly analysis (deterministic or consented AI) |
| `POST` | `/ai/ask` | Workspace Q&A; explicit context and provider |

### Phase 5 — Knowledge

Notes, journals, decision records, weekly/monthly reviews, search, links, and AI-assisted
summaries under `/notes`, `/reviews`, `/search`, and `/notes/{id}/links`.

### Phase 6 — Privacy, sync, cloud

- `/privacy/export`, `/privacy/deletion`, `/privacy/ai-consent`
- `/sync/pull`, `/sync/push`, `/sync/status`, `/sync/devices`
- `/ai/cloud/providers`, `/ai/cloud/usage`

These require explicit consent, encrypted provider secrets, audit events and usage/cost
tracking before exposure.

## 4. Versioning and compatibility

- URL major version: `/api/v1`.
- Additive response fields are allowed.
- Removing/renaming fields or changing semantics requires a new major version or a documented
  deprecation window.
- OpenAPI is generated by FastAPI. A committed or generated client can be added in Phase 7.
- Breaking schema changes use expand/contract migrations.

## 5. CORS, hosts and browser boundary

- Allowed origins come from `CORS_ORIGINS`; wildcard is rejected in production.
- Credentials are allowed only for explicit origins.
- `ALLOWED_HOSTS` protects against host-header attacks.
- Request bodies are validated by Pydantic models with explicit size limits at the proxy.
- Cookies and CSRF are preferred over storing tokens in `localStorage`.

## 6. Health semantics

- **Liveness** must not depend on external services; it answers “is the process alive?”
- **Readiness** checks PostgreSQL and answers “can this instance serve traffic?”
- The web app should not use readiness as a user-facing health gauge.
- Detailed dependency information and metrics are not exposed publicly.

## 7. Contract testing

- Backend route tests cover success, validation, not-found, auth failures and ownership.
- Problem-details shape and request IDs are asserted.
- Phase 7 adds generated TypeScript types/contract tests and end-to-end flows.
- Any new endpoint gets an explicit test before it is marked complete.
