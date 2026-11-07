const AUTH_PATHS = new Set([
  "/sign-in",
  "/sign-up",
  "/forgot-password",
  "/reset-password",
]);

export function safeNextPath(value: string | string[] | undefined): string {
  const candidate = Array.isArray(value) ? value[0] : value;
  if (!candidate || !candidate.startsWith("/") || candidate.startsWith("//")) {
    return "/dashboard";
  }
  const pathname = candidate.split("?")[0];
  if (AUTH_PATHS.has(pathname)) return "/dashboard";
  return candidate;
}
