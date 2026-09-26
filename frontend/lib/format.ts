const inr = new Intl.NumberFormat("en-IN", { maximumFractionDigits: 0 });

export function rupees(value: number | null | undefined): string {
  if (value === null || value === undefined) return "-";
  return `₹${inr.format(Math.round(value))}`;
}

/** Compact form for tight spaces: ₹48.5K, ₹1.2L */
export function rupeesShort(value: number): string {
  if (value >= 100000) return `₹${(value / 100000).toFixed(value % 100000 === 0 ? 0 : 1)}L`;
  if (value >= 1000) return `₹${(value / 1000).toFixed(value % 1000 === 0 ? 0 : 1)}K`;
  return `₹${Math.round(value)}`;
}

function parseDate(iso: string): Date {
  const [y, m, d] = iso.split("-").map(Number);
  return new Date(y, m - 1, d);
}

export function shortDate(iso: string | null | undefined): string {
  if (!iso) return "";
  return parseDate(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export function weekday(iso: string | null | undefined): string {
  if (!iso) return "";
  return parseDate(iso).toLocaleDateString("en-IN", { weekday: "short" });
}

export function dateRange(start: string | null, days: number): string {
  if (!start) return `${days} days`;
  const s = parseDate(start);
  const e = new Date(s);
  e.setDate(e.getDate() + days - 1);
  const fmt = (d: Date) => d.toLocaleDateString("en-IN", { day: "numeric", month: "short" });
  return `${fmt(s)} - ${fmt(e)}`;
}

export function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.round(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min ago`;
  const hrs = Math.round(mins / 60);
  if (hrs < 24) return `${hrs} h ago`;
  return new Date(iso).toLocaleDateString("en-IN", { day: "numeric", month: "short" });
}

export function baseName(destination: string): string {
  return destination.replace(/\s*\(.*\)\s*/, "").trim();
}

export function capitalize(text: string): string {
  return text.charAt(0).toUpperCase() + text.slice(1);
}
