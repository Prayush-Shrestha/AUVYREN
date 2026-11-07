"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage } from "@/components/ui/states";
import { useAuth } from "@/features/auth/auth-provider";
import { validateEmail, validatePassword } from "@/features/auth/validation";
import { ApiError } from "@/lib/api/client";

type Errors = { email?: string; password?: string };

const notices: Record<string, { tone: "info" | "warning" | "success"; title: string; copy: string }> = {
  expired: {
    tone: "warning",
    title: "Your session ended",
    copy: "Sign in again to return to your workspace.",
  },
  signin_required: {
    tone: "info",
    title: "Sign in to continue",
    copy: "Your workspace is private. Sign in to open it.",
  },
  signed_out: {
    tone: "success",
    title: "You are signed out",
    copy: "Your session was revoked on the server.",
  },
};

export function SignInForm({
  nextPath = "/dashboard",
  reason,
  resetSuccess = false,
}: {
  nextPath?: string;
  reason?: string;
  resetSuccess?: boolean;
}) {
  const router = useRouter();
  const { signIn } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const notice = reason ? notices[reason] : undefined;

  function validate(): Errors {
    return {
      email: validateEmail(email),
      password: validatePassword(password),
    };
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = validate();
    setErrors(next);
    setFormError(undefined);
    if (next.email || next.password) return;

    setSubmitting(true);
    try {
      await signIn({ email: email.trim(), password });
      router.replace(nextPath);
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.detail);
        setErrors({
          email: error.fieldErrors?.email,
          password: error.fieldErrors?.password,
        });
      } else {
        setFormError("Auvyren could not be reached. Check your connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
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

      {resetSuccess ? (
        <div className="mt-7">
          <InlineMessage tone="success" title="Password reset">
            Sign in with your new password. Every previous session has been revoked.
          </InlineMessage>
        </div>
      ) : notice ? (
        <div className="mt-7">
          <InlineMessage tone={notice.tone} title={notice.title}>
            {notice.copy}
          </InlineMessage>
        </div>
      ) : null}

      <form className="mt-7 space-y-5" noValidate onSubmit={handleSubmit}>
        {formError ? (
          <InlineMessage tone="danger" title="Sign-in failed">
            {formError}
          </InlineMessage>
        ) : null}

        <Field label="Email address" htmlFor="signin-email" error={errors.email}>
          <Input
            id="signin-email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            disabled={submitting}
            aria-invalid={Boolean(errors.email) || undefined}
            aria-describedby={errors.email ? "signin-email-error" : undefined}
            onChange={(event) => {
              setEmail(event.target.value);
              setErrors((current) => ({ ...current, email: undefined }));
              setFormError(undefined);
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
              disabled={submitting}
              aria-invalid={Boolean(errors.password) || undefined}
              aria-describedby={errors.password ? "signin-password-error" : undefined}
              onChange={(event) => {
                setPassword(event.target.value);
                setErrors((current) => ({ ...current, password: undefined }));
                setFormError(undefined);
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

        <Button type="submit" className="w-full" loading={submitting}>
          {submitting ? "Signing in…" : "Sign in"}
        </Button>
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
