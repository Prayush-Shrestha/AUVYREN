import Link from "next/link";

import { AuvyrenLogo } from "@/components/ui/logo";

const groups = [
  {
    title: "Explore",
    links: [
      { label: "The system", href: "/#system" },
      { label: "Quiet intelligence", href: "/#intelligence" },
      { label: "Principles", href: "/#philosophy" },
      { label: "Privacy", href: "/#privacy" },
    ],
  },
  {
    title: "Product",
    links: [
      { label: "Your workspace", href: "/dashboard" },
      { label: "Sign in", href: "/sign-in" },
      { label: "Create an account", href: "/sign-up" },
      { label: "Design system", href: "/design" },
    ],
  },
];

export function SiteFooter() {
  return (
    <footer className="border-t border-border/70">
      <div className="container-page py-14 sm:py-18">
        <div className="grid gap-12 lg:grid-cols-[1.2fr_1fr]">
          <div>
            <Link href="/" aria-label="Auvyren home" className="inline-flex">
              <AuvyrenLogo />
            </Link>
            <p className="mt-5 max-w-sm text-body leading-relaxed text-muted">
              A local-first personal operating system for clear thinking and intentional
              action.
            </p>
            <p className="mt-6 flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
              <span className="size-1.5 rounded-full bg-accent" aria-hidden="true" />
              Foundation · Accounts secured with Argon2id
            </p>
          </div>

          <div className="grid grid-cols-2 gap-8 sm:grid-cols-3">
            {groups.map((group) => (
              <div key={group.title}>
                <h2 className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                  {group.title}
                </h2>
                <ul className="mt-4 space-y-2.5">
                  {group.links.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="text-small text-muted transition-colors hover:text-foreground"
                      >
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            <div>
              <h2 className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
                The promise
              </h2>
              <ul className="mt-4 space-y-2.5 text-small text-muted">
                <li>Local-first</li>
                <li>Deterministic first</li>
                <li>AI by consent</li>
                <li>No training on your data</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="mt-14 flex flex-col gap-3 border-t border-border/70 pt-6 text-xs text-faint sm:flex-row sm:items-center sm:justify-between">
          <p>© 2026 Auvyren. Built quietly.</p>
          <p>Think clearly. Move intentionally.</p>
        </div>
      </div>
    </footer>
  );
}
