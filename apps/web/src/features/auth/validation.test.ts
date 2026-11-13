import { describe, expect, it } from "vitest";

import {
  validateEmail,
  validateName,
  validatePassword,
} from "@/features/auth/validation";

describe("auth validation", () => {
  it("accepts a sensible name and rejects one-character names", () => {
    expect(validateName("  Ada Lovelace  ")).toBeUndefined();
    expect(validateName("")).toBeUndefined();
    expect(validateName("A")).toBe("Use at least 2 characters.");
    expect(validateName("a".repeat(121))).toBe(
      "Keep your name under 120 characters.",
    );
  });

  it("requires a real-looking email address", () => {
    expect(validateEmail("ada@example.com")).toBeUndefined();
    expect(validateEmail("")).toBe("Enter your email address.");
    expect(validateEmail("not-an-email")).toBe("Enter a valid email address.");
    expect(validateEmail("a@b")).toBe("Enter a valid email address.");
    expect(validateEmail(`${"a".repeat(310)}@example.com`)).toBe(
      "That email address is too long.",
    );
  });

  it("enforces the twelve-character password floor", () => {
    expect(validatePassword("correct horse battery staple")).toBeUndefined();
    expect(validatePassword("")).toBe("Enter your password.");
    expect(validatePassword("short")).toBe("Use at least 12 characters.");
    expect(validatePassword("x".repeat(129))).toBe(
      "Keep your password under 128 characters.",
    );
  });
});
