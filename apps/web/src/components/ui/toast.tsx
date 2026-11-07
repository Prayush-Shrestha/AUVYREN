"use client";

import * as ToastPrimitive from "@radix-ui/react-toast";
import { CircleAlert, CircleCheck, Info, X } from "lucide-react";
import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";

import { cn } from "@/lib/cn";

type ToastTone = "neutral" | "success" | "error" | "info";

interface ToastOptions {
  title: string;
  description?: string;
  tone?: ToastTone;
  duration?: number;
}

interface ToastItem extends ToastOptions {
  id: number;
}

interface ToastContextValue {
  toast: (options: ToastOptions) => void;
}

const ToastContext = createContext<ToastContextValue | null>(null);

const toneConfig: Record<
  ToastTone,
  { icon: typeof Info; className: string }
> = {
  neutral: { icon: Info, className: "text-muted" },
  success: { icon: CircleCheck, className: "text-success" },
  error: { icon: CircleAlert, className: "text-danger" },
  info: { icon: Info, className: "text-info" },
};

export function ToastProvider({
  children,
  duration = 5000,
}: {
  children: React.ReactNode;
  duration?: number;
}) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const counter = useRef(0);

  const remove = useCallback((id: number) => {
    setToasts((current) => current.filter((item) => item.id !== id));
  }, []);

  const toast = useCallback((options: ToastOptions) => {
    counter.current += 1;
    setToasts((current) => [...current, { ...options, id: counter.current }]);
  }, []);

  const value = useMemo(() => ({ toast }), [toast]);

  return (
    <ToastPrimitive.Provider swipeDirection="right">
      <ToastContext.Provider value={value}>
        {children}
        {toasts.map((item) => {
          const tone = item.tone ?? "neutral";
          const config = toneConfig[tone];
          const Icon = config.icon;

          return (
            <ToastPrimitive.Root
              key={item.id}
              duration={item.duration ?? duration}
              onOpenChange={(open) => {
                if (!open) remove(item.id);
              }}
              className="pointer-events-auto flex w-full items-start gap-3 rounded-xl border border-border-strong bg-surface-elevated p-4 shadow-panel data-[state=open]:animate-toast-in data-[state=closed]:animate-toast-out"
            >
              <Icon className={cn("mt-0.5 size-4 shrink-0", config.className)} aria-hidden="true" />
              <div className="min-w-0 flex-1">
                <ToastPrimitive.Title className="text-small font-semibold text-foreground">
                  {item.title}
                </ToastPrimitive.Title>
                {item.description ? (
                  <ToastPrimitive.Description className="mt-0.5 text-xs leading-relaxed text-muted">
                    {item.description}
                  </ToastPrimitive.Description>
                ) : null}
              </div>
              <ToastPrimitive.Close
                className="-mr-1 -mt-1 flex size-7 shrink-0 items-center justify-center rounded-full text-muted transition-colors hover:bg-white/[0.06] hover:text-foreground"
                aria-label="Dismiss notification"
              >
                <X className="size-3.5" aria-hidden="true" />
              </ToastPrimitive.Close>
            </ToastPrimitive.Root>
          );
        })}
        <ToastPrimitive.Viewport className="fixed bottom-0 right-0 z-[100] flex w-full max-w-sm flex-col gap-2 p-4 outline-none" />
      </ToastContext.Provider>
    </ToastPrimitive.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);

  if (!context) {
    throw new Error("useToast must be used inside ToastProvider");
  }

  return context;
}
