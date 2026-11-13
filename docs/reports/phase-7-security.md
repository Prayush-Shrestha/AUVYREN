# Phase 7 — Security Review

**Date:** 13 November 2026  
**Scope:** browser security boundary, authentication/authorization, consent, secrets,
dependencies and the production Compose topology.  
**Result:** No open critical or high-severity application finding. Residual operational
risks are listed in §7.

## 1. Controls verified

| Area | Control |
| --- | --- |
| Passwords | Argon2id via `pwdlib[argon2]`; 12–128 characters; generic auth errors |
| Sessions | 256-bit opaque token, SHA-256 hash at rest, HttpOnly `SameSite=Lax` cookie, rotation |
| Session lifetime | 30-day sliding TTL, 90-day absolute cap, throttled `last_used_at` |
| CSRF | Session-bound token in a readable cookie plus `X-CSRF-Token`; Origin/Referer checks |
| Authorization | Every resource query scoped to the authenticated user; cross-user tests |
| Consent | Server-side consent check before any cloud context transmission |
| Account deletion | Re-authentication plus a single-use confirmation token; token hashed at rest |
| AI keys | No cloud key is accepted or stored; the cloud adapter is a refusing stub and `encrypted_secret` remains `NULL` |
| Audit | Privacy-sensitive actions emit audit events |
| Rate limits | Per-IP and per-email limits on auth paths; `429` with `Retry-After` |
| Errors/logs | RFC 9457 problem details; request IDs; no secrets or note content in logs |
| TLS | Caddy terminates HTTPS; HSTS on secure responses; HTTP is not exposed |
| Headers | CSP, nosniff, frame denial, referrer policy, permissions policy, COOP/CORP |
| Containers | API and web run as non-root; database and Mailpit only bind loopback on the host |

## 2. Content Security Policy

The web edge issues a **fresh nonce per document** and uses:

```text
default-src 'self';
script-src 'self' 'nonce-<random>' 'strict-dynamic';
style-src 'self' 'unsafe-inline';
img-src 'self' blob: data:;
font-src 'self' data:;
connect-src 'self' <api-origin>;
worker-src 'self' blob:;
manifest-src 'self';
object-src 'none';
base-uri 'self';
form-action 'self';
frame-ancestors 'none'
```

- `'unsafe-inline'` is limited to styles. It is required by React style attributes and the
  design catalogue's live swatches; scripts are nonce-bound with `strict-dynamic`.
- `'unsafe-eval'` is added only when `NODE_ENV !== "production"`.
- `upgrade-insecure-requests` and HSTS are added only for HTTPS requests.
- The API sends its own restrictive CSP in production: `default-src 'none'`,
  `script-src 'self'`, `connect-src 'self'`, `form-action 'self'`, plus HSTS.
- Playwright asserts that two consecutive documents receive different nonces and that every
  script nonce matches the header.

## 3. Verification evidence

| Check | Command | Result |
| --- | --- | --- |
| Backend integration suite | `npm run test:api` (real PostgreSQL) | 85 passed |
| Auth/CSRF/rate-limit tests | included above | Pass, including `429` + `Retry-After` |
| Consent enforcement | `test_intelligence.py`, `test_privacy.py` | Pass; no call without consent |
| Cross-user access | auth, knowledge and privacy suites | Pass; 404/empty results, never foreign rows |
| Web unit/component tests | `npm run test:web` | 41 passed |
| Browser security tests | `npx playwright test e2e/security.spec.ts` | Pass |
| Full browser journeys | `npx playwright test` | 21 desktop + 3 mobile |
| Production dependency audit | `npm audit --omit=dev --audit-level=high` | 0 vulnerabilities |
| Python dependency audit | `pip-audit` in `apps/api` | No known vulnerabilities |
| Full development audit | `npm audit` | 8 moderate, dev-only |
| Static checks | ESLint, `tsc --noEmit`, `ruff check app tests` | Pass |
| Migration drift | `alembic check` | Pass, 22 tables |

The 8 moderate development findings are the `minimatch` advisory reached through
`eslint-config-next`/`typescript-eslint`. They are not present in the standalone production
bundle. The accepted risk is recorded in §7; production dependencies remain clean.

