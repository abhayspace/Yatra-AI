import { ArrowUpRight, CalendarRange, CloudSun, Compass, Wallet } from "lucide-react";
import { BrandMark } from "./brand-mark";

export const SUGGESTIONS = [
  "Plan a 5-day trip from Delhi for 2 people under ₹50K, focused on nature and food, with a relaxed itinerary.",
  "Weekend in Goa from Mumbai for 4 friends, beaches and nightlife, budget ₹60,000",
  "3 days in Jaipur from Delhi for a couple, heritage and street food, under 30K",
];

export function ChatWelcome({ onPick }: { onPick: (text: string) => void }) {
  return (
    <div className="flex h-full flex-col justify-center gap-5 p-5" data-testid="chat-welcome">
      <div className="flex items-center gap-3">
        <BrandMark className="size-12" />
        <div>
          <h2 className="font-heading text-title">Where to next?</h2>
          <p className="text-sm text-muted-foreground">Describe a trip in plain English. I&apos;ll plan it, check the weather and stick to your budget.</p>
        </div>
      </div>
      <ul className="space-y-2">
        {SUGGESTIONS.map((s) => (
          <li key={s}>
            <button
              type="button" onClick={() => onPick(s)}
              className="group flex w-full items-start gap-2 rounded-xl border bg-card p-3 text-left text-sm transition-colors hover:border-primary/60 hover:bg-primary/5"
            >
              <span className="flex-1">{s}</span>
              <ArrowUpRight className="mt-0.5 size-4 shrink-0 text-muted-foreground transition-colors group-hover:text-primary" aria-hidden />
            </button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ItineraryEmpty() {
  const items = [
    { icon: Compass, title: "Picks the destination", text: "From your interests, season and budget, using a curated dataset." },
    { icon: CloudSun, title: "Checks the weather", text: "Live forecast for your dates; rainy days move indoors." },
    { icon: Wallet, title: "Keeps to your budget", text: "Costs are computed by tools, never guessed by the model." },
    { icon: CalendarRange, title: "Re-plans in place", text: "Change days, budget or focus and only the affected parts update." },
  ];
  return (
    <div className="grid h-full place-items-center p-6" data-testid="itinerary-empty">
      <div className="max-w-lg text-center">
        <svg viewBox="0 0 240 90" className="mx-auto mb-4 h-24 w-64 text-primary" fill="none" aria-hidden>
          <path d="M8 70 C 50 20, 80 90, 120 45 S 190 10, 232 40" stroke="currentColor" strokeWidth="2.5" strokeDasharray="2 7" strokeLinecap="round" />
          <circle cx="8" cy="70" r="5" fill="currentColor" />
          <circle cx="120" cy="45" r="4" className="fill-brand-2" />
          <path d="M232 40 l-10 -7 v14 z" fill="currentColor" />
        </svg>
        <h2 className="font-heading text-title">Your itinerary will appear here</h2>
        <p className="mt-1 text-sm text-muted-foreground">Day-by-day plan, cost breakdown and every tool the agent used.</p>
        <ul className="mt-6 grid gap-3 text-left sm:grid-cols-2">
          {items.map(({ icon: Icon, title, text }) => (
            <li key={title} className="flex gap-3 rounded-xl border bg-card p-3">
              <span className="grid size-9 shrink-0 place-items-center rounded-lg bg-primary/12 text-primary"><Icon className="size-4.5" aria-hidden /></span>
              <span><b className="block text-sm">{title}</b><span className="text-caption text-muted-foreground">{text}</span></span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
