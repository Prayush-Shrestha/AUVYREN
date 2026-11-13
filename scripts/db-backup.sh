#!/usr/bin/env bash
#
# Auvyren PostgreSQL backup and restore.
#
# Dumps are custom-format archives produced by pg_dump inside the Compose
# database container. Binary data never crosses a shell pipeline, so the script
# behaves the same on Linux, macOS and Git Bash.
#
# Usage:
#   ./scripts/db-backup.sh                 # timestamped backup + checksum
#   ./scripts/db-backup.sh --list          # list known backups
#   ./scripts/db-backup.sh --restore FILE  # restore (asks for confirmation)
#   ./scripts/db-backup.sh --restore FILE --yes
#
# Environment:
#   BACKUP_DIR        destination directory (default: <repo>/backups)
#   BACKUP_RETENTION_DAYS  delete local dumps older than this (default: 14)
#   COMPOSE_CMD       override, e.g. "docker compose"
#   POSTGRES_DB, POSTGRES_USER  must match docker-compose.yml

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
RETENTION_DAYS="${BACKUP_RETENTION_DAYS:-14}"
DB_SERVICE="${DB_SERVICE:-db}"
CONTAINER_DUMP="/tmp/auvyren-backup.dump"
CONTAINER_RESTORE="/tmp/auvyren-restore.dump"

read -r -a COMPOSE <<< "$COMPOSE_CMD"

log() { printf '[backup] %s\n' "$*"; }
fail() { printf '[backup] ERROR: %s\n' "$*" >&2; exit 1; }

# Read the database identity from the running container so the script always
# matches what Compose actually configured, instead of guessing defaults.
container_env() {
  "${COMPOSE[@]}" exec -T "$DB_SERVICE" printenv "$1" | tr -d '\r'
}

require_stack() {
  "${COMPOSE[@]}" ps --status running --services | grep -qx "$DB_SERVICE" \
    || fail "database service '$DB_SERVICE' is not running. Start it with: $COMPOSE_CMD up -d db"
}

checksum() {
  if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "$1"
  elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1"
  else
    fail "sha256sum or shasum is required to verify backups"
  fi
}

usage() {
  sed -n '2,20p' "${BASH_SOURCE[0]}" | sed 's/^# \{0,1\}//'
  exit 0
}

list_backups() {
  mkdir -p "$BACKUP_DIR"
  if ! compgen -G "$BACKUP_DIR/auvyren_*.dump" >/dev/null; then
    log "no backups in $BACKUP_DIR"
    return 0
  fi
  local file
  for file in "$BACKUP_DIR"/auvyren_*.dump; do
    printf '%s  %8s\n' "$(basename "$file")" "$(du -h "$file" | cut -f1)"
  done
}

backup() {
  require_stack

  local pg_user pg_db stamp target sidecar
  pg_user="$(container_env POSTGRES_USER)"
  pg_db="$(container_env POSTGRES_DB)"
  stamp="$(date -u +%Y%m%dT%H%M%SZ)"
  mkdir -p "$BACKUP_DIR"
  target="$BACKUP_DIR/auvyren_${stamp}.dump"
  sidecar="$target.sha256"

  log "dumping database '$pg_db' as '$pg_user'"
  "${COMPOSE[@]}" exec -T "$DB_SERVICE" \
    pg_dump -U "$pg_user" -d "$pg_db" \
    --format=custom --compress=9 --no-owner --no-acl \
    --file="$CONTAINER_DUMP"

  "${COMPOSE[@]}" cp "$DB_SERVICE:$CONTAINER_DUMP" "$target"
  "${COMPOSE[@]}" exec -T "$DB_SERVICE" rm -f "$CONTAINER_DUMP"

  [ -s "$target" ] || fail "pg_dump produced an empty archive"

  checksum "$target" > "$sidecar"
  chmod 600 "$target" "$sidecar" 2>/dev/null || true

  log "wrote $target ($(du -h "$target" | cut -f1))"
  log "sha256 $(cut -d' ' -f1 "$sidecar")"

  prune
}

prune() {
  [ "$RETENTION_DAYS" -ge 1 ] 2>/dev/null || return 0
  local removed
  removed="$(find "$BACKUP_DIR" -maxdepth 1 -type f \
    \( -name 'auvyren_*.dump' -o -name 'auvyren_*.dump.sha256' \) \
    -mtime +"$RETENTION_DAYS" -print -delete | wc -l | tr -d ' ')"
  if [ "$removed" -gt 0 ]; then
    log "pruned $removed file(s) older than $RETENTION_DAYS day(s)"
  fi
}

restore() {
  local archive="$1" confirm="${2:-}"
  [ -f "$archive" ] || fail "backup not found: $archive"
  [ -s "$archive" ] || fail "backup is empty: $archive"
  require_stack

  if [ -f "$archive.sha256" ]; then
    log "verifying checksum"
    local expected actual
    expected="$(cut -d' ' -f1 "$archive.sha256")"
    actual="$(checksum "$archive" | cut -d' ' -f1)"
    [ "$expected" = "$actual" ] || fail "checksum mismatch for $archive"
  else
    log "WARNING: no .sha256 sidecar; skipping integrity check"
  fi

  local pg_user pg_db
  pg_user="$(container_env POSTGRES_USER)"
  pg_db="$(container_env POSTGRES_DB)"

  if [ "$confirm" != "--yes" ]; then
    printf '[backup] This replaces database "%s" with %s.\n' "$pg_db" "$archive"
    printf '[backup] The API, web and proxy containers will be stopped.\n'
    printf 'Continue? (y/N): '
    local reply
    read -r reply
    [[ "$reply" =~ ^[Yy]$ ]] || { log "restore cancelled"; exit 0; }
  fi

  log "copying archive into the database container"
  "${COMPOSE[@]}" cp "$archive" "$DB_SERVICE:$CONTAINER_RESTORE"

  log "stopping API, web and proxy"
  "${COMPOSE[@]}" stop api web caddy >/dev/null

  trap '"${COMPOSE[@]}" exec -T "$DB_SERVICE" rm -f "$CONTAINER_RESTORE" >/dev/null 2>&1 || true' EXIT

  log "recreating database '$pg_db'"
  "${COMPOSE[@]}" exec -T "$DB_SERVICE" dropdb -U "$pg_user" --if-exists --force "$pg_db"
  "${COMPOSE[@]}" exec -T "$DB_SERVICE" createdb -U "$pg_user" "$pg_db"

  log "restoring archive"
  "${COMPOSE[@]}" exec -T "$DB_SERVICE" \
    pg_restore -U "$pg_user" -d "$pg_db" \
    --no-owner --no-acl --exit-on-error "$CONTAINER_RESTORE"

  log "restore complete; starting the stack"
  "${COMPOSE[@]}" up -d

  log "waiting for readiness"
  local attempt
  for attempt in $(seq 1 30); do
    if "${COMPOSE[@]}" ps --status running --services | grep -qx api \
      && "${COMPOSE[@]}" ps --status running --services | grep -qx web; then
      log "api and web are running"
      break
    fi
    sleep 2
  done
}

case "${1:-}" in
  ""|--backup)
    backup
    ;;
  --restore)
    [ -n "${2:-}" ] || fail "specify an archive with --restore FILE"
    shift
    archive="$1"
    shift || true
    restore "$archive" "${1:-}"
    ;;
  --list)
    list_backups
    ;;
  --help|-h)
    usage
    ;;
  *)
    fail "unknown argument '$1' (try --help)"
    ;;
esac
