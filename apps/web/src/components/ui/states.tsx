import {
  CircleAlert,
  CircleCheck,
  Info,
  LoaderCircle,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";

type MessageTone = "info" | "success" | "warning" | "danger";

const messageTones: Record<
  MessageTone,
  { wrapper: string; icon: LucideIcon; iconClass: string }
> = {
  info: {
    wrapper: "border-info/20 bg-info-soft/60 text-info",
    icon: Info,
    iconClass: "text-info",
  },
  success: {
    wrapper: "border-success/20 bg-success-soft/60 text-success",
    icon: CircleCheck,
    iconClass: "text-success",
  },
  warning: {
    wrapper: "border-warning/20 bg-warning-soft/60 text-warning",
    icon: TriangleAlert,
    iconClass: "text-warning",
  },
  danger: {
    wrapper: "border-danger/20 bg-danger-soft/60 text-danger",
    icon: CircleAlert,
    iconClass: "text-danger",
  },
};

export function InlineMessage({
  tone = "info",
  title,
  children,
  className,
  action,
}: {
  tone?: MessageTone;
  title?: string;
  children: React.ReactNode;
  className?: string;
  action?: React.ReactNode;
}) {
  const config = messageTones[tone];
  const Icon = config.icon;

  return (
    <div
      className={cn(
        "flex flex-col gap-3 rounded-xl border px-4 py-3 text-sm sm:flex-row sm:items-start",
        config.wrapper,
        className,
      )}
      role={tone === "danger" || tone === "warning" ? "alert" : "status"}
    >
      <div className="flex min-w-0 flex-1 items-start gap-3">
        <Icon className={cn("mt-0.5 size-4 shrink-0", config.iconClass)} aria-hidden="true" />
        <div className="min-w-0 flex-1">
          {title ? <p className="font-semibold leading-snug">{title}</p> : null}
          <div className={cn("leading-relaxed text-foreground-soft", title && "mt-0.5")}>
            {children}
          </div>
        </div>
      </div>
      {action ? <div className="shrink-0 pl-7 sm:pl-2">{action}</div> : null}
    </div>
  );
}

export function EmptyState({
  icon: Icon,
  eyebrow,
  title,
  description,
  action,
  className,
  compact = false,
}: {
  icon: LucideIcon;
  eyebrow?: string;
  title: string;
  description: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-dashed border-border-strong/70 bg-background-secondary/30 text-center",
        compact ? "px-5 py-8" : "px-6 py-12",
        className,
      )}
    >
      <span className="mb-4 flex size-10 items-center justify-center rounded-full border border-border bg-surface text-accent">
        <Icon className="size-4.5" aria-hidden="true" />
      </span>
      {eyebrow ? (
        <p className="mb-1.5 text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
          {eyebrow}
        </p>
      ) : null}
      <h3 className="font-serif text-xl font-normal text-foreground">{title}</h3>
      <p className="mt-2 max-w-sm text-small leading-relaxed text-muted">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  title = "Something went wrong",
  description,
  onRetry,
  className,
}: {
  title?: string;
  description: React.ReactNode;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-danger/25 bg-danger-soft/30 px-6 py-12 text-center",
        className,
      )}
    >
      <span className="mb-4 flex size-10 items-center justify-center rounded-full border border-danger/25 bg-danger-soft text-danger">
        <CircleAlert className="size-4.5" aria-hidden="true" />
      </span>
      <h3 className="font-serif text-xl font-normal text-foreground">{title}</h3>
      <p className="mt-2 max-w-sm text-small leading-relaxed text-muted">{description}</p>
      {onRetry ? (
        <Button variant="secondary" size="sm" className="mt-5" onClick={onRetry}>
          Try again
        </Button>
      ) : null}
    </div>
  );
}

export function SuccessState({
  title = "Everything is in order",
  description,
  action,
  className,
  compact = false,
}: {
  title?: string;
  description: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
  compact?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center rounded-xl border border-success/25 bg-success-soft/20 text-center",
        compact ? "px-5 py-8" : "px-6 py-12",
        className,
      )}
    >
      <span className="mb-4 flex size-10 items-center justify-center rounded-full border border-success/25 bg-success-soft text-success">
        <CircleCheck className="size-4.5" aria-hidden="true" />
      </span>
      <h3 className="font-serif text-xl font-normal text-foreground">{title}</h3>
      <p className="mt-2 max-w-sm text-small leading-relaxed text-muted">{description}</p>
      {action ? <div className="mt-5">{action}</div> : null}
    </div>
  );
}

export function Skeleton({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "relative overflow-hidden rounded-md bg-surface-hover/80",
        className,
      )}
      aria-hidden="true"
      {...props}
    >
      <span className="absolute inset-0 -translate-x-full animate-shimmer bg-gradient-to-r from-transparent via-white/[0.055] to-transparent" />
    </div>
  );
}

export function Spinner({ className }: { className?: string }) {
  return (
    <LoaderCircle
      className={cn("size-4 animate-spin text-muted", className)}
      aria-hidden="true"
    />
  );
}
