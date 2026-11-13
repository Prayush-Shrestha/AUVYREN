# Phase 7 — Performance and Query Review

**Date:** 13 November 2026  
**Scope:** production web build, key navigations, and the ten most important database
access paths on a representative data volume.

## 1. Method

- Build: `npm run build:web` (Next.js 16 standalone output).
- Static budget: gzip every file emitted under `apps/web/.next/static`; enforced by
  `npm run perf:ci`.
- Browser budget: start the standalone server, load each route cold at 1280×900, wait for
  fonts and network idle, then read LCP/CLS and decoded JS/CSS from the Performance API.
- Database: PostgreSQL 17 in the Compose container, 10,000 notes and 5,000 tasks for one
  synthetic user, `ANALYZE` run before `EXPLAIN (ANALYZE, BUFFERS)`. Seed data was deleted
  after the review; the database returned to its normal empty state.
- Timings are single-run observations on the development machine, not a load test.

## 2. Web budgets

| Metric | Result | Budget | Status |
| --- | ---: | ---: | --- |
| Static JavaScript (gzip) | 287.7 KB | 340 KB | Pass |
| Static CSS (gzip) | 12.6 KB | 40 KB | Pass |
| Decoded JS, `/` | 606 KB | 750 KB | Pass |
| Decoded CSS, `/` | 74 KB | 120 KB | Pass |
| LCP, `/` | 2,052 ms | 2,500 ms | Pass |
| CLS, `/` | 0.001 | 0.1 | Pass |
| LCP, `/sign-in` | 756 ms | 2,500 ms | Pass |
| LCP, `/design` | 1,348 ms | 2,500 ms | Pass |

The JS/CSS budgets apply to every measured route; `/` is the heaviest because it includes
the marketing composition and self-hosted fonts. Full per-route output is printed by:

```bash
npm run build:web
npm run perf:web
```

Budgets live in `scripts/web-budget.mjs` and are intentionally generous enough for shared CI
runners while still catching a second UI framework, an unoptimised image or an extra font
family. CI runs the static portion (`npm run perf:ci`) on every push.

## 3. Query and index review

The review focused on list, search and intelligence queries that run on every workspace load.

| Path | Plan | Execution | Assessment |
| --- | --- | ---: | --- |
| Notes list (`user_id`, `deleted_at IS NULL`, newest first, limit 50) | Index scan backward on `ix_notes_user_created` | 0.285 ms | Good; no sort, 5 buffers |
| Knowledge search (`ILIKE` on title/content/tags) | `BitmapOr` over `ix_notes_title_trgm`, `ix_notes_content_trgm`, `ix_notes_tags_trgm` | 20.6 ms | Acceptable for 10k rows; trigram GIN does the filtering |
| Task list (`user_id`, status filter, due date order, limit 50) | Index scan on `ix_tasks_user_due_at` | 0.205 ms | Good |
| Intelligence sweep (open tasks, limit 50) | Sequential scan + limit | 0.083 ms | Acceptable: the planner stops after 50 matching rows; an index would add little at this size |
| Note links by source | Unique index `uq_note_links_edge` | index lookup | Good; also enforces idempotent links |

Supporting changes:

- `pg_trgm` extension plus GIN indexes on `notes.title`, `notes.content` and `notes.tags`
  (migration `c9d0e1f2a3b4`).
- Unique constraint on note-link edges and a check preventing self-links.
- Existing user-scoped indexes cover notes, tasks, habits, goals, projects and sessions.

The search plan uses three bitmap index scans and a heap recheck. At larger volumes, monitor
the `BitmapOr` cost and consider a generated `search_vector` with a GIN index if search
becomes a p95 bottleneck. No change is justified by the current measurements.

## 4. Application-level work

- Next.js standalone output is used in both CI and the container; no dev server in
  production.
- Fonts are self-hosted through Fontsource; there are no third-party font or analytics
  requests on first paint.
- Server components fetch workspace data server-side through the internal API, avoiding a
  browser round trip before the first meaningful render.
- Caddy compresses responses (`zstd`, `gzip`), enforces a 10 MB request body limit and removes
  the `Server` header.
- Images are not part of the current product surface; when they are added, use
  `next/image` with explicit dimensions to protect CLS.

## 5. Limitations

- No load test or multi-user concurrency test was run. The API is deployed with one worker
  because rate limiting is in-process.
- Browser metrics use a local standalone server and a warm development machine. They are
  regression signals, not field data.
- Query timings used a single user's data and a warm cache. Re-run `EXPLAIN` against
  production-sized data before making further index decisions.
- The `/design` catalogue is internal and noindex; its metrics still matter because it shares
  the component bundle.

## 6. Reproduce

```bash
npm run build:web
npm run perf:ci
npm run perf:web
```

For the database review, apply migrations, seed a representative user, run `ANALYZE`, then
`EXPLAIN (ANALYZE, BUFFERS)` the queries above. Delete synthetic rows afterward.
