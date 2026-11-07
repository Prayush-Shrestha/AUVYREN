"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  loginRequest,
  logoutRequest,
  registerRequest,
  updateProfileRequest,
  type SignUpInput,
  type UpdateProfileInput,
} from "@/lib/api/auth";
import { ApiError, AUTH_EXPIRED_EVENT, clearCsrfToken } from "@/lib/api/client";
import type { AuthUser } from "@/lib/api/types";

const AUTH_PATHS = new Set([
  "/sign-in",
  "/sign-up",
  "/forgot-password",
  "/reset-password",
]);

interface AuthContextValue {
  user: AuthUser | null;
  status: "authenticated" | "anonymous";
  signIn: (input: { email: string; password: string }) => Promise<AuthUser>;
  signUp: (input: SignUpInput) => Promise<AuthUser>;
  signOut: () => Promise<void>;
  updateProfile: (input: UpdateProfileInput) => Promise<AuthUser>;
  markSessionEnded: (redirectTo?: string) => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({
  initialUser,
  children,
}: {
  initialUser: AuthUser | null;
  children: React.ReactNode;
}) {
  const [user, setUser] = useState<AuthUser | null>(initialUser);
  const router = useRouter();
  const pathname = usePathname();

  const markSessionEnded = useCallback(
    (redirectTo?: string) => {
      setUser(null);
      clearCsrfToken();
      if (redirectTo) {
        router.replace(redirectTo);
        router.refresh();
      }
    },
    [router],
  );

  useEffect(() => {
    function handleExpired() {
      if (AUTH_PATHS.has(pathname)) {
        setUser(null);
        return;
      }
      const next =
        typeof window === "undefined"
          ? pathname
          : `${pathname}${window.location.search}`;
      markSessionEnded(
        `/sign-in?reason=expired&next=${encodeURIComponent(next)}`,
      );
    }

    window.addEventListener(AUTH_EXPIRED_EVENT, handleExpired);
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, handleExpired);
  }, [markSessionEnded, pathname]);

  const signIn = useCallback(
    async (input: { email: string; password: string }) => {
      const response = await loginRequest(input);
      setUser(response.user);
      return response.user;
    },
    [],
  );

  const signUp = useCallback(async (input: SignUpInput) => {
    const response = await registerRequest(input);
    setUser(response.user);
    return response.user;
  }, []);

  const signOut = useCallback(async () => {
    try {
      await logoutRequest();
    } catch (error) {
      if (!(error instanceof ApiError && error.status === 401)) {
        throw error;
      }
    }
    setUser(null);
    clearCsrfToken();
    router.replace("/sign-in?reason=signed_out");
    router.refresh();
  }, [router]);

  const updateProfile = useCallback(async (input: UpdateProfileInput) => {
    const nextUser = await updateProfileRequest(input);
    setUser(nextUser);
    return nextUser;
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      status: user ? "authenticated" : "anonymous",
      signIn,
      signUp,
      signOut,
      updateProfile,
      markSessionEnded,
    }),
    [markSessionEnded, signIn, signOut, signUp, updateProfile, user],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used inside AuthProvider");
  }
  return context;
}
