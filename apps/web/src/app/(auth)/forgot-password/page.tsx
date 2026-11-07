import type { Metadata } from "next";

import { ForgotPasswordForm } from "@/features/auth/forgot-password-form";

export const metadata: Metadata = {
  title: "Reset your password",
  description: "Request a single-use password reset link for Auvyren.",
};

export default function ForgotPasswordPage() {
  return (
    <main id="main-content" tabIndex={-1}>
      <ForgotPasswordForm />
    </main>
  );
}