## 4. Findings resolved during Phase 7

| Finding | Severity | Resolution |
| --- | --- | --- |
| Cloud context path could run without a persisted consent check | High | Consent is enforced in the service before provider invocation; tests cover denial and grant |
| Deletion confirmation tokens were stored in a recoverable form | Medium | Only a hash is persisted; confirmation compares hashes and is single-use |
| Knowledge links did not consistently verify note ownership and source | High | Every source/target note and link operation is user-scoped; cross-user IDs return not found |
| Note link creation was not idempotent | Medium | Unique edge constraint plus deterministic handling returns the existing link |
| Enum filters accepted values outside the API contract | Medium | Explicit enum validation on list filters |
| Server-rendered pages did not forward session/CSRF context | Functional/high impact | Cookie and trusted Origin are forwarded server-side; CSRF remains header-bound |
| Missing CSP/security headers on web documents | High | Per-request nonce CSP and hardening headers in `proxy.ts`; verified in Chromium |
| Account menu label did not match its accessible name | Low (accessibility) | Trigger renamed to match visible text |
| Nonce read through `getAttribute` was empty | Test defect | Tests read `HTMLScriptElement.nonce` |

## 5. Deployment hardening

- Caddy is the only published HTTP endpoint; `db` and Mailpit bind `127.0.0.1` only.
- Caddy limits request bodies to 10 MB, removes the `Server` header and writes JSON access
  logs. Docker log rotation caps each service at 10 MB × 3.
- Compose runs `APP_ENV=production`, `DEBUG=false`, `DOCS_ENABLED=false`, forces
  `SESSION_COOKIE_SECURE=true`, and keeps the API to one worker for the in-process limiter.
- PostgreSQL data lives in a named volume; backups are checksummed custom archives.
- Mailpit is a local reset-mail capture service. It is not a production mail provider and
  must be replaced by SMTP for public users.

## 6. Security checklist

- [x] Authentication, session rotation, revocation and CSRF are tested against PostgreSQL.
- [x] Cross-user access is denied for every resource covered by the suite.
- [x] No cloud AI transmission without explicit, revocable consent.
- [x] Secrets are server-only; `.env` is gitignored; no secrets in `NEXT_PUBLIC_*`.
- [x] CSP is nonce-based for scripts; inline styles are the only relaxation.
- [x] Cookies are HttpOnly, `SameSite=Lax`, and Secure in Compose.
- [x] Rate limiting is enabled in production and covered by a `429` test.
- [x] Production dependency audit is clean; Python audit is clean.
- [x] Containers run as non-root; database and mail ports are loopback-only.
- [x] Backups are checksummed, permission-restricted and restorable (drill evidence in the
      backup/restore report).
- [x] Logs correlate through `X-Request-ID` and do not contain secrets.
- [ ] Public domain, certificate and SMTP relay — required before public launch, not part of
      the private reference deployment.
- [ ] Screen-reader and external penetration testing — recommended before broad launch.

## 7. Residual risks and accepted trade-offs

1. **In-process rate limiter.** Limits reset on restart and are not shared across workers.
   The deployment stays at one worker; move to Redis or the edge before scaling out.
2. **Private local CA.** The reference stack uses Caddy's internal CA. A public deployment
   must use a real certificate and domain, otherwise browsers cannot establish trust.
3. **Mailpit.** Reset tokens are visible to anyone who can reach the loopback UI. Public
   deployments must use a real SMTP relay and not expose Mailpit.
4. **Development-only audit findings.** Eight moderate `minimatch` advisories remain in the
   lint toolchain. They are not in production dependencies; upgrade when the upstream
   ESLint config allows it.
5. **No WAF or hosted monitoring.** Caddy body limits and application validation are the
   only edge protections. The health script and webhook cover availability, not intrusion
   detection.
6. **Cloud AI remains deliberately disabled.** The cloud adapter is a refusing stub; there
   is no outbound cloud transmission path to review or enable without a future phase.
7. **Single-host database.** There is no managed failover. Off-host backups and the restore
   drill are the recovery mechanism.
