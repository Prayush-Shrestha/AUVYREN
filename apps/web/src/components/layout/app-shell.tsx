"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";
import {
  BookOpen,
  CalendarDays,
  FolderKanban,
  LayoutDashboard,
  ListTodo,
  Menu,
  NotebookPen,
  Palette,
  Repeat2,
  Settings,
  Sparkles,
  Target,
} from "lucide-react";

import { AccountMenu } from "@/components/layout/account-menu";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { AuvyrenLogo, AuvyrenMark } from "@/components/ui/logo";
import { displayName, initials } from "@/features/auth/display";
import { useAuth } from "@/features/auth/auth-provider";
import { cn } from "@/lib/cn";

interface NavItem {
  label: string;
  icon: typeof LayoutDashboard;
  href?: string;
  phase?: string;
}

const primaryNav: NavItem[] = [
  { label: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { label: "Tasks", icon: ListTodo, phase: "Phase 3" },
  { label: "Goals", icon: Target, phase: "Phase 3" },
  { label: "Projects", icon: FolderKanban, phase: "Phase 3" },
  { label: "Habits", icon: Repeat2, phase: "Phase 3" },
  { label: "Calendar", icon: CalendarDays, phase: "Phase 3" },
  { label: "Intelligence", href: "/intelligence", icon: Sparkles },
  { label: "Notes", href: "/notes", icon: NotebookPen },
  { label: "Knowledge", href: "/knowledge", icon: BookOpen },
];

const secondaryNav: NavItem[] = [
  { label: "Settings", href: "/settings", icon: Settings },
  { label: "Design system", href: "/design", icon: Palette },
];

function isActive(pathname: string, href?: string) {
  if (!href) return false;
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavLink({
  item,
  pathname,
  onNavigate,
}: {
  item: NavItem;
  pathname: string;
  onNavigate?: () => void;
}) {
  const Icon = item.icon;

  if (!item.href) {
    return (
      <div
        aria-disabled="true"
        className="flex cursor-default items-center gap-3 rounded-xl px-3 py-2.5 text-small text-muted/65"
      >
        <Icon className="size-4 shrink-0" aria-hidden="true" />
        <span className="min-w-0 flex-1">{item.label}</span>
        <span className="text-[9px] font-semibold uppercase tracking-[0.1em] text-faint">
          {item.phase}
        </span>
      </div>
    );
  }

  const active = isActive(pathname, item.href);
  const content = (
    <>
      <Icon
        className={cn("size-4 shrink-0", active ? "text-accent" : "text-muted")}
        aria-hidden="true"
      />
      <span className="min-w-0 flex-1">{item.label}</span>
    </>
  );

  const className = cn(
    "flex items-center gap-3 rounded-xl border px-3 py-2.5 text-small transition-colors",
    active
      ? "border-border bg-surface-elevated text-foreground shadow-soft"
      : "border-transparent text-muted hover:bg-white/[0.04] hover:text-foreground",
  );

  if (onNavigate) {
    return (
      <DialogClose asChild>
        <Link
          href={item.href}
          onClick={onNavigate}
          className={className}
          aria-current={active ? "page" : undefined}
        >
          {content}
        </Link>
      </DialogClose>
    );
  }

  return (
    <Link
      href={item.href}
      className={className}
      aria-current={active ? "page" : undefined}
    >
      {content}
    </Link>
  );
}

function AccountIdentity() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <Link
      href="/settings"
      className="mt-6 flex items-center gap-3 rounded-xl border border-border bg-background/45 p-3 transition-colors hover:border-border-strong hover:bg-background/70"
    >
      <span className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-[11px] font-semibold text-accent">
        {initials(user)}
      </span>
      <span className="min-w-0 flex-1">
        <span className="block truncate text-small font-semibold text-foreground-soft">
          {displayName(user)}
        </span>
        <span className="mt-0.5 block truncate text-[11px] text-muted">{user.email}</span>
      </span>
      <span className="size-1.5 shrink-0 rounded-full bg-accent" aria-hidden="true" />
    </Link>
  );
}

