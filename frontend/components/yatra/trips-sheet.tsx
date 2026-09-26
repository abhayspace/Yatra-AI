"use client";

import { ArrowRight, Luggage, Plus, Trash2 } from "lucide-react";
import { useState } from "react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { baseName, rupees, timeAgo } from "@/lib/format";
import type { TripSummary } from "@/lib/types";
import { cn } from "cn";

/** Drawer listing past trips stored in the database. */
export function TripsSheet({
  open, onOpenChange, trips, activeId, onOpen, onNew, onDelete, onDeleteAll,
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  trips: TripSummary[];
  activeId: string | null;
  onOpen: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  onDeleteAll: () => void;
}) {
  const [confirming, setConfirming] = useState<string | null>(null); // trip id, or "all"
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
            <li key={t.id} className="group relative">
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
              {confirming === t.id ? (
                <span className="absolute top-2 right-2 flex gap-1 rounded-lg bg-card p-1 shadow-soft">
                  <Button size="xs" variant="destructive" onClick={() => { onDelete(t.id); setConfirming(null); }}>Delete</Button>
                  <Button size="xs" variant="ghost" onClick={() => setConfirming(null)}>Keep</Button>
                </span>
              ) : (
                <Button
                  size="icon-xs" variant="ghost" aria-label={`Delete ${t.title ?? "trip"}`}
                  className="absolute top-2 right-2 opacity-0 transition-opacity group-hover:opacity-100 focus-visible:opacity-100"
                  onClick={() => setConfirming(t.id)}
                ><Trash2 /></Button>
              )}
            </li>
          ))}
        </ul>
        {trips.length > 0 && (
          <div className="border-t p-3 text-caption text-muted-foreground">
            {confirming === "all" ? (
              <span className="flex items-center gap-2">Delete all {trips.length} trips and their history?
                <Button size="xs" variant="destructive" onClick={() => { onDeleteAll(); setConfirming(null); }}>Delete all</Button>
                <Button size="xs" variant="ghost" onClick={() => setConfirming(null)}>Cancel</Button>
              </span>
            ) : (
              <button type="button" className="underline-offset-4 hover:underline" onClick={() => setConfirming("all")}>Delete all my trips</button>
            )}
            <p className="mt-1">Trips are removed automatically after a period of inactivity (90 days by default).</p>
          </div>
        )}
      </SheetContent>
    </Sheet>
  );
}
