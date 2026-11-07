"use client";

import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

import { Button, ButtonLink } from "@/components/ui/button";
import { AuvyrenLogo } from "@/components/ui/logo";

export default function GlobalError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  useEffect(() => {
    console.error("Application error", error);
  }, [error]);

  return (
    <main
      id="main-content"
      tabIndex={-1}
      className="flex min-h-dvh flex-col items-center justify-center px-6 py-16 text-center"
    >
      <AuvyrenLogo />
      <p className="mt-14 text-[10px] font-semibold uppercase tracking-[0.18em] text-danger">
        An unexpected interruption
      </p>
      <h1 className="mt-4 max-w-xl font-serif text-display-sm font-light">
        The page lost its thread.
      </h1>
      <p className="mt-4 max-w-md text-small leading-relaxed text-muted">
        Something failed while rendering this surface. The rest of Auvyren is unaffected.
        Try again, or return to the beginning.
      </p>
      <div className="mt-8 flex flex-wrap justify-center gap-3">
        <Button onClick={() => retry()}>
          <RefreshCw className="size-4" aria-hidden="true" />
          Try again
        </Button>
        <ButtonLink href="/" variant="secondary">
          Return home
        </ButtonLink>
      </div>
    </main>
  );
}