function NavGroups({ pathname, onNavigate }: { pathname: string; onNavigate?: () => void }) {
  return (
    <>
      <nav aria-label="Workspace" className="flex-1">
        <p className="mb-2 px-3 text-[9px] font-semibold uppercase tracking-[0.18em] text-faint">
          Workspace
        </p>
        <div className="space-y-1">
          {primaryNav.map((item) => (
            <NavLink
              key={item.label}
              item={item}
              pathname={pathname}
              onNavigate={onNavigate}
            />
          ))}
        </div>
        <div className="my-5 h-px bg-border/70" />
        <p className="mb-2 px-3 text-[9px] font-semibold uppercase tracking-[0.18em] text-faint">
          System
        </p>
        <div className="space-y-1">
          {secondaryNav.map((item) => (
            <NavLink
              key={item.label}
              item={item}
              pathname={pathname}
              onNavigate={onNavigate}
            />
          ))}
        </div>
      </nav>

      <AccountIdentity />
    </>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { user } = useAuth();
  const current =
    [...primaryNav, ...secondaryNav].find((item) => isActive(pathname, item.href))?.label ??
    "Workspace";

  return (
    <div className="min-h-dvh bg-background">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 flex-col border-r border-border/70 bg-background-secondary/45 backdrop-blur lg:flex">
        <div className="flex h-18 shrink-0 items-center border-b border-border/60 px-5">
          <Link href="/" aria-label="Auvyren home">
            <AuvyrenLogo />
          </Link>
        </div>
        <div className="flex flex-1 flex-col overflow-y-auto p-3">
          <NavGroups pathname={pathname} />
        </div>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between gap-4 border-b border-border/60 bg-background/80 px-4 backdrop-blur-xl sm:px-6 lg:hidden">
          <div className="flex items-center gap-3">
            <Dialog open={mobileNavOpen} onOpenChange={setMobileNavOpen}>
              <DialogTrigger
                className="flex size-9 items-center justify-center rounded-full border border-border text-foreground-soft transition-colors hover:bg-white/[0.05]"
                aria-label="Open workspace navigation"
              >
                <Menu className="size-4" aria-hidden="true" />
              </DialogTrigger>
              <DialogContent className="max-h-[85dvh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-3">
                    <AuvyrenMark className="size-6" />
                    Workspace
                  </DialogTitle>
                  <DialogDescription>Move through your workspace.</DialogDescription>
                </DialogHeader>
                <div className="flex min-h-[60dvh] flex-col">
                  <NavGroups
                    pathname={pathname}
                    onNavigate={() => setMobileNavOpen(false)}
                  />
                </div>
              </DialogContent>
            </Dialog>

            <Link href="/" aria-label="Auvyren home">
              <AuvyrenLogo markClassName="size-6" wordmarkClassName="hidden sm:inline" />
            </Link>
          </div>

          <AccountMenu />
        </header>

        <div className="hidden h-18 items-center justify-between border-b border-border/60 px-8 lg:flex">
          <div>
            <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-faint">
              Auvyren / {current}
            </p>
            {user ? (
              <p className="mt-1 text-xs text-muted">Signed in as {displayName(user)}</p>
            ) : null}
          </div>
          <div className="flex items-center gap-4">
            <Badge tone="success" dot>
              Session active
            </Badge>
            <Link
              href="/"
              className="text-xs text-muted transition-colors hover:text-foreground"
            >
              Back to site
            </Link>
            <AccountMenu />
          </div>
        </div>

        <main
          id="main-content"
          tabIndex={-1}
          className="mx-auto w-full max-w-[1180px] px-4 py-7 sm:px-6 sm:py-9 lg:px-10 lg:py-10"
        >
          {children}
        </main>
      </div>
    </div>
  );
}
