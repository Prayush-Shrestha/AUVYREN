import { AuvyrenMark } from "@/components/ui/logo";

const satellites = [
  { label: "Plan", detail: "tasks · goals · calendar", position: "left-0 top-[21%]" },
  { label: "Practice", detail: "habits · routines", position: "right-0 top-[31%]" },
  { label: "Reflect", detail: "notes · reviews", position: "bottom-[22%] left-[2%]" },
  { label: "Understand", detail: "patterns · insight", position: "bottom-[12%] right-[1%]" },
];

export function Constellation() {
  return (
    <div className="relative mx-auto aspect-square w-full max-w-[34rem] select-none">
      <div
        aria-hidden="true"
        className="absolute inset-[8%] rounded-full bg-[radial-gradient(circle_at_50%_50%,rgba(183,232,200,0.1),transparent_66%)] blur-2xl"
      />

      <div aria-hidden="true" className="absolute inset-[5%]">
        <div className="absolute inset-0 rounded-full border border-border/70" />
        <div className="absolute inset-[12%] rounded-full border border-border/55" />
        <div className="absolute inset-[25%] rounded-full border border-dashed border-border/70" />
        <div className="absolute inset-[38%] rounded-full border border-border/65" />

        <div className="absolute inset-0 animate-orbit">
          <span className="absolute left-1/2 top-0 size-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-accent shadow-[0_0_18px_4px_rgba(183,232,200,0.45)]" />
        </div>
        <div className="absolute inset-[12%] animate-orbit [animation-direction:reverse] [animation-duration:82s]">
          <span className="absolute left-1/2 top-0 size-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-sand/80" />
        </div>
        <div className="absolute inset-[25%] animate-orbit [animation-duration:118s]">
          <span className="absolute left-1/2 top-0 size-1 -translate-x-1/2 -translate-y-1/2 rounded-full bg-foreground/45" />
        </div>

        <div className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-gradient-to-b from-transparent via-border/50 to-transparent" />
        <div className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-gradient-to-r from-transparent via-border/50 to-transparent" />
      </div>

      <div className="absolute left-1/2 top-1/2 w-[50%] -translate-x-1/2 -translate-y-1/2 text-center">
        <span className="mx-auto flex size-11 items-center justify-center rounded-full border border-accent/20 bg-background/80 text-accent shadow-glow backdrop-blur">
          <AuvyrenMark className="size-6" />
        </span>
        <p className="mt-4 font-serif text-2xl font-light leading-tight text-foreground sm:text-3xl">
          One clear day.
        </p>
        <p className="mt-2 text-[9px] font-semibold uppercase tracking-[0.2em] text-muted">
          Intention to action
        </p>
      </div>

      {satellites.map((satellite, index) => (
        <div
          key={satellite.label}
          className={`absolute ${satellite.position} animate-fade-in`}
          style={{ animationDelay: `${400 + index * 120}ms` }}
        >
          <div className="rounded-full border border-border-strong/80 bg-background/75 px-3 py-1.5 shadow-soft backdrop-blur-md">
            <span className="flex items-center gap-2 text-[10px] font-semibold uppercase tracking-[0.14em] text-foreground-soft">
              <span className="size-1 rounded-full bg-accent" aria-hidden="true" />
              {satellite.label}
            </span>
            <span className="mt-0.5 hidden text-[9px] tracking-wide text-faint sm:block">
              {satellite.detail}
            </span>
          </div>
        </div>
      ))}
    </div>
  );
}
