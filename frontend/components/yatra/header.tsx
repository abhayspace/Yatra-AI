import { History, Plus } from "lucide-react";
import { BrandMark } from "./brand-mark";
import { ThemeToggle } from "./theme-toggle";
import { Button } from "@/components/ui/button";

export function Header({ onNewTrip, onOpenTrips, tripCount }: { onNewTrip: () => void; onOpenTrips: () => void; tripCount: number }) {
  return (
    <header className="sticky top-0 z-30 border-b bg-background/80 backdrop-blur-md">
      <div className="mx-auto flex h-14 max-w-[1600px] items-center gap-3 px-3 lg:px-4">
        <BrandMark />
        <div className="leading-tight">
          <h1 className="font-heading text-xl font-semibold">Yatra <span className="text-primary">AI</span></h1>
          <p className="hidden text-caption text-muted-foreground sm:block">Plan it. Budget it. Change your mind.</p>
        </div>
        <div className="ml-auto flex items-center gap-1.5">
          <Button variant="outline" onClick={onOpenTrips} aria-label="Open your trips">
            <History />
            <span className="hidden sm:inline">My trips</span>
            {tripCount > 0 && <span className="rounded-full bg-primary/15 px-1.5 text-caption font-semibold text-primary tabular-nums">{tripCount}</span>}
          </Button>
          <Button onClick={onNewTrip}><Plus /><span className="hidden sm:inline">New trip</span></Button>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
