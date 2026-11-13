import type { Metadata } from "next";
import Link from "next/link";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/field";
import { EmptyState, InlineMessage } from "@/components/ui/states";
import { firstName } from "@/features/auth/display";
import { getServerUser, serverApiRequest } from "@/lib/api/server";
import type {
  KnowledgeSearchResponse,
  NoteListResponse,
  NoteResponse,
} from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Knowledge Library",
  description: "Search your notes and knowledge.",
};

export default async function KnowledgePage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const params = await searchParams;
  const rawQuery = Array.isArray(params.q) ? params.q[0] : params.q;
  const query = rawQuery?.trim() ?? "";

  const user = await getServerUser().catch(() => null);
  const greeting = user ? `Welcome back, ${firstName(user)}.` : "Welcome back.";

  let notes: NoteResponse[] = [];
  let total = 0;
  let failed = false;
  try {
    if (query) {
      const response = await serverApiRequest<KnowledgeSearchResponse>(
        "/knowledge/search",
        { method: "POST", body: { q: query, limit: 50 } },
      );
      notes = response.notes;
      total = response.total;
    } else {
      const response = await serverApiRequest<NoteListResponse>(
        "/knowledge?limit=50&offset=0",
      );
      notes = response.notes;
      total = response.notes.length;
    }
  } catch {
    failed = true;
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

      <form
        action="/knowledge"
        method="get"
        role="search"
        className="mt-8 flex max-w-3xl gap-2"
      >
        <label htmlFor="knowledge-search" className="sr-only">
          Search your notes
        </label>
        <Input
          id="knowledge-search"
          name="q"
          type="search"
          defaultValue={query}
          placeholder="Search your notes…"
          className="flex-1"
        />
        <Button type="submit" variant="secondary">
          <Search className="size-4" aria-hidden="true" />
          Search
        </Button>
      </form>

      <div className="mt-6 max-w-3xl" aria-live="polite">
        {failed ? (
          <InlineMessage tone="danger" title="Search unavailable">
            Your notes could not be loaded. Refresh the page to try again.
          </InlineMessage>
        ) : notes.length === 0 ? (
          <EmptyState
            icon={Search}
            title={query ? "No matching notes" : "Your library is quiet"}
            description={
              query
                ? `Nothing matched “${query}”. Try a shorter phrase or a different kind of note.`
                : "Notes you write will gather here. Capture a thought, a decision or a review to begin."
            }
            compact
          />
        ) : (
          <>
            <p className="text-xs text-muted">
              {total} result{total !== 1 ? "s" : ""}
              {query ? ` for “${query}”` : ""}
            </p>
            <ul className="mt-3 grid gap-3">
              {notes.map((note) => (
                <li
                  key={note.id}
                  className="rounded-xl border border-border bg-surface p-4"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[10px] font-semibold uppercase tracking-[0.1em] text-muted">
                          {note.kind}
                        </span>
                        {note.source_type === "generated" ? (
                          <span className="rounded bg-accent/10 px-1.5 py-0.5 text-[10px] font-semibold text-accent-ink">
                            Generated
                          </span>
                        ) : null}
                      </div>
                      <h2 className="mt-1 truncate text-sm font-semibold text-foreground">
                        <Link
                          href={`/notes/${note.id}`}
                          className="underline decoration-transparent underline-offset-4 transition-colors hover:decoration-border-strong"
                        >
                          {note.title}
                        </Link>
                      </h2>
                      {note.tags ? (
                        <p className="mt-1 text-xs text-muted">{note.tags}</p>
                      ) : null}
                    </div>
                    <Link
                      href={`/notes/${note.id}`}
                      className="shrink-0 text-xs text-muted underline decoration-border-strong underline-offset-4 hover:text-accent"
                    >
                      Open
                    </Link>
                  </div>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
    </div>
  );
}
