"use client";

import { KeyRound } from "lucide-react";
import { useState } from "react";
import { BrandMark } from "./brand-mark";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

/** Shown when the deployment is protected by a shared access code. */
export function AccessGate({ onSubmit, rejected }: { onSubmit: (code: string) => void; rejected: boolean }) {
  const [code, setCode] = useState("");
  return (
    <main className="grid min-h-dvh place-items-center p-6" data-testid="access-gate">
      <form
        className="w-full max-w-sm rounded-2xl border bg-card p-8 shadow-soft"
        onSubmit={(e) => { e.preventDefault(); if (code.trim()) onSubmit(code.trim()); }}
      >
        <BrandMark className="mb-4 size-12" />
        <h1 className="font-heading text-title">Enter the access code</h1>
        <p className="mt-1 text-sm text-muted-foreground">This Yatra AI deployment is private. Ask whoever shared it with you for the code.</p>
        <Textarea
          value={code} onChange={(e) => setCode(e.target.value.replace(/\n/g, ""))} rows={1} aria-label="Access code" autoFocus
          className="mt-4 min-h-9 resize-none font-mono"
        />
        {rejected && <p className="mt-2 text-sm text-destructive" role="alert">That code wasn&apos;t accepted.</p>}
        <Button type="submit" className="mt-4 w-full" disabled={!code.trim()}><KeyRound />Continue</Button>
      </form>
    </main>
  );
}
