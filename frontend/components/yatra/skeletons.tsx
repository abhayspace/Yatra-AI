import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export function ChatSkeleton() {
  return (
    <div className="space-y-4 p-4" aria-busy="true" aria-label="Loading your conversation">
      <div className="flex justify-end"><Skeleton className="h-10 w-2/3 rounded-2xl" /></div>
      <div className="flex gap-2.5">
        <Skeleton className="size-7 shrink-0 rounded-lg" />
        <div className="flex-1 space-y-2"><Skeleton className="h-20 w-full rounded-2xl" /><Skeleton className="h-6 w-1/2 rounded-full" /></div>
      </div>
    </div>
  );
}

export function ItinerarySkeleton() {
  return (
    <div className="space-y-4 p-1" aria-busy="true" aria-label="Building your itinerary">
      <Card className="gap-3 p-5">
        <Skeleton className="h-8 w-1/2" />
        <div className="flex gap-2"><Skeleton className="h-6 w-24 rounded-full" /><Skeleton className="h-6 w-20 rounded-full" /><Skeleton className="h-6 w-28 rounded-full" /></div>
      </Card>
      <Card className="gap-3 p-5">
        <Skeleton className="h-9 w-40" />
        <Skeleton className="h-3 w-full rounded-full" />
        <Skeleton className="h-3 w-full rounded-full" />
      </Card>
      <div className="flex gap-2">{[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-11 w-24 rounded-xl" />)}</div>
      <Card className="gap-4 p-5">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="flex gap-3">
            <Skeleton className="size-9 shrink-0 rounded-xl" />
            <div className="flex-1 space-y-2"><Skeleton className="h-4 w-2/3" /><Skeleton className="h-3 w-1/2" /></div>
            <Skeleton className="h-4 w-14" />
          </div>
        ))}
      </Card>
    </div>
  );
}
