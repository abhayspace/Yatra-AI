"use client";

import { ArrowRight, BedDouble, CalendarDays, Gauge, Info, Plane, TrainFront, Bus, Car, Users, CloudRain } from "lucide-react";
import { useState } from "react";
import { CategoryPill } from "./activity-icon";
import { CostBreakdown } from "./cost-breakdown";
import { DayCard } from "./day-card";
import { SourcesNote } from "./sources-note";
import { VersionHistory } from "./version-history";
import { WeatherIcon } from "./weather-strip";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { baseName, capitalize, dateRange, shortDate, weekday } from "@/lib/format";
import type { BudgetReport, Intent, Itinerary, VersionRow } from "@/lib/types";

const MODE_ICON = { flight: Plane, train: TrainFront, bus: Bus, cab: Car } as const;
const TIER = { budget: "Budget stay", mid: "Mid-range stay", premium: "Premium stay" } as const;

export function ItineraryView({
  itinerary, budget, intent, versions, shownVersion, previous, onSelectVersion, freshVersion,
}: {
  itinerary: Itinerary;
  budget: BudgetReport | null;
  intent: Intent | null;
  versions: VersionRow[];
  shownVersion: number;
  previous: Itinerary | null;
  onSelectVersion: (v: number | null) => void;
  freshVersion: number | null;
}) {
  const [day, setDay] = useState("1");
  const active = Number(day) > itinerary.days.length ? "1" : day;
  const ModeIcon = MODE_ICON[itinerary.transport_mode as keyof typeof MODE_ICON] ?? Car;
  const interests = intent?.interests ?? [];
  const assumptions = intent?.assumptions ?? [];

  return (
    <div className="space-y-4" data-testid="itinerary">
      <Card className="gap-3 p-5 shadow-soft">
        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-sm text-muted-foreground">
          <span className="font-medium text-foreground">{itinerary.origin}</span>
          <ArrowRight className="size-4" aria-hidden />
          <span className="font-medium text-foreground">{baseName(itinerary.destination_name)}</span>
          <Badge variant="teal" className="ml-auto"><ModeIcon aria-hidden />{capitalize(itinerary.transport_mode)}</Badge>
        </div>
        <h2 className="font-heading text-display">{itinerary.destination_name}</h2>
        <div className="flex flex-wrap gap-1.5 text-sm">
          <Badge variant="secondary" className="h-6 px-2.5"><CalendarDays aria-hidden />{dateRange(itinerary.start_date, itinerary.duration_days)} · {itinerary.duration_days} days</Badge>
          <Badge variant="secondary" className="h-6 px-2.5"><Users aria-hidden />{itinerary.travelers} traveller{itinerary.travelers === 1 ? "" : "s"}</Badge>
          <Badge variant="secondary" className="h-6 px-2.5"><Gauge aria-hidden />{capitalize(itinerary.pace)} pace</Badge>
          <Badge variant="secondary" className="h-6 px-2.5"><BedDouble aria-hidden />{TIER[itinerary.stay_tier]} · {itinerary.nights} night{itinerary.nights === 1 ? "" : "s"}</Badge>
        </div>
        {interests.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {interests.map((i) => <CategoryPill key={i} category={i} />)}
          </div>
        )}
      </Card>

      {budget && <CostBreakdown report={budget} travelers={itinerary.travelers} />}

      <VersionHistory versions={versions} shownVersion={shownVersion} onSelect={onSelectVersion} fresh={freshVersion} />

      {(itinerary.notes.length > 0 || assumptions.length > 0) && (
        <Alert variant={itinerary.notes.some((n) => /rain|hot|off-season|leaves almost/i.test(n)) ? "warning" : "info"}>
          {itinerary.notes.some((n) => /rain/i.test(n)) ? <CloudRain /> : <Info />}
          <AlertTitle>Good to know</AlertTitle>
          <AlertDescription>
            <ul className="list-disc space-y-0.5 pl-4">
              {[...itinerary.notes, ...assumptions].map((n) => <li key={n}>{n}</li>)}
            </ul>
          </AlertDescription>
        </Alert>
      )}

      <Tabs value={active} onValueChange={(v) => setDay(String(v))}>
        <TabsList variant="line" className="no-scrollbar h-auto w-full justify-start gap-2 overflow-x-auto p-1.5 group-data-horizontal/tabs:h-auto" aria-label="Days">
          {itinerary.days.map((d) => {
            return (
              <TabsTrigger
                key={d.day} value={String(d.day)}
                className="h-auto flex-none flex-col items-start gap-0 rounded-xl border border-border bg-card px-3.5 py-2 data-active:border-primary data-active:bg-primary/10 data-active:text-foreground after:hidden"
              >
                <span className="flex items-center gap-1.5 text-sm font-semibold">Day {d.day}{d.weather && <WeatherIcon weather={d.weather} className="size-3.5 text-muted-foreground" />}</span>
                <span className="text-caption font-normal text-muted-foreground">{d.date ? `${weekday(d.date)}, ${shortDate(d.date)}` : " "}</span>
              </TabsTrigger>
            );
          })}
        </TabsList>
        {itinerary.days.map((d) => (
          <TabsContent key={d.day} value={String(d.day)} className="mt-1">
            <DayCard day={d} itinerary={itinerary} previous={shownVersion > 1 ? previous : null} />
          </TabsContent>
        ))}
      </Tabs>

      <SourcesNote sources={itinerary.sources ?? []} />
    </div>
  );
}
