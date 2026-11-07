"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage } from "@/components/ui/states";
import { PreviewNotice } from "@/features/auth/preview-notice";
import { validateEmail } from "@/features/auth/validation";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string>();
  const [preview, setPreview] = useState(false);

  return (
    <div>
      <p className="eyebrow">Password reset</p>
      <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
        Find your way back in.
      </h1>
      <p className="mt-3 text-small leading-relaxed text-muted">
        Enter the email tied to your space. If it exists, a single-use reset link will be
        sent — the response is the same either way.
      </p>

      <div className="mt-7">
        <PreviewNotice />
      </div>

      <form
        className="mt-7 space-y-5"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          const next = validateEmail(email);
          setError(next);
          setPreview(!next);
        }}
      >
        <Field label="Email address" htmlFor="forgot-email" error={error}>
          <Input
            id="forgot-email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            aria-invalid={Boolean(error) || undefined}
            aria-describedby={error ? "forgot-email-error" : undefined}
            onChange={(event) => {
              setEmail(event.target.value);
              setError(undefined);
              setPreview(false);
            }}
            onBlur={() => {
              if (email) setError(validateEmail(email));
            }}
          />
        </Field>

        <Button type="submit" className="w-full">
          Send reset link
        </Button>

        {preview ? (
          <InlineMessage tone="info" title="No email was sent">
            Password reset and email delivery arrive in Phase 2. This screen validates the
            address only.
          </InlineMessage>
        ) : null}
      </form>

      <Link
        href="/sign-in"
        className="mt-7 flex items-center justify-center gap-2 text-small text-muted transition-colors hover:text-foreground"
      >
        <ArrowLeft className="size-3.5" aria-hidden="true" />
        Back to sign in
      </Link>
    </div>
  );
}
