# Security and Authentication Strategy

**Status:** Phase 0 establishes the security boundary and schema. Authentication endpoints,
CSRF enforcement, rate limiting and AI consent flows are implemented in later phases.

## 1. Security goals

1. A user can only read or modify their own records.
2. Browser credentials cannot be exfiltrated by application JavaScript.
3. Passwords and session/reset tokens are never stored in recoverable form.
4. Personal data is not sent to any external AI provider without explicit, revocable consent.
5. Errors, logs and analytics do not leak secrets or personal content.
6. Destructive and privacy-sensitive operations are explicit and auditable.

## 2. Threat model

| Threat | Primary controls |
| --- | --- |
| Credential stuffing / brute force | Argon2id, rate limits, progressive delay, generic errors, security events |
| Session theft via XSS | HttpOnly cookies, strict CSP on web, no tokens in localStorage, short-lived/revocable sessions |
| CSRF | `SameSite=Lax`, session-bound CSRF token header, Origin/Referer verification |
| IDOR / cross-user access | Server-side user scoping, ownership checks, integration tests, cascades |
| SQL injection | SQLAlchemy parameterization; no raw user SQL; strict query whitelists |
| Host-header attacks | TrustedHost allowlist |
| Secret leakage | Server-only env, gitignored env files, no secrets in `NEXT_PUBLIC_*`, redacted logs |
| Malicious local AI endpoint / SSRF | Endpoint scheme/address validation, private-network rules, no redirects, timeouts |
| Cloud AI data leakage | Explicit consent, data minimization, local-only default, server-side calls |
| Account enumeration | Uniform login/reset responses and timing awareness |
| Dependency compromise | Lockfile, audit in CI, minimal dependencies, review upgrades |
| Backup/media exposure | Private managed PostgreSQL, encrypted backups, no public dumps (Phase 7) |

Out of scope for the initial web release: nation-state adversaries, a compromised user device,
and malicious users with server root access. Self-hosted operators are trusted infrastructure
owners; the application still isolates user accounts.

## 3. Authentication (Phase 2)

### Passwords

- Hash with **Argon2id** via `pwdlib[argon2]`; parameters maintained with library defaults and
  reviewed as hardware improves.
- Minimum length 12 characters, maximum 128 to bound hashing cost; no arbitrary composition
  rules. Reject known-breached passwords when a breach-check integration is added.
- Normalize email to lowercase and trim; validate with a standards-compliant validator.
- Never log passwords, password hashes or reset tokens.
- Password reset invalidates all existing sessions after successful reset.

### Registration and login

- Unique email enforced in the database; conflicts return a safe, actionable validation error
  without exposing unrelated account details.
- Successful login creates a new opaque session, sets cookies and updates `last_login_at`.
- Failed login returns a generic invalid-credentials message and records a security event
  (Phase 6 audit table; interim logging in Phase 2).
- Inactive users cannot authenticate.
- The initial account response returns only id, email, display name and settings.

### Sessions

- 256-bit cryptographically random token generated with `secrets.token_urlsafe` (or equivalent).
- Store only the SHA-256 hash. A database leak does not yield usable session tokens.
- Cookie: `auv_session`, `HttpOnly`, `Secure` in production, `SameSite=Lax`, `Path=/`,
  appropriate max-age. Never readable by JavaScript.
- Session lifetime: 30-day sliding inactivity, absolute cap of 90 days. `last_used_at` updates
  are throttled (e.g. once per 5 minutes) to reduce writes.
- Login rotates/creates a session; logout revokes it; users can revoke other sessions.
- Session tokens are compared in constant time where relevant.
- A scheduled cleanup removes expired/revoked rows after a retention window.

### CSRF

- Session record includes a CSRF secret; a non-HttpOnly `auv_csrf` cookie carries the
  browser-readable token derived from it.
- Every mutating request must send `X-CSRF-Token`; the server verifies it against the session.
- `SameSite=Lax` blocks most cross-site submission; Origin/Referer validation adds defense in
  depth for state-changing requests.
- Login/logout endpoints are also CSRF-aware where applicable. CORS does not replace CSRF.

### Password reset

- Request returns the same generic message whether or not the email exists.
- 30-minute single-use token; only its hash is stored.
- Reset links use the configured web origin, never an attacker-controlled host.
- Rate limited per email and IP.
- Development uses a console email adapter that logs the link; production requires SMTP.
- No token appears in API responses.

### Account protection

- Rate-limit login, registration, forgot-password and reset endpoints.
- Optional email verification is supported by the schema but not required for Phase 2.
- Security-sensitive actions (password change, email change, export, deletion, AI consent)
  re-authenticate or require a fresh session in Phase 6.

## 4. Authorization and data isolation

