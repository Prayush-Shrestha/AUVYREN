import { describe, expect, it } from "vitest";

import { displayName, firstName, initials } from "@/features/auth/display";
import type { AuthUser } from "@/lib/api/types";

function user(overrides: Partial<AuthUser> = {}): AuthUser {
  return {
    id: "1",
    email: "ada@example.com",
    full_name: null,
    is_active: true,
    email_verified: false,
    last_login_at: null,
    created_at: "2026-01-01T00:00:00Z",
    settings: { timezone: "UTC", week_starts_on: 1 },
    ...overrides,
  };
}

describe("auth display helpers", () => {
  it("falls back to a readable label without a user", () => {
    expect(displayName(null)).toBe("Your account");
    expect(initials(null)).toBe("A");
  });

  it("prefers a trimmed full name", () => {
    expect(displayName(user({ full_name: "  Ada Lovelace " }))).toBe(
      "Ada Lovelace",
    );
    expect(firstName(user({ full_name: "Ada Lovelace" }))).toBe("Ada");
  });

  it("uses the email local part when no name is set", () => {
    expect(displayName(user())).toBe("ada");
    expect(initials(user())).toBe("AD");
  });

  it("builds one- and two-letter initials", () => {
    expect(initials(user({ full_name: "Ada" }))).toBe("AD");
    expect(initials(user({ full_name: "Ada Byron Lovelace" }))).toBe("AL");
  });
});
