"use client";

import { RefreshCw, TriangleAlert } from "lucide-react";
import { BrandMark } from "@/components/yatra/brand-mark";
import { Button } from "@/components/ui/button";

/** Last-resort boundary: a designed page instead of the framework's default error screen. */
export default function GlobalError({ reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <div className="max-w-md rounded-2xl border bg-card p-8 text-center shadow-soft">
        <BrandMark className="mx-auto mb-4 size-12" />
        <TriangleAlert className="mx-auto mb-2 size-6 text-destructive" aria-hidden />
        <h1 className="font-heading text-title">Something went wrong</h1>
        <p className="mt-2 text-sm text-muted-foreground">
          The page hit an unexpected problem. Your saved trips are safe, so reloading should bring you back to where you were.
        </p>
        <Button className="mt-5" onClick={reset}><RefreshCw />Try again</Button>
      </div>
    </main>
  );
}
