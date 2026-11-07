import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Bookmark,
  CheckCircle2,
  CircleAlert,
  Inbox,
  Info,
  Layers,
  Mail,
  Orbit,
  Pencil,
  Plus,
  Search,
  Sparkles,
  Trash2,
  Type,
  Waves,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button, ButtonLink, IconButton } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import { Field, Input, Select, Textarea, fieldMessageId } from "@/components/ui/field";
import { AuvyrenLogo, AuvyrenMark, AuvyrenWordmark } from "@/components/ui/logo";
import {
  EmptyState,
  InlineMessage,
  Skeleton,
  Spinner,
  SuccessState,
} from "@/components/ui/states";
import {
  BadgeActionsDemo,
  DialogDemo,
  DropdownDemo,
  ErrorStateDemo,
  FormDemo,
  TabsDemo,
  ToastDemo,
  TooltipDemo,
} from "@/features/design-system/interactive-showcase";
import { cn } from "@/lib/cn";

export const metadata: Metadata = {
  title: "Design system",
  description: "The internal token, component and accessibility catalogue for Auvyren.",
  robots: { index: false, follow: false },
};

const nav = [
  { label: "Identity", href: "#identity" },
  { label: "Type", href: "#typography" },
  { label: "Colour", href: "#colour" },
  { label: "Shape", href: "#shape" },
  { label: "Components", href: "#actions" },
  { label: "Accessibility", href: "#accessibility" },
];

const colours = [
  { name: "Canvas", token: "canvas", hex: "#0a0d0b", note: "Page surround" },
  { name: "Background", token: "background", hex: "#0c100d", note: "Primary ink" },
  { name: "Secondary", token: "background-secondary", hex: "#101511", note: "Recessed areas" },
  { name: "Surface", token: "surface", hex: "#141a15", note: "Cards and panels" },
  { name: "Elevated", token: "surface-elevated", hex: "#19211a", note: "Menus and dialogs" },
  { name: "Hover", token: "surface-hover", hex: "#1e271f", note: "Raised state" },
  { name: "Border", token: "border", hex: "#283129", note: "Quiet division" },
  { name: "Border strong", token: "border-strong", hex: "#39453a", note: "Emphasised edge" },
  {
    name: "Border control",
    token: "border-control",
    hex: "#5e6c5d",
    note: "3:1 input boundary",
  },
  { name: "Paper", token: "foreground", hex: "#f2f0e6", note: "Primary text" },
  { name: "Paper soft", token: "foreground-soft", hex: "#d8d7cc", note: "Secondary text" },
  { name: "Muted", token: "muted", hex: "#9ca498", note: "Supporting text" },
  { name: "Faint", token: "faint", hex: "#858f83", note: "Metadata text" },
  { name: "Accent", token: "accent", hex: "#b7e8c8", note: "Living signal" },
  { name: "Accent ink", token: "accent-ink", hex: "#0b1710", note: "Text on accent" },
  { name: "Sand", token: "sand", hex: "#d9c3a0", note: "Warm counterpoint" },
  { name: "Danger", token: "danger", hex: "#f2a9a2", note: "Failure text" },
  { name: "Success", token: "success", hex: "#a6dcb4", note: "Confirmation" },
  { name: "Warning", token: "warning", hex: "#e6cd95", note: "Caution" },
  { name: "Info", token: "info", hex: "#a9c8e8", note: "Explanation" },
];

const contrastPairs = [
  { pair: "Paper on background", ratio: "16.78:1", size: "All text", tone: "success" as const },
  { pair: "Paper soft on background", ratio: "13.25:1", size: "All text", tone: "success" as const },
  { pair: "Muted on background", ratio: "7.46:1", size: "All text", tone: "success" as const },
  { pair: "Faint on background", ratio: "5.71:1", size: "All text", tone: "success" as const },
  { pair: "Faint on elevated", ratio: "4.91:1", size: "All text", tone: "success" as const },
  { pair: "Accent on background", ratio: "14.05:1", size: "All text", tone: "success" as const },
  { pair: "Accent ink on accent", ratio: "13.45:1", size: "All text", tone: "success" as const },
  { pair: "Sand on background", ratio: "11.19:1", size: "All text", tone: "success" as const },
  { pair: "Danger on background", ratio: "10.02:1", size: "All text", tone: "success" as const },
  { pair: "Control border on ink", ratio: "3.45:1", size: "Non-text", tone: "success" as const },
  { pair: "Focus ring on ink", ratio: "14.05:1", size: "Non-text", tone: "success" as const },
];

const displayScale = [
  { token: "display-xl", className: "text-display-xl", sample: "Make room." },
  { token: "display-lg", className: "text-display-lg", sample: "A quieter default." },
  { token: "display-md", className: "text-display-md", sample: "Soft systems, sharp thinking." },
  { token: "display-sm", className: "text-display-sm", sample: "Return to your space." },
];

