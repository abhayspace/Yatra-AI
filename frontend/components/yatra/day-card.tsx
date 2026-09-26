import { ActivityBlock } from "./activity-block";
import { WeatherStrip } from "./weather-strip";
import { Card } from "@/components/ui/card";
import { rupees, shortDate, weekday } from "@/lib/format";
import type { Day, Itinerary } from "@/lib/types";

/** Everything for one day: theme, weather, timeline and the day's cost. */
export function DayCard({ day, itinerary, previous }: { day: Day; itinerary: Itinerary; previous: Itinerary | null }) {
  const oldIds = previous ? new Set(previous.days.flatMap((d) => d.blocks.map((b) => b.place_id).filter(Boolean))) : null;
  const meals = day.blocks.filter((b) => b.kind === "meal").reduce((s, b) => s + b.cost_total, 0);
  const acts = day.blocks.filter((b) => b.kind === "activity").reduce((s, b) => s + b.cost_total, 0);
  const travel = day.blocks.filter((b) => b.kind === "transit").reduce((s, b) => s + b.cost_total, 0);
  return (
    <Card className="gap-4 p-5 shadow-soft" data-testid="day-card">
      <header>
        <p className="text-caption font-medium uppercase tracking-wide text-primary">
          Day {day.day}{day.date ? ` · ${weekday(day.date)}, ${shortDate(day.date)}` : ""}
        </p>
        <h3 className="mt-0.5 font-heading text-title">{day.theme}</h3>
      </header>
      <WeatherStrip weather={day.weather} />
      <ol>
        {day.blocks.map((b) => (
          <ActivityBlock
            key={b.id} block={b} travelers={itinerary.travelers}
            isNew={!!oldIds && b.kind === "activity" && !!b.place_id && !oldIds.has(b.place_id)}
          />
        ))}
      </ol>
      <footer className="flex flex-wrap items-center gap-x-4 gap-y-1 rounded-xl bg-muted px-3 py-2 text-caption text-muted-foreground">
        {travel > 0 && <span>Travel <b className="font-semibold text-foreground tabular-nums">{rupees(travel)}</b></span>}
        {acts > 0 && <span>Activities <b className="font-semibold text-foreground tabular-nums">{rupees(acts)}</b></span>}
        {meals > 0 && <span>Meals <b className="font-semibold text-foreground tabular-nums">{rupees(meals)}</b></span>}
        {day.stay_cost > 0 && <span>Stay <b className="font-semibold text-foreground tabular-nums">{rupees(day.stay_cost)}</b></span>}
        {day.local_transport > 0 && <span>Local <b className="font-semibold text-foreground tabular-nums">{rupees(day.local_transport)}</b></span>}
        <span className="ml-auto text-sm">Day total <b className="font-semibold text-foreground tabular-nums">{rupees(day.day_cost)}</b></span>
      </footer>
    </Card>
  );
}
