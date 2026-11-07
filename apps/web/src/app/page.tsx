import type { Metadata } from "next";
import Link from "next/link";
import {
  ArrowRight,
  ArrowUpRight,
  Cloud,
  Compass,
  Cpu,
  Database,
  Lightbulb,
  ListChecks,
  LockKeyhole,
  NotebookPen,
  Repeat2,
  ShieldCheck,
  Sparkles,
  Waypoints,
} from "lucide-react";

import { SiteFooter } from "@/components/layout/site-footer";
import { SiteHeader } from "@/components/layout/site-header";
import { Constellation } from "@/components/marketing/constellation";
import { Reveal } from "@/components/marketing/reveal";
import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";

export const metadata: Metadata = {
  title: "A local-first personal operating system",
  description:
    "Auvyren gathers your plans, practice and reflection into one quiet system — deterministic insight first, AI only when you ask.",
};

const pillars = [
  {
    number: "01",
    icon: Compass,
    title: "Plan",
    copy: "Tasks, projects, goals and a calendar that answer one question: what deserves your attention now?",
    detail: "A daily surface, not another backlog.",
  },
  {
    number: "02",
    icon: Repeat2,
    title: "Practice",
    copy: "Habits and routines that make consistency visible without turning your life into a scoreboard.",
    detail: "Streaks inform. They do not judge.",
  },
  {
    number: "03",
    icon: NotebookPen,
    title: "Reflect",
    copy: "Notes, decisions and reviews that turn experience into a working memory you can return to.",
    detail: "A record of how you think.",
  },
  {
    number: "04",
    icon: Sparkles,
    title: "Understand",
    copy: "Patterns, workload and progress explained in plain language. Deterministic first; AI only when asked.",
    detail: "Insight with its reasoning attached.",
  },
];

const values = [
  "One calm system",
  "No borrowed urgency",
  "Private by default",
  "Explainable insight",
];

const principles = [
  {
    number: "01",
    title: "Calm over loud",
    copy: "The interface recedes. One clear priority is worth more than a wall of metrics, badges and urgent red dots.",
  },
  {
    number: "02",
    title: "Depth over dashboards",
    copy: "Auvyren is built for orientation, not performance. It should help you see your life clearly, not merely measure it.",
  },
  {
    number: "03",
    title: "Privacy by default",
    copy: "Local-first means your records remain yours. AI is optional, visible and consent-bound. Your life is never training data.",
  },
  {
    number: "04",
    title: "Tools that get out of the way",
    copy: "No streaks-as-guilt, no growth loops, no manufactured urgency. The work is the point; the software should know when to be quiet.",
  },
];

const reasoning = [
  {
    icon: Database,
    title: "Your records",
    copy: "Tasks, goals, habits and dates — scoped to you, never blended with anyone else.",
  },
  {
    icon: ListChecks,
    title: "A transparent model",
    copy: "Weights and rules you could read. Urgency, importance and fit, composed in the open.",
  },
  {
    icon: Lightbulb,
    title: "A reason you can read",
    copy: "Every recommendation carries the factors behind it. Nothing arrives as an unexplained command.",
  },
];