const bodyScale = [
  { token: "title-lg", className: "text-title-lg", sample: "Section title", note: "24 / 1.25 · Sans semibold" },
  { token: "title-md", className: "text-title-md", sample: "Card title", note: "18 / 1.35 · Sans semibold" },
  {
    token: "body-lg",
    className: "text-body-lg",
    sample: "Lead paragraphs open the page and carry the argument.",
    note: "17 / 1.7 · Sans regular",
  },
  {
    token: "body",
    className: "text-body",
    sample: "Body copy stays comfortable across long sessions and narrow screens.",
    note: "15 / 1.65 · Sans regular",
  },
  {
    token: "small",
    className: "text-small",
    sample: "Small supports labels, metadata and dense interface copy.",
    note: "13 / 1.55 · Sans regular",
  },
  {
    token: "micro",
    className: "text-micro uppercase",
    sample: "Micro · Eyebrow",
    note: "11 / 1.45 · 0.14em · Uppercase",
  },
];

const radii = [
  { token: "xs", className: "rounded-xs", size: "6px" },
  { token: "sm", className: "rounded-sm", size: "10px" },
  { token: "md", className: "rounded-md", size: "14px" },
  { token: "lg", className: "rounded-lg", size: "20px" },
  { token: "xl", className: "rounded-xl", size: "28px" },
  { token: "2xl", className: "rounded-2xl", size: "36px" },
];

function SectionIntro({
  id,
  index,
  title,
  description,
}: {
  id: string;
  index: string;
  title: string;
  description: string;
}) {
  return (
    <div className="grid gap-5 lg:grid-cols-[0.82fr_1.18fr] lg:items-end">
      <div>
        <p className="eyebrow">{index}</p>
        <h2 id={`${id}-heading`} className="mt-4 font-serif text-display-sm font-light">
          {title}
        </h2>
      </div>
      <p className="max-w-2xl text-body leading-relaxed text-muted lg:justify-self-end">
        {description}
      </p>
    </div>
  );
}

function Specimen({
  title,
  note,
  children,
  className,
  contentClassName,
}: {
  title: string;
  note?: string;
  children: React.ReactNode;
  className?: string;
  contentClassName?: string;
}) {
  return (
    <Card className={cn("overflow-hidden", className)}>
      <div className="flex flex-wrap items-baseline justify-between gap-2 border-b border-border/70 px-5 py-3.5">
        <h3 className="text-small font-semibold text-foreground-soft">{title}</h3>
        {note ? <p className="text-[11px] text-faint">{note}</p> : null}
      </div>
      <div className={cn("p-5 sm:p-6", contentClassName)}>{children}</div>
    </Card>
  );
}

function CatalogueSection({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      aria-labelledby={`${id}-heading`}
      className="scroll-mt-24 border-t border-border/60 py-16 sm:py-20"
    >
      <div className="container-page">{children}</div>
    </section>
  );
}

