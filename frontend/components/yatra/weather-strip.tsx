import { Cloud, CloudRain, CloudSun, Snowflake, Sun, Thermometer } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import type { DayWeather } from "@/lib/types";

/** Icon for a day's weather (rain, heat, snow, clear, or partly cloudy). */
export function WeatherIcon({ weather, className }: { weather: DayWeather | null; className?: string }) {
  if (!weather) return <Cloud className={className} aria-hidden />;
  if (weather.rainy) return <CloudRain className={className} aria-hidden />;
  if (weather.hot) return <Thermometer className={className} aria-hidden />;
  if (/snow/i.test(weather.summary)) return <Snowflake className={className} aria-hidden />;
  if (/clear/i.test(weather.summary)) return <Sun className={className} aria-hidden />;
  return <CloudSun className={className} aria-hidden />;
}

/** Weather line for one day, with the source (live forecast or last year's conditions). */
export function WeatherStrip({ weather }: { weather: DayWeather | null }) {
  if (!weather) return null;
  const temps =
    weather.temp_max_c !== null
      ? `${Math.round(weather.temp_min_c ?? weather.temp_max_c)}° / ${Math.round(weather.temp_max_c)}°C`
      : null;
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 rounded-xl bg-secondary px-3 py-2 text-sm text-secondary-foreground" data-testid="weather-strip">
      <WeatherIcon weather={weather} className="size-4" />
      <span className="font-medium">{weather.summary || "Weather"}</span>
      {temps && <span className="tabular-nums">{temps}</span>}
      {weather.precip_probability !== null && <span className="tabular-nums">{Math.round(weather.precip_probability)}% rain</span>}
      {weather.precip_probability === null && weather.precip_mm !== null && <span className="tabular-nums">{weather.precip_mm} mm rain</span>}
      <Badge variant={weather.source === "forecast" ? "teal" : "warning"} className="ml-auto">
        {weather.source === "forecast" ? "Live forecast" : "Typical (last year)"}
      </Badge>
    </div>
  );
}
