# Deployment Runbook

**Status:** Phase 7. The Compose stack is the reference single-host deployment: Next.js
standalone, FastAPI, PostgreSQL 17, Caddy and Mailpit. It runs the API in production mode
and serves the browser through Caddy with an internal CA at `https://localhost:8443`.

This is a complete, operable deployment for a private instance. A public deployment must
replace the local CA with a real domain and certificate, replace Mailpit with an SMTP relay,
and move backups off the host. Those steps are marked **[public]** below.

## 1. Topology

```text
Browser ── HTTPS :8443 ──> Caddy ──> web:3000   (Next.js standalone)
                              ├────> api:8000   (/api/*, /health/*)
                              └────> JSON access log on stdout

api ──> db:5432 (PostgreSQL 17, persistent volume)
api ──> mailpit:1025 (password-reset mail; operator UI on 127.0.0.1:8025)
migrate ──> db (one-shot `alembic upgrade head`, must exit 0)
```

Compose services:

| Service | Role | Health |
| --- | --- | --- |
| `db` | PostgreSQL 17, loopback-only host port | `pg_isready` |
| `mailpit` | Captures reset email for local operators | `/livez` |
| `migrate` | Applies migrations once | exit status 0 |
| `api` | FastAPI, one Uvicorn worker | `/health/ready` |
| `web` | Next.js standalone server | `GET /` |
| `caddy` | TLS edge, routing, body limit, access log | `caddy validate` |

The API deliberately runs **one worker** because the rate limiter is in-process. Do not add
workers or replicas without moving rate-limit state to a shared store.

## 2. Prerequisites

- Docker Engine 24+ with Compose v2 (Docker Desktop on Windows/macOS).
- 2 CPU cores, 2 GB RAM and 20 GB free disk for a small instance.
- Ports `8443` (HTTPS) and optionally `8025` (Mailpit UI) free on the host.
- `bash`, `curl` and `sha256sum`/`shasum` for the operational scripts (Git Bash on Windows).

## 3. Configure

```bash
cp .env.example .env
npm run setup:env   # optional: generates local development secrets
```

Edit `.env`. The Compose stack reads these values:

| Variable | Purpose | Reference value |
| --- | --- | --- |
| `POSTGRES_DB` | Database name | `auvyren` |
| `POSTGRES_USER` | Database role | `auvyren` |
| `POSTGRES_PASSWORD` | Database password; required | long random value |
| `POSTGRES_PORT` | Loopback host port for `db` | `5433` if `5432` is taken |
| `SECRET_KEY` | Session/CSRF signing key; required, 32+ chars | `secrets.token_urlsafe(48)` |
| `PUBLIC_ORIGIN` | Browser-facing HTTPS origin | `https://localhost:8443` |
| `APP_HTTPS_PORT` | Published Caddy port | `8443` |
| `MAILPIT_UI_PORT` | Loopback Mailpit UI port | `8025` |
| `SESSION_COOKIE_NAME` | Session cookie | `auv_session` |
| `CSRF_COOKIE_NAME` / `CSRF_HEADER_NAME` | CSRF pair | `auv_csrf` / `X-CSRF-Token` |
| `SESSION_TTL_DAYS` / `SESSION_ABSOLUTE_TTL_DAYS` | Sliding / absolute session life | `30` / `90` |
| `EMAIL_FROM` | Reset-mail sender | `no-reply@auvyren.local` |
| `OLLAMA_BASE_URL` | Optional host Ollama endpoint | `http://host.docker.internal:11434` |
| `AI_KEY_ENCRYPTION_KEY` | Reserved for a future cloud AI phase; currently unused | `secrets.token_urlsafe(32)` |
| `BACKUP_RETENTION_DAYS` | Local dump retention | `14` |

Generate secrets:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Notes:

- `DATABASE_URL` in `.env` is for host-side development/tests. Compose overrides it with
  `db:5432` and ignores the host port.
- Keep `POSTGRES_PORT` and the port in the host `DATABASE_URL` identical if you also run
  tests locally.
