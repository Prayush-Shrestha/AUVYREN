# Phase 7 — Backup and Restore Drill Report

**Date:** 15 November 2026  
**Stack:** Docker Compose production mode (PostgreSQL 17, FastAPI, Next.js standalone, Caddy)  
**Result:** Drill passed — sentinel record survived backup, deletion, and restore.

## 1. Drill Procedure

The drill followed the procedure in [`docs/deployment.md` §7](deployment.md):

1. Create a sentinel account and note through the public HTTPS edge (`https://localhost:8443`).
2. Take a checksummed backup with `scripts/db-backup.sh` (equivalent manual steps run from PowerShell since WSL bash lacks the Docker CLI).
3. Delete the sentinel account from PostgreSQL via `psql`.
4. Restore the database from the backup archive (`pg_restore --exit-on-error`).
5. Restart the stack and verify the sentinel record and all health checks.

## 2. Sentinel Creation (through HTTPS edge)

| Step | Request | Result |
| --- | --- | --- |
| CSRF bootstrap | `GET /api/v1/auth/csrf` with `Origin: https://localhost:8443` | 200, CSRF token returned |
| Registration | `POST /api/v1/auth/register` with CSRF header + cookies | 201 Created |
| Note creation | `POST /api/v1/knowledge` with CSRF header + cookies | 200, note created |

**Sentinel account:**

| Field | Value |
| --- | --- |
| User ID | `de4abb1b-dc95-49f1-9b65-54e0c4902494` |
| Email | `sentinel-20261115171359@e2e.auvyren.app` |
| Full name | Sentinel User |
| Note ID | `7f6843ab-22e0-45cc-8764-0aba764dff83` |
| Note title | Sentinel note |
| Note content | This is a sentinel restoration test note. |
| Note tags | sentinel,restore |

## 3. Backup

**Archive:** `backups/auvyren_20261115T171622Z.dump`  
**Checksum sidecar:** `backups/auvyren_20261115T171622Z.dump.sha256`  
**SHA-256:** `c7d55712273fc5912b72bf89932efb2b729a50226e2dec3a1241da35eed39b97`  
**Format:** PostgreSQL custom-format (`pg_dump --format=custom --compress=9`)  
**Taken:** 2026-11-15T17:16:22Z  
**Permissions:** 600 (owner read/write only)

The dump was produced by `pg_dump` inside the database container; binary data never crossed a shell pipeline.

## 4. Destructive Step

The sentinel account was deleted from PostgreSQL:

```sql
DELETE FROM users WHERE email LIKE 'sentinel%';
-- DELETE 1
```

Verification: `SELECT count(*) FROM users WHERE email LIKE 'sentinel%'` returned `0`.

## 5. Restore

The restore followed `scripts/db-backup.sh --restore` logic (executed manually from PowerShell because WSL bash does not expose the Docker CLI):

1. Stopped `api`, `web`, `caddy` (`docker compose stop api web caddy`).
2. Copied the archive into the database container (`docker compose cp ... db:/tmp/auvyren-restore.dump`).
3. Dropped and recreated the `auvyren` database (`dropdb --if-exists --force`, `createdb`).
4. Restored with `pg_restore -U auvyren -d auvyren --no-owner --no-acl --exit-on-error`.
5. Removed the temporary archive from the container.
6. Restarted the stack (`docker compose up -d`).

**Checksum verification:** The `.sha256` sidecar was checked before restore (match confirmed; the script's checksum step would fail on mismatch).

## 6. Post-Restore Verification

| Check | Result |
| --- | --- |
| `GET /health/live` through HTTPS | 200 `{"status":"ok",...}` |
| `GET /health/ready` through HTTPS | 200 `{"status":"ok","database":"ok"}` |
| `GET /` through HTTPS | 200 |
| Sentinel user in DB | 1 row, same ID `de4abb1b-dc95-49f1-9b65-54e0c4902494` |
| Sentinel note in DB | 1 row, same ID `7f6843ab-22e0-45cc-8764-0aba764dff83`, same content |
| `migrate` exit status | 0 |
| All Compose services healthy | `db`, `mailpit`, `api`, `web`, `caddy` |

The sentinel account and note were restored with identical IDs, timestamps, and content — confirming the backup is complete and restorable.

## 7. Checksum Sidecar Contents

```
c7d55712273fc5912b72bf89932efb2b729a50226e2dec3a1241da35eed39b97  auvyren_20261115T171622Z.dump
```

## 8. Notes

- The restore drill was executed against the local Compose stack with a real PostgreSQL 17 database.
- `.env` secrets (`SECRET_KEY`, `POSTGRES_PASSWORD`, `AI_KEY_ENCRYPTION_KEY`) are not part of the database dump and must be backed up separately.
- The Caddy internal CA (`caddy_data` volume) and Mailpit messages are not part of the database dump.
- `backups/` is gitignored; archives should be copied off-host after creation.
