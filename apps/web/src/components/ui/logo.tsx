import { cn } from "@/lib/cn";

export function AuvyrenMark({ className }: { className?: string }) {
  return (
    <svg
      viewBox="0 0 32 32"
      fill="none"
      aria-hidden="true"
      className={cn("size-8", className)}
    >
      <circle cx="16" cy="16" r="14" stroke="currentColor" strokeOpacity="0.26" />
      <path
        d="M6.75 22.25h18.5M10.35 22.25a5.65 5.65 0 0 1 11.3 0"
        stroke="currentColor"
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <circle cx="23.35" cy="9.65" r="2.15" fill="var(--color-accent)" />
    </svg>
  );
}

export function AuvyrenWordmark({ className }: { className?: string }) {
  return (
    <span
      className={cn(
        "text-[0.7rem] font-semibold uppercase leading-none tracking-[0.34em] text-foreground",
        className,
      )}
    >
      Auvyren
    </span>
  );
}

export function AuvyrenLogo({
  className,
  markClassName,
  wordmarkClassName,
}: {
  className?: string;
  markClassName?: string;
  wordmarkClassName?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-3 text-foreground", className)}>
      <AuvyrenMark className={cn("size-8", markClassName)} />
      <AuvyrenWordmark className={wordmarkClassName} />
    </span>
  );
}
