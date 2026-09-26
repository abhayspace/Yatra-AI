"use client";

import {
  ArrowLeftRight, Brain, Calculator, CalendarRange, ChevronDown, CircleAlert, CloudSun, Info, MapPin, MessageSquare, Plus, RefreshCw,
  Route, Scale, Search, ShieldAlert, ShieldCheck, Wrench, type LucideIcon,
} from "lucide-react";
import { createElement, useState } from "react";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import { rupees } from "@/lib/format";
import type { ToolCall } from "@/lib/types";
import { cn } from "cn";

const TOOL_ICONS: Record<string, LucideIcon> = {
  intent_parser: Brain,
  followup_parser: Brain,
  plan: Route,
  destination_search: Search,
  place_search: MapPin,
  weather: CloudSun,
  itinerary_builder: CalendarRange,
  budget: Calculator,
  budget_adjust: Scale,
  compare_alternatives: ArrowLeftRight,
  input_guard: ShieldAlert,
  output_guard: ShieldCheck,
  replan: RefreshCw,
  answer: MessageSquare,
  clarify: Info,
  new_trip: Plus,
};

const STATUS_STYLE: Record<ToolCall["status"], string> = {
  ok: "border-border bg-card text-foreground",
  flagged: "border-warning/50 bg-warning/12 text-warning-foreground dark:text-warning",
  error: "border-destructive/40 bg-destructive/10 text-destructive",
};

function ToolIcon({ name, error, className }: { name: string; error?: boolean; className?: string }) {
  return createElement(error ? CircleAlert : (TOOL_ICONS[name] ?? Wrench), { className, "aria-hidden": true });
}

/** One tool the agent used, shown as a compact chip. */
export function ToolCallChip({ call, className }: { call: ToolCall; className?: string }) {
  return (
    <span
      className={cn(
        "animate-rise inline-flex max-w-full items-center gap-1.5 rounded-full border px-2.5 py-1 text-caption font-medium",
        STATUS_STYLE[call.status],
        className,
      )}
      title={call.summary}
    >
      <ToolIcon name={call.name} error={call.status === "error"} className="size-3.5 shrink-0" />
      <span className="truncate">{call.label}</span>
      {call.duration_ms > 0 && <span className="text-muted-foreground tabular-nums">{call.duration_ms} ms</span>}
    </span>
  );
}

type Row = { id: string; name: string; score: number; reasons: string[]; min_cost: number | null };

function Details({ call }: { call: ToolCall }) {
  if (call.name === "destination_search") {
    const rows = (call.result.candidates as Row[] | undefined) ?? [];
    if (!rows.length) return null;
    return (
      <ol className="mt-2 space-y-1.5">
        {rows.map((c, i) => (
          <li key={c.id} className="rounded-lg bg-muted/60 px-2.5 py-1.5">
            <div className="flex items-baseline justify-between gap-2">
              <span className="font-medium">{i + 1}. {c.name.replace(/\s*\(.*\)/, "")}</span>
              <span className="text-caption text-muted-foreground tabular-nums">score {c.score}{c.min_cost ? ` · from ${rupees(c.min_cost)}` : ""}</span>
            </div>
            {c.reasons.length > 0 && <p className="text-caption text-muted-foreground">{c.reasons.join(" · ")}</p>}
          </li>
        ))}
      </ol>
    );
  }
  if (call.name === "compare_alternatives") {
    const alts = (call.result.alternatives as { destination_id: string; name: string; total_cost: number; difference_vs_chosen: number; within_budget: boolean | null }[] | undefined) ?? [];
    if (!alts.length) return null;
    return (
      <ul className="mt-2 space-y-1.5">
        {alts.map((a) => (
          <li key={a.destination_id} className="flex justify-between gap-2 rounded-lg bg-muted/60 px-2.5 py-1.5 text-caption">
            <span className="font-medium">{a.name.replace(/\s*\(.*\)/, "")}</span>
            <span className="tabular-nums text-muted-foreground">{rupees(a.total_cost)} ({a.difference_vs_chosen >= 0 ? "+" : "-"}{rupees(Math.abs(a.difference_vs_chosen))}){a.within_budget === false ? " · over budget" : ""}</span>
          </li>
        ))}
      </ul>
    );
  }
  if (call.name === "weather") {
    const days = (call.result.days as { date: string; summary: string; max_c: number | null; rain_pct: number | null }[] | undefined) ?? [];
    if (!days.length) return null;
    return (
      <div className="mt-2 flex flex-wrap gap-1.5">
        {days.map((d) => (
          <span key={d.date} className="rounded-lg bg-muted/60 px-2 py-1 text-caption tabular-nums">
            {d.date.slice(5)} · {d.summary || "n/a"}{d.max_c !== null ? ` · ${Math.round(d.max_c)}°` : ""}{d.rain_pct ? ` · ${Math.round(d.rain_pct)}% rain` : ""}
          </span>
        ))}
      </div>
    );
  }
  if (call.name === "budget") {
    const parts = Object.entries(call.args).filter(([, v]) => typeof v === "number") as [string, number][];
    if (!parts.length) return null;
    return (
      <dl className="mt-2 grid grid-cols-2 gap-x-4 gap-y-1 sm:grid-cols-3">
        {parts.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2 text-caption">
            <dt className="text-muted-foreground">{k.replace("_", " ")}</dt>
            <dd className="font-medium tabular-nums">{rupees(v)}</dd>
          </div>
        ))}
      </dl>
    );
  }
  const items = (call.args.patterns ?? call.args.violations) as string[] | undefined;
  if (Array.isArray(items) && items.length) {
    return <p className="mt-1.5 text-caption text-muted-foreground">{items.join(" · ")}</p>;
  }
  return null;
}

/** Expandable "tools used" trace under an assistant message. */
export function ToolTrace({ calls, defaultOpen = false }: { calls: ToolCall[]; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  if (!calls.length) return null;
  const issues = calls.filter((c) => c.status !== "ok").length;
  return (
    <Collapsible open={open} onOpenChange={setOpen} className="mt-2">
      <CollapsibleTrigger className="group flex w-full items-center gap-2 rounded-lg py-1 text-left text-caption font-medium text-muted-foreground transition-colors hover:text-foreground">
        <Wrench className="size-3.5" aria-hidden />
        <span>Tools used ({calls.length})</span>
        {issues > 0 && <span className="rounded-full bg-warning/25 px-1.5 text-warning-foreground dark:text-warning">{issues} flagged</span>}
        <ChevronDown className={cn("ml-auto size-4 transition-transform", open && "rotate-180")} aria-hidden />
      </CollapsibleTrigger>
      {!open && (
        <div className="mt-1 flex flex-wrap gap-1.5">
          {calls.map((c, i) => <ToolCallChip key={`${c.name}-${i}`} call={c} />)}
        </div>
      )}
      <CollapsibleContent>
        <ul className="mt-1 space-y-2">
          {calls.map((c, i) => {
            return (
              <li key={`${c.name}-${i}`} className={cn("rounded-xl border px-3 py-2 text-sm", STATUS_STYLE[c.status])}>
                <div className="flex items-center gap-2 font-medium">
                  <ToolIcon name={c.name} error={c.status === "error"} className="size-4 shrink-0" />
                  <span>{c.label}</span>
                  <span className="ml-auto text-caption font-normal text-muted-foreground tabular-nums">{c.duration_ms} ms</span>
                </div>
                <p className="mt-0.5 text-caption text-foreground/80">{c.summary}</p>
                <Details call={c} />
              </li>
            );
          })}
        </ul>
      </CollapsibleContent>
    </Collapsible>
  );
}
