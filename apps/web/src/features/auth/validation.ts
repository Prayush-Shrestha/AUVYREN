export function validateName(value: string): string | undefined {
  const name = value.trim();
  if (!name) return undefined;
  if (name.length < 2) return "Use at least 2 characters.";
  if (name.length > 120) return "Keep your name under 120 characters.";
  return undefined;
}

export function validateEmail(value: string): string | undefined {
  const email = value.trim();
  if (!email) return "Enter your email address.";
  if (email.length > 320) return "That email address is too long.";
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(email)) {
    return "Enter a valid email address.";
  }
  return undefined;
}

export function validatePassword(value: string): string | undefined {
  if (!value) return "Enter your password.";
  if (value.length < 12) return "Use at least 12 characters.";
  if (value.length > 128) return "Keep your password under 128 characters.";
  return undefined;
}
