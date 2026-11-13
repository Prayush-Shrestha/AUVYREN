# Incident Notes

Post-incident notes from Phase 7 verification. These are engineering records, not customer
communications. Each entry lists impact, cause, fix and the guardrail that prevents a repeat.

## INC-001 — API containers crash with `IndexError` on startup

**Detected:** during the first Compose deployment, in `docker compose logs migrate` and
`docker compose logs api`.

**Impact:** Migrations and the API could not start; the web container waited forever on a
healthy API. Local development was unaffected.

**Cause:** `apps/api/app/core/config.py` located the repository root with
`Path(__file__).resolve().parents[4]`. That is correct for `D:\AUVYREN\apps\api\app\core`,
but inside the image the file lives at `/app/app/core/config.py` and has only three parent
directories. Indexing `parents[4]` raised `IndexError: 4`, which surfaced during Alembic
configuration import.

**Fix:** discover the nearest ancestor that contains `.env.example`, falling back to
`Path.cwd()`. This works in the repository, the image and the migration container without
hardcoded depth.

**Guardrail:** the Compose smoke test is now part of the release checklist, and `migrate`
must exit `0` before the API starts. Reading application-relative paths through a helper is
preferred over index arithmetic.

## INC-002 — Server-rendered workspace pages lost the session

**Detected:** during Playwright and manual verification of `/notes`, `/notes/[id]`,
`/knowledge` search and `/intelligence`; the pages redirected or showed an
authentication error even with a valid browser session.

**Impact:** authenticated server components could not read or mutate workspace data. The
browser client worked because it sent cookies automatically; only server-side API calls were
affected.

**Cause:** `serverApiRequest` in `apps/web/src/lib/api/server.ts` forwarded neither the
incoming session/CSRF cookies nor a trusted `Origin`/`Referer`. The API correctly rejected
the anonymous request, and unsafe methods additionally returned `origin_required`.

**Fix:** forward the `Cookie` header and trusted origin metadata from the incoming Next.js
request for server-side calls. CSRF tokens remain server-side; no token was moved into
browser storage. Unsafe server actions still require the CSRF header and a trusted origin.

**Guardrail:** end-to-end journeys now cover server-rendered notes, note detail, knowledge
search and the intelligence briefing, not only client-side calls.

## INC-003 — Web image build could not resolve the workspace package

**Detected:** during `docker compose build web`, after the API image already built.

**Impact:** no web image; the stack could not start. This was a build-only failure.

**Cause:** the dependency stage ran `npm ci` for the root workspace and then the builder
copied only selected paths. The nested workspace dependency layout (including
`apps/web/node_modules`) was not preserved, so `next` was missing at build time.

**Fix:** copy `/app/apps` from the dependency stage into the builder, keeping the workspace
layout and hoisted/nested modules intact, before copying the application source. The
standalone output is then assembled from `.next/standalone` and `.next/static`.

**Guardrail:** CI builds and starts the production standalone server for the e2e job; a
broken image build cannot pass. Docker build changes must be verified with a clean cache
(`docker compose build --no-cache web`) before release.

## INC-004 — Production API image missing `httpx`

**Detected:** during the first successful `docker compose up -d`; `api` restarted with
`ModuleNotFoundError: No module named 'httpx'`.

**Impact:** the API container could not import `app.main`, so readiness never passed and
Caddy/web could not come up behind it. Tests and local development were unaffected because
the editable dev environment installs `.[dev]`, which included `httpx`.

**Cause:** `app/intelligence/providers.py` imports `httpx` at module load for the optional
Ollama client, but `httpx` was declared only in the `dev` extra. The production wheel
correctly excluded it.

**Fix:** move `httpx>=0.28,<1` into `[project].dependencies`. The dev extra no longer lists it
because installing the project already brings it in.

**Guardrail:** image builds are smoke-tested by starting the real container, not only by
running tests in the dev environment. Any module imported at application startup must be a
runtime dependency. CI's API job could additionally import `app.main` inside the built image
before deploying.

## INC-005 — Image layers contained zero-byte files

**Detected:** the first web container start after rebuilding the stack failed with
`ERR_INVALID_PACKAGE_CONFIG /app/apps/web/package.json`; inspection showed
`package.json` and `server.js` were 0 bytes. An earlier API image also had a 0-byte
`/etc/passwd`, which caused `unable to find user auvyren`.

**Impact:** the affected container could not start. Other layers in the same image were
intact, so the failure was per-file, not a whole-image build error.

**Cause:** Docker Desktop's containerd store was unstable while the host disk was nearly full
(`input/output error` writing `meta.db` during export). Some layer files were materialized as
empty files even though the build reported success. This is an environment fault, not an
application defect.

**Fix:** free disk space, restart the Docker engine (`wsl --shutdown` plus a Docker Desktop
restart), and rebuild the affected image with `--no-cache`. Verify critical files inside the
new image before starting the stack:

```bash
docker run --rm --user 0 --entrypoint sh auvyren-api:latest -c "wc -c /etc/passwd; getent passwd auvyren"
docker run --rm --entrypoint sh auvyren-web:latest -c "wc -c /app/apps/web/server.js /app/apps/web/package.json"
```

**Guardrail:** a build is not "done" until the produced image is started and a health probe
passes. Treat zero-byte configuration files as an engine/storage symptom and rebuild clean
after freeing space.

## Operational note — Docker Desktop engine instability

During verification, Docker Desktop occasionally stopped its Linux engine or failed while
exporting image layers (`failed to create temp dir ... input/output error`). This was a local
desktop environment fault, not an application failure. The recovery used in this repository
is documented in the deployment runbook: fully stop the Docker Desktop/backend processes,
run `wsl --shutdown`, start Docker Desktop and retry. Repeated layer-export failures indicate
a containerd/VM problem; retry after a restart before changing application code.

The host `C:` drive had roughly 1 GB free during the worst of this; Docker Desktop keeps its
15 GB virtual disk there. Low free space is the likely trigger for the `meta.db` write
failures. Operators should keep several GB free on the Docker data drive.
