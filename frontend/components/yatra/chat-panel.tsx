"use client";

import { useEffect, useRef } from "react";
import { ChatSkeleton } from "./skeletons";
import { ChatWelcome } from "./empty-states";
import { Composer } from "./composer";
import { ErrorBanner } from "./error-banner";
import { MessageBubble } from "./message-bubble";
import { ThinkingIndicator } from "./thinking-indicator";
import type { ApiErrorBody, ChatMessage } from "@/lib/types";
import type { LiveProgress } from "@/lib/use-yatra";

export function ChatPanel({
  booting, bootError, onRetryBoot, messages, busy, progress, error, onSend, onRetry, onDismissError, onOpenVersion, hasItinerary,
}: {
  booting: boolean;
  bootError: ApiErrorBody | null;
  onRetryBoot: () => void;
  messages: ChatMessage[];
  busy: boolean;
  progress: LiveProgress;
  error: ApiErrorBody | null;
  onSend: (text: string) => void;
  onRetry: () => void;
  onDismissError: () => void;
  onOpenVersion: (v: number) => void;
  hasItinerary: boolean;
}) {
  const endRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [messages.length, progress.steps.length, progress.tools.length, busy, error]);

  const empty = !booting && messages.length === 0 && !busy;
  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-hidden rounded-2xl border bg-card/70 shadow-soft" data-testid="chat-panel">
      <div className="min-h-0 flex-1 overflow-y-auto scrollbar-thin" aria-live="polite">
        {booting ? (
          <ChatSkeleton />
        ) : empty && !bootError ? (
          <ChatWelcome onPick={onSend} />
        ) : (
          <div className="space-y-4 p-4">
            {messages.map((m) => <MessageBubble key={m.id} message={m} onOpenVersion={onOpenVersion} />)}
            {busy && <ThinkingIndicator progress={progress} />}
            {bootError && <ErrorBanner error={bootError} onRetry={onRetryBoot} />}
            {error && <ErrorBanner error={error} onRetry={onRetry} onDismiss={onDismissError} />}
            <div ref={endRef} />
          </div>
        )}
        {empty && bootError && <div className="p-4"><ErrorBanner error={bootError} onRetry={onRetryBoot} /></div>}
      </div>
      <Composer
        busy={busy || booting}
        onSend={onSend}
        placeholder={hasItinerary ? "Ask for a change, e.g. “make it 3 days”" : "Describe your trip: where from, how long, budget, interests…"}
      />
    </div>
  );
}
