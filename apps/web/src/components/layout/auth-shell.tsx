import Link from "next/link";
import { Orbit } from "lucide-react";

import { AuvyrenLogo } from "@/components/ui/logo";

const trail = [
  { label: "Plan", copy: "See the shape of the day." },
  { label: "Practice", copy: "Keep what matters consistent." },
  { label: "Reflect", copy: "Turn experience into memory." },
];

export function AuthShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-dvh lg:grid lg:grid-cols-[1.02fr_0.98fr]">
      <aside className="relative hidden min-h-dvh flex-col justify-between overflow-hidden border-r border-border/70 bg-background-secondary/35 p-10 lg:flex xl:p-14">
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-40 bottom-[-12rem] size-[34rem] rounded-full border border-border/60"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute -left-24 bottom-[-7rem] size-[22rem] rounded-full border border-dashed border-border/70"
        />
        <div
          aria-hidden="true"
          className="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_at_20%_80%,rgba(183,232,200,0.09),transparent_55%)]"
        />

        <Link href="/" aria-label="Auvyren home" className="relative w-fit">
          <AuvyrenLogo />
        </Link>

        <div className="relative max-w-lg">
          <Orbit className="size-5 text-accent" aria-hidden="true" />
          <blockquote className="mt-7 font-serif text-4xl font-light leading-[1.12] tracking-[-0.03em] text-foreground xl:text-5xl">
            The goal is not to do more.
            <span className="serif-italic block text-accent">It is to see clearly.</span>
          </blockquote>
          <p className="mt-6 max-w-md text-small leading-relaxed text-muted">
            Auvyren is a quiet place to plan, practise and reflect — built around attention
            rather than engagement.
          </p>
        </div>

        <div className="relative">
          <dl className="divide-y divide-border/70 border-y border-border/70">
            {trail.map((item, index) => (
              <div key={item.label} className="flex items-baseline gap-5 py-3">
                <dt className="w-24 shrink-0 whitespace-nowrap text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                  0{index + 1} / {item.label}
                </dt>
                <dd className="text-small text-foreground-soft">{item.copy}</dd>
              </div>
            ))}
          </dl>
          <p className="mt-6 text-[10px] uppercase tracking-[0.16em] text-faint">
            Local-first · Deterministic first · AI by consent
          </p>
        </div>
      </aside>

      <div className="flex min-h-dvh flex-col">
        <header className="flex items-center justify-between p-5 sm:p-8 lg:justify-end">
          <Link href="/" aria-label="Auvyren home" className="lg:hidden">
            <AuvyrenLogo markClassName="size-7" />
          </Link>
          <Link
            href="/"
            className="text-xs text-muted transition-colors hover:text-foreground"
          >
            Back to Auvyren
          </Link>
        </header>

        <div className="flex flex-1 items-center justify-center px-5 py-8 sm:px-8 sm:py-10">
          <div className="w-full max-w-md">{children}</div>
        </div>

        <footer className="px-5 pb-6 text-center text-[10px] uppercase tracking-[0.14em] text-faint sm:px-8">
          Foundation preview · Accounts open in Phase 2
        </footer>
      </div>
    </div>
  );
}
