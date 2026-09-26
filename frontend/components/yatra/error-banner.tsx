import { CloudOff, Database, RefreshCw, ServerCrash, ShieldAlert, TriangleAlert, WifiOff, X, type LucideIcon } from "lucide-react";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import type { ApiErrorBody } from "@/lib/types";

const COPY: Record<string, { title: string; icon: LucideIcon; retry: boolean }> = {
  llm: { title: "The AI model isn't responding", icon: CloudOff, retry: true },
  database: { title: "Your trips can't be saved or loaded right now", icon: Database, retry: true },
  network: { title: "Can't reach the Yatra AI server", icon: WifiOff, retry: true },
  config: { title: "The server isn't fully configured", icon: ServerCrash, retry: false },
  limit: { title: "That request was too complex", icon: ShieldAlert, retry: false },
  tool: { title: "A planning tool couldn't complete", icon: TriangleAlert, retry: true },
  access_code_required: { title: "This deployment needs an access code", icon: ShieldAlert, retry: false },
  unauthorized: { title: "This browser couldn't be identified", icon: ShieldAlert, retry: false },
  rate_limited: { title: "Slow down a little", icon: ShieldAlert, retry: true },
  invalid: { title: "That message can't be sent", icon: TriangleAlert, retry: false },
  not_found: { title: "That trip no longer exists", icon: TriangleAlert, retry: false },
};
const DEFAULT = { title: "Something went wrong", icon: ServerCrash, retry: true };

/** Designed error state for LLM, database, network and tool failures. Never shows a stack trace. */
export function ErrorBanner({ error, onRetry, onDismiss }: { error: ApiErrorBody; onRetry?: () => void; onDismiss?: () => void }) {
  const copy = COPY[error.code] ?? DEFAULT;
  const Icon = copy.icon;
  return (
    <Alert variant="destructive" className="animate-rise" data-testid="error-banner" data-code={error.code}>
      <Icon />
      <AlertTitle>{copy.title}</AlertTitle>
      <AlertDescription>
        <p>{error.message}</p>
        <div className="mt-2 flex gap-2">
          {copy.retry && onRetry && (
            <Button size="sm" variant="outline" onClick={onRetry}><RefreshCw />Try again</Button>
          )}
          {onDismiss && (
            <Button size="sm" variant="ghost" onClick={onDismiss}><X />Dismiss</Button>
          )}
        </div>
      </AlertDescription>
    </Alert>
  );
}
