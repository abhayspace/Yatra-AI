"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ApiRequestError, api, runTurn } from "./api";
import type {
  ApiErrorBody, ApiMessage, BudgetReport, ChatMessage, ChatResult, Intent, Itinerary, StreamEvent, ToolCall,
  TripPayload, TripSummary, VersionRow,
} from "./types";

function fromApi(m: ApiMessage): ChatMessage {
  return {
    id: m.id, role: m.role, content: m.content, toolTrace: m.tool_trace ?? [],
    itineraryVersion: m.itinerary_version, isError: m.is_error,
  };
}

function toBody(err: unknown): ApiErrorBody {
  if (err instanceof ApiRequestError) return err.body;
  return { code: "internal", message: "Something went wrong. Please try again." };
}

export interface LiveProgress {
  steps: string[];
  tools: ToolCall[];
}

/** All client state for the app: the active trip, streamed progress, versions and errors. */
export function useYatra() {
  const [booting, setBooting] = useState(true);
  const [bootError, setBootError] = useState<ApiErrorBody | null>(null);
  const [bootNonce, setBootNonce] = useState(0);
  const [tripId, setTripId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [itinerary, setItinerary] = useState<Itinerary | null>(null);
  const [budget, setBudget] = useState<BudgetReport | null>(null);
  const [intent, setIntent] = useState<Intent | null>(null);
  const [versions, setVersions] = useState<VersionRow[]>([]);
  const [viewVersion, setViewVersion] = useState<number | null>(null);
  const [trips, setTrips] = useState<TripSummary[]>([]);
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState<LiveProgress>({ steps: [], tools: [] });
  const [error, setError] = useState<ApiErrorBody | null>(null);
  const [freshVersion, setFreshVersion] = useState<number | null>(null);
  const lastMessage = useRef<string | null>(null);
  const tripRef = useRef<string | null>(null);

  const applyPayload = useCallback((p: TripPayload) => {
    tripRef.current = p.trip.id;
    setTripId(p.trip.id);
    setMessages(p.messages.map(fromApi));
    setItinerary(p.trip.itinerary);
    setBudget(p.trip.budget_report);
    setIntent(p.trip.intent);
    setVersions(p.versions);
    setViewVersion(null);
    setFreshVersion(null);
  }, []);

  const refreshTrips = useCallback(async () => {
    try {
      setTrips(await api.listTrips());
    } catch {
      /* the trips list is a convenience; the main error surfaces elsewhere */
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    Promise.all([api.latestTrip(), api.listTrips()])
      .then(([latest, list]) => {
        if (cancelled) return;
        setTrips(list);
        if (latest) applyPayload(latest);
        setBooting(false);
      })
      .catch((err) => {
        if (cancelled) return;
        setBootError(toBody(err));
        setBooting(false);
      });
    return () => {
      cancelled = true;
    };
  }, [applyPayload, bootNonce]);

  const retryBoot = useCallback(() => {
    setBooting(true);
    setBootError(null);
    setBootNonce((n) => n + 1);
  }, []);

  const send = useCallback(
    async (text: string) => {
      const message = text.trim();
      if (!message || busy) return;
      lastMessage.current = message;
      setError(null);
      setBusy(true);
      setProgress({ steps: [], tools: [] });
      setMessages((prev) => [
        ...prev,
        { id: `local-${Date.now()}`, role: "user", content: message, toolTrace: [], itineraryVersion: null, isError: false },
      ]);
      const onEvent = (event: StreamEvent) => {
        if (event.type === "trip") {
          tripRef.current = event.trip_id;
          setTripId(event.trip_id);
        } else if (event.type === "step") {
          setProgress((p) => ({ ...p, steps: [...p.steps, event.label] }));
        } else if (event.type === "tool") {
          setProgress((p) => ({ ...p, tools: [...p.tools, event.call] }));
        }
      };
      try {
        const result: ChatResult = await runTurn(tripRef.current, message, onEvent);
        tripRef.current = result.trip_id;
        setTripId(result.trip_id);
        setMessages((prev) => [
          ...prev,
          {
            id: `local-a-${Date.now()}`, role: "assistant", content: result.reply, toolTrace: result.tool_trace,
            itineraryVersion: result.error ? null : result.version, isError: !!result.error,
          },
        ]);
        if (result.error) {
          setError(result.error);
        } else {
          setItinerary(result.itinerary);
          setBudget(result.budget_report);
          setIntent(result.intent);
          setViewVersion(null);
        }
        // pull the authoritative version list from the database
        try {
          const payload = await api.getTrip(result.trip_id);
          setVersions(payload.versions);
          if (!result.error && result.itinerary && payload.versions.length) {
            const latest = payload.versions[payload.versions.length - 1].version_number;
            setFreshVersion(latest > 1 ? latest : null);
          }
        } catch {
          /* versions refresh on next load */
        }
        void refreshTrips();
      } catch (err) {
        setError(toBody(err));
      } finally {
        setBusy(false);
      }
    },
    [busy, refreshTrips],
  );

  const retry = useCallback(() => {
    const last = lastMessage.current;
    if (!last) return;
    // drop the failed user message so it is not shown twice
    setMessages((prev) => {
      const idx = [...prev].reverse().findIndex((m) => m.role === "user");
      if (idx === -1) return prev;
      const cut = prev.length - 1 - idx;
      return prev.filter((_, i) => i < cut);
    });
    void send(last);
  }, [send]);

  const newTrip = useCallback(() => {
    tripRef.current = null;
    setTripId(null);
    setMessages([]);
    setItinerary(null);
    setBudget(null);
    setIntent(null);
    setVersions([]);
    setViewVersion(null);
    setFreshVersion(null);
    setError(null);
  }, []);

  const openTrip = useCallback(
    async (id: string) => {
      setError(null);
      try {
        applyPayload(await api.getTrip(id));
      } catch (err) {
        setError(toBody(err));
      }
    },
    [applyPayload],
  );

  const shown = useMemo(() => {
    if (viewVersion !== null) {
      const row = versions.find((v) => v.version_number === viewVersion);
      if (row) return { itinerary: row.itinerary_json, budget: row.budget_json ?? budget, version: row.version_number };
    }
    const latest = versions.length ? versions[versions.length - 1].version_number : itinerary ? 1 : 0;
    return { itinerary, budget, version: latest };
  }, [viewVersion, versions, itinerary, budget]);

  const previousItinerary = useMemo(() => {
    const idx = versions.findIndex((v) => v.version_number === shown.version);
    return idx > 0 ? versions[idx - 1].itinerary_json : null;
  }, [versions, shown.version]);

  return {
    booting, bootError, retryBoot, tripId, messages, intent, versions, trips, busy, progress, error,
    dismissError: () => setError(null), send, retry, newTrip, openTrip, shown, previousItinerary,
    viewVersion, setViewVersion, freshVersion,
    isLatest: viewVersion === null || (versions.length > 0 && viewVersion === versions[versions.length - 1].version_number),
  };
}
