"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage } from "@/components/ui/states";
import { useAuth } from "@/features/auth/auth-provider";
import {
  validateEmail,
  validateName,
  validatePassword,
} from "@/features/auth/validation";
import { ApiError } from "@/lib/api/client";

type Errors = { name?: string; email?: string; password?: string };

export function SignUpForm() {
  const router = useRouter();
  const { signUp } = useAuth();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [formError, setFormError] = useState<string>();
  const [submitting, setSubmitting] = useState(false);

  const passwordReady = password.length >= 12 && password.length <= 128;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const next = {
      name: validateName(name),
      email: validateEmail(email),
      password: validatePassword(password),
    };
    setErrors(next);
    setFormError(undefined);
    if (next.name || next.email || next.password) return;

    setSubmitting(true);
    try {
      await signUp({
        email: email.trim(),
        password,
        full_name: name.trim() || undefined,
      });
      router.replace("/dashboard");
      router.refresh();
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.detail);
        setErrors({
          name: error.fieldErrors?.full_name,
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
      <p className="eyebrow">Create your space</p>
      <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
        Begin with a quieter default.
      </h1>
      <p className="mt-3 text-small leading-relaxed text-muted">
        One account for your plans, practice and reflection. No noise, no public profile.
      </p>

      <form className="mt-7 space-y-5" noValidate onSubmit={handleSubmit}>
        {formError ? (
          <InlineMessage tone="danger" title="Account not created">
            {formError}
          </InlineMessage>
        ) : null}

        <Field label="Your name" htmlFor="signup-name" error={errors.name} optional>
          <Input
            id="signup-name"
            name="name"
            autoComplete="name"
            placeholder="How should Auvyren address you?"
            value={name}
            disabled={submitting}
            aria-invalid={Boolean(errors.name) || undefined}
            aria-describedby={errors.name ? "signup-name-error" : undefined}
            onChange={(event) => {
              setName(event.target.value);
              setErrors((current) => ({ ...current, name: undefined }));
              setFormError(undefined);
            }}
            onBlur={() => {
              if (name) {
                setErrors((current) => ({ ...current, name: validateName(name) }));
              }
            }}
          />
        </Field>

        <Field label="Email address" htmlFor="signup-email" error={errors.email}>
          <Input
            id="signup-email"
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            placeholder="you@example.com"
            value={email}
            disabled={submitting}
            aria-invalid={Boolean(errors.email) || undefined}
            aria-describedby={errors.email ? "signup-email-error" : undefined}
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

        <Field
          label="Password"
          htmlFor="signup-password"
          error={errors.password}
          hint="At least 12 characters. A phrase you can remember works well."
        >
          <Input
            id="signup-password"
            name="password"
            type="password"
            autoComplete="new-password"
            placeholder="Create a password"
            value={password}
            disabled={submitting}
            aria-invalid={Boolean(errors.password) || undefined}
            aria-describedby={
              errors.password ? "signup-password-error" : "signup-password-hint"
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

        <ul className="space-y-1.5" aria-label="Password guidance">
          <li
            className={`flex items-center gap-2 text-xs ${
              passwordReady ? "text-success" : "text-faint"
            }`}
          >
            <Check className="size-3.5" aria-hidden="true" />
            12–128 characters
          </li>
        </ul>

        <Button type="submit" className="w-full" loading={submitting}>
          {submitting ? "Creating account…" : "Create account"}
        </Button>
      </form>

      <p className="mt-7 text-center text-small text-muted">
        Already have a space?{" "}
        <Link
          href="/sign-in"
          className="font-semibold text-foreground underline decoration-border-strong underline-offset-4 transition-colors hover:text-accent"
        >
          Sign in
        </Link>
      </p>
    </div>
  );
}
