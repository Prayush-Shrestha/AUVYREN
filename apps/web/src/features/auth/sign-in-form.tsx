"use client";

import Link from "next/link";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage } from "@/components/ui/states";
import { PreviewNotice } from "@/features/auth/preview-notice";
import {
  validateEmail,
  validatePassword,
} from "@/features/auth/validation";

type Errors = { email?: string; password?: string };

export function SignInForm() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [preview, setPreview] = useState(false);

  function validate(): Errors {
    return {
      email: validateEmail(email),
      password: validatePassword(password),
    };
  }

  return (
    <div>
      <p className="eyebrow">Welcome back</p>
      <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
        Return to your space.
      </h1>
      <p className="mt-3 text-small leading-relaxed text-muted">
        Sign in to see your day, your practice and the thread between them.
      </p>

      <div className="mt-7">
        <PreviewNotice />
      </div>

      <form
        className="mt-7 space-y-5"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          const next = validate();
          setErrors(next);
          setPreview(!next.email && !next.password);
        }}
      >
        <Field label="Email address" htmlFor="signin-email" error={errors.email}>
          <Input
            id="signin-email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            aria-invalid={Boolean(errors.email) || undefined}
            aria-describedby={errors.email ? "signin-email-error" : undefined}
            onChange={(event) => {
              setEmail(event.target.value);
              setErrors((current) => ({ ...current, email: undefined }));
              setPreview(false);
            }}
            onBlur={() => {
              if (email) {
                setErrors((current) => ({ ...current, email: validateEmail(email) }));
              }
            }}
          />
        </Field>

        <div className="space-y-2">
          <Field label="Password" htmlFor="signin-password" error={errors.password}>
            <Input
              id="signin-password"
              name="password"
              type="password"
              autoComplete="current-password"
              placeholder="Your password"
              value={password}
              aria-invalid={Boolean(errors.password) || undefined}
              aria-describedby={errors.password ? "signin-password-error" : undefined}
              onChange={(event) => {
                setPassword(event.target.value);
                setErrors((current) => ({ ...current, password: undefined }));
                setPreview(false);
              }}
              onBlur={() => {
                if (password) {
                  setErrors((current) => ({
                    ...current,
                    password: validatePassword(password),
                  }));
                }
              }}
            />
          </Field>
          <div className="flex justify-end">
            <Link
              href="/forgot-password"
              className="text-xs text-muted underline decoration-border-strong underline-offset-4 transition-colors hover:text-accent"
            >
              Forgot password?
            </Link>
          </div>
        </div>

        <Button type="submit" className="w-full">
          Sign in
        </Button>

        {preview ? (
          <InlineMessage tone="info" title="No session was created">
            This screen is ready for Phase 2. Authentication is not connected yet, so no
            account was accessed.
          </InlineMessage>
        ) : null}
      </form>

      <p className="mt-7 text-center text-small text-muted">
        New to Auvyren?{" "}
        <Link
          href="/sign-up"
          className="font-semibold text-foreground underline decoration-border-strong underline-offset-4 transition-colors hover:text-accent"
        >
          Create an account
        </Link>
      </p>
    </div>
  );
}