- Every authenticated request resolves a `CurrentUser` server-side from the session.
- Product services require `user_id` for every create and filter every read by it.
- `milestones` and `routine_steps` do not carry `user_id`; access must join the parent goal or
  routine and verify ownership.
- Cross-user resource access returns **404**, not 403, to avoid confirming existence.
- The frontend route guard is UX only. The API authorizes independently.
- Database cascades ensure account deletion removes owned data; export precedes deletion.
- IDOR tests are mandatory for every resource added in Phase 3 and repeated in Phase 7.

PostgreSQL row-level security is not used in the initial architecture. Application-level
scoping plus tests is the chosen boundary; RLS will be reconsidered if background jobs or
multi-tenant analytics make it necessary.

## 5. Transport and browser security

- HTTPS only in production; HSTS enabled when secure cookies are on.
- Trusted host allowlist from environment.
- Explicit CORS origins with credentials; wildcard rejected in production.
- API responses set `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`,
  `Referrer-Policy: strict-origin-when-cross-origin`, a restrictive `Permissions-Policy` and
  `Cross-Origin-Resource-Policy: same-site`.
- The web app adds a Content Security Policy, frame protections and route-appropriate headers
  in Phase 1/7. The API CSP is not a substitute for the web CSP.
- No credentials or personal data in URLs or query strings.
- Request body size limits are enforced at the proxy and in application validation.

## 6. Secrets and key management

- Secrets are read only by the API from server-side environment variables.
- `.env` files are gitignored; `.env.example` contains placeholders only.
- `NEXT_PUBLIC_*` is treated as public. No keys, passwords or private URLs belong there.
- AI provider API keys will be encrypted at rest with a dedicated key
  (`AI_KEY_ENCRYPTION_KEY`) using an authenticated encryption scheme (e.g. Fernet/AES-GCM).
  Encrypted values are never returned to clients.
- Production secrets live in the platform secret manager; rotation and audit are Phase 7.
- Logs redact authorization headers, cookies, password fields, tokens and provider keys.
- Error responses never include stack traces, SQL or configuration.

## 7. AI privacy controls (Phases 4 and 6)

- Default mode is **deterministic only**; no external AI is called unless configured.
- Local AI processing is indicated in the UI as local. A hosted Auvyren instance cannot reach
  a user's machine unless the user explicitly connects a reachable runtime; this is never
  implied or simulated.
- Cloud AI requires explicit, per-provider consent and a visible indicator before sending
  personal context. Consent can be revoked.
- Context is minimized to the specific request (e.g. relevant tasks/goals), not the entire
  workspace by default.
- No training on user data by Auvyren. Cloud provider terms and data-retention settings are
  surfaced before consent.
- Generated content is stored with provenance and clearly distinguished from user records.
- Usage limits, cost estimation and spend caps are required before cloud AI is enabled in
  production.
- Export and deletion include AI-generated insights and provider configuration.

## 8. Data export and account deletion (Phase 6)

- Export includes user-authored records and generated insights with provenance in a portable
  format; secrets are excluded.
- Deletion requires re-authentication and explicit confirmation.
- Deletion is transactional and cascades from the user row. Backups expire according to the
  documented retention policy; deletion from backups is handled operationally.
- Export/deletion events are recorded in security/audit logs without personal content.

## 9. Logging and monitoring

- Request ID correlation is implemented.
- Never log bodies by default; especially not auth, journal or AI prompts.
- Authentication failures, rate-limit hits, session revocations, exports, deletions and AI
  consent changes are security events (audit table in Phase 6).
- Production logs are JSON; centralized retention and alerting are Phase 7.
- Health endpoints do not reveal schema or dependency credentials.

## 10. Implemented vs planned

| Control | Phase 0 | Target phase |
| --- | --- | --- |
| Env separation and gitignored secrets | ✅ | — |
| Strong secret/config validation (production mode) | ✅ | — |
| Request IDs, RFC 9457 errors, safe 500s | ✅ | — |
| CORS allowlist, trusted hosts, security headers | ✅ | — |
| Database constraints, cascades, unique tokens | ✅ | — |
| Argon2id passwords and registration/login | — | 2 |
| Opaque sessions, secure cookies, CSRF | Schema only | 2 |
| Password reset email flow | Schema/config only | 2 |
| Login rate limiting and security events | — | 2/6 |
| AI consent and encrypted provider keys | — | 4/6 |
| Export, deletion, audit trail | — | 6 |
| CSP, dependency audit in CI, penetration tests | — | 7 |

## 11. Security review gates

A phase is not complete if it introduces a mutation path without:

1. Server-side authentication and ownership checks.
2. Input validation and safe error responses.
3. An authorization test proving cross-user access fails.
4. Logs that do not contain secrets or personal content.
5. A documented privacy impact when AI or external services are involved.
