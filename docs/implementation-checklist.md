# Implementation Checklist

**Legend:** ✅ complete · ◐ partial (foundation only) · ☐ not started

## Phase 0 — Product Foundation & Architecture

### Repository and tooling

- [x] Inspect the repository before modifying (workspace was empty; greenfield)
- [x] Establish monorepo structure: `apps/web`, `apps/api`, `docs`, `scripts`
- [x] Pin runtime expectations (Node 22+, Python 3.12+)
- [x] Root package scripts for dev, checks, migrations and database lifecycle
- [x] Cross-platform API runner and environment generator
- [x] `.gitignore`, `.editorconfig`, `.env.example`
- [x] PostgreSQL via Docker Compose with healthcheck and persistent volume

### Frontend foundation

- [x] Next.js 16 App Router + TypeScript + Tailwind CSS v4 scaffold
- [x] Dark foundation tokens matching the product palette
- [x] Root layout, metadata and Phase 0 technical status page
- [x] Typed API client with RFC 9457 problem-details handling
- [x] Public environment access isolated in `lib/env.ts`
- [x] Responsive foundation layout
- [x] ESLint, TypeScript and production build green

### Backend foundation

- [x] FastAPI application factory and versioned `/api/v1` router
- [x] Pydantic settings with production safety validation
- [x] Async SQLAlchemy engine/session using asyncpg
- [x] Logging with request-ID correlation; JSON in production
- [x] Request ID middleware with input validation
- [x] RFC 9457 error responses and safe 500 handling
- [x] CORS allowlist, trusted hosts and security headers
- [x] `/health/live`, `/health/ready`, `/api/v1/meta`
- [x] Ruff lint/format and 14 tests

### Database and architecture

- [x] PostgreSQL naming/timestamp/UUID conventions
- [x] Identity tables: users, user_settings, sessions, password_reset_tokens
- [x] Productivity tables: projects, tasks, goals, milestones, habits, habit_logs, routines,
      routine_steps, calendar_events
- [x] Lowercase constrained string enums and validation checks
- [x] User-scoped indexes and cascade/set-null deletion rules
- [x] Alembic async environment and initial migration
- [x] `updated_at` trigger for all mutable tables
- [x] Migration upgrade/downgrade/upgrade and drift check
- [x] Schema integration tests against real PostgreSQL
- [x] Architecture, database, API, security and AI documentation
- [x] Roadmap, this checklist, and Phase 0 completion report

### Phase 0 exit gate

- [x] PostgreSQL healthy and migration applied
- [x] API live/readiness checked over real HTTP
- [x] Backend tests pass
- [x] Frontend lint/typecheck/build pass
- [x] No secrets committed
- [ ] **Explicit user approval to begin Phase 1**

## Phase 1 — Brand Identity & UI Foundation

### Design system

- [ ] Final typography selection and scale
- [ ] Spacing, radius, elevation and border tokens
- [ ] Motion principles and reduced-motion variants
- [ ] Primitive components: buttons, inputs, textareas, selects, checkboxes, dialogs, menus,
      tabs, toasts, tooltips, badges
- [ ] State components: skeleton/loading, empty, error, success, inline validation
- [ ] Component catalogue/preview route (development only or documented examples)
- [ ] Focus, hover, active and disabled states across all primitives
- [ ] Keyboard navigation and screen-reader labels

### Routes and shells

- [ ] Premium landing page
- [ ] Sign-in screen
- [ ] Sign-up screen
- [ ] Forgot-password screen
- [ ] Responsive dashboard shell
- [ ] Responsive settings shell
- [ ] Desktop, tablet and mobile navigation
- [ ] 404 and error surfaces

### Quality

- [ ] Contrast and focus review
- [ ] Mobile/tablet/desktop visual review
- [ ] Lint, typecheck and production build
- [ ] Documentation of the design system
- [ ] Completion report and approval gate

## Phase 2 — Authentication & Core Application

### Backend

- [ ] Argon2id password hashing
- [ ] Registration with normalized email and validation
- [ ] Login/logout and session rotation
- [ ] Opaque sessions stored hashed; secure cookie settings
- [ ] CSRF token generation and enforcement
- [ ] Forgot/reset password with single-use hashed tokens
- [ ] Rate limiting for auth endpoints
- [ ] Profile and settings endpoints
- [ ] Session listing and revocation
- [ ] Account-enumeration-safe responses
- [ ] Auth, ownership, CSRF and session-expiry tests

### Frontend

- [ ] Wire sign-in/sign-up/forgot/reset screens
- [ ] Session-aware navigation
- [ ] Protected dashboard/settings routes
- [ ] Profile and account settings UI
- [ ] Loading, success, field-error and auth-error states
- [ ] Logout and session-expired handling
- [ ] No hardcoded credentials or tokens in storage

### Phase 2 exit gate

- [ ] Real PostgreSQL-backed auth verified end to end
- [ ] Cross-user access tests pass
- [ ] Documentation updated
- [ ] Completion report and approval gate

