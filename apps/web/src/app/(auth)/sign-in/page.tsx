import type { Metadata } from "next";

import { SignInForm } from "@/features/auth/sign-in-form";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Return to your Auvyren workspace.",
};

export default function SignInPage() {
  return (
    <main id="main-content" tabIndex={-1}>
      <SignInForm />
    </main>
  );
}