- `AI_KEY_ENCRYPTION_KEY` is reserved for a future cloud AI phase and is not read by the
  current code. You may set it now to avoid changing secrets later; keep it stable if you do.
- Do not commit `.env`. Do not put any of these values in `NEXT_PUBLIC_*`.

## 4. First deployment

```bash
# Validate configuration without starting anything
npm run stack:config

# Build and start; the migrate job runs before the API
docker compose up -d --build

# Wait for health, then inspect
docker compose ps
```

Expected: `db`, `mailpit`, `api`, `web`, `caddy` are `healthy`; `migrate` exited `0`.
If `migrate` fails, the API will not start (by design).

Verify through the real edge:

```bash
curl -kfsS https://localhost:8443/health/live
curl -kfsS https://localhost:8443/health/ready
curl -kfsS -o /dev/null -w '%{http_code}\n' https://localhost:8443/
```

`-k` is only for the first check because the Caddy local CA is not yet trusted.

### 4.1 Trust the local CA (development/private instance)

```bash
docker compose cp caddy:/data/caddy/pki/authorities/local/root.crt ./caddy-root.crt
```

Windows (current user, no admin required):

```powershell
Import-Certificate -FilePath .\caddy-root.crt -CertStoreLocation Cert:\CurrentUser\Root
```

macOS:

```bash
sudo security add-trusted-cert -d -r trustRoot \
  -k /Library/Keychains/System.keychain caddy-root.crt
```

Debian/Ubuntu:

```bash
sudo cp caddy-root.crt /usr/local/share/ca-certificates/auvyren-caddy.crt
sudo update-ca-certificates
```

Now `curl -fsS https://localhost:8443/health/live` works without `-k`, and browsers stop
warning. `caddy-root.crt` is gitignored. Losing the `caddy_data` volume creates a new CA;
clients must trust the new root.

### 4.2 Public deployment **[public]**

1. Point a DNS record at the host and allow inbound `443` (and `80` for ACME).
2. Replace `https://localhost:8443` with the real origin in `.env` (`PUBLIC_ORIGIN`).
3. Change the Caddy site address from `https://localhost:8443` to the real hostname and
   replace `tls internal` with automatic HTTPS. Publish `443:443` / `80:80`.
4. Rebuild `web` so the inlined `NEXT_PUBLIC_API_BASE_URL` matches the new origin.
5. Replace Mailpit with a real SMTP relay and set `SMTP_*`; do not expose the Mailpit UI.
6. Set `SESSION_COOKIE_SECURE=true` (already forced by Compose) and keep `APP_ENV=production`.
7. Remove or firewall the loopback PostgreSQL port if host tooling does not need it.
8. Put the host behind a firewall and restrict SSH; back up `.env` in a secret manager.

## 5. Update and rollback

### Update

```bash
git pull --ff-only
bash scripts/db-backup.sh          # always take a pre-change backup
docker compose build
docker compose up -d               # migrate runs first
docker compose ps
curl -kfsS https://localhost:8443/health/ready
```

Take a backup before every schema-changing release. Migrations are forward-only in normal
operation; write and test a downgrade before relying on one.

### Rollback

```bash
git checkout <previous-tag-or-commit>
bash scripts/db-backup.sh --restore backups/<pre-change>.dump --yes
docker compose build
docker compose up -d
```

If the previous release did not change the schema, skip the restore and only redeploy the
previous images. If it did, restore the pre-change dump; do not run `alembic downgrade`
against live data without a fresh backup.

### Stop / start

```bash
docker compose stop          # keep containers and volumes
docker compose up -d         # resume
docker compose down          # remove containers; volumes are retained
docker compose down -v       # DESTROYS database, Caddy data and Mailpit state
```

## 6. Logging and monitoring

### Logs

- API: structured JSON on stdout in production (`timestamp`, `level`, `logger`, `message`,
  `request_id`, optional `exception`).
- Caddy: JSON access logs on stdout; response header `Server` is removed.
- Docker: `json-file` driver with 10 MB × 3 rotation per service, so logs do not fill the disk.
- Request correlation: API responses carry `X-Request-ID`; search API logs for that value.

