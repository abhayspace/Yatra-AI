import { ArrowLeft, History } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { rupees } from "@/lib/format";
import type { VersionRow } from "@/lib/types";
import { cn } from "cn";

/** Revisions of the itinerary: pick a version to view; what changed is listed for each. */
export function VersionHistory({
  versions, shownVersion, onSelect, fresh,
}: {
  versions: VersionRow[];
  shownVersion: number;
  onSelect: (version: number | null) => void;
  fresh: number | null;
}) {
  if (versions.length < 2) return null;
  const latest = versions[versions.length - 1].version_number;
  const current = versions.find((v) => v.version_number === shownVersion) ?? versions[versions.length - 1];
  return (
    <Card className={cn("gap-3 p-4 shadow-soft", fresh === latest && shownVersion === latest && "animate-glow")} data-testid="version-history">
      <div className="flex flex-wrap items-center gap-2">
        <History className="size-4 text-muted-foreground" aria-hidden />
        <span className="text-sm font-medium">Itinerary history</span>
        <div className="ml-auto flex flex-wrap gap-1.5" role="tablist" aria-label="Itinerary versions">
          {versions.map((v) => (
            <button
              key={v.version_number} type="button" role="tab" aria-selected={v.version_number === shownVersion}
              onClick={() => onSelect(v.version_number === latest ? null : v.version_number)}
              className={cn(
                "rounded-full border px-3 py-1 text-caption font-medium tabular-nums transition-colors",
                v.version_number === shownVersion ? "border-primary bg-primary text-primary-foreground" : "border-border bg-card hover:bg-muted",
              )}
            >
              v{v.version_number} · {rupees(v.total_cost)}
            </button>
          ))}
        </div>
      </div>
      {current.change_summary.length > 0 ? (
        <div>
          <p className="mb-1 text-caption font-medium uppercase tracking-wide text-muted-foreground">What changed in v{current.version_number}</p>
          <ul className="list-disc space-y-0.5 pl-5 text-sm">
            {current.change_summary.map((c) => <li key={c}>{c}</li>)}
          </ul>
        </div>
      ) : (
        <p className="text-sm text-muted-foreground">v{current.version_number} is the first version of this plan.</p>
      )}
      {shownVersion !== latest && (
        <div className="flex items-center justify-between gap-2 rounded-lg bg-warning/15 px-3 py-2 text-sm text-warning-foreground dark:text-warning">
          <span>You are viewing an older version (v{shownVersion}).</span>
          <Button size="sm" variant="outline" onClick={() => onSelect(null)}><ArrowLeft />Back to latest</Button>
        </div>
      )}
    </Card>
  );
}
