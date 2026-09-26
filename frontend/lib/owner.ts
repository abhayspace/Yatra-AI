/**
 * Anonymous per-browser owner token. There are no accounts: the browser keeps a random secret and sends it with
 * every request, and the backend scopes trips to its hash, so one visitor cannot see or change another's trips.
 */
const KEY = "yatra-owner-token";
let memoryToken: string | null = null;

function randomToken(): string {
  return (crypto.randomUUID() + crypto.randomUUID()).replaceAll("-", "");
}

export function getOwnerToken(): string {
  try {
    const stored = localStorage.getItem(KEY);
    if (stored && /^[A-Za-z0-9_-]{32,128}$/.test(stored)) return stored;
    const fresh = randomToken();
    localStorage.setItem(KEY, fresh);
    return fresh;
  } catch {
    // storage blocked (private mode): the token lasts for this tab only
    memoryToken ??= randomToken();
    return memoryToken;
  }
}

const ACCESS_KEY = "yatra-access-code";
let memoryCode = "";

/** Optional shared access code for deployments that require one. */
export function getAccessCode(): string {
  try {
    return localStorage.getItem(ACCESS_KEY) ?? memoryCode;
  } catch {
    return memoryCode;
  }
}

export function setAccessCode(code: string): void {
  memoryCode = code;
  try {
    localStorage.setItem(ACCESS_KEY, code);
  } catch {
    /* kept in memory for this tab */
  }
}
