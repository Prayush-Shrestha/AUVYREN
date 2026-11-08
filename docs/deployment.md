# Auvyren Deployment Guide

This document describes how to deploy Auvyren in production using Docker Compose.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Deployment](#deployment)
4. [Backup and Restore](#backup-and-restore)
5. [Monitoring and Health Checks](#monitoring-and-health-checks)
6. [Troubleshooting](#troubleshooting)
7. [Security Checklist](#security-checklist)

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 2GB RAM
- At least 2 CPU cores
- At least 20GB disk space

## Environment Configuration

Copy `.env.example` to `.env` and configure all required values:

```bash
cp .env.example .env
```

### Required Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_DB` | Database name | `auvyren` |
| `POSTGRES_USER` | Database user | `auvyren` |
| `POSTGRES_PASSWORD` | Database password | `strong-password` |
| `POSTGRES_PORT` | PostgreSQL port | `5432` |
| `SECRET_KEY` | API secret key (min 32 chars) | `secrets.token_urlsafe(48)` |
| `WEB_APP_URL` | Web application URL | `https://auvyren.app` |
| `API_V1_PREFIX` | API version prefix | `/api/v1` |
| `SESSION_COOKIE_NAME` | Session cookie name | `auv_session` |
| `SESSION_COOKIE_SECURE` | Secure cookies in production | `true` |
| `SESSION_TTL_DAYS` | Session sliding TTL (days) | `30` |
| `SESSION_ABSOLUTE_TTL_DAYS` | Session absolute lifetime (days) | `90` |
| `SESSION_REFRESH_MINUTES` | Session refresh interval (minutes) | `5` |
| `CSRF_COOKIE_NAME` | CSRF cookie name | `auv_csrf` |
| `CSRF_HEADER_NAME` | CSRF header name | `X-CSRF-Token` |
| `PASSWORD_RESET_TTL_MINUTES` | Password reset TTL (minutes) | `30` |
| `EMAIL_PROVIDER` | Email provider: `console` or `smtp` | `smtp` |
| `SMTP_HOST` | SMTP host | `smtp.example.com` |
| `SMTP_PORT` | SMTP port | `587` |
| `SMTP_USERNAME` | SMTP username | `user@example.com` |
| `SMTP_PASSWORD` | SMTP password | `password` |
| `SMTP_USE_TLS` | Use TLS for SMTP | `true` |
| `AI_KEY_ENCRYPTION_KEY` | AI key encryption key | `secrets.token_urlsafe(32)` |
| `NEXT_PUBLIC_API_BASE_URL` | Public API URL | `https://api.auvyren.app/api/v1` |
| `API_INTERNAL_URL` | Internal API URL | `http://api:8000/api/v1` |
| `AUV_SESSION_COOKIE_NAME` | Session cookie name | `auv_session` |

### Generating Secrets

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(48))"

# Generate AI_KEY_ENCRYPTION_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Deployment

### 1. Clone and Configure

```bash
git clone https://github.com/auvyren/auvyren.git
cd auvyren
cp .env.example .env
# Edit .env with your production values
```

### 2. Start Services

```bash
# Start PostgreSQL only (for migrations)
docker compose up -d db

# Wait for PostgreSQL to be ready
docker compose logs -f db  # Wait until "database system is ready to accept connections"

# Run database migrations
npm run migrate

# Start all services
docker compose up -d
```

### 3. Verify Deployment

```bash
# Check API health
curl http://localhost:8000/

# Check web health
curl http://localhost:3000/

# Check API readiness
curl http://localhost:8000/health/ready
```

## Backup and Restore

### Backup

```bash
# Backup the database
./scripts/db-backup.sh

# Backup to a specific location
./scripts/db-backup.sh /backups/auvyren_20240101.sql.gz
```

### Restore

```bash
# Restore from backup
./scripts/db-backup.sh --restore /backups/auvyren_20240101.sql.gz
```

**Warning:** Restoring will drop and recreate the database. All existing data will be lost.

### Automated Backups (Cron)

Add to crontab for daily backups:

```bash
# Daily backup at 2 AM
0 2 * * * /path/to/auvyren/scripts/db-backup.sh /backups/auvyren_$(date +\%Y\%m\%d).sql.gz
```

## Monitoring and Health Checks

### API Health Check

```bash
curl http://localhost:8000/
```

Expected response:
```json
{
  "name": "Auvyren API",
  "version": "0.1.0",
  "status": "ok",
  "documentation": "/docs"
}
```

### Web Health Check

```bash
curl http://localhost:3000/
```

Should return HTML content.

### Database Readiness

```bash
curl http://localhost:8000/health/ready
```

Should return `{"database":"ok"}`.

## Troubleshooting

### API won't start

1. Check logs: `docker compose logs api`
2. Verify DATABASE_URL is correct
3. Verify SECRET_KEY is set
4. Check database connectivity

### Web won't start

1. Check logs: `docker compose logs web`
2. Verify NEXT_PUBLIC_API_BASE_URL is correct
3. Verify API is running and accessible

### Database connection issues

1. Check PostgreSQL is running: `docker compose logs db`
2. Verify POSTGRES_PASSWORD matches in .env
3. Check port mapping: `POSTGRES_PORT:5432`

### Sessions not working

1. Verify SESSION_COOKIE_NAME matches between API and web
2. Verify SESSION_COOKIE_SECURE is true in production (HTTPS)
3. Verify WEB_APP_URL matches your domain

## Security Checklist

- [ ] `.env` is not committed to version control
- `SECRET_KEY` is strong and unique (32+ characters)
- `SESSION_COOKIE_SECURE=true` in production
- `SESSION_COOKIE_DOMAIN` is set for production domains
- `EMAIL_PROVIDER=smtp` in production
- `SMTP_HOST` is configured in production
- `WEB_APP_URL` uses HTTPS in production
- `AI_KEY_ENCRYPTION_KEY` is set and strong
- All `.env` values are unique and not placeholders
- Database backups are scheduled and tested
- Firewall restricts database port (5432) to internal only
