"use client";

import { MessageCircle, Route } from "lucide-react";
import { useState } from "react";
import { AccessGate } from "./access-gate";
import { ChatPanel } from "./chat-panel";
import { ItineraryEmpty } from "./empty-states";
import { Header } from "./header";
import { ItineraryView } from "./itinerary-view";
import { ItinerarySkeleton } from "./skeletons";
import { TripsSheet } from "./trips-sheet";
import { setAccessCode } from "@/lib/owner";
import { useYatra } from "@/lib/use-yatra";
import { cn } from "cn";

export function AppShell() {
  const y = useYatra();
  const [tab, setTab] = useState<"chat" | "plan">("chat");
  const [tripsOpen, setTripsOpen] = useState(false);
  const [seenKey, setSeenKey] = useState<string | null>(null);
  const [codeTries, setCodeTries] = useState(0);

  const { shown } = y;
  const version = shown.version;
  const planKey = shown.itinerary ? `${y.tripId}:${version}` : null;
  const unseen = tab === "chat" && !!planKey && planKey !== seenKey;

  const goPlan = () => { setTab("plan"); setSeenKey(planKey); };
  const firstPlanLoading = y.busy && !shown.itinerary;

  if (y.bootError?.code === "access_code_required") {
    return <AccessGate rejected={codeTries > 0} onSubmit={(code) => { setAccessCode(code); setCodeTries((n) => n + 1); y.retryBoot(); }} />;
  }

  return (
    <div className="flex h-dvh flex-col">
      <Header onNewTrip={() => { y.newTrip(); setTab("chat"); }} onOpenTrips={() => setTripsOpen(true)} tripCount={y.trips.length} />
      <main className="mx-auto grid min-h-0 w-full max-w-[1600px] flex-1 grid-cols-[minmax(0,1fr)] gap-3 p-3 pb-2 lg:grid-cols-[minmax(24rem,32rem)_minmax(0,1fr)] lg:gap-4 lg:p-4">
        <section className={cn("min-h-0 min-w-0 flex-col", tab === "chat" ? "flex" : "hidden lg:flex")} aria-label="Chat">
          <ChatPanel
            booting={y.booting} bootError={y.bootError} onRetryBoot={y.retryBoot}
            messages={y.messages} busy={y.busy} progress={y.progress} error={y.error}
            onSend={y.send} onRetry={y.retry} onDismissError={y.dismissError}
            onOpenVersion={(v) => { y.setViewVersion(v === version && y.isLatest ? null : v); goPlan(); }}
            hasItinerary={!!shown.itinerary}
          />
        </section>
        <section
          className={cn("min-h-0 min-w-0 overflow-y-auto rounded-2xl scrollbar-thin", tab === "plan" ? "block" : "hidden lg:block")}
          aria-label="Itinerary" data-testid="itinerary-panel"
        >
          {y.booting || firstPlanLoading ? (
            <ItinerarySkeleton />
          ) : shown.itinerary ? (
            <ItineraryView
              itinerary={shown.itinerary} budget={shown.budget} intent={y.intent} versions={y.versions}
              shownVersion={shown.version} previous={y.previousItinerary} onSelectVersion={y.setViewVersion}
              freshVersion={y.freshVersion}
            />
          ) : (
            <div className="h-full rounded-2xl border border-dashed bg-card/40"><ItineraryEmpty /></div>
          )}
        </section>
      </main>
      <nav className="grid grid-cols-2 gap-1 border-t bg-background/90 p-1.5 backdrop-blur lg:hidden" aria-label="Switch view">
        <button type="button" onClick={() => setTab("chat")} className={cn("flex items-center justify-center gap-2 rounded-xl py-2 text-sm font-medium", tab === "chat" ? "bg-primary/12 text-primary" : "text-muted-foreground")}>
          <MessageCircle className="size-4" aria-hidden />Chat
        </button>
        <button type="button" onClick={goPlan} className={cn("relative flex items-center justify-center gap-2 rounded-xl py-2 text-sm font-medium", tab === "plan" ? "bg-primary/12 text-primary" : "text-muted-foreground")}>
          <Route className="size-4" aria-hidden />Itinerary
          {unseen && <span className="absolute top-2 right-[28%] size-2 rounded-full bg-primary" aria-label="New itinerary" />}
        </button>
      </nav>
      <TripsSheet
        open={tripsOpen} onOpenChange={setTripsOpen} trips={y.trips} activeId={y.tripId}
        onOpen={(id) => { void y.openTrip(id); setTab("chat"); }} onDelete={(id) => void y.deleteTrip(id)} onDeleteAll={() => void y.deleteAll()} onNew={() => { y.newTrip(); setTab("chat"); }}
      />
    </div>
  );
}
