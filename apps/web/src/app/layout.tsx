import type { Metadata, Viewport } from "next";
import "@fontsource-variable/manrope";
import "@fontsource-variable/newsreader";
import "@fontsource-variable/newsreader/wght-italic.css";

import "./globals.css";

import { Providers } from "@/components/providers";

export const metadata: Metadata = {
  title: {
    default: "Auvyren — A local-first personal operating system",
    template: "%s — Auvyren",
  },
  description:
    "Auvyren is a quiet, local-first personal operating system for planning, practice and reflection. Deterministic insight first; AI only when you ask.",
  applicationName: "Auvyren",
  openGraph: {
    title: "Auvyren — A local-first personal operating system",
    description:
      "Make room for what matters. Plan, practise and reflect in one quiet system.",
    siteName: "Auvyren",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Auvyren — A local-first personal operating system",
    description:
      "Make room for what matters. Plan, practise and reflect in one quiet system.",
  },
};

export const viewport: Viewport = {
  themeColor: "#0c100d",
  colorScheme: "dark",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-dvh bg-background text-foreground antialiased">
        <a
          href="#main-content"
          className="sr-only focus:not-sr-only focus:fixed focus:left-4 focus:top-4 focus:z-[200] focus:rounded-full focus:bg-accent focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-accent-ink"
        >
          Skip to content
        </a>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
