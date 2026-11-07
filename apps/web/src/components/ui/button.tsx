import Link from "next/link";
import { forwardRef } from "react";
import { LoaderCircle } from "lucide-react";

import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
type ButtonSize = "sm" | "md" | "lg" | "icon";

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-accent text-accent-ink shadow-[0_1px_0_rgba(255,255,255,0.35)_inset] hover:bg-accent-strong",
  secondary:
    "border border-border-strong bg-surface-elevated/70 text-foreground hover:bg-surface-hover",
  ghost: "text-foreground-soft hover:bg-white/[0.055] hover:text-foreground",
  danger: "border border-danger/30 bg-danger-soft text-danger hover:bg-danger/15",
};

const sizes: Record<ButtonSize, string> = {
  sm: "h-9 gap-1.5 px-3.5 text-small",
  md: "h-11 gap-2 px-5 text-sm",
  lg: "h-12 gap-2.5 px-6 text-body",
  icon: "size-10 p-0",
};

export function buttonClassName({
  variant = "primary",
  size = "md",
  className,
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  className?: string;
} = {}) {
  return cn(
    "inline-flex select-none items-center justify-center whitespace-nowrap rounded-full font-semibold transition-[background-color,color,border-color,opacity,box-shadow] duration-200 ease-out-expo disabled:pointer-events-none disabled:opacity-45",
    variants[variant],
    sizes[size],
    className,
  );
}

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    className,
    variant = "primary",
    size = "md",
    loading = false,
    type = "button",
    children,
    disabled,
    style,
    ...props
  },
  ref,
) {
  return (
    <button
      ref={ref}
      type={type}
      className={buttonClassName({ variant, size, className })}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
      style={loading ? { ...style, opacity: 1 } : style}
      {...props}
    >
      {loading ? <LoaderCircle className="size-4 animate-spin" aria-hidden="true" /> : null}
      {children}
    </button>
  );
});

export function IconButton({
  label,
  className,
  variant = "ghost",
  children,
  ...props
}: Omit<ButtonProps, "size" | "children"> & {
  label: string;
  children: React.ReactNode;
}) {
  return (
    <Button
      aria-label={label}
      size="icon"
      variant={variant}
      className={cn("rounded-full", className)}
      {...props}
    >
      {children}
    </Button>
  );
}

export function ButtonLink({
  href,
  variant = "primary",
  size = "md",
  className,
  children,
  ...props
}: React.ComponentProps<typeof Link> & {
  variant?: ButtonVariant;
  size?: ButtonSize;
}) {
  return (
    <Link href={href} className={buttonClassName({ variant, size, className })} {...props}>
      {children}
    </Link>
  );
}
