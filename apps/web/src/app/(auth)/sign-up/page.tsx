import type { Metadata } from "next";

import { SignUpForm } from "@/features/auth/sign-up-form";

export const metadata: Metadata = {
  title: "Create your space",
  description: "Create an Auvyren account in a quieter, local-first workspace.",
};

export default function SignUpPage() {
  return (
    <main id="main-content" tabIndex={-1}>
      <SignUpForm />
    </main>
  );
}
