"use client";

import { useState } from "react";
import {
  ArrowRight,
  Bell,
  Bookmark,
  Copy,
  MoreHorizontal,
  Pencil,
  Sparkles,
  Trash2,
} from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Field, Input } from "@/components/ui/field";
import { ErrorState, InlineMessage } from "@/components/ui/states";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useToast } from "@/components/ui/toast";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

export function TabsDemo() {
  return (
    <Tabs defaultValue="today">
      <TabsList aria-label="Example workspace views">
        <TabsTrigger value="today">Today</TabsTrigger>
        <TabsTrigger value="week">This week</TabsTrigger>
        <TabsTrigger value="review">Review</TabsTrigger>
      </TabsList>
      <TabsContent value="today">
        <div className="rounded-xl border border-border bg-background/40 p-5">
          <p className="font-serif text-xl">A single day, composed.</p>
          <p className="mt-2 max-w-md text-small leading-relaxed text-muted">
            Tabs use arrow-key navigation, roving focus and a visible active state. Content
            is real markup, not a simulated frame.
          </p>
        </div>
      </TabsContent>
      <TabsContent value="week">
        <div className="rounded-xl border border-border bg-background/40 p-5">
          <p className="font-serif text-xl">The week in context.</p>
          <p className="mt-2 max-w-md text-small leading-relaxed text-muted">
            This panel demonstrates the same primitive with different content. No fake
            metrics are involved.
          </p>
        </div>
      </TabsContent>
      <TabsContent value="review">
        <div className="rounded-xl border border-border bg-background/40 p-5">
          <p className="font-serif text-xl">Reflection, held lightly.</p>
          <p className="mt-2 max-w-md text-small leading-relaxed text-muted">
            Keyboard users can move between tabs with the arrow keys. Tab content receives
            focus when it is interactive.
          </p>
        </div>
      </TabsContent>
    </Tabs>
  );
}

export function DialogDemo() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="secondary">
          Open dialog
          <ArrowRight className="size-4" aria-hidden="true" />
        </Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Begin a focus block?</DialogTitle>
          <DialogDescription>
            This is a real accessible dialog: focus is trapped, escape closes it, and the
            trigger regains focus. The action is deliberately local to this demo.
          </DialogDescription>
        </DialogHeader>
        <div className="rounded-xl border border-border bg-background/50 p-4">
          <p className="text-small font-semibold text-foreground-soft">25 minutes</p>
          <p className="mt-1 text-xs leading-relaxed text-muted">
            A focus block would protect attention in the real product. Nothing is scheduled
            here.
          </p>
        </div>
        <DialogFooter>
          <DialogClose asChild>
            <Button variant="ghost">Cancel</Button>
          </DialogClose>
          <DialogClose asChild>
            <Button>Done</Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export function DropdownDemo() {
  const { toast } = useToast();

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="secondary" aria-label="Open example actions">
          <MoreHorizontal className="size-4" aria-hidden="true" />
          Actions
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start">
        <DropdownMenuLabel>Example item</DropdownMenuLabel>
        <DropdownMenuItem
          onSelect={() =>
            toast({ title: "Rename selected", description: "Demo action only." })
          }
        >
          <Pencil className="size-4" aria-hidden="true" />
          Rename
        </DropdownMenuItem>
        <DropdownMenuItem
          onSelect={() =>
            toast({ title: "Copied", description: "Demo action only.", tone: "success" })
          }
        >
          <Copy className="size-4" aria-hidden="true" />
          Duplicate
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem
          className="text-danger data-[highlighted]:text-danger"
          onSelect={() =>
            toast({ title: "Delete is disabled", description: "This is a demo menu.", tone: "error" })
          }
        >
          <Trash2 className="size-4" aria-hidden="true" />
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}

export function TooltipDemo() {
  return (
    <Tooltip>
      <TooltipTrigger asChild>
        <Button variant="secondary">Hover or focus me</Button>
      </TooltipTrigger>
      <TooltipContent>
        Tooltips appear on hover and keyboard focus. They never hold essential information.
      </TooltipContent>
    </Tooltip>
  );
}

export function ToastDemo() {
  const { toast } = useToast();

  return (
    <div className="flex flex-wrap gap-2">
      <Button
        variant="secondary"
        size="sm"
        onClick={() =>
          toast({
            title: "A quiet confirmation",
            description: "The notification is announced by screen readers.",
          })
        }
      >
        <Bell className="size-3.5" aria-hidden="true" />
        Neutral toast
      </Button>
      <Button
        variant="secondary"
        size="sm"
        onClick={() =>
          toast({
            title: "Saved locally",
            description: "This is a demo; no record was written.",
            tone: "success",
          })
        }
      >
        Success toast
      </Button>
      <Button
        variant="secondary"
        size="sm"
        onClick={() =>
          toast({
            title: "Something needs attention",
            description: "Error toasts explain what happened without leaking internals.",
            tone: "error",
          })
        }
      >
        Error toast
      </Button>
    </div>
  );
}

export function FormDemo() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string>();
  const [validated, setValidated] = useState(false);

  return (
    <form
      noValidate
      className="max-w-md space-y-4"
      onSubmit={(event) => {
        event.preventDefault();
        const value = email.trim();
        if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(value)) {
          setError("Enter a valid email address.");
          setValidated(false);
          return;
        }
        setError(undefined);
        setValidated(true);
      }}
    >
      <Field
        label="Email address"
        htmlFor="demo-email"
        error={error}
        hint="Inline validation is driven by the form, not the input."
      >
        <Input
          id="demo-email"
          type="email"
          placeholder="you@example.com"
          value={email}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={error ? "demo-email-error" : "demo-email-hint"}
          onChange={(event) => {
            setEmail(event.target.value);
            setError(undefined);
            setValidated(false);
          }}
        />
      </Field>

      <Button type="submit" size="sm">
        Validate example
      </Button>

      {validated ? (
        <InlineMessage tone="success" title="Validated locally">
          The value passes the example rule. Nothing was transmitted or stored.
        </InlineMessage>
      ) : null}
    </form>
  );
}

export function BadgeActionsDemo() {
  return (
    <div className="flex flex-wrap items-center gap-2">
      <Badge tone="accent" dot>
        Local
      </Badge>
      <Badge tone="outline">
        <Bookmark className="size-3" aria-hidden="true" />
        Saved
      </Badge>
      <Badge tone="sand">
        <Sparkles className="size-3" aria-hidden="true" />
        Generated
      </Badge>
    </div>
  );
}

export function ErrorStateDemo() {
  const [attempts, setAttempts] = useState(0);

  return (
    <ErrorState
      description={
        attempts === 0
          ? "The surface could not load its records. Retry keeps your place."
          : `Retry received. This demo has been asked to recover ${attempts} ${
              attempts === 1 ? "time" : "times"
            }; no network request was made.`
      }
      onRetry={() => setAttempts((current) => current + 1)}
    />
  );
}
