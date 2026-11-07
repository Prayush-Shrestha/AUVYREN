import { clsx, type ClassValue } from "clsx";
import { extendTailwindMerge } from "tailwind-merge";

/**
 * The Auvyren type scale lives in the `--text-*` theme namespace. Tailwind
 * Merge cannot infer custom size names, and would otherwise treat classes
 * such as `text-small` as text colours — silently stripping `text-accent-ink`
 * from primary buttons. Register the scale explicitly.
 */
const twMerge = extendTailwindMerge({
  extend: {
    theme: {
      text: [
        "display-2xl",
        "display-xl",
        "display-lg",
        "display-md",
        "display-sm",
        "title-lg",
        "title-md",
        "body-lg",
        "body",
        "small",
        "micro",
      ],
      animate: [
        "fade-up",
        "fade-in",
        "shimmer",
        "drift",
        "orbit",
        "pulse-soft",
        "overlay-in",
        "overlay-out",
        "panel-in",
        "panel-out",
        "toast-in",
        "toast-out",
      ],
    },
  },
});

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
