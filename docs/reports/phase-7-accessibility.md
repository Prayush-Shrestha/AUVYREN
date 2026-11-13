# Phase 7 — Accessibility Audit

**Date:** 13 November 2026  
**Standard:** WCAG 2.0/2.1 A and AA, including WCAG 2.2 AA rules exposed by axe-core.  
**Result:** No critical or serious violations in the audited states. Automated checks are
green; the manual limitations are listed in §5.

## 1. Method

- Engine: `@axe-core/playwright` with tags `wcag2a`, `wcag2aa`, `wcag21a`, `wcag21aa`,
  `wcag22aa`.
- Motion: scans run with `reducedMotion: "reduce"` so reveal animations cannot hide content
  mid-scan; reduced motion itself is verified separately.
- Browser: Chromium desktop at 1280×900; responsive journeys also run at Pixel 7 (412×915).
- Each scan waits for fonts before analysis. Violations, impact, target and failure summary
  are printed on failure.

## 2. Audited states

| Surface | States covered |
| --- | --- |
| Landing | `/` full page, header, hero, footer |
| Authentication | `/sign-in`, `/sign-up` |
| Design catalogue | `/design` (all primitive examples) |
| Dashboard | authenticated welcome and empty state |
| Intelligence | briefing, empty and local/cloud indicators |
| Notes | list and editor entry points |
| Knowledge | search and results |
| Settings | profile, preferences, sessions, privacy controls |

The workspace test opens each page with a real account created through the API and asserts
that `#main-content` is present before scanning. This catches route-level regressions, not
only the public marketing page.

## 3. Results

| Check | Result |
| --- | --- |
| axe WCAG A/AA violations | **0** across 9 page states |
| Critical/serious violations | **0** |
| Skip link is first keyboard stop and focuses `#main-content` | Pass |
| Reduced motion removes transitions/animations > 50 ms | Pass |
| Mobile horizontal overflow at 412 px | Pass on landing, sign-in, dashboard, knowledge |
| Keyboard-opened mobile navigation, Escape close | Pass |
| Focus visibility on interactive primitives | Reviewed — visible focus ring retained |
| Colour contrast | Reviewed in Phase 1; no regressions introduced in Phase 7 |

Automated coverage is 6 Playwright accessibility tests (landing, auth pair, design,
workspace pages, skip link, reduced motion). They run in every desktop e2e job.

## 4. Fixes made in Phase 7

- **Account menu accessible name:** the trigger's visible label and accessible name now
  agree, removing the `label-content-name-mismatch` failure.
- **Settings loading state:** the loading surface exposes `role="status"` so assistive
  technology announces it instead of silently replacing content.
- **Smooth-scroll declaration:** moved to the document's `data-scroll-behavior` attribute to
  satisfy the framework's hydration and accessibility guidance while preserving reduced
  motion behaviour.
- **Reveal animations:** all content remains present and readable when animations are
  disabled; reduced-motion mode is tested, not assumed.

## 5. Manual limitations

This is an automated audit plus targeted keyboard/responsive checks, not a full assistive
technology certification.

- No screen-reader pass (NVDA, VoiceOver or TalkBack) was performed.
- No 200% zoom / 400% reflow check beyond the 412 px mobile viewport.
- No formal WCAG 2.2 AAA review; AAA is out of scope.
- Contrast was reviewed during the design-system phase; Phase 7 checked for regressions but
  did not re-measure every token pair.
- The design catalogue is internal and noindex, but it is included because it exercises all
  primitives.

No critical accessibility issue remains in the audited surfaces. A screen-reader pass is the
recommended next step before marketing the product to a broad public audience.

## 6. Reproduce

```bash
cd apps/web
npx playwright test e2e/accessibility.spec.ts --project=chromium
npx playwright test e2e/responsive.spec.ts --project=mobile
```

The desktop suite also runs the security boundary tests, so CSP and cookie assertions are
verified alongside accessibility in the same browser environment.
