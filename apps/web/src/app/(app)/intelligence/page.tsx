import type { Metadata } from "next";

import { Sunrise } from "lucide-react";

import { getServerUser, serverApiRequest } from "@/lib/api/server";
import { firstName } from "@/features/auth/display";
import { EmptyState } from "@/components/ui/states";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import type { BriefingResponse } from "@/lib/api/types";

export const metadata: Metadata = {
  title: "Intelligence",
  description: "Your Auvyren intelligence dashboard and daily briefing.",
};

export default async function IntelligencePage() {
  const user = await getServerUser().catch(() => null);
  const greeting = user ? `Welcome back, ${firstName(user)}.` : "Welcome back.";

  let briefing: BriefingResponse | null;
  try {
    briefing = await serverApiRequest<BriefingResponse>(
      "/intelligence/daily-plan",
    );
  } catch {
    briefing = null;
  }

  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Intelligence</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          {greeting}
        </h1>
        <p className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          Deterministic insights computed from your real records. No sample data,
          no invented metrics — everything is derived from your actual tasks,
          goals, habits, and sessions.
        </p>
      </header>

      {!briefing ? (
        <div className="mt-8">
          <EmptyState
            icon={Sunrise}
            title="Intelligence is starting up."
            description="Your workspace data is being analyzed. Refresh the page to see your daily briefing."
            compact
          />
        </div>
      ) : (
        <>
          <div className="mt-8 grid gap-4 xl:grid-cols-3">
            <Card>
              <CardHeader eyebrow="Today's plan" title="Focus for today" />
              <CardBody className="pt-5 space-y-4">
                <div className="flex items-center justify-between gap-4 border-b border-border/70 pb-3">
                  <span className="text-xs text-muted">
                    {briefing.daily_plan?.estimated_remaining_minutes ?? 0}
                  </span>
                  <span className="text-xs text-muted">
                    estimated minutes remaining
                  </span>
                </div>
                {briefing.daily_plan?.overload ? (
                  <div className="p-3 rounded-xl border border-warning/25 bg-warning-soft/60 text-warning">
                    <p className="text-xs font-semibold text-warning">
                      Your day is overbooked. Consider moving some tasks.
                    </p>
                  </div>
                ) : (
                  <div className="p-3 rounded-xl border border-success/25 bg-success-soft/60 text-success">
                    <p className="text-xs font-semibold text-success">
                      Your day looks manageable.
                    </p>
                  </div>
                )}
                <div className="space-y-2">
                  {briefing.daily_plan?.priorities.map((task) => {
                    return (
                      <div
                        key={task.task_id}
                        className="flex items-start gap-3"
                      >
                        <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                          <span className="text-[10px] font-semibold text-accent">
                            {task.score}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-foreground">
                            {task.title}
                          </p>
                          <p className="text-[10px] text-muted leading-tight">
                            {task.reasons.join(", ")}
                          </p>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardBody>
            </Card>

            <Card>
              <CardHeader eyebrow="Deadlines" title="Upcoming deadlines" />
              <CardBody className="pt-5 space-y-3">
                {briefing.deadlines.length === 0 ? (
                  <p className="text-xs text-muted">
                    No upcoming deadlines.
                  </p>
                ) : (
                  briefing.deadlines.slice(0, 5).map((item) => {
                    return (
                      <div key={item.id} className="flex items-start gap-3">
                        <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                          <span className="text-[10px] font-semibold text-accent">
                            {item.due}
                          </span>
                        </div>
                        <div className="min-w-0 flex-1">
                          <p className="text-xs font-semibold text-foreground">
                            {item.title}
                          </p>
                          <p className="text-[10px] text-muted">
                            {item.classification.replace(/_/g, " ")}
                          </p>
                        </div>
                      </div>
                    );
                  })
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader eyebrow="Goals" title="Goal progress" />
              <CardBody className="pt-5 space-y-3">
                {briefing.goal_progress.length === 0 ? (
                  <p className="text-xs text-muted">
                    No active goals.
                  </p>
                ) : (
                  briefing.goal_progress.slice(0, 5).map((goal) => {
                    return (
                      <div key={goal.goal_id} className="space-y-2">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs font-semibold text-foreground">
                            {goal.title}
                          </p>
                          <p className="text-[10px] font-mono text-muted">
                            {goal.progress}%
                          </p>
                        </div>
                        <div className="w-full h-2 rounded-full border border-border bg-surface">
                          <div
                            className="h-full rounded-full bg-accent text-accent-ink text-[10px] font-semibold flex items-center justify-center px-1"
                            style={{ width: `${goal.progress}%` }}
                          >
                            {goal.progress}%
                          </div>
                        </div>
                        {goal.is_neglected && (
                          <p className="text-[10px] text-warning">
                            ⚠ No recent activity — target date approaching
                          </p>
                        )}
                      </div>
                    );
                  })
                )}
              </CardBody>
            </Card>
          </div>

          <div className="mt-8 grid gap-4 xl:grid-cols-2">
            <Card>
              <CardHeader eyebrow="Habits" title="Consistency" />
              <CardBody className="pt-5 space-y-3">
                {briefing.habit_consistency.length === 0 ? (
                  <p className="text-xs text-muted">
                    No active habits.
                  </p>
                ) : (
                  briefing.habit_consistency.map((habit) => {
                    return (
                      <div key={habit.habit_id} className="space-y-2">
                        <div className="flex items-center justify-between gap-2">
                          <p className="text-xs font-semibold text-foreground">
                            {habit.name}
                          </p>
                          <p className="text-[10px] font-mono text-muted">
                            Streak: {habit.streak} day{habit.streak === 1 ? "" : "s"}
                          </p>
                        </div>
                        <div className="flex items-center justify-between gap-2 text-[10px] text-muted">
                          <span>
                            {habit.completion_rate_7d * 100}% (7 days)
                          </span>
                          <span>
                            {habit.completion_rate_30d * 100}% (30 days)
                          </span>
                        </div>
                        {habit.is_inconsistent && (
                          <p className="text-[10px] text-warning">
                            ⚠ Falling behind on this habit
                          </p>
                        )}
                      </div>
                    );
                  })
                )}
              </CardBody>
            </Card>

            <Card>
              <CardHeader eyebrow="Patterns" title="What the data shows" />
              <CardBody className="pt-5 space-y-3">
                {briefing.patterns.length === 0 ? (
                  <p className="text-xs text-muted">
                    No significant patterns detected yet. Keep using Auvyren and
                    patterns will emerge as you build up data.
                  </p>
                ) : (
                  briefing.patterns.map((pattern) => {
                    return (
                      <div key={pattern.kind} className="rounded-xl border border-border/70 bg-background/35 p-3">
                        <div className="flex items-start gap-3">
                          <div className="flex size-8 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                            <span className="text-[10px] font-semibold text-accent">
                              {pattern.confidence[0].toUpperCase()}
                            </span>
                          </div>
                          <div className="min-w-0 flex-1">
                            <p className="text-xs font-semibold text-foreground">
                              {pattern.description}
                            </p>
                            <p className="text-[10px] text-muted">
                              {pattern.evidence}
                            </p>
                          </div>
                        </div>
                      </div>
                    );
                  })
                )}
              </CardBody>
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
