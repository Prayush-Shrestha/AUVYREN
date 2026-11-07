import { headers } from "next/headers";
import { redirect } from "next/navigation";

import { AppShell } from "@/components/layout/app-shell";
import { getServerUser } from "@/lib/api/server";

export default async function WorkspaceLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const user = await getServerUser();

  if (!user) {
    const requestHeaders = await headers();
    const requestedPath = requestHeaders.get("x-auvyren-pathname") ?? "/dashboard";
    redirect(
      `/sign-in?reason=expired&next=${encodeURIComponent(requestedPath)}`,
    );
  }

  return <AppShell>{children}</AppShell>;
}
