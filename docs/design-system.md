# Auvyren Design System — Phase 1

**Status:** Implemented and verified. This is the visual and interaction contract for every
later phase. Extend it deliberately; do not fork it per screen.

**Live catalogue:** `/design` (internal, `noindex`, linked from the landing footer and app
shell). Every component and state below is rendered there with real interactions.

---

## 1. Principles

1. **Quiet over loud.** One accent, warm paper text, generous negative space. Hierarchy comes
   from scale, serif contrast and hairlines — not gradients, glows or stacked cards.
2. **Editorial, not decorative.** Display type is a voice; UI type is a tool. Italic serif is
   reserved for emphasis inside a statement, never for controls.
3. **Honest surfaces.** Empty, loading, error and preview states tell the truth. No sample
   metrics, invented users or fake success.
4. **Motion is optional.** Content is visible by default. Animation may decorate an already
   readable page; it must never gate legibility or depend on JavaScript.
5. **Accessible by construction.** Contrast, focus, keyboard paths and reduced motion are part
   of the token and component contract, not a later audit.
6. **One system, many phases.** New modules compose these primitives. A one-off control is a
   design-system change, reviewed once.

---

## 2. Identity

| Element | Specification |
| --- | --- |
| Wordmark | `AUVYREN` — Manrope, uppercase, `0.24em` tracking, semibold |
| Mark | Circular horizon: a quiet sun over a line, moss accent dot |
| Display face | Newsreader Variable, weight 300–350, tight tracking |
| UI face | Manrope Variable, weight 400–700 |
| Voice | Short declaratives, second person, no exclamation marks, no productivity clichés |
| Tagline | “Think clearly. Move intentionally.” |
| Metadata tone | Lowercase phase labels, uppercase micro-labels, explicit “Preview” wording |

The favicon and in-app mark share the same geometry (`src/components/ui/logo.tsx`,
`src/app/icon.svg`).

---

## 3. Colour

A single dark theme. `color-scheme: dark` is declared; a light theme is not part of Phase 1.
All values live in the `@theme` block of `src/app/globals.css`.

### 3.1 Surfaces and ink

| Token | Hex | Use |
| --- | --- | --- |
| `canvas` | `#0a0d0b` | Outermost page, browser chrome |
| `background` | `#0c100d` | Page background under texture |
| `background-secondary` | `#101511` | Input wells, quiet bands |
| `surface` | `#141a15` | Cards, panels |
| `surface-elevated` | `#19211a` | Raised cards, menus, dialogs |
| `surface-hover` | `#1e271f` | Hover fill |
| `border` | `#283129` | Default divider |
| `border-strong` | `#39453a` | Secondary button, structural edge |
| `border-control` | `#5e6c5d` | Input boundary (3:1 non-text minimum) |
| `foreground` | `#f2f0e6` | Primary text (warm paper) |
| `foreground-soft` | `#d8d7cc` | Secondary text |
| `muted` | `#9ca498` | Supporting copy |
| `faint` | `#858f83` | Metadata, placeholders, disabled-adjacent |
| `accent` | `#b7e8c8` | Primary action, focus ring, live emphasis |
| `accent-strong` | `#cdf3da` | Primary hover |
| `accent-ink` | `#0b1710` | Text on accent |
| `sand` | `#d9c3a0` | Warm counterpoint, editorial labels |
| `danger` | `#f2a9a2` | Errors, destructive text |
| `danger-soft` | `#3a211f` | Destructive fill |
| `success` | `#a6dcb4` | Confirmation |
| `success-soft` | `#1b2d20` | Confirmation fill |
| `warning` | `#e6cd95` | Caution |
| `warning-soft` | `#2f2818` | Caution fill |
| `info` | `#a9c8e8` | Neutral notice |
| `info-soft` | `#1b2633` | Notice fill |

Texture: two very low-opacity radial washes (moss top-left, sand top-right) plus an SVG noise
layer at `0.16` opacity. Never add a third decorative gradient.

### 3.2 Contrast audit

Measured values, also shown in `/design`:

