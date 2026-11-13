#!/usr/bin/env bash
#
# Auvyren production stack health check and alert hook.
#
# Verifies that the Compose services are running, the HTTPS edge serves the web
# application, the API can reach PostgreSQL, a recent database backup exists and
# the host still has disk headroom. Intended for cron/systemd timers. When a
# check fails and ALERT_WEBHOOK_URL is set, a JSON message is POSTed to the
# webhook (Slack-compatible; any endpoint that accepts JSON works).
#
# Usage:
#   ./scripts/stack-health.sh
#   ALERT_WEBHOOK_URL=https://hooks.example/... ./scripts/stack-health.sh
#
# Environment:
#   COMPOSE_CMD             override, e.g. "docker compose"
#   APP_HTTPS_PORT          published HTTPS port (auto-detected from Compose)
#   BACKUP_DIR              backup directory (default: <repo>/backups)
#   REQUIRE_FRESH_BACKUP    1 to fail when no backup is younger than the limit
#   BACKUP_MAX_AGE_HOURS    freshness limit (default: 36)
#   DISK_MAX_USED_PCT       fail when root filesystem use reaches this (default: 90)
#   ALERT_WEBHOOK_URL       optional JSON webhook for failures

set -uo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

COMPOSE_CMD="${COMPOSE_CMD:-docker compose}"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
REQUIRE_FRESH_BACKUP="${REQUIRE_FRESH_BACKUP:-1}"
BACKUP_MAX_AGE_HOURS="${BACKUP_MAX_AGE_HOURS:-36}"
DISK_MAX_USED_PCT="${DISK_MAX_USED_PCT:-90}"
REQUIRED_SERVICES=(db api web caddy)

read -r -a COMPOSE <<< "$COMPOSE_CMD"

failures=0
messages=()

pass() { printf '[ok]   %s\n' "$*"; }
warn() { printf '[warn] %s\n' "$*"; }
fail() {
  failures=$((failures + 1))
  messages+=("$*")
  printf '[FAIL] %s\n' "$*" >&2
}

port="$("${COMPOSE[@]}" port caddy 8443 2>/dev/null | awk -F: 'NF { print $NF; exit }')"
HTTPS_PORT="${APP_HTTPS_PORT:-${port:-8443}}"
ORIGIN="https://localhost:${HTTPS_PORT}"

running="$("${COMPOSE[@]}" ps --status running --services 2>&1)"
if [ $? -ne 0 ]; then
  fail "docker compose unavailable: ${running//$'\n'/ }"
else
  for service in "${REQUIRED_SERVICES[@]}"; do
    if grep -qx "$service" <<< "$running"; then
      pass "service $service is running"
    else
      fail "service $service is not running"
    fi
  done
fi

http_check() {
  local label="$1" url="$2" code
  code="$(curl -k -sS -o /dev/null -w '%{http_code}' --max-time 10 "$url" 2>/dev/null)" || code="000"
  if [ "$code" = "200" ]; then
    pass "$label (HTTP $code)"
  else
    fail "$label returned HTTP $code ($url)"
  fi
}

if ! command -v curl >/dev/null 2>&1; then
  fail "curl is required for HTTP health checks"
else
  http_check "API liveness" "$ORIGIN/health/live"
  http_check "API readiness" "$ORIGIN/health/ready"
  http_check "web application" "$ORIGIN/"
fi

if [ "$REQUIRE_FRESH_BACKUP" = "1" ]; then
  recent="$(find "$BACKUP_DIR" -maxdepth 1 -type f -name 'auvyren_*.dump' \
    -mmin -"$((BACKUP_MAX_AGE_HOURS * 60))" -print -quit 2>/dev/null)"
  if [ -n "$recent" ]; then
    pass "recent backup: $(basename "$recent")"
  else
    fail "no backup newer than ${BACKUP_MAX_AGE_HOURS}h in $BACKUP_DIR"
  fi
fi

used_pct="$(df -Pk "$ROOT_DIR" 2>/dev/null | awk 'NR == 2 { gsub(/%/, "", $5); print $5 }')"
if [ -n "$used_pct" ] && [ "$used_pct" -ge "$DISK_MAX_USED_PCT" ] 2>/dev/null; then
  fail "disk usage ${used_pct}% has reached ${DISK_MAX_USED_PCT}%"
else
  pass "disk usage ${used_pct:-unknown}% (limit ${DISK_MAX_USED_PCT}%)"
fi

if [ "$failures" -gt 0 ]; then
  summary="Auvyren health check failed: ${messages[*]}"
  printf '[health] %s\n' "$summary" >&2

  if [ -n "${ALERT_WEBHOOK_URL:-}" ]; then
    safe_summary="$(printf '%s' "$summary" | tr -d '"' | tr '\n' ' ')"
    payload="$(printf '{"text":"%s","status":"failing","source":"auvyren-stack-health","host":"%s"}' \
      "$safe_summary" "$(hostname 2>/dev/null || echo unknown)")"
    if curl -fsS --max-time 10 -H 'Content-Type: application/json' \
      -d "$payload" "$ALERT_WEBHOOK_URL" >/dev/null 2>&1; then
      printf '[health] alert webhook delivered\n' >&2
    else
      warn "alert webhook could not be delivered"
    fi
  fi

  exit 1
fi

printf '[health] all checks passed\n'
