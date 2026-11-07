import Link from "next/link";
import { ArrowLeft, Compass } from "lucide-react";

import { ButtonLink } from "@/components/ui/button";
import { AuvyrenLogo } from "@/components/ui/logo";

export default function NotFound() {
  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="relative flex min-h-dvh flex-col overflow-hidden px-6 py-8"
    >
      <div
        aria-hidden="true"
        className="pointer-events-none absolute left-1/2 top-1/3 size-[32rem] -translate-x-1/2 -translate-y-1/2 rounded-full bg-[radial-gradient(circle,rgba(183,232,200,0.07),transparent_68%)] blur-2xl"
      />
      <header className="relative">
        <Link href="/" aria-label="Auvyren home" className="inline-flex">
          <AuvyrenLogo />
        </Link>
      </header>

      <div className="relative flex flex-1 flex-col items-center justify-center py-16 text-center">
        <p className="font-serif text-[7rem] font-light leading-none tracking-[-0.06em] text-border-strong sm:text-[10rem]">
          404
        </p>
        <p className="mt-2 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-accent">
          <Compass className="size-3.5" aria-hidden="true" />
          Off the map
        </p>
        <h1 className="mt-4 max-w-lg font-serif text-display-sm font-light">
          This page has wandered off.
        </h1>
        <p className="mt-4 max-w-md text-small leading-relaxed text-muted">
          The address may be wrong, or the page may not exist yet. Auvyren is still being
          built, one deliberate phase at a time.
        </p>
        <div className="mt-8 flex flex-wrap justify-center gap-3">
          <ButtonLink href="/">
            <ArrowLeft className="size-4" aria-hidden="true" />
            Return home
          </ButtonLink>
          <ButtonLink href="/dashboard" variant="secondary">
            Preview workspace
          </ButtonLink>
        </div>
      </div>

      <footer className="relative text-center text-[10px] uppercase tracking-[0.14em] text-faint">
        Auvyren · Think clearly. Move intentionally.
      </footer>
    </main>
  );
}