export default function Home() {
  return (
    <>
      <SiteHeader />
      <main id="main-content" tabIndex={-1}>
        <section className="relative overflow-hidden pb-20 pt-14 sm:pb-28 sm:pt-20">
          <div
            aria-hidden="true"
            className="pointer-events-none absolute -top-40 left-1/2 h-[36rem] w-[72rem] -translate-x-1/2 rounded-full bg-[radial-gradient(ellipse_at_center,rgba(183,232,200,0.09),transparent_65%)] blur-2xl"
          />
          <div className="container-page relative">
            <div className="grid items-center gap-16 lg:grid-cols-[1.04fr_0.96fr]">
              <Reveal>
                <p className="eyebrow">A personal operating system</p>
                <h1 className="mt-7 font-serif text-display-xl font-light text-foreground">
                  Make room for
                  <span className="serif-italic block text-accent">what matters.</span>
                </h1>
                <p className="mt-7 max-w-xl text-body-lg leading-relaxed text-muted">
                  Auvyren gathers your plans, practice and reflection into one quiet
                  system — so attention can go where intention already is.
                </p>
                <div className="mt-9 flex flex-col gap-3 sm:flex-row">
                  <ButtonLink href="/dashboard" size="lg">
                    Explore the workspace
                    <ArrowRight className="size-4" aria-hidden="true" />
                  </ButtonLink>
                  <ButtonLink href="#system" variant="secondary" size="lg">
                    See the system
                  </ButtonLink>
                </div>
                <p className="mt-6 text-xs leading-relaxed text-faint">
                  Deterministic by default · Local AI optional · Cloud only with consent
                </p>
              </Reveal>

              <Reveal delay={0.12}>
                <Constellation />
              </Reveal>
            </div>

            <div className="mt-20 grid grid-cols-2 gap-x-6 gap-y-4 border-y border-border/60 py-5 sm:grid-cols-4">
              {values.map((value) => (
                <p
                  key={value}
                  className="flex items-center gap-2.5 text-[11px] font-medium uppercase tracking-[0.14em] text-muted"
                >
                  <span className="size-1 rounded-full bg-accent/80" aria-hidden="true" />
                  {value}
                </p>
              ))}
            </div>
          </div>
        </section>

        <section id="system" className="scroll-mt-24 py-24 sm:py-32">
          <div className="container-page">
            <Reveal className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
              <div>
                <p className="eyebrow">01 / The system</p>
                <h2 className="mt-6 max-w-xl font-serif text-display-md font-light">
                  A place for the whole shape of your day.
                </h2>
              </div>
              <p className="max-w-xl text-body leading-relaxed text-muted lg:justify-self-end">
                Most tools are built for capture. Auvyren is designed for orientation —
                seeing what matters, choosing the next move, and noticing what changes over
                time.
              </p>
            </Reveal>

            <div className="mt-12 grid gap-4 md:grid-cols-2">
              {pillars.map((pillar, index) => {
                const Icon = pillar.icon;
                return (
                  <Reveal key={pillar.title} delay={index * 0.05}>
                    <article className="group relative h-full overflow-hidden rounded-2xl border border-border bg-surface/55 p-6 transition-colors duration-300 hover:border-border-strong hover:bg-surface-elevated/65 sm:p-8">
                      <div
                        aria-hidden="true"
                        className="absolute -right-16 -top-16 size-40 rounded-full bg-[radial-gradient(circle,rgba(183,232,200,0.07),transparent_70%)] opacity-0 transition-opacity duration-500 group-hover:opacity-100"
                      />
                      <div className="flex items-start justify-between gap-6">
                        <span className="flex size-10 items-center justify-center rounded-full border border-border bg-background/60 text-accent">
                          <Icon className="size-4.5" aria-hidden="true" />
                        </span>
                        <span className="font-serif text-sm font-light italic text-faint">
                          {pillar.number}
                        </span>
                      </div>
                      <h3 className="mt-8 font-serif text-2xl font-normal">{pillar.title}</h3>
                      <p className="mt-3 max-w-md text-body leading-relaxed text-muted">
                        {pillar.copy}
                      </p>
                      <p className="mt-6 border-t border-border/70 pt-4 text-[11px] uppercase tracking-[0.14em] text-faint">
                        {pillar.detail}
                      </p>
                    </article>
                  </Reveal>
                );
              })}
            </div>
          </div>
        </section>

        <section
          id="intelligence"
          className="scroll-mt-24 border-y border-border/60 bg-background-secondary/35 py-24 sm:py-32"
        >
          <div className="container-page grid gap-14 lg:grid-cols-[0.86fr_1.14fr] lg:items-center">
            <Reveal>
              <p className="eyebrow">02 / Quiet intelligence</p>
              <h2 className="mt-6 max-w-lg font-serif text-display-md font-light">
                Help that can show its work.
              </h2>
              <p className="mt-6 max-w-lg text-body leading-relaxed text-muted">
                Auvyren starts with rules, not guesses. Priorities, workload and progress
                are computed from your own records, and every recommendation carries a
                reason. Language models are an optional layer — never the foundation.
              </p>

              <dl className="mt-9 divide-y divide-border/70 border-y border-border/70">
                {[
                  [
                    "Explainable by default",
                    "Every insight shows the factors that produced it.",
                  ],
                  [
                    "Useful without a model",
                    "The deterministic engine needs no GPU, network or subscription.",
                  ],
                  [
                    "Local when you want it",
                    "Connect your own Ollama runtime on a self-hosted instance.",
                  ],
                  [
                    "Cloud only by consent",
                    "Explicit, revocable, and never a silent fallback.",
                  ],
                ].map(([title, copy]) => (
                  <div key={title} className="grid gap-1 py-3.5 sm:grid-cols-[1fr_1.35fr] sm:gap-6">
                    <dt className="text-small font-semibold text-foreground-soft">{title}</dt>
                    <dd className="text-small leading-relaxed text-muted">{copy}</dd>
                  </div>
                ))}
              </dl>
            </Reveal>

            <Reveal delay={0.1}>
              <Card className="overflow-hidden">
                <CardHeader
                  eyebrow="Reasoning path"
                  title="From record to recommendation"
                  description="No black box at the centre of your day."
                  action={<Badge tone="accent" dot>Always available</Badge>}
                />
                <CardBody>
                  <ol className="mt-2 space-y-3">
                    {reasoning.map((step, index) => {
                      const Icon = step.icon;
                      return (
                        <li
                          key={step.title}
                          className="relative flex gap-4 rounded-xl border border-border/80 bg-background/45 p-4"
                        >
                          <span className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                            <Icon className="size-4" aria-hidden="true" />
                          </span>
                          <div>
                            <p className="text-small font-semibold text-foreground">
                              <span className="mr-2 font-serif text-xs font-light italic text-faint">
                                0{index + 1}
                              </span>
                              {step.title}
                            </p>
                            <p className="mt-1 text-xs leading-relaxed text-muted">{step.copy}</p>
                          </div>
                        </li>
                      );
                    })}
                  </ol>

                  <div className="mt-4 rounded-xl border border-dashed border-border-strong/70 bg-surface/40 p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <p className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-faint">
                        <Waypoints className="size-3.5" aria-hidden="true" />
                        Optional layers
                      </p>
                      <Badge tone="outline">Off by default</Badge>
                    </div>
                    <div className="mt-3 grid gap-2 sm:grid-cols-2">
                      <div className="flex items-center gap-2.5 rounded-lg border border-border/70 bg-background/50 px-3 py-2.5">
                        <Cpu className="size-3.5 text-accent" aria-hidden="true" />
                        <span className="text-xs font-medium text-foreground-soft">
                          Local AI · Ollama
                        </span>
                      </div>
                      <div className="flex items-center gap-2.5 rounded-lg border border-border/70 bg-background/50 px-3 py-2.5">
                        <Cloud className="size-3.5 text-muted" aria-hidden="true" />
                        <span className="text-xs font-medium text-foreground-soft">
                          Cloud · consent required
                        </span>
                      </div>
                    </div>
                  </div>
                </CardBody>
              </Card>
            </Reveal>
          </div>
        </section>

        <section id="philosophy" className="scroll-mt-24 py-24 sm:py-32">
          <div className="container-page">
            <Reveal className="grid gap-6 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
              <div>
                <p className="eyebrow">03 / Principles</p>
                <h2 className="mt-6 max-w-xl font-serif text-display-md font-light">
                  Soft systems,
                  <span className="serif-italic text-sand"> sharp thinking.</span>
                </h2>
              </div>
              <p className="max-w-xl text-body leading-relaxed text-muted lg:justify-self-end">
                The product is shaped by a few convictions. They are not features; they are
                constraints that keep the system honest.
              </p>
            </Reveal>

            <div className="mt-12 border-t border-border/70">
              {principles.map((principle, index) => (
                <Reveal key={principle.number} delay={index * 0.04}>
                  <div className="group grid gap-3 border-b border-border/70 py-7 transition-colors hover:bg-surface/25 sm:grid-cols-[4rem_1fr_1.2fr] sm:items-start sm:gap-8 sm:px-3">
                    <span className="font-serif text-sm font-light italic text-faint">
                      {principle.number}
                    </span>
                    <h3 className="font-serif text-xl font-normal text-foreground sm:text-2xl">
                      {principle.title}
                    </h3>
                    <p className="max-w-xl text-small leading-relaxed text-muted">
                      {principle.copy}
                    </p>
                  </div>
                </Reveal>
              ))}
            </div>
          </div>
        </section>

        <section id="privacy" className="scroll-mt-24 pb-24 sm:pb-32">
          <div className="container-page">
            <Reveal>
              <div className="relative overflow-hidden rounded-3xl border border-accent/20 bg-[linear-gradient(135deg,rgba(183,232,200,0.07),rgba(12,16,13,0.4)_42%,rgba(217,195,160,0.04))] p-7 sm:p-10 lg:p-14">
                <div
                  aria-hidden="true"
                  className="absolute -right-24 -top-24 size-72 rounded-full bg-[radial-gradient(circle,rgba(183,232,200,0.1),transparent_68%)] blur-2xl"
                />
                <div className="relative grid gap-10 lg:grid-cols-[1.15fr_0.85fr] lg:items-center">
                  <div>
                    <p className="eyebrow">04 / Privacy</p>
                    <h2 className="mt-6 max-w-xl font-serif text-display-sm font-light sm:text-display-md">
                      Your life is not
                      <span className="serif-italic text-accent"> training data.</span>
                    </h2>
                    <p className="mt-5 max-w-xl text-body leading-relaxed text-muted">
                      Auvyren is designed to be self-hosted and local-first. Your records are
                      the source of truth. AI is never required, and cloud processing never
                      happens silently.
                    </p>
                    <ul className="mt-7 space-y-2.5">
                      {[
                        "Records remain in your PostgreSQL database.",
                        "No model is called unless you configure one.",
                        "Every cloud request requires explicit consent.",
                      ].map((item) => (
                        <li
                          key={item}
                          className="flex items-start gap-2.5 text-small text-foreground-soft"
                        >
                          <ShieldCheck
                            className="mt-0.5 size-4 shrink-0 text-accent"
                            aria-hidden="true"
                          />
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div className="rounded-2xl border border-border/80 bg-background/55 p-5 shadow-soft backdrop-blur">
                    <div className="flex items-center justify-between gap-4">
                      <div className="flex items-center gap-3">
                        <span className="flex size-10 items-center justify-center rounded-full border border-accent/20 bg-accent/5 text-accent">
                          <LockKeyhole className="size-4" aria-hidden="true" />
                        </span>
                        <div>
                          <p className="text-small font-semibold text-foreground">
                            Local by default
                          </p>
                          <p className="text-[10px] uppercase tracking-[0.14em] text-faint">
                            Privacy posture
                          </p>
                        </div>
                      </div>
                      <Badge tone="success" dot>
                        On
                      </Badge>
                    </div>
                    <dl className="mt-5 space-y-3 border-t border-border/70 pt-4 text-xs">
                      <div className="flex items-center justify-between gap-4">
                        <dt className="text-muted">Deterministic engine</dt>
                        <dd className="font-medium text-foreground-soft">Always local</dd>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <dt className="text-muted">Local model</dt>
                        <dd className="font-medium text-foreground-soft">Optional</dd>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <dt className="text-muted">Cloud model</dt>
                        <dd className="font-medium text-foreground-soft">Consent only</dd>
                      </div>
                      <div className="flex items-center justify-between gap-4">
                        <dt className="text-muted">Training on your data</dt>
                        <dd className="font-medium text-accent">Never</dd>
                      </div>
                    </dl>
                  </div>
                </div>
              </div>
            </Reveal>
          </div>
        </section>

        <section className="border-t border-border/60 py-24 sm:py-32">
          <div className="container-page text-center">
            <Reveal>
              <p className="eyebrow justify-center before:hidden">A quieter default</p>
              <h2 className="mx-auto mt-6 max-w-3xl font-serif text-display-md font-light">
                Begin with a system that asks
                <span className="serif-italic text-accent"> less of your attention.</span>
              </h2>
              <p className="mx-auto mt-6 max-w-xl text-body leading-relaxed text-muted">
                Explore the workspace shell, or step through the account screens. Real
                accounts and synchronization arrive in Phase 2.
              </p>
              <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <ButtonLink href="/dashboard" size="lg">
                  Preview the workspace
                  <ArrowUpRight className="size-4" aria-hidden="true" />
                </ButtonLink>
                <ButtonLink href="/sign-up" variant="secondary" size="lg">
                  Create an account
                </ButtonLink>
              </div>
              <p className="mt-6 text-xs text-faint">
                Already have a space?{" "}
                <Link
                  href="/sign-in"
                  className="text-foreground-soft underline decoration-border-strong underline-offset-4 transition-colors hover:text-accent"
                >
                  Sign in
                </Link>
              </p>
            </Reveal>
          </div>
        </section>
      </main>
      <SiteFooter />
    </>
  );
}
