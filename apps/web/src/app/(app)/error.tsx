"use client";

import { useEffect } from "react";
import { RefreshCw } from "lucide-react";

import { Button, ButtonLink } from "@/components/ui/button";
import { Card, CardBody } from "@/components/ui/card";

export default function WorkspaceError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  useEffect(() => {
    console.error("Workspace error", error);
  }, [error]);

  return (
    <Card className="mx-auto max-w-xl text-center">
      <CardBody className="flex flex-col items-center px-6 py-14">
        <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-danger">
          Workspace interrupted
        </p>
        <h1 className="mt-4 font-serif text-display-sm font-light">
          This surface could not load.
        </h1>
        <p className="mt-3 max-w-sm text-small leading-relaxed text-muted">
          The rest of Auvyren is still standing. Try the workspace again, or return to the
          site.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <Button onClick={() => retry()}>
            <RefreshCw className="size-4" aria-hidden="true" />
            Try again
          </Button>
          <ButtonLink href="/" variant="secondary">
            Back to site
          </ButtonLink>
        </div>
      </CardBody>
    </Card>
  );
}
