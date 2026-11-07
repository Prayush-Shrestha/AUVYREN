import { cn } from "@/lib/cn";

export function Card({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "rounded-2xl border border-border bg-surface/70 shadow-soft backdrop-blur-[2px]",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}

export function CardHeader({
  eyebrow,
  title,
  description,
  action,
  className,
}: {
  eyebrow?: string;
  title: React.ReactNode;
  description?: React.ReactNode;
  action?: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("flex items-start justify-between gap-4 px-5 pt-5 sm:px-6 sm:pt-6", className)}>
      <div className="min-w-0">
        {eyebrow ? (
          <p className="mb-2 text-[10px] font-semibold uppercase tracking-[0.18em] text-muted">
            {eyebrow}
          </p>
        ) : null}
        <h2 className="font-serif text-title-lg font-normal text-foreground">{title}</h2>
        {description ? (
          <p className="mt-1.5 max-w-prose text-small leading-relaxed text-muted">
            {description}
          </p>
        ) : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}

export function CardBody({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div className={cn("px-5 pb-5 sm:px-6 sm:pb-6", className)} {...props}>
      {children}
    </div>
  );
}

export function CardFooter({
  className,
  children,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return (
    <div
      className={cn(
        "flex flex-wrap items-center gap-3 border-t border-border/80 px-5 py-3.5 sm:px-6",
        className,
      )}
      {...props}
    >
      {children}
    </div>
  );
}
