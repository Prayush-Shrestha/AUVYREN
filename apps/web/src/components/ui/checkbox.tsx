import { Check } from "lucide-react";

import { cn } from "@/lib/cn";

export function Checkbox({
  label,
  description,
  className,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & {
  label: React.ReactNode;
  description?: React.ReactNode;
}) {
  return (
    <label
      className={cn(
        "group flex cursor-pointer items-start gap-3 text-sm text-foreground-soft",
        props.disabled && "cursor-not-allowed opacity-50",
        className,
      )}
    >
      <input type="checkbox" className="peer sr-only" {...props} />
      <span
        aria-hidden="true"
        className="mt-0.5 flex size-4.5 shrink-0 items-center justify-center rounded-[5px] border border-border-control bg-background-secondary transition-colors duration-150 peer-checked:border-accent peer-checked:bg-accent peer-focus-visible:outline-2 peer-focus-visible:outline-offset-2 peer-focus-visible:outline-accent peer-checked:[&>svg]:opacity-100 group-hover:border-accent/60"
      >
        <Check className="size-3 text-accent-ink opacity-0" strokeWidth={3} />
      </span>
      <span className="min-w-0">
        <span className="block leading-snug">{label}</span>
        {description ? (
          <span className="mt-0.5 block text-xs leading-relaxed text-muted">
            {description}
          </span>
        ) : null}
      </span>
    </label>
  );
}
