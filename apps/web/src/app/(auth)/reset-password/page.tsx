import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { ResetPasswordForm } from "@/features/auth/reset-password-form";
import { getServerUser } from "@/lib/api/server";

export const metadata: Metadata = {
  title: "Choose a new password",
  description: "Complete a single-use Auvyren password reset.",
};

export default async function ResetPasswordPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const token = Array.isArray(params.token) ? params.token[0] : params.token;
  const user = await getServerUser().catch(() => null);

  if (user) {
    redirect("/dashboard");
  }

  return (
    <main id="main-content" tabIndex={-1}>
      <ResetPasswordForm token={token} />
    </main>
  );
}
