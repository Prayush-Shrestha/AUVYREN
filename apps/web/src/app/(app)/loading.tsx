import { Skeleton } from "@/components/ui/states";

export default function WorkspaceLoading() {
  return (
    <div aria-busy="true" aria-label="Loading workspace">
      <div className="space-y-3">
        <Skeleton className="h-3 w-28" />
        <Skeleton className="h-9 w-2/3 max-w-lg" />
        <Skeleton className="h-4 w-full max-w-xl" />
      </div>
      <div className="mt-8 grid gap-4 lg:grid-cols-3">
        <Skeleton className="h-32 rounded-2xl lg:col-span-2" />
        <Skeleton className="h-32 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
        <Skeleton className="h-48 rounded-2xl" />
      </div>
    </div>
  );
}
