import type { AuthUser } from "@/lib/api/types";

export function displayName(user: AuthUser | null): string {
  if (!user) return "Your account";
  if (user.full_name?.trim()) return user.full_name.trim();
  return user.email.split("@")[0];
}

export function firstName(user: AuthUser | null): string {
  const name = displayName(user);
  return name.split(/\s+/)[0] ?? name;
}

export function initials(user: AuthUser | null): string {
  if (!user) return "A";
  const parts = displayName(user).split(/\s+/).filter(Boolean);
  if (parts.length === 0) return user.email.slice(0, 1).toUpperCase();
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
}
