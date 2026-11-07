"use client";

import { AuthProvider } from "@/features/auth/auth-provider";
import type { AuthUser } from "@/lib/api/types";
import { ToastProvider } from "@/components/ui/toast";
import { TooltipProvider } from "@/components/ui/tooltip";

export function Providers({
  initialUser,
  children,
}: {
  initialUser: AuthUser | null;
  children: React.ReactNode;
}) {
  return (
    <TooltipProvider>
      <ToastProvider>
        <AuthProvider initialUser={initialUser}>{children}</AuthProvider>
      </ToastProvider>
    </TooltipProvider>
  );
}
