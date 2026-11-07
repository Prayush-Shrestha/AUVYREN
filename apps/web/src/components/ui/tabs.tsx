"use client";

import * as TabsPrimitive from "@radix-ui/react-tabs";

import { cn } from "@/lib/cn";

export const Tabs = TabsPrimitive.Root;

export function TabsList({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.List>) {
  return (
    <TabsPrimitive.List
      className={cn(
        "inline-flex items-center gap-1 rounded-full border border-border bg-surface/80 p-1 backdrop-blur",
        className,
      )}
      {...props}
    />
  );
}

export function TabsTrigger({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Trigger>) {
  return (
    <TabsPrimitive.Trigger
      className={cn(
        "inline-flex select-none items-center justify-center gap-2 whitespace-nowrap rounded-full px-4 py-1.5 text-small font-semibold text-muted transition-[background-color,color] duration-200 hover:text-foreground disabled:pointer-events-none disabled:opacity-45 data-[state=active]:bg-surface-elevated data-[state=active]:text-foreground data-[state=active]:shadow-soft",
        className,
      )}
      {...props}
    />
  );
}

export function TabsContent({
  className,
  ...props
}: React.ComponentProps<typeof TabsPrimitive.Content>) {
  return (
    <TabsPrimitive.Content
      className={cn("mt-6 focus-visible:outline-2 focus-visible:outline-offset-4", className)}
      {...props}
    />
  );
}
