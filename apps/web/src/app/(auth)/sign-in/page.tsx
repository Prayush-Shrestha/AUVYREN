import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { SignInForm } from "@/features/auth/sign-in-form";
import { safeNextPath } from "@/features/auth/navigation";
import { getServerUser } from "@/lib/api/server";

export const metadata: Metadata = {
  title: "Sign in",
  description: "Return to your Auvyren workspace.",
};

export default async function SignInPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const nextPath = safeNextPath(params.next);
  const reason = Array.isArray(params.reason) ? params.reason[0] : params.reason;
  const user = await getServerUser().catch(() => null);

  if (user) {
    redirect(nextPath);
  }

  return (
    <main id="main-content" tabIndex={-1}>
      <SignInForm
        nextPath={nextPath}
        reason={reason}
        resetSuccess={reason === "reset"}
      />
    </main>
  );
}
