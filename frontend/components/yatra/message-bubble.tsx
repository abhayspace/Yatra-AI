import { CircleAlert, History } from "lucide-react";
import { BrandMark } from "./brand-mark";
import { ToolTrace } from "./tool-trace";
import { Badge } from "@/components/ui/badge";
import type { ChatMessage } from "@/lib/types";
import { cn } from "cn";

export function MessageBubble({ message, onOpenVersion }: { message: ChatMessage; onOpenVersion?: (version: number) => void }) {
  if (message.role === "user") {
    return (
      <div className="animate-rise flex justify-end">
        <p className="max-w-[88%] whitespace-pre-wrap rounded-2xl rounded-br-md bg-primary px-4 py-2.5 text-primary-foreground shadow-soft">
          {message.content}
        </p>
      </div>
    );
  }
  return (
    <div className="animate-rise flex gap-2.5">
      <BrandMark className="mt-0.5 size-7 shrink-0" />
      <div className="min-w-0 flex-1">
        <div
          className={cn(
            "rounded-2xl rounded-tl-md border px-4 py-2.5 shadow-soft",
            message.isError ? "border-destructive/30 bg-destructive/8 text-destructive" : "border-border bg-card",
          )}
        >
          {message.isError && <CircleAlert className="mr-1.5 mb-0.5 inline size-4" aria-hidden />}
          <p className="whitespace-pre-wrap">{message.content}</p>
          {message.itineraryVersion && message.itineraryVersion > 0 && !message.isError && (
            <button
              type="button"
              onClick={() => onOpenVersion?.(message.itineraryVersion!)}
              className="mt-2 inline-flex"
              aria-label={`Show itinerary version ${message.itineraryVersion}`}
            >
              <Badge variant={message.itineraryVersion > 1 ? "brand" : "teal"} className="cursor-pointer gap-1">
                <History aria-hidden />
                {message.itineraryVersion > 1 ? `Updated to v${message.itineraryVersion}` : "Itinerary v1"}
              </Badge>
            </button>
          )}
        </div>
        <ToolTrace calls={message.toolTrace} />
      </div>
    </div>
  );
}
