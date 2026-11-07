"use client";

import Link from "next/link";
import { Menu } from "lucide-react";

import { AuvyrenLogo } from "@/components/ui/logo";
import { ButtonLink } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { useAuth } from "@/features/auth/auth-provider";

const navigation = [
  { label: "System", href: "/#system" },
  { label: "Intelligence", href: "/#intelligence" },
  { label: "Principles", href: "/#philosophy" },
  { label: "Privacy", href: "/#privacy" },
];

export function SiteHeader() {
  const { user } = useAuth();

  return (
    <header className="sticky top-0 z-40 border-b border-border/60 bg-background/72 backdrop-blur-xl">
      <div className="container-page flex h-18 items-center justify-between gap-6">
        <Link href="/" aria-label="Auvyren home" className="shrink-0">
          <AuvyrenLogo markClassName="size-7" />
        </Link>

        <nav aria-label="Primary" className="hidden items-center gap-8 lg:flex">
          {navigation.map((item) => (
            <Link
              key={item.label}
              href={item.href}
              className="text-small text-muted transition-colors hover:text-foreground"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 sm:flex">
          {user ? (
            <ButtonLink href="/dashboard" size="sm">
              Open workspace
            </ButtonLink>
          ) : (
            <>
              <ButtonLink href="/sign-in" variant="ghost" size="sm">
                Sign in
              </ButtonLink>
              <ButtonLink href="/sign-up" size="sm">
                Create an account
              </ButtonLink>
            </>
          )}
        </div>

        <Dialog>
          <DialogTrigger
            className="flex size-10 items-center justify-center rounded-full border border-border text-foreground-soft transition-colors hover:bg-white/[0.05] sm:hidden"
            aria-label="Open navigation"
          >
            <Menu className="size-4.5" aria-hidden="true" />
          </DialogTrigger>
          <DialogContent className="max-w-sm">
            <DialogHeader>
              <DialogTitle>Auvyren</DialogTitle>
              <DialogDescription>
                A local-first personal operating system.
              </DialogDescription>
            </DialogHeader>
            <nav aria-label="Mobile" className="flex flex-col">
              {navigation.map((item) => (
                <DialogClose key={item.label} asChild>
                  <Link
                    href={item.href}
                    className="border-b border-border/70 py-3.5 text-body text-foreground-soft transition-colors hover:text-foreground"
                  >
                    {item.label}
                  </Link>
                </DialogClose>
              ))}
              {!user ? (
                <DialogClose asChild>
                  <Link
                    href="/sign-in"
                    className="py-3.5 text-body text-foreground-soft transition-colors hover:text-foreground"
                  >
                    Sign in
                  </Link>
                </DialogClose>
              ) : null}
            </nav>
            <div className="mt-6 flex flex-col gap-2">
              <DialogClose asChild>
                <ButtonLink href={user ? "/dashboard" : "/sign-up"}>
                  {user ? "Open workspace" : "Create an account"}
                </ButtonLink>
              </DialogClose>
              <DialogClose asChild>
                <ButtonLink href="/design" variant="ghost">
                  Design system
                </ButtonLink>
              </DialogClose>
            </div>
          </DialogContent>
        </Dialog>
      </div>
    </header>
  );
}
