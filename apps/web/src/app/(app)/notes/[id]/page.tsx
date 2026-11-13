import type { Metadata } from "next";

import { getServerUser, serverApiRequest } from "@/lib/api/server";
import { firstName } from "@/features/auth/display";
import type { NoteResponse } from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Note",
  description: "View your note.",
};

export default async function NotePage({
  params,
}: {
  params: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const paramsResolved = await params;
  const noteId = Array.isArray(paramsResolved.id)
    ? paramsResolved.id[0]
    : paramsResolved.id ?? "";

  const user = await getServerUser().catch(() => null);
  const greeting = user ? `Welcome back, ${firstName(user)}.` : "Welcome back.";

  let note;
  try {
    note = await serverApiRequest<NoteResponse>(
      `/knowledge/${encodeURIComponent(noteId)}`,
    );
  } catch {
    note = null;
  }

  if (!note) {
    return (
      <div>
        <header className="max-w-3xl">
          <p className="eyebrow">Note</p>
          <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
            Note not found
          </h1>
        </header>
      </div>
    );
  }

  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Note</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          {greeting}
        </h1>
        <div className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">
              {note.kind}
            </span>
            {note.source_type === "generated" && (
              <span className="text-[10px] font-semibold text-accent-ink bg-accent/10 px-1.5 py-0.5 rounded">
                Generated
              </span>
            )}
          </div>
          <h2 className="mt-1 text-xl font-serif text-foreground font-light">
            {note.title}
          </h2>
          <p className="mt-1 text-xs text-muted">
            {note.tags || "No tags"}
          </p>
        </div>
      </header>

      <div className="mt-8 max-w-3xl">
        <div className="prose prose-lg max-w-none">
          {note.content || ""}
        </div>
      </div>
    </div>
  );
}
