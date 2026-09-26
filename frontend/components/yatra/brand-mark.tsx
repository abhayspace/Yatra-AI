import { cn } from "cn";

/** The Yatra AI logo mark: a compass ring with a winding route. Colours come from theme tokens. */
export function BrandMark({ className }: { className?: string }) {
  return (
    <svg viewBox="0 0 40 40" className={cn("size-9", className)} role="img" aria-label="Yatra AI">
      <rect width="40" height="40" rx="12" className="fill-primary" />
      <circle cx="20" cy="20" r="11.5" fill="none" stroke="currentColor" strokeOpacity="0.35" strokeWidth="1.4" className="text-primary-foreground" />
      <path
        d="M12.5 26.5c3.5-1 4-5.5 7.5-6.5s4.5-4.5 7.5-6"
        fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" className="text-primary-foreground"
      />
      <circle cx="12.5" cy="26.5" r="2" className="fill-primary-foreground" />
      <path d="M27.5 13.5l-1 4.2-3.4-2.6z" className="fill-primary-foreground" />
    </svg>
  );
}
