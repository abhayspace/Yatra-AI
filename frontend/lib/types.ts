export type Pace = "relaxed" | "balanced" | "packed";
export type StayTier = "budget" | "mid" | "premium";
export type BlockKind = "transit" | "stay" | "activity" | "meal" | "leisure";

export interface Block {
  id: string;
  time_of_day: "morning" | "afternoon" | "evening";
  start: string;
  end: string;
  kind: BlockKind;
  category: string;
  title: string;
  description: string;
  place_id: string | null;
  area: string | null;
  cost_per_person: number;
  cost_total: number;
  indoor: boolean;
  weather_note: string | null;
}

export interface DayWeather {
  date: string;
  temp_max_c: number | null;
  temp_min_c: number | null;
  precip_probability: number | null;
  precip_mm: number | null;
  summary: string;
  rainy: boolean;
  hot: boolean;
  source: "forecast" | "last-year-archive";
}

export interface Day {
  day: number;
  date: string | null;
  theme: string;
  blocks: Block[];
  weather: DayWeather | null;
  stay_cost: number;
  local_transport: number;
  day_cost: number;
}

export interface CostLines {
  transport: number;
  stay: number;
  food: number;
  activities: number;
  local_transport: number;
}

export interface SourceRef {
  kind: "dataset" | "weather";
  label: string;
  detail: string;
}

export interface Itinerary {
  destination_id: string;
  destination_name: string;
  origin: string;
  start_date: string | null;
  duration_days: number;
  travelers: number;
  pace: Pace;
  stay_tier: StayTier;
  transport_mode: string;
  rooms: number;
  nights: number;
  days: Day[];
  cost_lines: CostLines;
  total_cost: number;
  notes: string[];
  sources: SourceRef[];
}

export type BudgetStatus = "within_budget" | "tight" | "over_budget" | "no_budget_given";

export interface BudgetReport {
  components: CostLines;
  total: number;
  per_person: number;
  budget: number | null;
  remaining: number | null;
  status: BudgetStatus;
  overage: number;
  breakdown_pct: Record<string, number>;
  suggestions: string[];
}

export interface ToolCall {
  name: string;
  label: string;
  status: "ok" | "error" | "flagged";
  args: Record<string, unknown>;
  summary: string;
  result: Record<string, unknown>;
  duration_ms: number;
}

export interface Intent {
  origin: string | null;
  destinations: string[];
  region: string | null;
  duration_days: number | null;
  travelers: number | null;
  budget: number | null;
  interests: string[];
  interest_weights: Record<string, number>;
  pace: Pace | null;
  start_date: string | null;
  assumptions: string[];
}

export interface ApiErrorBody {
  code: string;
  message: string;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  toolTrace: ToolCall[];
  itineraryVersion: number | null;
  isError: boolean;
}

export interface ApiMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  tool_trace: ToolCall[];
  itinerary_version: number | null;
  is_error: boolean;
  created_at: string;
}

export interface VersionRow {
  version_number: number;
  itinerary_json: Itinerary;
  budget_json: BudgetReport | null;
  total_cost: number;
  change_summary: string[];
  created_at: string;
}

export interface TripSummary {
  id: string;
  title: string | null;
  origin: string | null;
  destination: string | null;
  start_date: string | null;
  duration_days: number | null;
  travelers: number | null;
  budget: number | null;
  interests: string[];
  pace: Pace | null;
  current_version: number;
  updated_at: string;
  created_at: string;
}

export interface TripPayload {
  trip: TripSummary & { intent: Intent | null; itinerary: Itinerary | null; budget_report: BudgetReport | null };
  messages: ApiMessage[];
  versions: VersionRow[];
}

export interface ChatResult {
  trip_id: string;
  reply: string;
  error: ApiErrorBody | null;
  tool_trace: ToolCall[];
  itinerary: Itinerary | null;
  budget_report: BudgetReport | null;
  intent: Intent | null;
  version: number;
  change_summary: string[];
  warnings: string[];
}

export type StreamEvent =
  | { type: "trip"; trip_id: string }
  | { type: "step"; node: string; label: string }
  | { type: "tool"; call: ToolCall }
  | { type: "done"; result: ChatResult }
  | { type: "error"; error: ApiErrorBody };