| Pair | Ratio | Requirement |
| --- | --- | --- |
| Paper on background | 16.78:1 | AA/AAA text |
| Paper soft on background | 13.25:1 | AA/AAA text |
| Muted on background | 7.46:1 | AA/AAA text |
| Faint on background | 5.71:1 | AA text |
| Faint on elevated | 4.91:1 | AA text (lowest normal-text pair) |
| Accent on background | 14.05:1 | AA/AAA text |
| Accent ink on accent | 13.45:1 | AA/AAA text |
| Sand on background | 11.19:1 | AA/AAA text |
| Danger on background | 10.02:1 | AA/AAA text |
| Control border on ink | 3.45:1 | 3:1 non-text |
| Focus ring on ink | 14.05:1 | 3:1 non-text |

Rules:

- Body copy uses `foreground`, `foreground-soft` or `muted`. `faint` is allowed for metadata
  and placeholders, never for essential instructions.
- Do not place `muted` or `faint` on `surface-hover`; verify any new pairing.
- Disabled controls are exempt from contrast minimums but must remain legible; the system uses
  45–60% opacity, never near-invisible.
- Colour is never the only carrier of meaning: errors include an icon and text, success
  includes an icon and text, badges include a label.

---

## 4. Typography

Self-hosted via `@fontsource-variable/newsreader` and `@fontsource-variable/manrope` — no
runtime font CDN, no layout shift from a third-party request.

### 4.1 Families

- **Display / editorial:** Newsreader Variable (`--font-serif`), weights 300–350 for display,
  italic 300 for emphasis (`.serif-italic`).
- **UI / body:** Manrope Variable (`--font-sans`), 400–700.
- **Code / numerals:** system monospace via Tailwind `font-mono`; used for hex values, ratios
  and numeric metadata.

### 4.2 Scale

| Token | Size | Line height | Tracking | Notes |
| --- | --- | --- | --- | --- |
| `display-2xl` | `clamp(3.75rem, 9vw, 8.5rem)` | 0.90 | -0.05em | Hero statements only |
| `display-xl` | `clamp(3.25rem, 7vw, 6.5rem)` | 0.94 | -0.045em | Page-level statement |
| `display-lg` | `clamp(2.75rem, 5.2vw, 4.75rem)` | 0.98 | -0.04em | Section lead |
| `display-md` | `clamp(2.25rem, 4vw, 3.5rem)` | 1.02 | -0.035em | Section heading |
| `display-sm` | `clamp(1.75rem, 3vw, 2.5rem)` | 1.08 | -0.025em | Card group heading |
| `title-lg` | 1.5rem | 1.25 | -0.02em | Panel title |
| `title-md` | 1.125rem | 1.35 | -0.01em | Subsection |
| `body-lg` | 1.0625rem | 1.70 | — | Intro copy |
| `body` | 0.9375rem | 1.65 | — | Default body |
| `small` | 0.8125rem | 1.55 | — | Labels, dense copy |
| `micro` | 0.6875rem | 1.45 | 0.14em | Uppercase eyebrows |

Rules:

- One `h1` per page. Display sizes use `text-wrap: balance`; paragraphs use `pretty`.
- Never set display type below 1.75rem; use `title-*` for compact headings.
- Uppercase is limited to micro labels, badges and short metadata. Never uppercase a sentence.
- Maximum measure: ~68 characters for body copy, ~20 for display statements.

---

## 5. Layout, shape and depth

| Concern | Contract |
| --- | --- |
| Page container | `.container-page`: max 1200px, 20px / 32px / 40px inline padding |
| App frame | 256px fixed sidebar at ≥1024px; content max 1180px |
| Grid | 12-column mental model; cards use 1 / 2 / 3 columns at 390 / 820 / 1440 |
| Spacing | Tailwind 4px base; common rhythm 8 / 12 / 16 / 24 / 32 / 48 / 64 |
| Radii | `xs` 6px, `sm` 10px, `md` 14px, `lg` 20px, `xl` 28px, `2xl` 36px; controls 12px, buttons and badges pill |
| Borders | 1px; structural edges use `border`; interactive boundaries use `border-control` |
| Shadows | `soft` for cards, `panel` for overlays, `glow` sparingly behind hero art |
| Target size | 44px minimum for primary touch actions; 36px compact desktop only |

No nested cards beyond one level. No full-page glassmorphism. Backdrop blur is limited to
sticky navigation and overlays.

---

## 6. Motion

