import Link from "next/link";
import { Compass } from "lucide-react";
import { BrandMark } from "@/components/yatra/brand-mark";
import { buttonVariants } from "@/components/ui/button";

export default function NotFound() {
  return (
    <main className="grid min-h-dvh place-items-center p-6">
      <div className="max-w-md rounded-2xl border bg-card p-8 text-center shadow-soft">
        <BrandMark className="mx-auto mb-4 size-12" />
        <h1 className="font-heading text-title">This route isn&apos;t on the map</h1>
        <p className="mt-2 text-sm text-muted-foreground">The page you asked for doesn&apos;t exist. Let&apos;s get you back to planning.</p>
        <Link href="/" className={buttonVariants({ className: "mt-5" })}><Compass />Plan a trip</Link>
      </div>
    </main>
  );
}
