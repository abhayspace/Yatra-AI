import { CostBadge } from "./cost-badge";
import { Card } from "@/components/ui/card";
import { rupees } from "@/lib/format";
import type { BudgetReport, CostLines } from "@/lib/types";
import { cn } from "cn";

const LINES: { key: keyof CostLines; label: string; color: string }[] = [
  { key: "transport", label: "Travel", color: "bg-chart-2" },
  { key: "stay", label: "Stay", color: "bg-chart-1" },
  { key: "food", label: "Food", color: "bg-chart-3" },
  { key: "activities", label: "Activities", color: "bg-chart-4" },
  { key: "local_transport", label: "Local transport", color: "bg-chart-5" },
];

const METER: Record<BudgetReport["status"], string> = {
  within_budget: "bg-success",
  tight: "bg-warning",
  over_budget: "bg-destructive",
  no_budget_given: "bg-brand-2",
};

/** Total, budget meter, per-person figure and a stacked breakdown of where the money goes. */
export function CostBreakdown({ report, travelers }: { report: BudgetReport; travelers: number }) {
  const { total, budget } = report;
  const meterPct = budget ? Math.min(100, (total / budget) * 100) : 100;
  return (
    <Card className="gap-4 p-5 shadow-soft" data-testid="cost-breakdown">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <p className="text-caption font-medium uppercase tracking-wide text-muted-foreground">Estimated total</p>
          <p className="font-heading text-display tabular-nums" data-testid="total-cost">{rupees(total)}</p>
          <p className="text-sm text-muted-foreground">
            {rupees(report.per_person)} per person · {travelers} traveller{travelers === 1 ? "" : "s"}
          </p>
          <p className="mt-1 text-caption text-muted-foreground">A planning estimate from a curated dataset, not a live quote. Nothing is booked.</p>
        </div>
        <CostBadge status={report.status} />
      </div>

      {budget ? (
        <div>
          <div className="mb-1.5 flex justify-between text-caption text-muted-foreground">
            <span>{rupees(total)} of {rupees(budget)}</span>
            <span className="font-medium">
              {report.status === "over_budget"
                ? `${rupees(report.overage)} over`
                : `${rupees(report.remaining)} to spare`}
            </span>
          </div>
          <div
            className="h-2.5 overflow-hidden rounded-full bg-muted"
            role="progressbar" aria-valuenow={Math.round(meterPct)} aria-valuemin={0} aria-valuemax={100} aria-label="Share of budget used"
          >
            <div className={cn("h-full rounded-full transition-all duration-700", METER[report.status])} style={{ width: `${meterPct}%` }} />
          </div>
        </div>
      ) : null}

      <div>
        <div className="flex h-2.5 overflow-hidden rounded-full bg-muted" aria-hidden>
          {LINES.map((l) => (
            <div key={l.key} className={l.color} style={{ width: `${report.breakdown_pct[l.key] ?? 0}%` }} />
          ))}
        </div>
        <ul className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 sm:grid-cols-3">
          {LINES.map((l) => (
            <li key={l.key} className="flex items-center gap-2 text-sm">
              <span className={cn("size-2.5 shrink-0 rounded-full", l.color)} aria-hidden />
              <span className="text-muted-foreground">{l.label}</span>
              <span className="ml-auto font-medium tabular-nums">{rupees(report.components[l.key])}</span>
            </li>
          ))}
        </ul>
      </div>

      {report.suggestions.length > 0 && (
        <p className="rounded-lg bg-muted px-3 py-2 text-caption text-muted-foreground">{report.suggestions.join(" ")}</p>
      )}
    </Card>
  );
}