| Token | Value | Use |
| --- | --- | --- |
| `ease-out-expo` | `cubic-bezier(0.16, 1, 0.3, 1)` | Entrances, reveals |
| `ease-in-out-soft` | `cubic-bezier(0.65, 0, 0.35, 1)` | Ambient loops |
| `fade-up` / `fade-in` | 700ms / 500ms | Content entrance |
| `overlay-in` / `overlay-out` | 200ms / 150ms | Dialog scrim |
| `panel-in` / `panel-out` | 220ms / 150ms | Dialog panel |
| `toast-in` / `toast-out` | 260ms / 160ms | Toast |
| `drift` / `orbit` / `pulse-soft` | 26s / 54s / 5s | Decorative hero only |

Rules:

- The global reduced-motion media query collapses animation and transition durations to
  `0.01ms` and disables smooth scrolling.
- The `Reveal` component is visible by default and only hides below-fold content after
  hydration when motion is allowed. It never leaves content at `opacity: 0` for reduced-motion
  users or without JavaScript. Framer Motion is available for future complex choreography but
  is not required by any Phase 1 surface.
- Motion communicates state (open/close, enter/exit) or direction. It never blocks input, loops
  in the reading path, or exceeds ~700ms.
- Loading indication is a spinner plus text; the button keeps full opacity and sets
  `aria-busy`.

---

## 7. Components

All primitives live in `apps/web/src/components/ui/`. Class merging goes through
`src/lib/cn.ts`, which registers the full custom `--text-*` scale with `tailwind-merge` so
type tokens are never mistaken for colours.

### 7.1 Actions

| Component | API | States |
| --- | --- | --- |
| `Button` | `variant: primary \| secondary \| ghost \| danger`, `size: sm \| md \| lg \| icon`, `loading`, native button props | hover, active, focus-visible, disabled, loading (`disabled` + `aria-busy`) |
| `ButtonLink` | same variants/sizes, Next `Link` props | hover, focus-visible |
| `IconButton` | `variant: primary \| secondary \| ghost \| danger`, `size: sm \| md \| lg`, `label` (required accessible name), icon child | as `Button` |

Rules: one primary action per region; destructive actions use `danger` and explicit verbs;
`loading` is for in-flight actions only, never decoration.

### 7.2 Forms

| Component | API | Notes |
| --- | --- | --- |
| `Field` | `label`, `htmlFor`, `hint`, `error`, `success`, `optional` | Renders label, message, `role="alert"` error and `role="status"` success |
| `fieldMessageId` | `(id, state)` | Produces deterministic `id-error` / `id-success` / `id-hint` |
| `Input`, `Textarea`, `Select` | native props, forwarded refs | 44px control height, custom select chevron |
| `Checkbox` | native input + label content | Radix-independent; 20px box, visible focus ring |

Validation contract: set `aria-invalid` and `aria-describedby` to the matching message id; show
the message only after submit or blur; never clear a user's value; announce errors with
`role="alert"`. Forms that do not persist data must say so in visible copy and still validate
fully.

### 7.3 Content and status

| Component | API | Notes |
| --- | --- | --- |
| `Badge` | `tone: neutral \| accent \| sand \| success \| warning \| danger \| info \| outline`, `size: sm \| md`, `dot` | Uppercase micro label; optional leading dot |
| `Card` + `CardHeader` / `CardBody` / `CardFooter` | compositional | Surface, border, radius `lg`, optional hover |
| `InlineMessage` | `tone: info \| success \| warning \| danger`, `title`, `action` | Stacks action below text on mobile; `role="alert"` for danger/warning |
| `EmptyState` | icon, title, description, action | Honest “nothing here yet” language |
| `ErrorState` | title, description, `onRetry` | Retry must perform a real action |
| `SuccessState` | title, description, action | Confirmation, not celebration |
| `Skeleton` | `className` | `animate-shimmer`, `aria-hidden`; pair with explicit loading text |
| `Spinner` | `className` | Decorative; expose status via surrounding text |

### 7.4 Overlays

| Component | API | Accessibility |
| --- | --- | --- |
| `Dialog` family | Root, Trigger, Close, Content, Header, Title, Description, Footer | Focus trap, Escape, focus return, labelled title |
| `DropdownMenu` family | Root, Trigger, Content, Item, Separator, Label | Arrow keys, typeahead, Escape, focus return |
| `Tabs` family | Root, List, Trigger, Content | Arrow keys, Home/End, one tab stop, labelled panels |
| `Tooltip` family | Provider, Root, Trigger, Content | Hover and focus, Escape dismiss, never sole information source |
| `Toast` | `ToastProvider`, `useToast().toast({ title, description, tone, duration })` | `role="status"` region, pause on hover/focus, dismiss button, 5s default |

