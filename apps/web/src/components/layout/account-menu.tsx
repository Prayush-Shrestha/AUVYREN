"use client";

import Link from "next/link";
import { LoaderCircle, LogOut, Settings } from "lucide-react";
import { useState } from "react";

import { ButtonLink } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useToast } from "@/components/ui/toast";
import { displayName, initials } from "@/features/auth/display";
import { useAuth } from "@/features/auth/auth-provider";
import { cn } from "@/lib/cn";

export function AccountMenu({ className }: { className?: string }) {
  const { user, signOut } = useAuth();
  const [signingOut, setSigningOut] = useState(false);
  const { toast } = useToast();

  if (!user) {
    return (
      <ButtonLink href="/sign-in" size="sm" className={className}>
        Sign in
      </ButtonLink>
    );
  }

  async function handleSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } catch {
      setSigningOut(false);
      toast({
        tone: "error",
        title: "Could not sign out",
        description: "Check your connection and try again.",
      });
    }
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={`Account menu for ${displayName(user)}`}
          className={cn(
            "flex size-9 items-center justify-center rounded-full border border-border bg-surface text-[11px] font-semibold tracking-[0.04em] text-accent transition-colors hover:border-border-strong hover:bg-surface-elevated focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
            className,
          )}
        >
          {initials(user)}
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent>
        <DropdownMenuLabel>
          <p className="truncate text-small font-semibold text-foreground">
            {displayName(user)}
          </p>
          <p className="mt-0.5 truncate text-xs text-muted">{user.email}</p>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />
        <DropdownMenuItem asChild>
          <Link href="/settings">
            <Settings className="size-4 text-muted" aria-hidden="true" />
            Account settings
          </Link>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          disabled={signingOut}
          onSelect={(event) => {
            event.preventDefault();
            void handleSignOut();
          }}
        >
          {signingOut ? (
            <LoaderCircle className="size-4 animate-spin text-muted" aria-hidden="true" />
          ) : (
            <LogOut className="size-4 text-muted" aria-hidden="true" />
          )}
          {signingOut ? "Signing out…" : "Sign out"}
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
