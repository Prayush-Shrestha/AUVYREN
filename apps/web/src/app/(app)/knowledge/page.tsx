import type { Metadata } from "next";

import { getServerUser } from "@/lib/api/server";
import { firstName } from "@/features/auth/display";
import { searchNotesRequest } from "@/lib/api/intelligence";
import type { NoteResponse } from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Knowledge Library",
  description: "Search your notes and knowledge.",
};

export default async function KnowledgePage() {
  const user = await getServerUser().catch(() => null);
  const greeting = user ? `Welcome back, ${firstName(user)}.` : "Welcome back.";

  let notes: NoteResponse[] = [];
  let total = 0;
  const query = "";
  try {
    const response = await searchNotesRequest({
      q: "",
      limit: 50,
    });
    notes = response.notes;
    total = response.total;
  } catch {
    notes = [];
  }

  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Knowledge Library</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          {greeting}
        </h1>
        <p className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          Search across all your notes, journal entries, decisions, and reviews.
        </p>
      </header>

      <div className="mt-8 max-w-3xl">
        <div className="flex gap-2">
          <input
            type="text"
            placeholder="Search your notes…"
            className="w-full rounded-xl border border-border-control bg-background-secondary/80 text-foreground shadow-[0_1px_0_rgba(255,255,255,0.025)_inset] transition-[border-color,background-color] duration-200 placeholder:text-faint hover:border-faint disabled:cursor-not-allowed disabled:border-border disabled:bg-surface/40 disabled:text-muted disabled:opacity-60 px-3.5 h-11 text-sm"
            defaultValue={query}
          />
          <button className="px-4 h-11 rounded-xl border border-border bg-surface-elevated/70 text-foreground hover:bg-surface-hover">
            Search
          </button>
        </div>
      </div>

      <div className="mt-6">
        <p className="text-xs text-muted">
          {total} result{total !== 1 ? "s" : ""}
        </p>
        <div className="mt-2 grid gap-3">
          {notes.length === 0 ? (
            <p className="text-xs text-muted">
              No notes found.
            </p>
          ) : (
            notes.map((note) => (
              <div
                key={note.id}
                className="rounded-xl border border-border bg-surface p-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                        {note.kind}
                      </span>
                      {note.source_type === "generated" && (
                        <span className="text-[10px] font-semibold text-accent-ink bg-accent/10 px-1.5 py-0.5 rounded">
                          Generated
                        </span>
                      )}
                    </div>
                    <h3 className="mt-1 text-sm font-semibold text-foreground">
                      {note.title}
                    </h3>
                    {note.tags && (
                      <p className="mt-1 text-xs text-muted">
                        {note.tags}
                      </p>
                    )}
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
    </div>
  );
}