Overlays use Radix primitives underneath. Portal content inherits the dark theme; no white
flash or mismatched scrim.

### 7.5 Shells and identity

- `AppShell` — fixed desktop sidebar, mobile dialog navigation, active-state aware links,
  skip link, phase labels, honest foundation notice.
- `AuthShell` — split preview layout: brand-side statement on desktop, form column with
  explicit “Phase 1 preview” notice.
- `SiteHeader` / `SiteFooter` — marketing navigation, mobile dialog menu, catalogue link.
- `AuvyrenLogo` / `AuvyrenMark` / `AuvyrenWordmark` — shared identity.
- `Constellation` — decorative hero SVG, `aria-hidden`, reduced-motion aware.

---

## 8. Accessibility contract

- **Skip link:** first tab stop on every route; targets `main#main-content` with `tabIndex={-1}`
  so focus actually moves.
- **Focus ring:** global `:focus-visible` — 2px accent outline, 3px offset, 14.05:1 contrast.
  Mouse focus does not draw the ring.
- **Keyboard:** every interactive surface is reachable and operable; dialog/menu/tabs follow
  Radix semantics; Escape closes and focus returns to the trigger.
- **Semantics:** one `h1`, one `main`, landmark header/nav/main/footer, labelled icon buttons,
  `aria-current` on active navigation, `aria-busy` on loading actions.
- **Announcements:** field errors `role="alert"`, inline success `role="status"`, toast region
  polite, warning/danger inline messages assertive.
- **Reduced motion:** content never hidden; animation durations collapsed.
- **Zoom/reflow:** no horizontal page overflow at 320–1440px; wide tables scroll inside a
  labelled, focusable `role="region"`.
- **Audit:** axe-core WCAG 2.0/2.1 A/AA — 17 states across 1440px and 390px, plus an open
  dialog, zero violations at Phase 1 exit.

---

## 9. Responsive contract

| Width | Navigation | Layout | Notes |
| --- | --- | --- | --- |
| 320–639px | Dialog menu; 44px targets | Single column | Auth brands-side hidden; inline actions stack |
| 640–1023px | Dialog menu until 1024px | Two-column cards where useful | Settings tabs become full-width |
| ≥1024px | 256px fixed sidebar / desktop header | 2–3 columns, 1180px content frame | Sticky headers, hover states |

Tested at 390, 820 and 1440 CSS pixels. The shell collapses below 1024px; auth screens collapse
their brand panel below 1024px. Tables are the only intentional horizontal scrollers, and each
is keyboard-focusable with an accessible name.

---

## 10. Content rules

- Say what is true: “No account connected”, “Changes are saved in Phase 2”, “No email was
  sent”.
- Phase labels are lowercase metadata (`Phase 2`, `Phase 3`), never disguised as working
  features.
- Buttons use verbs (`Create account`, `Send reset link`, `Try again`), not “Submit”.
- Errors explain the fix and preserve dignity: “Enter a valid email address.”
- No fake counts, streaks, percentages, people or activity. Empty means empty.
- Auth screens are explicitly marked as visual previews and never claim a session or account.

---

## 11. Catalogue and file map

| Path | Purpose |
| --- | --- |
| `src/app/globals.css` | Tokens, base styles, focus, reduced motion, utilities |
| `src/lib/cn.ts` | `clsx` + configured `tailwind-merge` |
| `src/components/ui/` | Primitives listed above |
| `src/components/layout/` | Marketing, auth and app shells |
| `src/components/marketing/` | Reveal and hero constellation |
| `src/features/auth/` | Preview forms, validation, notice |
| `src/app/design/page.tsx` | Internal catalogue, contrast and review log |

The catalogue is `noindex`, excluded from marketing navigation, and reachable from the landing
footer and app sidebar. It is the review surface for any design-system change.

---

## 12. Change protocol

1. Change a token or primitive once, in the design system — never patch a screen locally.
2. Update `/design` and this document in the same change.
3. Re-run contrast, keyboard and axe checks.
4. Capture 390 / 820 / 1440 screenshots for affected surfaces.
5. Keep the reduced-motion path visible-by-default.
6. Do not introduce a second accent, a second display face or a light theme without an
   explicit product decision.
