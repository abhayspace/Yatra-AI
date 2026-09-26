import {
  Bird, BedDouble, Bus, Car, Coffee, Drama, Flower2, Landmark, Moon, Mountain, PartyPopper, Plane, ShoppingBag,
  Sparkles, TrainFront, Trees, Umbrella, Utensils, Waves, type LucideIcon,
} from "lucide-react";
import { cn } from "cn";

interface CategoryStyle {
  icon: LucideIcon;
  token: string;
  label: string;
}

const CATEGORIES: Record<string, CategoryStyle> = {
  nature: { icon: Trees, token: "--cat-nature", label: "Nature" },
  wildlife: { icon: Bird, token: "--cat-wildlife", label: "Wildlife" },
  food: { icon: Utensils, token: "--cat-food", label: "Food" },
  culture: { icon: Drama, token: "--cat-culture", label: "Culture" },
  heritage: { icon: Landmark, token: "--cat-heritage", label: "Heritage" },
  adventure: { icon: Mountain, token: "--cat-adventure", label: "Adventure" },
  beach: { icon: Waves, token: "--cat-beach", label: "Beach" },
  spiritual: { icon: Sparkles, token: "--cat-spiritual", label: "Spiritual" },
  nightlife: { icon: Moon, token: "--cat-nightlife", label: "Nightlife" },
  shopping: { icon: ShoppingBag, token: "--cat-shopping", label: "Shopping" },
  wellness: { icon: Flower2, token: "--cat-wellness", label: "Wellness" },
  relaxation: { icon: Coffee, token: "--cat-relaxation", label: "Relaxation" },
  train: { icon: TrainFront, token: "--cat-transit", label: "Train" },
  flight: { icon: Plane, token: "--cat-transit", label: "Flight" },
  bus: { icon: Bus, token: "--cat-transit", label: "Bus" },
  cab: { icon: Car, token: "--cat-transit", label: "Cab" },
  stay: { icon: BedDouble, token: "--cat-stay", label: "Stay" },
  leisure: { icon: Umbrella, token: "--cat-relaxation", label: "Leisure" },
  party: { icon: PartyPopper, token: "--cat-nightlife", label: "Evening" },
};
const FALLBACK: CategoryStyle = { icon: Sparkles, token: "--cat-default", label: "Activity" };

export function categoryStyle(category: string): CategoryStyle {
  return CATEGORIES[category] ?? FALLBACK;
}

/** Tinted rounded square with the icon for an activity category (nature, food, train, ...). */
export function ActivityIcon({ category, className }: { category: string; className?: string }) {
  const { icon: Icon, token } = categoryStyle(category);
  return (
    <span
      className={cn(
        "grid size-9 shrink-0 place-items-center rounded-xl bg-[color-mix(in_oklch,var(--c)_16%,transparent)] text-(--c)",
        className,
      )}
      style={{ ["--c" as string]: `var(${token})` }}
    >
      <Icon className="size-[1.15rem]" aria-hidden />
    </span>
  );
}

/** Small pill labelling an interest or category using the same colour token. */
export function CategoryPill({ category, className }: { category: string; className?: string }) {
  const { icon: Icon, token, label } = categoryStyle(category);
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full bg-[color-mix(in_oklch,var(--c)_14%,transparent)] px-2 py-0.5 text-caption font-medium text-(--c)",
        className,
      )}
      style={{ ["--c" as string]: `var(${token})` }}
    >
      <Icon className="size-3" aria-hidden />
      {label}
    </span>
  );
}