```bash
docker compose logs -f --tail=100 api
docker compose logs -f --tail=100 caddy
docker compose logs --since=30m web
docker compose logs migrate
```

### Health checks

| Probe | Meaning |
| --- | --- |
| `GET /health/live` | API process is alive; no database access |
| `GET /health/ready` | API can query PostgreSQL |
| Compose health | Container-level restart/replacement signal |
| `npm run stack:health` | End-to-end edge, DB readiness, backup freshness, disk |

`stack-health.sh` exits non-zero on failure. Optional alert webhook:

```bash
ALERT_WEBHOOK_URL=https://hooks.example/... npm run stack:health
```

The POST body is Slack-compatible: `{"text": "...", "status": "failing", ...}`. Any endpoint
that accepts JSON works.

Example cron (every 5 minutes; adjust the path and shell):

```cron
*/5 * * * * cd /srv/auvyren && ALERT_WEBHOOK_URL=... ./scripts/stack-health.sh >> /var/log/auvyren-health.log 2>&1
```

### Metrics and alert thresholds

There is no hosted APM in this reference deployment. Use host/Docker metrics and these
thresholds:

| Signal | Warning | Page |
| --- | --- | --- |
| `stack-health.sh` failure | 1 run | 2 consecutive runs |
| API readiness failing | 1 min | 5 min |
| Container restart loop | 3 restarts/10 min | 5 restarts/10 min |
| Disk use | 80% | 90% |
| Backup age | 24 h | 36 h |
| `5xx` rate at Caddy | >1% for 5 min | >5% for 5 min |
| p95 API latency | >500 ms | >2 s |

Wire the thresholds to the webhook or your existing monitor. Recovery notifications need
state in the monitor; the script itself is stateless and only alerts on failure.

### Routine checks

```bash
docker compose ps
docker stats --no-stream
bash scripts/db-backup.sh --list
npm run stack:health
```

## 7. Backup and restore

Backups are PostgreSQL custom-format archives produced by `pg_dump` **inside** the database
container. The script writes a SHA-256 sidecar, restricts permissions, prunes old local
dumps and verifies checksums on restore. The database is the source of truth; uploads are
not part of this application.

### Take a backup

```bash
bash scripts/db-backup.sh
# or: npm run db:backup
```

Output: `backups/auvyren_<UTC timestamp>.dump` plus `.sha256`.

```bash
bash scripts/db-backup.sh --list
BACKUP_RETENTION_DAYS=30 bash scripts/db-backup.sh
```

Schedule daily backups at 02:00 and copy them off-host (restic, rclone, object storage).
A backup on the same disk is not a backup.

```cron
0 2 * * * cd /srv/auvyren && ./scripts/db-backup.sh >> /var/log/auvyren-backup.log 2>&1
```

### Restore

```bash
# 1. Take a safety backup of the current state
bash scripts/db-backup.sh

# 2. Stop writers and replace the database
bash scripts/db-backup.sh --restore backups/auvyren_<timestamp>.dump --yes
```

The script verifies the checksum, copies the archive into the database container, stops
`api`, `web` and `caddy`, drops and recreates the database, runs `pg_restore
--exit-on-error`, starts the stack and waits for `api`/`web`.

After a restore:

```bash
curl -kfsS https://localhost:8443/health/ready
docker compose ps
docker compose logs migrate
```

### Restore drill

A drill is mandatory before go-live and after changing backup tooling. The evidence is in
[`docs/reports/phase-7-backup-restore.md`](reports/phase-7-backup-restore.md): create a
sentinel record through the HTTPS edge, back up, destroy the record, restore, and verify the
record and all health checks. Record the archive name, checksum, timestamps and results.

### What is not in the database dump

- `.env` secrets, especially `SECRET_KEY` and `AI_KEY_ENCRYPTION_KEY`.
- The Caddy internal CA (`caddy_data` volume). Losing it only requires re-trusting the CA.
- Mailpit messages (`MP_MAX_MESSAGES` is ephemeral by design).
- Off-host copies. Configure these separately.

