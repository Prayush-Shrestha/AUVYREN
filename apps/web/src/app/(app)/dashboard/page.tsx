import type { Metadata } from "next";
import {
  CalendarDays,
  Crosshair,
  FolderKanban,
  NotebookPen,
  Repeat2,
  Sunrise,
  Target,
} from "lucide-react";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { ButtonLink } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { EmptyState, InlineMessage } from "@/components/ui/states";
import { firstName } from "@/features/auth/display";
import { getServerUser } from "@/lib/api/server";

export const metadata: Metadata = {
  title: "Dashboard",
  description: "Your Auvyren workspace and its honest empty states.",
};

const upcoming = [
  {
    label: "Goals",
    copy: "Direction with a measurable outcome and a visible next milestone.",
    icon: Target,
    phase: "Phase 3",
  },
  {
    label: "Calendar",
    copy: "Deadlines, milestones and events woven into one calm view of time.",
    icon: CalendarDays,
    phase: "Phase 3",
  },
  {
    label: "Notes",
    copy: "Journal entries, decision records and reviews with links back to the work.",
    icon: NotebookPen,
    phase: "Phase 5",
  },
];

export default async function DashboardPage() {
  const user = await getServerUser().catch(() => null);
  const greeting = user ? `Welcome back, ${firstName(user)}.` : "Welcome back.";

  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Your workspace</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          {greeting}
        </h1>
        <p className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          An honest, empty beginning. Tasks, goals and calendar data arrive in Phase 3 —
          until then, nothing here is invented.
        </p>
      </header>

      <div className="mt-7">
        <InlineMessage
          tone="info"
          title="Your account is ready. Your day arrives in Phase 3."
          action={
            <ButtonLink href="/settings" variant="secondary" size="sm">
              Account settings
            </ButtonLink>
          }
        >
          Tasks, goals, habits and calendar data are intentionally absent — there is no
          sample data anywhere in this build.
        </InlineMessage>
      </div>

      <div className="mt-5 grid gap-4 xl:grid-cols-[1.45fr_1fr]">
        <Card className="flex min-h-[26rem] flex-col">
          <CardHeader
            eyebrow="Today"
            title="A clear page, for now."
            description="Your tasks, focus block and events will gather here once the productivity modules are connected."
            action={<Badge tone="accent">Phase 3</Badge>}
          />
          <CardBody className="flex flex-1 flex-col pt-5">
            <EmptyState
              icon={Sunrise}
              title="Nothing is asking for you yet."
              description="This is an honest empty state. There are no invented metrics, sample tasks or borrowed urgency."
              action={
                <ButtonLink href="/design" variant="ghost" size="sm">
                  Explore the component system
                </ButtonLink>
              }
              className="flex-1"
            />
          </CardBody>
        </Card>

        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-1">
          <Card>
            <CardHeader
              eyebrow="Focus"
              title="One thing at a time."
              action={<Badge tone="outline">Phase 3</Badge>}
            />
            <CardBody className="pt-3">
              <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-background/40 p-4">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                  <Crosshair className="size-4" aria-hidden="true" />
                </span>
                <p className="text-small leading-relaxed text-muted">
                  The deterministic engine will suggest a small set of priorities — with
                  the reasons attached, never an unexplained score.
                </p>
              </div>
            </CardBody>
          </Card>

          <Card>
            <CardHeader
              eyebrow="Practice"
              title="Consistency, not streaks."
              action={<Badge tone="outline">Phase 3</Badge>}
            />
            <CardBody className="pt-3">
              <div className="flex items-start gap-3 rounded-xl border border-border/70 bg-background/40 p-4">
                <span className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                  <Repeat2 className="size-4" aria-hidden="true" />
                </span>
                <p className="text-small leading-relaxed text-muted">
                  Habits will be measured from real completion logs, with missed days shown
                  plainly instead of hidden behind a vague score.
                </p>
              </div>
            </CardBody>
          </Card>
        </div>
      </div>

      <section className="mt-8" aria-labelledby="upcoming-heading">
        <div className="flex items-end justify-between gap-4">
          <div>
            <p className="text-[10px] font-semibold uppercase tracking-[0.16em] text-faint">
              Coming into focus
            </p>
            <h2 id="upcoming-heading" className="mt-2 font-serif text-title-lg font-normal">
              The rest of the system
            </h2>
          </div>
          <Link
            href="/design"
            className="hidden text-xs text-muted underline decoration-border-strong underline-offset-4 transition-colors hover:text-accent sm:block"
          >
            See the design language
          </Link>
        </div>

        <div className="mt-4 grid gap-4 md:grid-cols-3">
          {upcoming.map((item) => {
            const Icon = item.icon;
            return (
              <Card key={item.label} className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <span className="flex size-9 items-center justify-center rounded-full border border-border bg-background/50 text-accent">
                    <Icon className="size-4" aria-hidden="true" />
                  </span>
                  <Badge tone="outline">{item.phase}</Badge>
                </div>
                <h3 className="mt-5 font-serif text-xl font-normal">{item.label}</h3>
                <p className="mt-2 text-small leading-relaxed text-muted">{item.copy}</p>
              </Card>
            );
          })}
        </div>
      </section>

      <div className="mt-4 flex items-center gap-2 text-[10px] uppercase tracking-[0.14em] text-faint">
        <FolderKanban className="size-3.5" aria-hidden="true" />
        No mock repositories · no sample records · no fabricated progress
      </div>
    </div>
  );
}
