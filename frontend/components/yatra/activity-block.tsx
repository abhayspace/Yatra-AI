import { CloudRain, MapPin } from "lucide-react";
import { ActivityIcon } from "./activity-icon";
import { PriceTag } from "./cost-badge";
import { Badge } from "@/components/ui/badge";
import type { Block } from "@/lib/types";
import { cn } from "cn";

const KIND_LABEL: Record<Block["kind"], string> = {
  transit: "Travel", stay: "Stay", activity: "Activity", meal: "Meal", leisure: "Free time",
};

/** One row on a day's timeline: time, icon, title, notes and price. */
export function ActivityBlock({ block, travelers, isNew }: { block: Block; travelers: number; isNew?: boolean }) {
  const icon = block.kind === "meal" ? "food" : block.kind === "stay" ? "stay" : block.category;
  return (
    <li className={cn("group/blk relative flex gap-3 pb-5 last:pb-0", isNew && "animate-rise")} data-testid="block" data-kind={block.kind}>
      <div className="w-12 shrink-0 pt-1.5 text-right text-caption font-medium tabular-nums text-muted-foreground">
        {block.start}
      </div>
      <div className="relative flex flex-col items-center">
        <ActivityIcon category={icon} className="z-10 ring-4 ring-card" />
        <span className="absolute top-9 bottom-[-1.25rem] w-px bg-border group-last/blk:hidden" aria-hidden />
      </div>
      <div className="min-w-0 flex-1 pt-0.5">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="font-medium leading-snug">
              {block.title}
              {isNew && <Badge variant="brand" className="ml-2 align-middle">New</Badge>}
            </p>
            <p className="mt-0.5 flex flex-wrap items-center gap-x-2 text-caption text-muted-foreground">
              <span>{block.start}-{block.end}</span>
              <span aria-hidden>·</span>
              <span>{KIND_LABEL[block.kind]}</span>
              {block.area && (
                <span className="inline-flex items-center gap-0.5"><MapPin className="size-3" aria-hidden />{block.area}</span>
              )}
              {block.indoor && block.kind === "activity" && <Badge variant="secondary">Indoor</Badge>}
            </p>
          </div>
          {(block.kind === "activity" || block.kind === "meal" || block.kind === "transit") && (
            <PriceTag amount={block.cost_total} perPerson={travelers > 1 ? block.cost_per_person : undefined} className="shrink-0" />
          )}
        </div>
        {block.description && <p className="mt-1 text-sm text-muted-foreground">{block.description}</p>}
        {block.weather_note && (
          <p className="mt-1.5 flex items-start gap-1.5 rounded-lg bg-warning/15 px-2.5 py-1.5 text-caption text-warning-foreground dark:text-warning">
            <CloudRain className="mt-0.5 size-3.5 shrink-0" aria-hidden />
            {block.weather_note}
          </p>
        )}
      </div>
    </li>
  );
}
