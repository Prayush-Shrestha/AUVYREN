import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { SignUpForm } from "@/features/auth/sign-up-form";
import { getServerUser } from "@/lib/api/server";

export const metadata: Metadata = {
  title: "Create your space",
  description: "Create an Auvyren account in a quieter, local-first workspace.",
};

export default async function SignUpPage() {
  const user = await getServerUser().catch(() => null);

  if (user) {
    redirect("/dashboard");
  }

  return (
    <main id="main-content" tabIndex={-1}>
      <SignUpForm />
    </main>
  );
}
