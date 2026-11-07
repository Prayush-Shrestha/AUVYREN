"use client";

import { useEffect, useMemo, useState } from "react";
import {
  CalendarDays,
  Clock3,
  Globe2,
  KeyRound,
  Laptop,
  LogOut,
  Mail,
  ShieldCheck,
  UserRound,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardBody, CardHeader } from "@/components/ui/card";
import { Field, Input, Select } from "@/components/ui/field";
import {
  EmptyState,
  ErrorState,
  InlineMessage,
  Skeleton,
} from "@/components/ui/states";
import { useToast } from "@/components/ui/toast";
import { useAuth } from "@/features/auth/auth-provider";
import { displayName } from "@/features/auth/display";
import { listSessionsRequest, revokeSessionRequest } from "@/lib/api/auth";
import { ApiError } from "@/lib/api/client";
import type { AuthSession } from "@/lib/api/types";

const WEEK_STARTS = [
  { value: 0, label: "Sunday" },
  { value: 1, label: "Monday" },
  { value: 6, label: "Saturday" },
];

function formatDate(value: string | null, timeZone?: string): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  try {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeZone,
    }).format(date);
  } catch {
    return new Intl.DateTimeFormat("en-US", { dateStyle: "medium" }).format(date);
  }
}

function formatDateTime(value: string | null, timeZone?: string): string {
  if (!value) return "Not yet";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Unknown";
  try {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
      timeZone,
    }).format(date);
  } catch {
    return new Intl.DateTimeFormat("en-US", {
      dateStyle: "medium",
      timeStyle: "short",
    }).format(date);
  }
}

function describeDevice(userAgent: string | null): string {
  if (!userAgent) return "Unrecognised device";
  const browser = /Edg\//.test(userAgent)
    ? "Edge"
    : /OPR\//.test(userAgent)
      ? "Opera"
      : /Firefox\//.test(userAgent)
        ? "Firefox"
        : /Chrome\//.test(userAgent)
          ? "Chrome"
          : /Safari\//.test(userAgent)
            ? "Safari"
            : "Browser";
  const os = /iPhone|iPad|iPod/.test(userAgent)
    ? "iOS"
    : /Android/.test(userAgent)
      ? "Android"
      : /Windows/.test(userAgent)
        ? "Windows"
        : /Macintosh|Mac OS X/.test(userAgent)
          ? "macOS"
          : /Linux/.test(userAgent)
            ? "Linux"
            : null;
  return os ? `${browser} on ${os}` : browser;
}

