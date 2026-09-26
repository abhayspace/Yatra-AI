-- Yatra AI schema: trips, conversation messages and per-revision itinerary versions.
-- Apply with the Supabase CLI (`supabase db push`) or paste into the SQL editor.

create table if not exists public.trips (
    id              uuid primary key default gen_random_uuid(),
    created_at      timestamptz not null default now(),
    updated_at      timestamptz not null default now(),
    title           text,
    origin          text,
    destination     text,
    start_date      date,
    duration_days   integer check (duration_days between 1 and 14),
    travelers       integer check (travelers between 1 and 20),
    budget          numeric(12, 2) check (budget is null or budget > 0),
    interests       text[] not null default '{}',
    pace            text check (pace in ('relaxed', 'balanced', 'packed')),
    -- graph state carried between turns (intent, candidates, weather, itinerary, budget report, ...)
    state_json      jsonb not null default '{}'::jsonb,
    current_version integer not null default 0
);

create table if not exists public.messages (
    id                 uuid primary key default gen_random_uuid(),
    trip_id            uuid not null references public.trips (id) on delete cascade,
    role               text not null check (role in ('user', 'assistant')),
    content            text not null,
    -- tools the agent fired for this turn, shown as the "tools used" trace in the UI
    tool_trace         jsonb not null default '[]'::jsonb,
    itinerary_version  integer,
    is_error           boolean not null default false,
    created_at         timestamptz not null default now()
);

create table if not exists public.itinerary_versions (
    id               uuid primary key default gen_random_uuid(),
    trip_id          uuid not null references public.trips (id) on delete cascade,
    version_number   integer not null check (version_number >= 1),
    itinerary_json   jsonb not null,
    budget_json      jsonb,
    total_cost       numeric(12, 2) not null check (total_cost >= 0),
    change_summary   jsonb not null default '[]'::jsonb,
    created_at       timestamptz not null default now(),
    unique (trip_id, version_number)
);

create index if not exists trips_updated_at_idx on public.trips (updated_at desc);
create index if not exists messages_trip_created_idx on public.messages (trip_id, created_at);
create index if not exists itinerary_versions_trip_idx on public.itinerary_versions (trip_id, version_number);

create or replace function public.touch_updated_at() returns trigger
language plpgsql as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trips_touch_updated_at on public.trips;
create trigger trips_touch_updated_at
    before update on public.trips
    for each row execute function public.touch_updated_at();

-- The backend uses the service role key, which bypasses row level security. Enabling RLS with no
-- policies means the public anon key can read or write nothing, so the tables are unreachable
-- from a browser even though the frontend never talks to Supabase.
alter table public.trips enable row level security;
alter table public.messages enable row level security;
alter table public.itinerary_versions enable row level security;
