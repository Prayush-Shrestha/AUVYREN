"use client";

import { useEffect, useRef, useState } from "react";

import { cn } from "@/lib/cn";

type RevealState = "static" | "hidden" | "shown";

/**
 * Content is visible by default. Only content that starts below the fold is
 * hidden after hydration, then revealed by IntersectionObserver.
 *
 * This keeps the page fully readable without JavaScript and for anyone who
 * prefers reduced motion — the failure mode of a purely animated reveal is
 * invisible content, which is never acceptable.
 */
export function Reveal({
  children,
  className,
  delay = 0,
  y = 18,
}: {
  children: React.ReactNode;
  className?: string;
  delay?: number;
  y?: number;
}) {
  const ref = useRef<HTMLDivElement>(null);
  const [state, setState] = useState<RevealState>("static");

  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    if (node.getBoundingClientRect().top < window.innerHeight * 0.92) return;

    setState("hidden");

    const observer = new IntersectionObserver(
      (entries) => {
        if (entries.some((entry) => entry.isIntersecting)) {
          setState("shown");
          observer.disconnect();
        }
      },
      { rootMargin: "0px 0px -8% 0px" },
    );

    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const hidden = state === "hidden";

  return (
    <div
      ref={ref}
      className={cn(
        "transition-[opacity,transform] duration-700 ease-out-expo motion-reduce:transition-none",
        hidden ? "opacity-0" : "opacity-100",
        className,
      )}
      style={{
        transform: hidden
          ? `translateY(${y}px)`
          : state === "shown"
            ? "translateY(0px)"
            : undefined,
        transitionDelay: state === "shown" ? `${Math.round(delay * 1000)}ms` : undefined,
      }}
    >
      {children}
    </div>
  );
}
