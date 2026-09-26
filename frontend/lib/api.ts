import type { ApiErrorBody, ChatResult, StreamEvent, TripPayload, TripSummary } from "./types";

export class ApiRequestError extends Error {
  constructor(public body: ApiErrorBody) {
    super(body.message);
  }
}

const NETWORK_ERROR: ApiErrorBody = {
  code: "network",
  message: "Check your connection, or that the backend is running, then try again.",
};

let apiUrlPromise: Promise<string> | null = null;

/** The backend URL comes from the frontend container's runtime config (API_URL), not the build. */
export function getApiUrl(): Promise<string> {
  if (!apiUrlPromise) {
    apiUrlPromise = fetch("/api/runtime-config")
      .then((r) => r.json())
      .then((j: { apiUrl: string }) => j.apiUrl)
      .catch(() => {
        apiUrlPromise = null;
        throw new ApiRequestError(NETWORK_ERROR);
      });
  }
  return apiUrlPromise;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = await getApiUrl();
  let res: Response;
  try {
    res = await fetch(`${base}${path}`, {
      ...init,
      headers: { "Content-Type": "application/json", ...(init?.headers ?? {}) },
    });
  } catch {
    throw new ApiRequestError(NETWORK_ERROR);
  }
  if (!res.ok) {
    let body: ApiErrorBody = { code: "internal", message: "Something went wrong. Please try again." };
    try {
      const json = await res.json();
      if (json?.detail?.code) body = json.detail;
      else if (res.status === 422) body = { code: "invalid", message: "That message couldn't be sent. Keep it between 1 and 2000 characters." };
    } catch {
      /* keep the generic body */
    }
    throw new ApiRequestError(body);
  }
  return (await res.json()) as T;
}

export const api = {
  listTrips: () => request<TripSummary[]>("/api/trips"),
  latestTrip: () => request<TripPayload | null>("/api/trips/latest"),
  getTrip: (id: string) => request<TripPayload>(`/api/trips/${id}`),
  chat: (tripId: string | null, message: string) =>
    request<ChatResult>("/api/chat", { method: "POST", body: JSON.stringify({ trip_id: tripId, message }) }),
};

/**
 * One chat turn over the WebSocket, streaming step/tool events as the agent works.
 * Resolves with the final result; rejects with ApiRequestError. If the socket cannot be
 * opened at all it falls back to the plain REST endpoint, so the app still works behind
 * proxies that block WebSockets.
 */
export async function runTurn(
  tripId: string | null,
  message: string,
  onEvent: (event: StreamEvent) => void,
): Promise<ChatResult> {
  const base = await getApiUrl();
  const wsUrl = base.replace(/^http/, "ws") + "/ws/chat";

  return new Promise<ChatResult>((resolve, reject) => {
    let opened = false;
    let settled = false;
    let socket: WebSocket;
    try {
      socket = new WebSocket(wsUrl);
    } catch {
      api.chat(tripId, message).then(resolve, reject);
      return;
    }
    const finish = (fn: () => void) => {
      if (settled) return;
      settled = true;
      fn();
      try {
        socket.close();
      } catch {
        /* already closed */
      }
    };

    socket.onopen = () => {
      opened = true;
      socket.send(JSON.stringify({ trip_id: tripId, message }));
    };
    socket.onmessage = (msg) => {
      let event: StreamEvent;
      try {
        event = JSON.parse(msg.data as string) as StreamEvent;
      } catch {
        return;
      }
      if (event.type === "done") finish(() => resolve(event.result));
      else if (event.type === "error") finish(() => reject(new ApiRequestError(event.error)));
      else onEvent(event);
    };
    socket.onerror = () => {
      if (!opened) {
        settled = true;
        api.chat(tripId, message).then(resolve, reject);
      }
    };
    socket.onclose = () => {
      if (opened && !settled) finish(() => reject(new ApiRequestError(NETWORK_ERROR)));
    };
  });
}
