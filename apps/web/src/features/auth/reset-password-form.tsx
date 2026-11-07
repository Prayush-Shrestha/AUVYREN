"use client";

import Link from "next/link";
import { useState } from "react";
import { ArrowLeft, KeyRound } from "lucide-react";

import { Button, ButtonLink } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage, SuccessState } from "@/components/ui/states";
import { resetPasswordRequest } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import { validatePassword } from "@/features/auth/validation";

type Errors = { password?: string; confirm?: string };

export function ResetPasswordForm({ token }: { token?: string }) {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);
  const [done, setDone] = useState(false);
  const [tokenRejected, setTokenRejected] = useState(false);

  function validate(): Errors {
    return {
      password: validatePassword(password),
      confirm: !confirm
        ? "Repeat your new password."
        : password !== confirm
          ? "Passwords do not match."
          : undefined,
    };
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!token) return;

    const next = validate();
    setErrors(next);
    setFormError(undefined);
    if (next.password || next.confirm) return;

    setSubmitting(true);
    try {
      await resetPasswordRequest({ token, password });
      setDone(true);
    } catch (error) {
      if (error instanceof ApiError) {
        if (error.code === "invalid_reset_token") {
          setTokenRejected(true);
          return;
        }
        setFormError(error.detail);
        setErrors({
          password: error.fieldErrors?.password,
        });
      } else {
        setFormError(
          "Auvyren could not be reached. Check your connection and try again.",
        );
      }
    } finally {
      setSubmitting(false);
    }
  }

  if (!token || tokenRejected) {
    return (
      <div>
        <p className="eyebrow">Password reset</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          This link cannot be used.
        </h1>
        <p className="mt-3 text-small leading-relaxed text-muted">
          {token
            ? "The reset link is invalid, has expired, or has already been used. Reset links work once and last 30 minutes."
            : "The reset link is missing its token. Open the link from your email again, or request a new one."}
        </p>

        <div className="mt-7">
          <InlineMessage tone="warning" title="Request a fresh link">
            A new link invalidates every earlier reset link for your account.
          </InlineMessage>
        </div>

        <div className="mt-7 space-y-3">
          <ButtonLink href="/forgot-password" className="w-full">
            <KeyRound className="size-4" aria-hidden="true" />
            Request a new link
          </ButtonLink>
          <ButtonLink href="/sign-in" variant="ghost" className="w-full">
            Back to sign in
          </ButtonLink>
        </div>
      </div>
    );
  }

  if (done) {
    return (
      <div>
        <SuccessState
          title="Password updated"
          description="Every previous session has been revoked. Sign in with your new password to return to your workspace."
          action={
            <ButtonLink href="/sign-in?reason=reset" className="w-full">
              Sign in with the new password
            </ButtonLink>
          }
        />
      </div>
    );
  }

  return (
    <div>
      <p className="eyebrow">Password reset</p>
      <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
        Choose a new password.
      </h1>
      <p className="mt-3 text-small leading-relaxed text-muted">
        This link can be used once. Setting a new password signs out every session that is
        currently open.
      </p>

      <form className="mt-7 space-y-5" noValidate onSubmit={handleSubmit}>
        {formError ? (
          <InlineMessage tone="danger" title="Password not updated">
            {formError}
          </InlineMessage>
        ) : null}

        <Field
          label="New password"
          htmlFor="reset-password"
          error={errors.password}
          hint="At least 12 characters. A phrase you can remember works well."
        >
          <Input
            id="reset-password"
            name="password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a new password"
            value={password}
            disabled={submitting}
            aria-invalid={Boolean(errors.password) || undefined}
            aria-describedby={
              errors.password ? "reset-password-error" : "reset-password-hint"
            }
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

        <Field label="Repeat new password" htmlFor="reset-confirm" error={errors.confirm}>
          <Input
            id="reset-confirm"
            name="confirm-password"
            type="password"
            autoComplete="new-password"
            placeholder="Type it again"
            value={confirm}
            disabled={submitting}
            aria-invalid={Boolean(errors.confirm) || undefined}
            aria-describedby={errors.confirm ? "reset-confirm-error" : undefined}
            onChange={(event) => {
              setConfirm(event.target.value);
              setErrors((current) => ({ ...current, confirm: undefined }));
              setFormError(undefined);
            }}
            onBlur={() => {
              if (confirm) {
                setErrors((current) => ({
                  ...current,
                  confirm:
                    password === confirm ? undefined : "Passwords do not match.",
                }));
              }
            }}
          />
        </Field>

        <Button type="submit" className="w-full" loading={submitting}>
          {submitting ? "Updating password…" : "Set new password"}
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
