import type { Metadata } from "next";

import { getServerUser } from "@/lib/api/server";
import { firstName } from "@/features/auth/display";
import { listNotesRequest } from "@/lib/api/intelligence";
import type { NoteResponse } from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Notes",
  description: "Your notes and knowledge library.",
};

export default async function NotesPage() {
  const user = await getServerUser().catch(() => null);
  const greeting = user ? `Welcome back, ${firstName(user)}.` : "Welcome back.";

  let notes: NoteResponse[] = [];
  try {
    const response = await listNotesRequest({
      limit: 50,
      offset: 0,
    });
    notes = response.notes;
  } catch {
    notes = [];
  }

  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Notes</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          {greeting}
        </h1>
        <p className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          Your notes, journal entries, decisions, and reviews. All notes are
          private to your account and stored securely on your server.
        </p>
      </header>

      <div className="mt-8 grid gap-4">
        {notes.length === 0 ? (
          <div className="col-span-full">
            <p className="text-xs text-muted">
              No notes yet. Create your first note to get started.
            </p>
          </div>
        ) : (
          notes.map((note) => (
            <div
              key={note.id}
              className="rounded-xl border border-border bg-surface p-4"
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
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
                  <h2 className="mt-1 text-sm font-semibold text-foreground">
                    {note.title}
                  </h2>
                  <p className="mt-1 text-xs text-muted">
                    {note.tags || "No tags"}
                  </p>
                </div>
                <a
                  href={`/notes/${note.id}`}
                  className="text-xs text-muted underline decoration-border-strong underline-offset-4 hover:text-accent"
                >
                  Open
                </a>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
