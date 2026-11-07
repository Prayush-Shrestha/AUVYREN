"use client";

import Link from "next/link";
import { useState } from "react";
import { Check } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Field, Input } from "@/components/ui/field";
import { InlineMessage } from "@/components/ui/states";
import { PreviewNotice } from "@/features/auth/preview-notice";
import {
  validateEmail,
  validateName,
  validatePassword,
} from "@/features/auth/validation";

type Errors = { name?: string; email?: string; password?: string };

export function SignUpForm() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Errors>({});
  const [preview, setPreview] = useState(false);

  const passwordReady = password.length >= 12 && password.length <= 128;

  return (
    <div>
      <p className="eyebrow">Create your space</p>
      <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
        Begin with a quieter default.
      </h1>
      <p className="mt-3 text-small leading-relaxed text-muted">
        One account for your plans, practice and reflection. No noise, no public profile.
      </p>

      <div className="mt-7">
        <PreviewNotice />
      </div>

      <form
        className="mt-7 space-y-5"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          const next = {
            name: validateName(name),
            email: validateEmail(email),
            password: validatePassword(password),
          };
          setErrors(next);
          setPreview(!next.name && !next.email && !next.password);
        }}
      >
        <Field label="Your name" htmlFor="signup-name" error={errors.name} optional>
          <Input
            id="signup-name"
            name="name"
            autoComplete="name"
            placeholder="How should Auvyren address you?"
            value={name}
            aria-invalid={Boolean(errors.name) || undefined}
            aria-describedby={errors.name ? "signup-name-error" : undefined}
            onChange={(event) => {
              setName(event.target.value);
              setErrors((current) => ({ ...current, name: undefined }));
              setPreview(false);
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
            aria-invalid={Boolean(errors.email) || undefined}
            aria-describedby={errors.email ? "signup-email-error" : undefined}
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
            aria-invalid={Boolean(errors.password) || undefined}
            aria-describedby={
              errors.password ? "signup-password-error" : "signup-password-hint"
            }
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

        <Button type="submit" className="w-full">
          Create account
        </Button>

        {preview ? (
          <InlineMessage tone="info" title="No account was created">
            Account creation arrives in Phase 2. This preview validates input only and does
            not store or transmit it.
          </InlineMessage>
        ) : null}
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