## Phase 3 — Personal Productivity System

### Dashboard

- [ ] Today's priorities from real tasks
- [ ] Upcoming tasks
- [ ] Active goals with computed progress
- [ ] Habit progress
- [ ] Daily overview
- [ ] Deterministic productivity insights
- [ ] Responsive loading/empty/error states

### Tasks

- [ ] Create, edit, delete
- [ ] Priorities and deadlines
- [ ] Categories
- [ ] Complete/reopen
- [ ] Filter, sort and search
- [ ] Project association
- [ ] Authorization and validation tests

### Goals and milestones

- [ ] Create/edit/archive goals
- [ ] Measurable outcome and target date
- [ ] Milestone CRUD and ordering
- [ ] Computed progress fallback
- [ ] Completed milestone history
- [ ] Ownership tests

### Projects

- [ ] CRUD and description
- [ ] Status and dates
- [ ] Task association
- [ ] Deadline monitoring
- [ ] Soft-delete behavior

### Habits and routines

- [ ] Daily/weekly habits
- [ ] Log completion/undo
- [ ] Streak computation
- [ ] Weekly consistency
- [ ] Routine and step CRUD
- [ ] Timezone-aware day boundaries

### Calendar

- [ ] Month, week and day views
- [ ] Task deadlines
- [ ] Goal milestones
- [ ] Events CRUD
- [ ] Upcoming agenda
- [ ] Range query performance check

### Phase 3 exit gate

- [ ] No module relies on mock data
- [ ] Every resource enforces ownership
- [ ] API and UI tests pass
- [ ] Responsive review
- [ ] Documentation updated
- [ ] Completion report and approval gate

## Phase 4 — Auvyren Intelligence Engine

- [ ] Deterministic prioritization with explanation
- [ ] Deadline awareness
- [ ] Goal progress calculations
- [ ] Habit consistency analysis
- [ ] Daily planning and workload analysis
- [ ] Pattern detection with minimum sample rules
- [ ] Provider abstraction: deterministic/local/cloud interface
- [ ] Ollama configuration, connection test and model discovery
- [ ] Local daily summary and workspace Q&A
- [ ] Deterministic fallback on provider failure
- [ ] Provenance metadata and UI indicators
- [ ] No cloud transmission or cloud keys
- [ ] Engine/provider tests
- [ ] Documentation and completion report

## Phase 5 — Personal Intelligence & Knowledge Workspace

- [ ] Notes CRUD with Markdown-safe rendering
- [ ] Knowledge library and search
- [ ] Daily journal
- [ ] Decision records
- [ ] Weekly and monthly reviews
- [ ] Links to goals, projects, tasks and notes
- [ ] Neglected-goal detection
- [ ] Deadline/habit/overload surfacing
- [ ] AI-assisted summaries with provenance
- [ ] Generated vs user-authored distinction throughout
- [ ] Tests and completion report

## Phase 6 — Privacy, Synchronization & Cloud AI

- [ ] User-controlled AI permissions
- [ ] Encrypted cloud provider keys
- [ ] Local/cloud processing indicators
- [ ] Cloud provider adapter with server-side calls
- [ ] Consent before context transmission
- [ ] Usage limits and cost tracking
- [ ] Local-only and hybrid modes
- [ ] Data export
- [ ] Account deletion with re-authentication
- [ ] Sync support and conflict handling
- [ ] Sync status and offline-friendly workflows
- [ ] Audit/security events
- [ ] Privacy and permission tests
- [ ] Documentation and completion report

## Phase 7 — Testing, Optimization & Deployment

- [ ] Frontend component tests
- [ ] Backend API tests
- [ ] Authentication and permission tests
- [ ] Database tests
- [ ] AI provider tests (mocked/isolated)
- [ ] Responsive UI tests
- [ ] End-to-end workflows
- [ ] Performance budgets and page optimization
- [ ] Query/index review
- [ ] Accessibility audit
- [ ] Security review and CSP
- [ ] Dependency audit
- [ ] Next.js deployment
- [ ] FastAPI deployment
- [ ] Managed PostgreSQL, backups and restore drill
- [ ] Production logging, monitoring and alerts
- [ ] Deployment documentation
- [ ] Completion report and approval gate

## Phase 8 — Mobile Application (blocked until Phase 7 approval)

- [ ] Flutter project scaffold
- [ ] Secure authentication/session storage
- [ ] Daily dashboard
- [ ] Tasks, goals, habits, notes
- [ ] AI daily briefing with same consent/provenance
- [ ] Push notifications
- [ ] Data synchronization and conflict handling
- [ ] Android/iOS testing and release docs

## Global requirements (checked every phase)

- [x] No mock data in production backend paths (none introduced)
- [x] Secrets only server-side
- [x] Responsive foundation established
- [x] Loading/empty/error state plan documented for future modules
- [x] Existing functionality preserved
- [ ] Every phase documented and tested before approval
