import { CloudSun, Database } from "lucide-react";
import type { SourceRef } from "@/lib/types";

/** Provenance: where the prices, places and weather in the plan came from. */
export function SourcesNote({ sources }: { sources: SourceRef[] }) {
  if (!sources.length) return null;
  return (
    <section className="rounded-xl border border-dashed bg-card/50 p-4" aria-label="Sources" data-testid="sources">
      <h3 className="mb-2 font-sans text-caption font-semibold uppercase tracking-wide text-muted-foreground">Where the numbers come from</h3>
      <ul className="space-y-2">
        {sources.map((s) => {
          const Icon = s.kind === "weather" ? CloudSun : Database;
          return (
            <li key={s.kind} className="flex gap-2.5 text-caption text-muted-foreground">
              <Icon className="mt-0.5 size-3.5 shrink-0 text-brand-2" aria-hidden />
              <span><b className="font-medium text-foreground">{s.label}.</b> {s.detail}</span>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
