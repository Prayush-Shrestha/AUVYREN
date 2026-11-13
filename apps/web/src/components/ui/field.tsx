import { cloneElement, forwardRef, isValidElement } from "react";
import { ChevronDown, CircleAlert, CircleCheck } from "lucide-react";

import { cn } from "@/lib/cn";

export function fieldMessageId(
  id: string,
  state: "error" | "success" | "hint" | undefined,
) {
  return state ? `${id}-${state}` : undefined;
}

export function Field({
  label,
  htmlFor,
  hint,
  error,
  success,
  optional = false,
  className,
  children,
}: {
  label: string;
  htmlFor: string;
  hint?: string;
  error?: string;
  success?: string;
  optional?: boolean;
  className?: string;
  children: React.ReactNode;
}) {
  const state = error ? "error" : success ? "success" : hint ? "hint" : undefined;
  const messageId = fieldMessageId(htmlFor, state);

  // Wire the visible hint/error to the control without asking every caller to
  // remember the id. Existing aria-describedby values are preserved.
  const describedBy = isValidElement<{ "aria-describedby"?: string }>(children)
    ? [
        ...new Set(
          [
            children.props["aria-describedby"],
            state ? messageId : undefined,
          ].filter(Boolean),
        ),
      ].join(" ") || undefined
    : undefined;
  const control =
    describedBy && isValidElement<Record<string, unknown>>(children)
      ? cloneElement(children, { "aria-describedby": describedBy })
      : children;

  return (
    <div className={cn("space-y-2", className)}>
      <div className="flex items-baseline justify-between gap-3">
        <label
          htmlFor={htmlFor}
          className="text-small font-semibold text-foreground-soft"
        >
          {label}
        </label>
        {optional ? (
          <span className="text-[10px] uppercase tracking-[0.14em] text-faint">
            Optional
          </span>
        ) : null}
      </div>
      {control}
      {error ? (
        <p
          id={messageId}
          className="flex items-start gap-1.5 text-xs leading-relaxed text-danger"
          role="alert"
        >
          <CircleAlert className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          <span>{error}</span>
        </p>
      ) : success ? (
        <p
          id={messageId}
          className="flex items-start gap-1.5 text-xs leading-relaxed text-success"
          role="status"
        >
          <CircleCheck className="mt-0.5 size-3.5 shrink-0" aria-hidden="true" />
          <span>{success}</span>
        </p>
      ) : hint ? (
        <p id={messageId} className="text-xs leading-relaxed text-muted">
          {hint}
        </p>
      ) : null}
    </div>
  );
}

const controlClassName =
  "w-full rounded-xl border border-border-control bg-background-secondary/80 text-foreground shadow-[0_1px_0_rgba(255,255,255,0.025)_inset] transition-[border-color,background-color] duration-200 placeholder:text-faint hover:border-faint disabled:cursor-not-allowed disabled:border-border disabled:bg-surface/40 disabled:text-muted disabled:opacity-60 aria-invalid:border-danger/65 aria-invalid:hover:border-danger/80";

export const Input = forwardRef<
  HTMLInputElement,
  React.InputHTMLAttributes<HTMLInputElement>
>(function Input({ className, ...props }, ref) {
  return (
    <input
      ref={ref}
      className={cn(controlClassName, "h-11 px-3.5 text-sm", className)}
      {...props}
    />
  );
});

export const Textarea = forwardRef<
  HTMLTextAreaElement,
  React.TextareaHTMLAttributes<HTMLTextAreaElement>
>(function Textarea({ className, ...props }, ref) {
  return (
    <textarea
      ref={ref}
      className={cn(controlClassName, "min-h-28 resize-y px-3.5 py-3 text-sm", className)}
      {...props}
    />
  );
});

export const Select = forwardRef<
  HTMLSelectElement,
  React.SelectHTMLAttributes<HTMLSelectElement>
>(function Select({ className, children, ...props }, ref) {
  return (
    <div className="relative">
      <select
        ref={ref}
        className={cn(controlClassName, "h-11 appearance-none px-3.5 pr-10 text-sm", className)}
        {...props}
      >
        {children}
      </select>
      <ChevronDown
        className="pointer-events-none absolute right-3.5 top-1/2 size-4 -translate-y-1/2 text-muted"
        aria-hidden="true"
      />
    </div>
  );
});
