import { BrandMark } from "./brand-mark";
import { ToolCallChip } from "./tool-trace";
import type { LiveProgress } from "@/lib/use-yatra";

/** The in-flight state: animated dots, the current step, and tool chips as they finish. */
export function ThinkingIndicator({ progress }: { progress: LiveProgress }) {
  const current = progress.steps[progress.steps.length - 1] ?? "Starting up";
  return (
    <div className="animate-rise flex gap-2.5" role="status" aria-live="polite">
      <BrandMark className="mt-0.5 size-7 shrink-0" />
      <div className="min-w-0 flex-1 rounded-2xl rounded-tl-md border border-border bg-card px-4 py-3 shadow-soft">
        <div className="flex items-center gap-2 text-muted-foreground">
          <span className="flex gap-1" aria-hidden>
            {[0, 1, 2].map((i) => (
              <span key={i} className="animate-dot size-1.5 rounded-full bg-primary" style={{ animationDelay: `${i * 0.18}s` }} />
            ))}
          </span>
          <span className="text-sm">{current}…</span>
        </div>
        {progress.tools.length > 0 && (
          <div className="mt-2.5 flex flex-wrap gap-1.5">
            {progress.tools.map((c, i) => <ToolCallChip key={`${c.name}-${i}`} call={c} />)}
          </div>
        )}
      </div>
    </div>
  );
}
