import type { Metadata } from "next";
import {
  Bell,
  BellOff,
  Cloud,
  Cpu,
  Download,
  Palette,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/field";
import { EmptyState, InlineMessage } from "@/components/ui/states";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";

export const metadata: Metadata = {
  title: "Settings",
  description: "The Auvyren settings shell and its privacy posture.",
};

const appearanceSwatches = [
  { name: "Ink", value: "#0c100d" },
  { name: "Moss surface", value: "#141a15" },
  { name: "Paper", value: "#f2f0e6" },
  { name: "Living accent", value: "#b7e8c8" },
  { name: "Warm sand", value: "#d9c3a0" },
];

const privacyRows = [
  {
    icon: ShieldCheck,
    title: "Local database",
    status: "Active",
    tone: "success" as const,
    copy: "Records live in PostgreSQL on the server you control.",
  },
  {
    icon: Cpu,
    title: "Local AI",
    status: "Off",
    tone: "outline" as const,
    copy: "An Ollama runtime can be connected in Phase 4.",
  },
  {
    icon: Cloud,
    title: "Cloud AI",
    status: "Not configured",
    tone: "outline" as const,
    copy: "Requires explicit, revocable consent in Phase 6.",
  },
  {
    icon: Download,
    title: "Export & deletion",
    status: "Phase 6",
    tone: "outline" as const,
    copy: "Portable export and account deletion are added with the privacy controls.",
  },
];

export default function SettingsPage() {
  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Settings</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          Shape the space around you.
        </h1>
        <p className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          The settings shell is in place. Account details, preferences and privacy controls
          are wired behind it in later phases.
        </p>
      </header>

      <Tabs
        defaultValue="profile"
        orientation="vertical"
        className="mt-8 grid gap-6 lg:grid-cols-[14rem_minmax(0,1fr)] lg:items-start"
      >
        <TabsList className="flex w-full items-center gap-1 overflow-x-auto rounded-2xl p-1.5 lg:sticky lg:top-24 lg:flex-col lg:items-stretch">
          <TabsTrigger value="profile" className="shrink-0 justify-start rounded-xl px-3 py-2.5 lg:w-full">
            <UserRound className="size-4" aria-hidden="true" />
            Profile
          </TabsTrigger>
          <TabsTrigger value="appearance" className="shrink-0 justify-start rounded-xl px-3 py-2.5 lg:w-full">
            <Palette className="size-4" aria-hidden="true" />
            Appearance
          </TabsTrigger>
          <TabsTrigger value="notifications" className="shrink-0 justify-start rounded-xl px-3 py-2.5 lg:w-full">
            <Bell className="size-4" aria-hidden="true" />
            Notifications
          </TabsTrigger>
          <TabsTrigger value="privacy" className="shrink-0 justify-start rounded-xl px-3 py-2.5 lg:w-full">
            <ShieldCheck className="size-4" aria-hidden="true" />
            Privacy & AI
          </TabsTrigger>
        </TabsList>

        <TabsContent value="profile" className="mt-0">
          <Card>
            <CardHeader
              eyebrow="Profile"
              title="The person behind the space."
              description="Your account identity and locale. These controls become active in Phase 2."
              action={<Badge tone="outline">Phase 2</Badge>}
            />
            <CardBody className="space-y-5 pt-5">
              <InlineMessage tone="info" title="No account connected">
                This preview is not signed in. The fields below are disabled placeholders,
                not stored user data.
              </InlineMessage>

              <div className="grid gap-5 sm:grid-cols-2">
                <Field label="Display name" htmlFor="settings-name">
                  <Input id="settings-name" disabled placeholder="No account connected" />
                </Field>
                <Field label="Email address" htmlFor="settings-email">
                  <Input
                    id="settings-email"
                    type="email"
                    disabled
                    placeholder="No account connected"
                  />
                </Field>
              </div>

              <div className="max-w-xs">
                <Field
                  label="Timezone"
                  htmlFor="settings-timezone"
                  hint="Used for daily boundaries, habit dates and calendar views."
                >
                  <Select id="settings-timezone" disabled defaultValue="">
                    <option value="" disabled>
                      Select a timezone
                    </option>
                  </Select>
                </Field>
              </div>

              <div className="flex items-center justify-between gap-4 border-t border-border/70 pt-5">
                <p className="text-xs text-faint">Changes are saved in Phase 2.</p>
                <Button disabled>Save changes</Button>
              </div>
            </CardBody>
          </Card>
        </TabsContent>

        <TabsContent value="appearance" className="mt-0">
          <Card>
            <CardHeader
              eyebrow="Appearance"
              title="Ink, moss and warm paper."
              description="One deliberate theme, tuned for long, quiet sessions."
              action={<Badge tone="accent">Current</Badge>}
            />
            <CardBody className="space-y-6 pt-5">
              <div>
                <p className="text-[10px] font-semibold uppercase tracking-[0.15em] text-faint">
                  Palette
                </p>
                <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-5">
                  {appearanceSwatches.map((swatch) => (
                    <div
                      key={swatch.name}
                      className="overflow-hidden rounded-xl border border-border bg-background/40"
                    >
                      <div
                        className="h-14 border-b border-border/70"
                        style={{ backgroundColor: swatch.value }}
                        aria-hidden="true"
                      />
                      <div className="p-2.5">
                        <p className="text-[11px] font-medium text-foreground-soft">
                          {swatch.name}
                        </p>
                        <p className="mt-0.5 font-mono text-[9px] uppercase text-faint">
                          {swatch.value}
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              <div className="divide-y divide-border/70 border-y border-border/70">
                <div className="flex items-center justify-between gap-4 py-3.5">
                  <div>
                    <p className="text-small font-semibold text-foreground-soft">Theme</p>
                    <p className="text-xs text-muted">Auvyren is dark by design.</p>
                  </div>
                  <Badge tone="neutral">Dark</Badge>
                </div>
                <div className="flex items-center justify-between gap-4 py-3.5">
                  <div>
                    <p className="text-small font-semibold text-foreground-soft">Motion</p>
                    <p className="text-xs text-muted">
                      Follows your operating system&apos;s reduced-motion preference.
                    </p>
                  </div>
                  <Badge tone="success">Automatic</Badge>
                </div>
                <div className="flex items-center justify-between gap-4 py-3.5">
                  <div>
                    <p className="text-small font-semibold text-foreground-soft">Density</p>
                    <p className="text-xs text-muted">
                      Comfortable spacing, responsive from phone to desktop.
                    </p>
                  </div>
                  <Badge tone="neutral">Comfortable</Badge>
                </div>
              </div>
            </CardBody>
          </Card>
        </TabsContent>

        <TabsContent value="notifications" className="mt-0">
          <Card>
            <CardHeader
              eyebrow="Notifications"
              title="A quiet inbox."
              description="Only signals that deserve your attention — never engagement prompts."
              action={<Badge tone="outline">Phase 3+</Badge>}
            />
            <CardBody className="pt-5">
              <EmptyState
                icon={BellOff}
                title="Nothing to notify you about yet."
                description="Deadline reminders, review invitations and AI usage limits will appear here when the modules that produce them exist."
              />
            </CardBody>
          </Card>
        </TabsContent>

        <TabsContent value="privacy" className="mt-0">
          <Card>
            <CardHeader
              eyebrow="Privacy & AI"
              title="Local by default. Consent by design."
              description="Auvyren never sends your records to a model without an explicit decision."
              action={<Badge tone="success" dot>Local-first</Badge>}
            />
            <CardBody className="space-y-3 pt-5">
              {privacyRows.map((row) => {
                const Icon = row.icon;
                return (
                  <div
                    key={row.title}
                    className="flex flex-col gap-3 rounded-xl border border-border/70 bg-background/40 p-4 sm:flex-row sm:items-center sm:justify-between"
                  >
                    <div className="flex items-start gap-3">
                      <span className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                        <Icon className="size-4" aria-hidden="true" />
                      </span>
                      <div>
                        <p className="text-small font-semibold text-foreground-soft">
                          {row.title}
                        </p>
                        <p className="mt-0.5 text-xs leading-relaxed text-muted">
                          {row.copy}
                        </p>
                      </div>
                    </div>
                    <Badge tone={row.tone}>{row.status}</Badge>
                  </div>
                );
              })}

              <p className="pt-2 text-xs leading-relaxed text-faint">
                Privacy controls, usage limits and export/deletion are documented in
                <span className="text-muted"> docs/security.md</span> and arrive in Phases
                4–6.
              </p>
            </CardBody>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