## 8. Troubleshooting

### Docker engine unavailable

Symptom: `failed to connect to the docker API ... dockerDesktopLinuxEngine`.

1. Start Docker Desktop and wait for the whale to stabilize.
2. If it fails to start, fully stop `Docker Desktop`, `com.docker.backend` and
   `com.docker.build`, run `wsl --shutdown`, then start Docker Desktop again.
3. A transient `failed to create temp dir ... input/output error` during image export is a
   Docker Desktop/containerd failure; retry the build. If it repeats, restart Docker Desktop.

### Port already allocated

Change `APP_HTTPS_PORT`, `MAILPIT_UI_PORT` or `POSTGRES_PORT` in `.env`, then
`docker compose up -d`. Keep `PUBLIC_ORIGIN` and the port consistent, and rebuild `web`
because the public API URL is baked into the client bundle.

### `migrate` exits non-zero

```bash
docker compose logs migrate
docker compose run --rm migrate alembic current
docker compose run --rm migrate alembic history
```

Usually a database password mismatch or an unreachable `db`. Confirm `db` is healthy and
`POSTGRES_*` in `.env` matches the URL Compose builds.

### API is unhealthy / 502 from Caddy

```bash
docker compose logs api
curl -kfsS https://localhost:8443/health/live
curl -kfsS https://localhost:8443/health/ready
```

If live works but ready fails, check `db`. If both fail, check the API container logs and
that `migrate` completed.

### Browser certificate warning

Trust `caddy-root.crt` as described in §4.1, or use a public certificate **[public]**.
`curl -k` is only a diagnostic shortcut.

### Password-reset email does not arrive

Mailpit captures mail instead of delivering it. Open `http://127.0.0.1:8025` and check the
message. For real users, configure an SMTP relay **[public]**.

### Rate limiting behaves unexpectedly

The limiter is per-process and in-memory. Keep one API worker. Restarting the API resets
counters. For horizontal scaling, move limits to Redis or the edge first.

### Account menu or page copy is stale after deploy

Rebuild `web`; `NEXT_PUBLIC_API_BASE_URL` is a build-time value. Then hard-refresh the
browser. Session cookies survive a web-only restart.

## 9. Security hardening checklist

- [ ] `.env` is gitignored, owner-readable only, and backed up in a secret manager.
- [ ] `SECRET_KEY` and `POSTGRES_PASSWORD` are unique and random (`AI_KEY_ENCRYPTION_KEY` is
      reserved for future cloud AI and currently unused).
- [ ] `APP_ENV=production`, `DEBUG=false`, `DOCS_ENABLED=false` in Compose.
- [ ] HTTPS only; public deployment uses a trusted certificate, not the internal CA.
- [ ] `SESSION_COOKIE_SECURE=true`; cookies are HttpOnly and `SameSite=Lax`.
- [ ] Mailpit is loopback-only and replaced by SMTP for public users.
- [ ] PostgreSQL is loopback-only or firewalled; never exposed to the internet.
- [ ] Caddy body limit (10 MB), security headers and API CSP are intact.
- [ ] One API worker while the in-process rate limiter is in use.
- [ ] Backups run daily, are copied off-host, and a restore drill has passed.
- [ ] `npm run audit:prod` and `pip-audit` are clean before each release.
- [ ] `npm run stack:health` runs on a timer with a working alert webhook.
- [ ] Docker and base images are updated on a schedule; review release notes first.

## 10. Release checklist

1. `npm run check` green.
2. `npm run build:web` and `npm run perf:ci` within budget.
3. `npm run test:e2e` and `npm run test:e2e:mobile` green.
4. `npm run audit:prod` and `pip-audit` clean.
5. Backup taken and verified.
6. `docker compose build` and `docker compose up -d` succeed.
7. `docker compose ps` healthy; `/health/ready` returns 200; sign-in and one workspace
   journey work through HTTPS.
8. `npm run stack:health` passes.
9. Record the release, image digests and any incidents.