export default function DesignSystemPage() {
  return (
    <div className="min-h-dvh">
      <header className="sticky top-0 z-40 border-b border-border/60 bg-background/85 backdrop-blur-xl">
        <div className="container-page flex h-16 items-center justify-between gap-4">
          <Link href="/" aria-label="Auvyren home" className="shrink-0">
            <AuvyrenLogo markClassName="size-7" />
          </Link>

          <nav aria-label="Catalogue sections" className="hidden items-center gap-5 xl:flex">
            {nav.map((item) => (
              <a
                key={item.href}
                href={item.href}
                className="text-xs text-muted transition-colors hover:text-foreground"
              >
                {item.label}
              </a>
            ))}
          </nav>

          <div className="flex items-center gap-2">
            <Badge tone="outline" className="hidden sm:inline-flex">
              Internal · Noindex
            </Badge>
            <ButtonLink href="/dashboard" variant="ghost" size="sm">
              Workspace
              <ArrowUpRight className="size-3.5" aria-hidden="true" />
            </ButtonLink>
          </div>
        </div>
      </header>

      <main id="main-content" tabIndex={-1}>
        <section className="relative overflow-hidden pb-16 pt-14 sm:pb-20 sm:pt-20">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -top-32 left-1/2 h-[26rem] w-[60rem] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(183,232,200,0.08),transparent_65%)] blur-2xl"
          />
          <div className="container-page relative grid gap-12 lg:grid-cols-[1.15fr_0.85fr] lg:items-end">
            <div>
              <p className="eyebrow">Phase 1 · Internal catalogue</p>
              <h1 className="mt-6 max-w-3xl font-serif text-display-lg font-light">
                The system behind
                <span className="serif-italic block text-accent">the calm.</span>
              </h1>
              <p className="mt-6 max-w-xl text-body-lg leading-relaxed text-muted">
                Every token, control and state used across Auvyren. This page is a working
                reference, not a marketing surface: each specimen renders the same
                production component used in the product.
              </p>
              <div className="mt-7 flex flex-wrap items-center gap-2">
                <Badge tone="accent" dot>
                  Version 0.1
                </Badge>
                <Badge tone="outline">Dark only</Badge>
                <Badge tone="outline">WCAG 2.1 AA</Badge>
                <Badge tone="outline">Reduced motion aware</Badge>
              </div>
            </div>

            <Card className="p-5 sm:p-6">
              <div className="flex items-center justify-between gap-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                  Contents
                </p>
                <Layers className="size-4 text-accent" aria-hidden="true" />
              </div>
              <ol className="mt-4 divide-y divide-border/70">
                {[
                  ["01", "Identity", "#identity"],
                  ["02", "Typography", "#typography"],
                  ["03", "Colour", "#colour"],
                  ["04", "Shape, depth and motion", "#shape"],
                  ["05", "Actions and badges", "#actions"],
                  ["06", "Form controls", "#forms"],
                  ["07", "Feedback and states", "#feedback"],
                  ["08", "Navigation and overlays", "#overlays"],
                  ["09", "Accessibility", "#accessibility"],
                ].map(([number, label, href]) => (
                  <li key={number}>
                    <a
                      href={href}
                      className="flex items-center justify-between gap-4 py-2.5 text-small text-foreground-soft transition-colors hover:text-accent"
                    >
                      <span className="flex items-center gap-3">
                        <span className="font-serif text-xs italic text-faint">{number}</span>
                        {label}
                      </span>
                      <ArrowRight className="size-3.5 text-faint" aria-hidden="true" />
                    </a>
                  </li>
                ))}
              </ol>
              <p className="mt-4 border-t border-border/70 pt-4 text-[11px] leading-relaxed text-faint">
                Reviewed 6 November 2026 · Source of truth:{" "}
                <span className="font-mono text-[10px] text-muted">src/app/globals.css</span>
              </p>
            </Card>
          </div>
        </section>

        <CatalogueSection id="identity">
          <SectionIntro
            id="identity"
            index="01 / Identity"
            title="A quiet mark, built from an orbit."
            description="The logo is a horizon crossed by a single living point: intention above, ground below. It works at 20px, holds its shape in one colour, and never relies on the accent to be recognisable."
          />

          <div className="mt-10 grid gap-4 lg:grid-cols-3">
            <Specimen title="Primary lockup" note="Mark + wordmark" contentClassName="flex items-center justify-center">
              <div className="flex min-h-40 w-full items-center justify-center rounded-xl border border-border/70 bg-background/40">
                <AuvyrenLogo />
              </div>
            </Specimen>

            <Specimen title="Mark" note="Minimum 20px" contentClassName="flex items-center justify-center">
              <div className="flex min-h-40 w-full items-center justify-center gap-8 rounded-xl border border-border/70 bg-background/40">
                <AuvyrenMark className="size-20 text-foreground" />
                <AuvyrenMark className="size-8 text-foreground" />
                <AuvyrenMark className="size-5 text-foreground" />
              </div>
            </Specimen>

            <Specimen title="Wordmark" note="0.34em tracking" contentClassName="flex items-center justify-center">
              <div className="flex min-h-40 w-full items-center justify-center rounded-xl border border-border/70 bg-background/40">
                <AuvyrenWordmark className="text-base" />
              </div>
            </Specimen>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-2xl border border-success/20 bg-success-soft/25 p-5">
              <div className="flex items-center gap-2 text-success">
                <CheckCircle2 className="size-4" aria-hidden="true" />
                <p className="text-small font-semibold">Use</p>
              </div>
              <ul className="mt-3 space-y-1.5 text-small leading-relaxed text-muted">
                <li>Warm paper on ink, or ink on warm paper.</li>
                <li>Keep clear space equal to the mark diameter on all sides.</li>
                <li>Pair with the serif display face; let the mark stay quiet.</li>
              </ul>
            </div>
            <div className="rounded-2xl border border-danger/20 bg-danger-soft/25 p-5">
              <div className="flex items-center gap-2 text-danger">
                <CircleAlert className="size-4" aria-hidden="true" />
                <p className="text-small font-semibold">Do not</p>
              </div>
              <ul className="mt-3 space-y-1.5 text-small leading-relaxed text-muted">
                <li>Stretch, rotate or outline the mark.</li>
                <li>Place it on photography without a protective field.</li>
                <li>Introduce a second accent or gradient into the lockup.</li>
              </ul>
            </div>
          </div>
        </CatalogueSection>

        <CatalogueSection id="typography">
          <SectionIntro
            id="typography"
            index="02 / Typography"
            title="One serif for thought. One sans for work."
            description="Newsreader carries the editorial voice: headlines, quotations and reflective moments. Manrope runs the interface. Both are self-hosted variable fonts, so no request leaves the machine."
          />

          <div className="mt-10 grid gap-4 md:grid-cols-2">
            <Card className="p-6">
              <div className="flex items-center justify-between gap-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                  Display
                </p>
                <Badge tone="sand">Newsreader Variable</Badge>
              </div>
              <p className="mt-6 font-serif text-5xl font-light leading-none tracking-[-0.03em]">
                Aa
              </p>
              <p className="mt-5 font-serif text-2xl font-light">
                Think clearly. Move intentionally.
              </p>
              <p className="mt-3 font-serif text-lg italic text-muted">
                The italic carries emphasis without raising its voice.
              </p>
              <p className="mt-5 border-t border-border/70 pt-4 font-mono text-[10px] uppercase tracking-wide text-faint">
                Weights 200–800 · roman + italic
              </p>
            </Card>

            <Card className="p-6">
              <div className="flex items-center justify-between gap-4">
                <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                  Interface
                </p>
                <Badge tone="accent">Manrope Variable</Badge>
              </div>
              <p className="mt-6 text-5xl font-light leading-none tracking-[-0.02em]">Aa</p>
              <p className="mt-5 text-2xl font-semibold tracking-[-0.02em]">
                Clear labels, honest states.
              </p>
              <p className="mt-3 text-lg leading-relaxed text-muted">
                Reserved for actions, navigation, forms and every piece of running UI copy.
              </p>
              <p className="mt-5 border-t border-border/70 pt-4 font-mono text-[10px] uppercase tracking-wide text-faint">
                Weights 200–800 · variable
              </p>
            </Card>
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1.2fr_0.8fr]">
            <Specimen title="Display scale" note="Fluid clamp() sizes">
              <div className="space-y-7">
                {displayScale.map((item) => (
                  <div key={item.token} className="border-b border-border/60 pb-6 last:border-0 last:pb-0">
                    <p className="mb-2 font-mono text-[10px] uppercase tracking-wide text-faint">
                      {item.token}
                    </p>
                    <p className={cn("font-serif font-light leading-none", item.className)}>
                      {item.sample}
                    </p>
                  </div>
                ))}
              </div>
            </Specimen>

            <div className="grid content-start gap-4">
              <Specimen title="Editorial accents">
                <div className="space-y-5">
                  <p className="eyebrow">The quiet dossier</p>
                  <p className="font-serif text-3xl font-light leading-tight">
                    A record of
                    <span className="serif-italic text-accent"> how you think.</span>
                  </p>
                  <p className="text-small leading-relaxed text-muted">
                    Italic is reserved for a single emphasised phrase, never for entire
                    paragraphs or interface labels.
                  </p>
                </div>
              </Specimen>
              <Specimen title="Type rules">
                <ul className="space-y-2.5 text-small leading-relaxed text-muted">
                  <li>Maximum line length: 68 characters.</li>
                  <li>Body copy never drops below 15px.</li>
                  <li>Headings use balanced wrapping; paragraphs use pretty wrapping.</li>
                  <li>Uppercase labels never exceed 11px with 0.14em tracking.</li>
                </ul>
              </Specimen>
            </div>
          </div>

          <Specimen title="Body and utility scale" className="mt-4">
            <div className="divide-y divide-border/60">
              {bodyScale.map((item) => (
                <div key={item.token} className="grid gap-2 py-4 sm:grid-cols-[8rem_1fr_13rem] sm:items-baseline sm:gap-6">
                  <p className="font-mono text-[10px] uppercase tracking-wide text-faint">
                    {item.token}
                  </p>
                  <p className={cn("text-foreground-soft", item.className)}>{item.sample}</p>
                  <p className="text-[11px] text-faint sm:text-right">{item.note}</p>
                </div>
              ))}
            </div>
          </Specimen>
        </CatalogueSection>

        <CatalogueSection id="colour">
          <SectionIntro
            id="colour"
            index="03 / Colour"
            title="Ink, moss and warm paper."
            description="A single dark theme with one living accent. Colour carries meaning only where meaning exists; the interface never uses hue as decoration. Every text pair below meets WCAG 2.1 AA, and form boundaries meet the 3:1 non-text threshold."
          />

          <div className="mt-10 grid grid-cols-2 gap-3 sm:grid-cols-4 lg:grid-cols-5">
            {colours.map((colour) => (
              <div
                key={colour.token}
                className="overflow-hidden rounded-xl border border-border bg-surface/50"
              >
                <div
                  className="h-20 border-b border-border/70"
                  style={{ backgroundColor: colour.hex }}
                  aria-hidden="true"
                />
                <div className="p-3">
                  <p className="text-xs font-semibold text-foreground-soft">{colour.name}</p>
                  <p className="mt-0.5 font-mono text-[9px] uppercase tracking-wide text-faint">
                    {colour.hex}
                  </p>
                  <p className="mt-1.5 text-[10px] leading-relaxed text-muted">{colour.note}</p>
                </div>
              </div>
            ))}
          </div>

          <div className="mt-4 grid gap-4 lg:grid-cols-[1.05fr_0.95fr]">
            <Specimen title="Contrast audit" note="Measured against actual token values">
              <div
                className="overflow-x-auto"
                role="region"
                aria-label="Contrast audit table"
                tabIndex={0}
              >
                <table className="w-full min-w-[26rem] border-collapse text-left">
                  <thead>
                    <tr className="border-b border-border/70 text-[10px] uppercase tracking-[0.14em] text-faint">
                      <th scope="col" className="pb-2.5 font-semibold">
                        Pair
                      </th>
                      <th scope="col" className="pb-2.5 font-semibold">
                        Ratio
                      </th>
                      <th scope="col" className="pb-2.5 text-right font-semibold">
                        Result
                      </th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50">
                    {contrastPairs.map((row) => (
                      <tr key={row.pair}>
                        <td className="py-2.5 pr-4 text-small text-foreground-soft">
                          {row.pair}
                          <span className="ml-2 text-[10px] text-faint">{row.size}</span>
                        </td>
                        <td className="py-2.5 font-mono text-xs text-muted">{row.ratio}</td>
                        <td className="py-2.5 text-right">
                          <Badge tone={row.tone}>AA</Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <p className="mt-4 text-[11px] leading-relaxed text-faint">
                Ratios computed with the WCAG relative-luminance formula. Large display text
                exceeds 3:1 by a wide margin; normal text exceeds 4.5:1.
              </p>
            </Specimen>

            <div className="grid content-start gap-4">
              <Specimen title="Meaning">
                <ul className="space-y-3 text-small">
                  {[
                    ["Accent", "Attention, selection, presence. Never danger.", "text-accent"],
                    ["Sand", "Reflection, history, editorial warmth.", "text-sand"],
                    ["Success", "Completed or verified states only.", "text-success"],
                    ["Warning", "Caution that still allows proceeding.", "text-warning"],
                    ["Danger", "Failure, destructive actions, invalid input.", "text-danger"],
                    ["Info", "Neutral explanation and preview notices.", "text-info"],
                  ].map(([name, meaning, className]) => (
                    <li key={name} className="flex items-start gap-3">
                      <span
                        className={cn("mt-1.5 size-2 shrink-0 rounded-full bg-current", className)}
                        aria-hidden="true"
                      />
                      <span>
                        <span className={cn("font-semibold", className)}>{name}</span>
                        <span className="text-muted"> — {meaning}</span>
                      </span>
                    </li>
                  ))}
                </ul>
              </Specimen>
              <Specimen title="Rules">
                <ul className="space-y-2.5 text-small leading-relaxed text-muted">
                  <li>Never rely on colour alone; pair it with text, icon or shape.</li>
                  <li>Tinted backgrounds stay below 12% opacity unless they are state panels.</li>
                  <li>Pure black and pure white are avoided; ink and paper are warmer.</li>
                  <li>Disabled controls are exempt from contrast minimums, but remain legible.</li>
                </ul>
              </Specimen>
            </div>
          </div>
        </CatalogueSection>

        <CatalogueSection id="shape">
          <SectionIntro
            id="shape"
            index="04 / Shape, depth and motion"
            title="Soft edges, shallow depth."
            description="Radii are generous but never playful. Depth is closer to paper lifted from a desk than glass floating in space. Motion is short, eased and entirely optional."
          />

          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            <Specimen title="Radius scale">
              <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
                {radii.map((radius) => (
                  <div key={radius.token} className="text-center">
                    <div
                      className={cn(
                        "flex h-20 items-center justify-center border border-border-control bg-surface text-[10px] uppercase tracking-[0.14em] text-faint",
                        radius.className,
                      )}
                    >
                      {radius.size}
                    </div>
                    <p className="mt-2 font-mono text-[10px] text-faint">{radius.token}</p>
                  </div>
                ))}
              </div>
              <p className="mt-5 text-[11px] leading-relaxed text-faint">
                Controls use <span className="text-muted">xl</span> (14px); cards use{" "}
                <span className="text-muted">2xl</span> (20px); dialogs and feature panels use
                the next step up.
              </p>
            </Specimen>

            <div className="grid content-start gap-4">
              <Specimen title="Depth">
                <div className="grid gap-3 sm:grid-cols-3">
                  {[
                    ["shadow-soft", "Lifted card"],
                    ["shadow-panel", "Dialog / menu"],
                    ["shadow-glow", "Living signal"],
                  ].map(([token, label]) => (
                    <div
                      key={token}
                      className={cn(
                        "flex h-24 items-end rounded-xl border border-border bg-surface p-3 shadow-soft",
                        token === "shadow-panel" && "shadow-panel",
                        token === "shadow-glow" && "shadow-glow",
                      )}
                    >
                      <div>
                        <p className="text-xs font-medium text-foreground-soft">{label}</p>
                        <p className="mt-0.5 font-mono text-[9px] text-faint">{token}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </Specimen>
              <Specimen title="Motion" note="Respects prefers-reduced-motion">
                <div className="flex flex-wrap items-center gap-6">
                  <div className="flex items-center gap-3">
                    <span className="size-2.5 animate-pulse-soft rounded-full bg-accent shadow-glow" aria-hidden="true" />
                    <div>
                      <p className="text-xs font-medium text-foreground-soft">pulse-soft</p>
                      <p className="font-mono text-[9px] text-faint">5s · presence</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="flex size-9 items-center justify-center rounded-full border border-border">
                      <Orbit className="size-4 animate-spin text-sand [animation-duration:9s]" aria-hidden="true" />
                    </span>
                    <div>
                      <p className="text-xs font-medium text-foreground-soft">orbit</p>
                      <p className="font-mono text-[9px] text-faint">slow · ambient</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <Waves className="size-5 text-info" aria-hidden="true" />
                    <div>
                      <p className="text-xs font-medium text-foreground-soft">fade-up</p>
                      <p className="font-mono text-[9px] text-faint">700ms · expo-out</p>
                    </div>
                  </div>
                </div>
                <p className="mt-5 border-t border-border/70 pt-4 text-[11px] leading-relaxed text-faint">
                  Entrances are single-run. Nothing loops for attention except ambient
                  constellation marks, which pause entirely under reduced motion.
                </p>
              </Specimen>
            </div>
          </div>
        </CatalogueSection>

        <CatalogueSection id="actions">
          <SectionIntro
            id="actions"
            index="05 / Actions and badges"
            title="Actions with one clear priority."
            description="A screen gets one primary action. Secondary actions carry a boundary; ghost actions recede. Every button defaults to type=button, has a visible focus ring and a minimum 36px target."
          />

          <div className="mt-10 grid gap-4">
            <Specimen title="Button variants" note="Primary · secondary · ghost · danger">
              <div className="flex flex-wrap items-center gap-3">
                <Button>
                  Primary action
                  <ArrowRight className="size-4" aria-hidden="true" />
                </Button>
                <Button variant="secondary">
                  Secondary
                  <Pencil className="size-4" aria-hidden="true" />
                </Button>
                <Button variant="ghost">Ghost action</Button>
                <Button variant="danger">
                  <Trash2 className="size-4" aria-hidden="true" />
                  Delete
                </Button>
              </div>
            </Specimen>

            <div className="grid gap-4 md:grid-cols-2">
              <Specimen title="Sizes and icon buttons">
                <div className="flex flex-wrap items-center gap-3">
                  <Button size="sm">Small · 36</Button>
                  <Button size="md">Medium · 44</Button>
                  <Button size="lg">Large · 48</Button>
                  <IconButton label="Search">
                    <Search className="size-4" aria-hidden="true" />
                  </IconButton>
                  <IconButton label="Add item" variant="secondary">
                    <Plus className="size-4" aria-hidden="true" />
                  </IconButton>
                  <IconButton label="Save item">
                    <Bookmark className="size-4" aria-hidden="true" />
                  </IconButton>
                </div>
              </Specimen>

              <Specimen title="States">
                <div className="flex flex-wrap items-center gap-3">
                  <Button loading>Saving</Button>
                  <Button disabled>Unavailable</Button>
                  <Button variant="secondary" loading>
                    Checking
                  </Button>
                  <ButtonLink href="/dashboard" variant="secondary" size="sm">
                    Link action
                    <ArrowRight className="size-3.5" aria-hidden="true" />
                  </ButtonLink>
                </div>
                <p className="mt-4 text-[11px] leading-relaxed text-faint">
                  Loading sets aria-busy and prevents double submission. Disabled controls
                  explain themselves through nearby copy, never through a tooltip alone.
                </p>
              </Specimen>
            </div>

            <Specimen title="Badges" note="Status is always spelled out">
              <div className="flex flex-wrap items-center gap-2">
                <Badge>Neutral</Badge>
                <Badge tone="accent" dot>
                  Local
                </Badge>
                <Badge tone="sand">Reflection</Badge>
                <Badge tone="success" dot>
                  Complete
                </Badge>
                <Badge tone="warning">Needs review</Badge>
                <Badge tone="danger">Failed</Badge>
                <Badge tone="info">Informational</Badge>
                <Badge tone="outline">Outline</Badge>
                <Badge size="md" tone="outline">
                  <Sparkles className="size-3" aria-hidden="true" />
                  Generated
                </Badge>
              </div>
              <div className="mt-5 border-t border-border/70 pt-5">
                <p className="mb-3 text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
                  Badges as quiet signals, not actions
                </p>
                <BadgeActionsDemo />
              </div>
            </Specimen>
          </div>
        </CatalogueSection>

        <CatalogueSection id="forms">
          <SectionIntro
            id="forms"
            index="06 / Form controls"
            title="Validation that explains itself."
            description="Labels sit above their controls. Hints and errors occupy reserved space so the layout does not jump. Errors are attached with aria-describedby, announced politely, and never rely on red alone."
          />

          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            <Specimen title="Input states">
              <div className="grid gap-5">
                <Field
                  label="Display name"
                  htmlFor="ds-name"
                  hint="Shown only to you, across your workspace."
                >
                  <Input
                    id="ds-name"
                    placeholder="Your name"
                    aria-describedby={fieldMessageId("ds-name", "hint")}
                  />
                </Field>

                <Field
                  label="Email address"
                  htmlFor="ds-error-field"
                  error="Enter a valid email address."
                >
                  <Input
                    id="ds-error-field"
                    type="email"
                    defaultValue="not-an-email"
                    aria-invalid
                    aria-describedby={fieldMessageId("ds-error-field", "error")}
                  />
                </Field>

                <Field
                  label="Recovery address"
                  htmlFor="ds-success-field"
                  success="Address confirmed."
                >
                  <Input
                    id="ds-success-field"
                    type="email"
                    defaultValue="you@example.com"
                    aria-describedby={fieldMessageId("ds-success-field", "success")}
                  />
                </Field>

                <Field
                  label="Account email"
                  htmlFor="ds-disabled"
                  hint="Available after accounts arrive in Phase 2."
                >
                  <Input
                    id="ds-disabled"
                    placeholder="No account connected"
                    disabled
                    aria-describedby={fieldMessageId("ds-disabled", "hint")}
                  />
                </Field>
              </div>
            </Specimen>

            <Specimen title="Text, selection and choice">
              <div className="grid gap-5">
                <Field label="Reflection" htmlFor="ds-notes" optional hint="Markdown is not required.">
                  <Textarea
                    id="ds-notes"
                    placeholder="What changed today?"
                    aria-describedby={fieldMessageId("ds-notes", "hint")}
                  />
                </Field>

                <Field label="Timezone" htmlFor="ds-timezone">
                  <Select id="ds-timezone" defaultValue="Europe/London">
                    <option value="Europe/London">Europe / London</option>
                    <option value="Europe/Berlin">Europe / Berlin</option>
                    <option value="America/New_York">America / New York</option>
                  </Select>
                </Field>

                <fieldset className="space-y-3">
                  <legend className="text-small font-semibold text-foreground-soft">
                    Quiet preferences
                  </legend>
                  <Checkbox label="Weekly review invitation" defaultChecked />
                  <Checkbox
                    label="Local AI suggestions"
                    description="Disabled until a local runtime is connected."
                    disabled
                  />
                </fieldset>
              </div>
            </Specimen>
          </div>

          <Specimen
            title="Live validation"
            note="Client-side only · nothing stored"
            className="mt-4"
          >
            <FormDemo />
          </Specimen>
        </CatalogueSection>

        <CatalogueSection id="feedback">
          <SectionIntro
            id="feedback"
            index="07 / Feedback and states"
            title="Honest states, fully drawn."
            description="Every surface has a loading, empty, error and success expression. Empty means empty: no invented rows, sample counts or fabricated progress. Feedback explains what happened and what to do next."
          />

          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            <Specimen title="Inline messages">
              <div className="space-y-3">
                <InlineMessage tone="info" title="Preview notice">
                  This surface is ready for the next phase. Nothing was saved.
                </InlineMessage>
                <InlineMessage tone="success" title="Saved locally">
                  The record now lives in your own PostgreSQL database.
                </InlineMessage>
                <InlineMessage tone="warning" title="Optional service unavailable">
                  Deterministic features continue to work; the local model did not respond.
                </InlineMessage>
                <InlineMessage tone="danger" title="Could not save">
                  Check the connection and try again. Your draft remains in this tab.
                </InlineMessage>
              </div>
            </Specimen>

            <Specimen title="Empty, error and success">
              <div className="grid gap-3">
                <EmptyState
                  icon={Inbox}
                  title="Nothing is waiting."
                  description="An honest empty state with no sample rows or invented counts."
                  compact
                />
                <ErrorStateDemo />
                <SuccessState
                  title="Everything is in order."
                  description="A confirmed state, reserved for outcomes that actually happened."
                  compact
                />
              </div>
            </Specimen>
          </div>

          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <Specimen title="Loading">
              <div className="space-y-3">
                <Skeleton className="h-3 w-24" />
                <Skeleton className="h-8 w-2/3" />
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-4/5" />
              </div>
              <div className="mt-6 flex items-center gap-3 border-t border-border/70 pt-5 text-small text-muted">
                <Spinner />
                Loading in place — never a full-page takeover.
              </div>
            </Specimen>

            <Specimen title="Message anatomy">
              <div className="flex items-start gap-3 rounded-xl border border-info/20 bg-info-soft/60 px-4 py-3">
                <Info className="mt-0.5 size-4 shrink-0 text-info" aria-hidden="true" />
                <div>
                  <p className="text-sm font-semibold text-info">Tone carries meaning</p>
                  <p className="mt-0.5 text-sm leading-relaxed text-foreground-soft">
                    Icon, title and body work together. The heading names the state; the body
                    says what happened and what comes next.
                  </p>
                </div>
              </div>
              <ul className="mt-5 space-y-2 text-small leading-relaxed text-muted">
                <li>Info: neutral explanation or preview boundary.</li>
                <li>Success: a confirmed outcome, never encouragement.</li>
                <li>Warning: degraded but usable.</li>
                <li>Error: failed, with a recovery path.</li>
              </ul>
            </Specimen>
          </div>
        </CatalogueSection>

        <CatalogueSection id="overlays">
          <SectionIntro
            id="overlays"
            index="08 / Navigation and overlays"
            title="Layered, but never loud."
            description="Tabs, dialogs, menus, tooltips and toasts are treated as instruments: they open only when needed, trap focus correctly, close on escape, and return focus to their trigger."
          />

          <div className="mt-10 grid gap-4 lg:grid-cols-2">
            <Specimen title="Tabs" note="Arrow-key navigation">
              <TabsDemo />
            </Specimen>

            <div className="grid content-start gap-4">
              <Specimen title="Dialog">
                <DialogDemo />
              </Specimen>
              <Specimen title="Dropdown menu">
                <DropdownDemo />
              </Specimen>
              <div className="grid gap-4 sm:grid-cols-2">
                <Specimen title="Tooltip">
                  <TooltipDemo />
                </Specimen>
                <Specimen title="Toast">
                  <ToastDemo />
                </Specimen>
              </div>
            </div>
          </div>
        </CatalogueSection>

        <CatalogueSection id="accessibility">
          <SectionIntro
            id="accessibility"
            index="09 / Accessibility"
            title="Calm is an accessibility property."
            description="The system targets WCAG 2.1 AA: sufficient contrast, visible focus, full keyboard operation, honest semantics and respect for reduced motion. Accessibility is reviewed with every component, not after the fact."
          />

          <div className="mt-10 grid gap-4 lg:grid-cols-[1.1fr_0.9fr]">
            <Specimen title="Focus and keyboard">
              <div className="flex flex-wrap items-center gap-3">
                <Button>Tab to me</Button>
                <Button variant="secondary">And me</Button>
                <a
                  href="#accessibility"
                  className="rounded-sm text-small text-foreground-soft underline decoration-border-strong underline-offset-4 hover:text-accent"
                >
                  A focusable link
                </a>
              </div>
              <p className="mt-4 text-[11px] leading-relaxed text-faint">
                The accent focus ring is 2px with a 3px offset and 14.05:1 contrast. It is
                applied globally through :focus-visible, including custom checkbox and Radix
                controls.
              </p>
              <div
                className="mt-5 overflow-x-auto"
                role="region"
                aria-label="Keyboard behaviour table"
                tabIndex={0}
              >
                <table className="w-full min-w-[24rem] border-collapse text-left">
                  <thead>
                    <tr className="border-b border-border/70 text-[10px] uppercase tracking-[0.14em] text-faint">
                      <th scope="col" className="pb-2.5 font-semibold">Surface</th>
                      <th scope="col" className="pb-2.5 font-semibold">Required behaviour</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-border/50 text-small">
                    {[
                      ["Dialog", "Focus trapped · Escape closes · focus returns"],
                      ["Menu", "Arrow keys move · typeahead · Escape closes"],
                      ["Tabs", "Arrow keys move · Home / End · one tab stop"],
                      ["Tooltip", "Hover and focus · Escape dismisses"],
                      ["Toast", "Announced · pause on hover · dismiss button"],
                      ["Checkbox", "Space toggles · visible focus ring"],
                    ].map(([surface, behaviour]) => (
                      <tr key={surface}>
                        <td className="py-2.5 pr-4 font-medium text-foreground-soft">{surface}</td>
                        <td className="py-2.5 text-muted">{behaviour}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Specimen>

            <div className="grid content-start gap-4">
              <Specimen title="Responsive contract">
                <div
                  className="overflow-x-auto"
                  role="region"
                  aria-label="Responsive contract table"
                  tabIndex={0}
                >
                  <table className="w-full min-w-[20rem] border-collapse text-left">
                    <thead>
                      <tr className="border-b border-border/70 text-[10px] uppercase tracking-[0.14em] text-faint">
                        <th scope="col" className="pb-2.5 font-semibold">Width</th>
                        <th scope="col" className="pb-2.5 font-semibold">Behaviour</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-border/50 text-small">
                      {[
                        ["390px", "Single column · dialog navigation · 44px targets"],
                        ["820px", "Two-column cards · full-width tabs"],
                        ["1440px", "Fixed 256px sidebar · 1180px content frame"],
                      ].map(([width, behaviour]) => (
                        <tr key={width}>
                          <td className="py-2.5 pr-4 font-mono text-[11px] text-foreground-soft">{width}</td>
                          <td className="py-2.5 text-muted">{behaviour}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <p className="mt-4 text-[11px] leading-relaxed text-faint">
                  Tested at 390, 820 and 1440 CSS pixels. No horizontal scrolling at 320px;
                  the shell collapses its sidebar below 1024px.
                </p>
              </Specimen>

              <Specimen title="Inclusive defaults">
                <ul className="space-y-2.5 text-small leading-relaxed text-muted">
                  <li>Every page provides one main landmark and a global skip link.</li>
                  <li>Icons are decorative unless they are the only label.</li>
                  <li>Status messages use role=status; errors use role=alert.</li>
                  <li>Motion, shimmer and orbit are suppressed for reduced-motion users.</li>
                  <li>Text remains usable at 200% zoom and with system font overrides.</li>
                </ul>
              </Specimen>
            </div>
          </div>

          <Specimen title="Review log" className="mt-4">
            <div className="grid gap-6 md:grid-cols-3">
              {[
                {
                  icon: Type,
                  title: "Type & contrast",
                  copy: "All text pairs re-measured after the faint tone was lifted. The weakest normal-text pair is 4.91:1 on elevated surfaces.",
                },
                {
                  icon: CheckCircle2,
                  title: "Keyboard & focus",
                  copy: "Dialog, menu, tabs, tooltip and toast reviewed with keyboard only. Focus is visible on every control, including custom inputs.",
                },
                {
                  icon: CircleAlert,
                  title: "Non-text contrast",
                  copy: "Form controls now use a dedicated boundary token at 3.45:1 against ink, keeping inputs identifiable without raising the whole interface.",
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div key={item.title} className="flex gap-3">
                    <span className="mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-background/50 text-accent">
                      <Icon className="size-3.5" aria-hidden="true" />
                    </span>
                    <div>
                      <p className="text-small font-semibold text-foreground-soft">{item.title}</p>
                      <p className="mt-1 text-xs leading-relaxed text-muted">{item.copy}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          </Specimen>
        </CatalogueSection>

        <section className="border-t border-border/60 py-16 sm:py-20">
          <div className="container-page">
            <div className="relative overflow-hidden rounded-3xl border border-accent/20 bg-[linear-gradient(135deg,rgba(183,232,200,0.06),rgba(12,16,13,0.4)_45%,rgba(217,195,160,0.04))] p-7 sm:p-10">
              <div
                aria-hidden="true"
                className="absolute -right-20 -top-20 size-64 rounded-full bg-[radial-gradient(circle,rgba(183,232,200,0.1),transparent_68%)] blur-2xl"
              />
              <div className="relative flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
                <div>
                  <p className="eyebrow">Next surface</p>
                  <h2 className="mt-4 max-w-xl font-serif text-display-sm font-light">
                    See the system at work in the shell.
                  </h2>
                  <p className="mt-3 max-w-lg text-small leading-relaxed text-muted">
                    The dashboard and settings previews use these exact primitives, with
                    honest empty states and no sample data.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <ButtonLink href="/dashboard">
                    Open workspace
                    <ArrowUpRight className="size-4" aria-hidden="true" />
                  </ButtonLink>
                  <ButtonLink href="/" variant="secondary">
                    Return to site
                  </ButtonLink>
                </div>
              </div>
            </div>

            <div className="mt-10 flex flex-col gap-3 border-t border-border/60 pt-6 text-[10px] uppercase tracking-[0.14em] text-faint sm:flex-row sm:items-center sm:justify-between">
              <p>Auvyren design system · Phase 1</p>
              <p className="flex items-center gap-2">
                <Mail className="size-3" aria-hidden="true" />
                Internal reference · not indexed
              </p>
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}
