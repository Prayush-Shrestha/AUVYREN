# Auvyren Web

Next.js 16 App Router frontend for Auvyren.

- `src/app/` — routes, layouts, metadata (server components by default)
- `src/app/design/` — internal, noindex design-system catalogue
- `src/components/ui/` — design-system primitives
- `src/components/layout/` — marketing, auth and app shells
- `src/features/` — feature composition (auth previews in Phase 1)
- `src/lib/api/` — typed API client and problem-details types
- `src/lib/env.ts` — browser-safe environment access
- `src/lib/cn.ts` — class merging configured for the custom type scale
- `src/app/globals.css` — Tailwind v4 import, Phase 1 tokens and base styles

The visual identity and component system are implemented in Phase 1. Auth screens validate
locally but are visual previews only; accounts and sessions arrive in Phase 2. Workspace
screens show honest empty states, never sample data.

The full contract is documented in [`docs/design-system.md`](../../docs/design-system.md).

## Development

From the repository root:

```bash
npm run dev:web
```

Open `/` for the landing page, `/design` for the catalogue, and `/dashboard` or `/settings`
for the workspace shells. See the root [README](../../README.md) for full setup.
