"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, MailCheck } from "lucide-react";

import { Button, ButtonLink } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage } from "@/components/ui/states";
import { forgotPasswordRequest } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { validateEmail } from "@/features/auth/validation";

export function ForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [fieldError, setFieldError] = useState<string>();
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = validateEmail(email);
    setFieldError(next);
    setFormError(undefined);
    if (next) return;

    setSubmitting(true);
    try {
      await forgotPasswordRequest({ email: email.trim() });
      setSent(true);
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.detail);
        setFieldError(error.fieldErrors?.email);
      } else {
        setFormError(
          "Auvyren could not be reached. Check your connection and try again.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (sent) {
    return (
      <div>
        <p className="eyebrow">Password reset</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          Check your inbox.
        </h1>
        <p className="mt-3 text-small leading-relaxed text-muted">
          We sent a request for the address you entered. The response is always the same,
          whether or not an account exists.
        </p>

        <div className="mt-7">
          <InlineMessage tone="info" title="If the account exists">
            A single-use link is on its way to <strong>{email.trim()}</strong>. It expires
            in 30 minutes, and using it signs out every other session.
          </InlineMessage>
        </div>

        <div className="mt-7 space-y-3">
          <ButtonLink href="/sign-in" className="w-full">
            <MailCheck className="size-4" aria-hidden="true" />
            Back to sign in
          </ButtonLink>
          <Button
            type="button"
            variant="ghost"
            className="w-full"
            onClick={() => {
              setSent(false);
              setFormError(undefined);
            }}
          >
            Use a different email
          </Button>
        </div>
      </div>
    );
  }

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

      <form className="mt-7 space-y-5" noValidate onSubmit={handleSubmit}>
        {formError ? (
          <InlineMessage tone="danger" title="Request not sent">
            {formError}
          </InlineMessage>
        ) : null}

        <Field label="Email address" htmlFor="forgot-email" error={fieldError}>
          <Input
            id="forgot-email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            disabled={submitting}
            aria-invalid={Boolean(fieldError) || undefined}
            aria-describedby={fieldError ? "forgot-email-error" : undefined}
            onChange={(event) => {
              setEmail(event.target.value);
              setFieldError(undefined);
              setFormError(undefined);
            }}
            onBlur={() => {
              if (email) setFieldError(validateEmail(email));
            }}
          />
        </Field>

        <Button type="submit" className="w-full" loading={submitting}>
          {submitting ? "Sending…" : "Send reset link"}
        </Button>
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
