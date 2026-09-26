import { CircleAlert, CircleCheck, Info, TriangleAlert } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { rupees } from "@/lib/format";
import type { BudgetStatus } from "@/lib/types";
import { cn } from "cn";

const STATUS = {
  within_budget: { variant: "success", icon: CircleCheck, text: "Within budget" },
  tight: { variant: "warning", icon: TriangleAlert, text: "Tight fit" },
  over_budget: { variant: "destructive", icon: CircleAlert, text: "Over budget" },
  no_budget_given: { variant: "secondary", icon: Info, text: "No budget set" },
} as const;

/** Budget status pill: success / warning / error semantics. */
export function CostBadge({ status, className }: { status: BudgetStatus; className?: string }) {
  const s = STATUS[status];
  const Icon = s.icon;
  return (
    <Badge variant={s.variant} className={cn("h-6 px-2.5 text-[0.8rem]", className)}>
      <Icon aria-hidden />
      {s.text}
    </Badge>
  );
}

/** Price shown next to an itinerary block. */
export function PriceTag({ amount, perPerson, className }: { amount: number; perPerson?: number; className?: string }) {
  if (amount <= 0) {
    return <span className={cn("text-caption font-medium text-success", className)}>Free</span>;
  }
  return (
    <span className={cn("text-right", className)}>
      <span className="block text-sm font-semibold tabular-nums">{rupees(amount)}</span>
      {perPerson !== undefined && perPerson > 0 && (
        <span className="block text-caption text-muted-foreground tabular-nums">{rupees(perPerson)} pp</span>
      )}
    </span>
  );
}
