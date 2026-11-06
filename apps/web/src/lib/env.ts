const apiBaseUrl =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const env = {
  apiBaseUrl: apiBaseUrl.replace(/\/$/, ""),
  apiOrigin: new URL(apiBaseUrl).origin,
} as const;
