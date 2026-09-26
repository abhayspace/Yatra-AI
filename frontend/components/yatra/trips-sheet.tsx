"use client";

import { ArrowRight, Luggage, Plus } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { baseName, rupees, timeAgo } from "@/lib/format";
import type { TripSummary } from "@/lib/types";
import { cn } from "cn";

/** Drawer listing past trips stored in the database. */
export function TripsSheet({
  open, onOpenChange, trips, activeId, onOpen, onNew,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trips: TripSummary[];
  activeId: string | null;
  onOpen: (id: string) => void;
  onNew: () => void;
}) {
  return (
    <Sheet open={open} onOpenChange={onOpenChange}>
      <SheetContent side="right" className="w-full gap-0 sm:max-w-md">
        <SheetHeader className="border-b p-5">
          <SheetTitle className="text-title">Your trips</SheetTitle>
          <SheetDescription>Saved in your database, so they are still here after a reload.</SheetDescription>
          <Button className="mt-3 w-fit" onClick={() => { onNew(); onOpenChange(false); }}><Plus />Plan a new trip</Button>
        </SheetHeader>
        <ul className="flex-1 space-y-2 overflow-y-auto p-4 scrollbar-thin" data-testid="trips-list">
          {trips.length === 0 && (
            <li className="grid place-items-center gap-2 py-16 text-center text-muted-foreground">
              <Luggage className="size-8" aria-hidden />
              <span>No trips yet. Describe one in the chat to get started.</span>
            </li>
          )}
          {trips.map((t) => (
            <li key={t.id}>
              <button
                type="button"
                onClick={() => { onOpen(t.id); onOpenChange(false); }}
                className={cn(
                  "w-full rounded-xl border p-3 text-left transition-colors hover:bg-muted",
                  t.id === activeId ? "border-primary bg-primary/8" : "border-border bg-card",
                )}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="font-heading text-heading">{t.title ?? "New trip"}</span>
                  {t.current_version > 1 && <Badge variant="brand">v{t.current_version}</Badge>}
                </div>
                <p className="mt-0.5 flex flex-wrap items-center gap-x-1.5 text-caption text-muted-foreground">
                  {t.origin && t.destination && (<>{t.origin}<ArrowRight className="size-3" aria-hidden />{baseName(t.destination)}</>)}
                  {t.travelers ? <span>· {t.travelers} traveller{t.travelers === 1 ? "" : "s"}</span> : null}
                  {t.budget ? <span>· {rupees(t.budget)}</span> : null}
                  <span className="ml-auto">{timeAgo(t.updated_at)}</span>
                </p>
              </button>
            </li>
          ))}
        </ul>
      </SheetContent>
    </Sheet>
  );
}
