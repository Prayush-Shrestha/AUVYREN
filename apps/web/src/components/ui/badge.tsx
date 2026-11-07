import { cn } from "@/lib/cn";

type BadgeTone =
  | "neutral"
  | "accent"
  | "sand"
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "outline";

const tones: Record<BadgeTone, string> = {
  neutral: "border-border bg-surface text-muted",
  accent: "border-accent/25 bg-accent/10 text-accent",
  sand: "border-sand/25 bg-sand/10 text-sand",
  success: "border-success/25 bg-success/10 text-success",
  warning: "border-warning/25 bg-warning/10 text-warning",
  danger: "border-danger/25 bg-danger/10 text-danger",
  info: "border-info/25 bg-info/10 text-info",
  outline: "border-border-strong bg-transparent text-foreground-soft",
};

export function Badge({
  children,
  tone = "neutral",
  size = "sm",
  dot = false,
  className,
}: {
  children: React.ReactNode;
  tone?: BadgeTone;
  size?: "sm" | "md";
  dot?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 whitespace-nowrap rounded-full border font-semibold uppercase",
        size === "sm"
          ? "px-2.5 py-0.5 text-[10px] tracking-[0.12em]"
          : "px-3 py-1 text-micro tracking-[0.12em]",
        tones[tone],
        className,
      )}
    >
      {dot ? <span className="size-1.5 rounded-full bg-current" aria-hidden="true" /> : null}
      {children}
    </span>
  );
}
