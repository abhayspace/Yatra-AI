"use client";

import { ArrowUp } from "lucide-react";
import { useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const MAX = 2000;

export function Composer({ busy, onSend, placeholder }: { busy: boolean; onSend: (text: string) => void; placeholder: string }) {
  const [text, setText] = useState("");
  const ref = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  }, [text]);

  const submit = () => {
    if (!text.trim() || busy) return;
    onSend(text);
    setText("");
  };

  return (
    <form
      className="border-t bg-card/60 p-3"
      onSubmit={(e) => { e.preventDefault(); submit(); }}
    >
      <div className="flex items-end gap-2 rounded-2xl border bg-card p-2 shadow-soft focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/40">
        <Textarea
          ref={ref} value={text} rows={1} maxLength={MAX} placeholder={placeholder} aria-label="Message Yatra AI"
          onChange={(e) => setText(e.target.value)}
          onKeyDown={(e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); submit(); } }}
          className="max-h-40 min-h-9 flex-1 resize-none border-0 bg-transparent px-2 py-1.5 shadow-none focus-visible:ring-0 dark:bg-transparent"
        />
        <Button type="submit" size="icon-lg" disabled={busy || !text.trim()} aria-label="Send message" className="rounded-xl">
          <ArrowUp />
        </Button>
      </div>
      <p className="mt-1.5 px-1 text-caption text-muted-foreground">
        Enter to send · Shift+Enter for a new line{text.length > MAX - 200 ? ` · ${MAX - text.length} characters left` : ""}
      </p>
    </form>
  );
}