function ProfileCard() {
  const { user, updateProfile } = useAuth();
  const { toast } = useToast();
  const [name, setName] = useState(user?.full_name ?? "");
  const [nameError, setNameError] = useState<string>();
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  if (!user) return null;

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = name.trim();
    setSaved(false);
    if (trimmed && trimmed.length < 2) {
      setNameError("Use at least 2 characters.");
      return;
    }
    setNameError(undefined);
    setSaving(true);
    try {
      const nextUser = await updateProfile({ full_name: trimmed || null });
      setName(nextUser.full_name ?? "");
      setSaved(true);
    } catch (error) {
      if (error instanceof ApiError) {
        setNameError(error.fieldErrors?.full_name);
        toast({
          tone: "error",
          title: "Profile not saved",
          description: error.detail,
        });
      } else {
        toast({
          tone: "error",
          title: "Profile not saved",
          description: "Check your connection and try again.",
        });
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader
        eyebrow="Profile"
        title="The person behind the space."
        description="Your display name is used across the workspace. Your email is the key to your account."
      />
      <CardBody className="pt-5">
        <form className="space-y-5" noValidate onSubmit={handleSubmit}>
          <Field
            label="Display name"
            htmlFor="settings-name"
            error={nameError}
            success={saved ? "Saved." : undefined}
            hint="Leave it empty to be addressed by your email name."
          >
            <Input
              id="settings-name"
              name="full_name"
              autoComplete="name"
              placeholder="How should Auvyren address you?"
              value={name}
              disabled={saving}
              aria-invalid={Boolean(nameError) || undefined}
              aria-describedby={
                nameError
                  ? "settings-name-error"
                  : saved
                    ? "settings-name-success"
                    : "settings-name-hint"
              }
              onChange={(event) => {
                setName(event.target.value);
                setNameError(undefined);
                setSaved(false);
              }}
            />
          </Field>

          <Field
            label="Email address"
            htmlFor="settings-email"
            hint="Email changes arrive with account verification in a later release."
          >
            <Input
              id="settings-email"
              type="email"
              value={user.email}
              readOnly
              className="text-muted"
            />
          </Field>

          <div className="flex items-center justify-between gap-4 border-t border-border/70 pt-5">
            <p className="flex items-center gap-2 text-xs text-faint">
              <UserRound className="size-3.5" aria-hidden="true" />
              {user.email_verified ? "Email verified" : "Email verification comes later"}
            </p>
            <Button type="submit" loading={saving}>
              {saving ? "Saving…" : "Save profile"}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

function PreferencesCard() {
  const { user, updateProfile } = useAuth();
  const [timezone, setTimezone] = useState(user?.settings.timezone ?? "UTC");
  const [weekStartsOn, setWeekStartsOn] = useState(user?.settings.week_starts_on ?? 0);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [formError, setFormError] = useState<string>();

  const timezones = useMemo(() => {
    let supported: string[] = [];
    try {
      if (typeof Intl.supportedValuesOf === "function") {
        supported = Intl.supportedValuesOf("timeZone");
      }
    } catch {
      supported = [];
    }
    const current = user?.settings.timezone;
    if (supported.length === 0) {
      return Array.from(new Set(["UTC", current].filter(Boolean) as string[]));
    }
    return current && !supported.includes(current)
      ? [current, ...supported]
      : supported;
  }, [user?.settings.timezone]);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSaved(false);
    setFormError(undefined);
    setSaving(true);
    try {
      await updateProfile({ timezone, week_starts_on: weekStartsOn });
      setSaved(true);
    } catch (error) {
      if (error instanceof ApiError) {
        setFormError(error.detail);
      } else {
        setFormError("Preferences could not be saved. Check your connection and try again.");
      }
    } finally {
      setSaving(false);
    }
  }

  return (
    <Card>
      <CardHeader
        eyebrow="Preferences"
        title="Your days, in your time."
        description="These values shape daily boundaries, habit dates and calendar views."
      />
      <CardBody className="pt-5">
        <form className="space-y-5" noValidate onSubmit={handleSubmit}>
          {formError ? (
            <InlineMessage tone="danger" title="Preferences not saved">
              {formError}
            </InlineMessage>
          ) : null}

          <Field
            label="Timezone"
            htmlFor="settings-timezone"
            hint="Validated against the IANA timezone database."
          >
            <Select
              id="settings-timezone"
              name="timezone"
              value={timezone}
              disabled={saving}
              onChange={(event) => {
                setTimezone(event.target.value);
                setSaved(false);
                setFormError(undefined);
              }}
            >
              {timezones.map((zone) => (
                <option key={zone} value={zone}>
                  {zone.replaceAll("_", " ")}
                </option>
              ))}
            </Select>
          </Field>

          <Field
            label="Week starts on"
            htmlFor="settings-week-start"
            hint="Used by calendar and weekly review surfaces."
          >
            <Select
              id="settings-week-start"
              name="week_starts_on"
              value={weekStartsOn}
              disabled={saving}
              onChange={(event) => {
                setWeekStartsOn(Number(event.target.value));
                setSaved(false);
                setFormError(undefined);
              }}
            >
              {WEEK_STARTS.map((day) => (
                <option key={day.value} value={day.value}>
                  {day.label}
                </option>
              ))}
            </Select>
          </Field>

          <div className="flex items-center justify-between gap-4 border-t border-border/70 pt-5">
            <p className="flex items-center gap-2 text-xs text-faint">
              <Globe2 className="size-3.5" aria-hidden="true" />
              {saved ? "Preferences saved." : "Stored with your account."}
            </p>
            <Button type="submit" loading={saving}>
              {saving ? "Saving…" : "Save preferences"}
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

function AccountSummary() {
  const { user } = useAuth();
  if (!user) return null;

  const rows = [
    {
      icon: Mail,
      label: "Email status",
      value: user.email_verified ? "Verified" : "Not verified",
    },
    {
      icon: CalendarDays,
      label: "Member since",
      value: formatDate(user.created_at, user.settings.timezone),
    },
    {
      icon: Clock3,
      label: "Last sign-in",
      value: formatDateTime(user.last_login_at, user.settings.timezone),
    },
    {
      icon: KeyRound,
      label: "Password",
      value: "Argon2id",
    },
  ];

  return (
    <Card>
      <CardHeader
        eyebrow="Account"
        title={displayName(user)}
        description={user.email}
        action={
          <Badge tone={user.email_verified ? "success" : "outline"}>
            {user.email_verified ? "Verified" : "Unverified"}
          </Badge>
        }
      />
      <CardBody className="pt-5">
        <dl className="divide-y divide-border/70 border-y border-border/70">
          {rows.map((row) => {
            const Icon = row.icon;
            return (
              <div key={row.label} className="flex items-center justify-between gap-4 py-3">
                <dt className="flex items-center gap-2.5 text-xs text-muted">
                  <Icon className="size-3.5 text-faint" aria-hidden="true" />
                  {row.label}
                </dt>
                <dd className="text-right text-xs font-medium text-foreground-soft">
                  {row.value}
                </dd>
              </div>
            );
          })}
        </dl>
        <p className="mt-4 flex items-start gap-2 text-xs leading-relaxed text-faint">
          <ShieldCheck className="mt-0.5 size-3.5 shrink-0 text-accent" aria-hidden="true" />
          Passwords are stored as Argon2id hashes. Session tokens are hashed before they
          touch the database.
        </p>
      </CardBody>
    </Card>
  );
}

function SessionsCard() {
  const { user, signOut } = useAuth();
  const { toast } = useToast();
  const [sessions, setSessions] = useState<AuthSession[] | null>(null);
  const [error, setError] = useState<string>();
  const [revokingId, setRevokingId] = useState<string>();
  const [signingOut, setSigningOut] = useState(false);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const next = await listSessionsRequest();
        if (!cancelled) setSessions(next);
      } catch (caught) {
        if (cancelled) return;
        if (caught instanceof ApiError && caught.status === 401) {
          return;
        }
        setError(
          caught instanceof ApiError
            ? caught.detail
            : "Sessions could not be loaded. Check your connection and try again.",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  async function retryLoad() {
    setError(undefined);
    setSessions(null);
    try {
      setSessions(await listSessionsRequest());
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 401) {
        return;
      }
      setError(
        caught instanceof ApiError
          ? caught.detail
          : "Sessions could not be loaded. Check your connection and try again.",
      );
    }
  }
  async function handleCurrentSignOut() {
    setSigningOut(true);
    try {
      await signOut();
    } catch {
      toast({
        tone: "error",
        title: "Could not sign out",
        description: "Check your connection and try again.",
      });
      setSigningOut(false);
    }
  }

  async function handleRevoke(session: AuthSession) {
    if (session.current) {
      await handleCurrentSignOut();
      return;
    }

    setRevokingId(session.id);
    try {
      await revokeSessionRequest(session.id);
      setSessions((current) =>
        current ? current.filter((item) => item.id !== session.id) : current,
      );
      toast({
        tone: "success",
        title: "Session revoked",
        description: "That device has been signed out immediately.",
      });
    } catch (caught) {
      if (caught instanceof ApiError && caught.status === 404) {
        setSessions((current) =>
          current ? current.filter((item) => item.id !== session.id) : current,
        );
        return;
      }
      if (caught instanceof ApiError && caught.status === 401) {
        return;
      }
      toast({
        tone: "error",
        title: "Session not revoked",
        description:
          caught instanceof ApiError
            ? caught.detail
            : "Check your connection and try again.",
      });
    } finally {
      setRevokingId(undefined);
    }
  }

  return (
    <Card>
      <CardHeader
        eyebrow="Security"
        title="Active sessions."
        description="Every device holding a live session. Revocation takes effect on the next request."
        action={
          sessions ? (
            <Badge tone={sessions.length > 1 ? "accent" : "outline"}>
              {sessions.length} active
            </Badge>
          ) : undefined
        }
      />
      <CardBody className="pt-5">
        {error ? (
          <ErrorState
            title="Sessions are out of reach"
            description={error}
            onRetry={() => {
              void retryLoad();
            }}
          />
        ) : sessions === null ? (
          <div className="space-y-3" aria-label="Loading sessions" aria-busy="true">
            <Skeleton className="h-24 w-full rounded-xl" />
            <Skeleton className="h-24 w-full rounded-xl" />
          </div>
        ) : sessions.length === 0 ? (
          <EmptyState
            icon={Laptop}
            title="No active sessions"
            description="This should not happen while you are signed in. Refresh the page or sign in again."
            compact
          />
        ) : (
          <ul className="space-y-3">
            {sessions.map((session) => (
              <li
                key={session.id}
                className="rounded-xl border border-border/70 bg-background/35 p-4"
              >
                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
                  <div className="flex min-w-0 items-start gap-3">
                    <span className="flex size-9 shrink-0 items-center justify-center rounded-full border border-border bg-surface text-accent">
                      <Laptop className="size-4" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="text-small font-semibold text-foreground-soft">
                          {describeDevice(session.user_agent)}
                        </p>
                        {session.current ? (
                          <Badge tone="accent" dot>
                            This device
                          </Badge>
                        ) : null}
                      </div>
                      <p className="mt-1 text-xs text-muted">
                        {session.ip_address ? `${session.ip_address} · ` : ""}
                        Started{" "}
                        {formatDateTime(session.created_at, user?.settings.timezone)}
                      </p>
                      <p className="mt-0.5 text-xs text-faint">
                        Last used{" "}
                        {formatDateTime(session.last_used_at, user?.settings.timezone)} ·
                        Expires {formatDateTime(session.expires_at, user?.settings.timezone)}
                      </p>
                    </div>
                  </div>

                  <Button
                    variant={session.current ? "secondary" : "danger"}
                    size="sm"
                    loading={
                      session.current ? signingOut : revokingId === session.id
                    }
                    onClick={() => void handleRevoke(session)}
                  >
                    {session.current ? (
                      <LogOut className="size-3.5" aria-hidden="true" />
                    ) : null}
                    {session.current ? "Sign out" : "Revoke"}
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        )}

        <p className="mt-4 text-xs leading-relaxed text-faint">
          Sessions expire after 30 days of inactivity and cannot outlive 90 days from
          creation. Signing out or resetting your password revokes sessions on the server,
          not only in this browser.
        </p>
      </CardBody>
    </Card>
  );
}

export function SettingsView() {
  const { user } = useAuth();

  if (!user) {
    return (
      <div className="space-y-4" aria-busy="true" aria-label="Loading settings">
        <Skeleton className="h-24 w-full max-w-2xl rounded-2xl" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  return (
    <div>
      <header className="max-w-3xl">
        <p className="eyebrow">Account</p>
        <h1 className="mt-5 font-serif text-display-sm font-light text-foreground">
          Shape the space around you.
        </h1>
        <p className="mt-3 max-w-2xl text-body leading-relaxed text-muted">
          You are signed in as {displayName(user)}. Update your profile and preferences,
          and review every device that can reach your workspace.
        </p>
      </header>

      <div className="mt-8 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <ProfileCard />
        <AccountSummary />
      </div>

      <div className="mt-4 grid gap-4 xl:grid-cols-[1.15fr_0.85fr]">
        <PreferencesCard />
        <Card>
          <CardHeader
            eyebrow="Privacy"
            title="Local by default. Consent by design."
            description="Auvyren never sends your records to a model without an explicit decision."
          />
          <CardBody className="space-y-3 pt-5">
            {(
              [
                { label: "Local database", status: "Active", tone: "success" },
                { label: "Local AI", status: "Phase 4", tone: "outline" },
                { label: "Cloud AI", status: "Consent only", tone: "outline" },
              ] as const
            ).map((row) => (
              <div
                key={row.label}
                className="flex items-center justify-between gap-4 rounded-xl border border-border/70 bg-background/40 px-4 py-3"
              >
                <p className="text-small text-foreground-soft">{row.label}</p>
                <Badge tone={row.tone}>{row.status}</Badge>
              </div>
            ))}
            <p className="pt-1 text-xs leading-relaxed text-faint">
              Privacy controls, usage limits and export/deletion arrive with the AI and
              data-portability phases.
            </p>
          </CardBody>
        </Card>
      </div>

      <div className="mt-4">
        <SessionsCard />
      </div>
    </div>
  );
}
