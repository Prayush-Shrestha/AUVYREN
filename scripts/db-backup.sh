#!/usr/bin/env bash
"""
Backup script for Auvyren PostgreSQL database.

Usage:
  ./scripts/db-backup.sh              # Backup to default location
  ./scripts/db-backup.sh /path/to/backup.sql.gz  # Backup to specific file
  ./scripts/db-backup.sh --restore /path/to/backup.sql.gz  # Restore from backup

Environment variables:
  POSTGRES_HOST, POSTGRES_PORT, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
  (defaults match docker-compose defaults)
"""

set -euo pipefail

# Configuration
PG_HOST="${POSTGRES_HOST:-localhost}"
PG_PORT="${POSTGRES_PORT:-5432}"
PG_USER="${POSTGRES_USER:-auvyren}"
PG_PASSWORD="${POSTGRES_PASSWORD:-auvyren}"
PG_DB="${POSTGRES_DB:-auvyren}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*" >&2
}

# Export PGPASSWORD for non-interactive psql
export PGPASSWORD="${PG_PASSWORD}"

# Create backup directory if it doesn't exist
mkdir -p "${BACKUP_DIR}"

# Generate backup filename with timestamp
BACKUP_FILE="${BACKUP_DIR}/auvyren_$(date +%Y%m%d_%H%M%S).sql.gz"

usage() {
    echo "Usage: $0 [backup_file.sql.gz]"
    echo "       $0 --restore backup_file.sql.gz"
    echo ""
    echo "Environment variables:"
    echo "  POSTGRES_HOST      Database host (default: localhost)"
    echo "  POSTGRES_PORT      Database port (default: 5432)"
    echo "  POSTGRES_USER      Database user (default: auvyren)"
    echo "  POSTGRES_PASSWORD  Database password (default: auvyren)"
    echo "  POSTGRES_DB        Database name (default: auvyren)"
    echo "  BACKUP_DIR         Backup directory (default: ./backups)"
}

# Create a database backup
backup() {
    local target_file="${1:-${BACKUP_FILE}}"

    log_info "Starting database backup to ${target_file}..."

    # Check if database is reachable
    if ! pg_isready -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d "${PG_DB}" > /dev/null 2>&1; then
        log_error "Cannot connect to PostgreSQL at ${PG_HOST}:${PG_PORT}"
        exit 1
    fi

    # Create backup
    pg_dump \
        --host="${PG_HOST}" \
        --port="${PG_PORT}" \
        --username="${PG_USER}" \
        --dbname="${PG_DB}" \
        --no-password \
        --no-password \
        --verbose \
        --verbose \
        --no-password \
        --format=custom \
        --compress=9 \
        --file="${target_file}" \
        2>&1

    if [ $? -ne 0 ]; then
        log_error "Backup failed"
        exit 1
    fi

    # Get file size
    local size
    size=$(du -h "${target_file}" | cut -f1)

    log_info "Backup completed successfully: ${target_file} (${size})"
}

# Restore from backup
restore() {
    local backup_file="$1"

    if [[ ! -f "${backup_file}" ]]; then
        log_error "Backup file not found: ${backup_file}"
        exit 1
    fi

    log_warn "WARNING: This will DROP and RECREATE the database ${PG_DB}"
    log_warn "All existing data will be lost."
    read -p "Are you sure you want to continue? (y/N): " -r
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        log_info "Restore cancelled"
        exit 0
    fi

    log_info "Starting restore from ${backup_file}..."

    # Drop and recreate database
    PGPASSWORD="${PG_PASSWORD}" psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d postgres -c "DROP DATABASE IF EXISTS ${PG_DB};" 2>/dev/null || true
    PGPASSWORD="${PG_PASSWORD}" psql -h "${PG_HOST}" -p "${PG_PORT}" -U "${PG_USER}" -d postgres -c "CREATE DATABASE ${PG_DB};" 2>/dev/null || true

    # Restore from backup
    PGPASSWORD="${PG_PASSWORD}" pg_restore \
        --host="${PG_HOST}" \
        --port="${PG_PORT}" \
        --username="${PG_USER}" \
        --dbname="${PG_DB}" \
        --no-password \
        --no-owner \
        --verbose \
        "${backup_file}" \
        2>&1

    if [ $? -ne 0 ]; then
        log_error "Restore failed"
        exit 1
    fi

    log_info "Restore completed successfully"
}

# Main logic
case "${1:-}" in
    ""|--help|-h)
        usage
        exit 0
        ;;
    --restore)
        if [[ -z "${2:-}" ]]; then
            log_error "Please specify a backup file to restore from"
            usage
            exit 1
        fi
        restore "${2}"
        ;;
    *)
        backup "${1}"
        ;;
esac
