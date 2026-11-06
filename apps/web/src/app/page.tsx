import { env } from "@/lib/env";

const stack = [
  { label: "Frontend", value: "Next.js 16 · TypeScript" },
  { label: "Backend", value: "FastAPI · PostgreSQL" },
  { label: "Intelligence", value: "Deterministic first" },
];

export default function Home() {
  const docsUrl = `${env.apiOrigin}/docs`;

  return (
    <main className="relative flex min-h-dvh items-center overflow-hidden px-6 py-16 sm:px-10">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-x-0 top-0 h-px bg-gradient-to-r from-transparent via-accent/40 to-transparent"
      />
      <div className="mx-auto w-full max-w-5xl">
        <p className="mb-10 flex items-center gap-3 text-xs font-medium uppercase tracking-[0.22em] text-muted">
          <span className="h-1.5 w-1.5 rounded-full bg-accent" aria-hidden="true" />
          Auvyren · Phase 0
        </p>

        <div className="grid gap-12 lg:grid-cols-[1.4fr_0.6fr] lg:items-end">
          <div>
            <h1 className="max-w-3xl text-balance text-4xl font-medium leading-[1.04] tracking-[-0.035em] sm:text-6xl lg:text-7xl">
              A quiet foundation for
              <span className="text-accent"> clear thinking.</span>
            </h1>
            <p className="mt-7 max-w-xl text-base leading-7 text-muted sm:text-lg">
              Phase 0 establishes the architecture, data model and service boundaries.
              The brand system, authentication and personal productivity modules follow
              in controlled phases.
            </p>
            <div className="mt-9 flex flex-wrap gap-3">
              <a
                href={docsUrl}
                className="inline-flex h-11 items-center justify-center rounded-full border border-accent/30 bg-accent px-6 text-sm font-semibold text-background transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
              >
                Open API documentation
              </a>
              <span className="inline-flex h-11 items-center rounded-full border border-border px-5 text-sm text-muted">
                Foundation online
              </span>
            </div>
          </div>

          <dl className="divide-y divide-border border-y border-border">
            {stack.map((item) => (
              <div key={item.label} className="py-4">
                <dt className="text-[11px] uppercase tracking-[0.18em] text-muted">
                  {item.label}
                </dt>
                <dd className="mt-1.5 text-sm text-foreground">{item.value}</dd>
              </div>
            ))}
          </dl>
        </div>

        <footer className="mt-20 flex flex-col gap-3 border-t border-border pt-6 text-xs text-muted sm:flex-row sm:items-center sm:justify-between">
          <p>Think clearly. Move intentionally.</p>
          <p>Local-first · Privacy by design</p>
        </footer>
      </div>
    </main>
  );
}
