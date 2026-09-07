import type { Session, User } from "./types";
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public code = "",
    public details?: { location: string[]; message: string }[],
  ) {
    super(message);
  }
}
let refreshPromise: Promise<void> | null = null;
async function refreshSession() {
  const perform = async () => {
    const current = await fetch("/api/session", { cache: "no-store" });
    if (!current.ok)
      throw new ApiError(
        current.status,
        "Unable to restore your session. Please try again.",
      );
    const session: Session = await current.json();
    if (session.user && session.expires_at > Date.now() + 5000) return;
    const res = await fetch("/api/auth/refresh", { method: "POST" });
    if (!res.ok)
      throw new ApiError(
        res.status,
        "Your session has expired. Please sign in again.",
      );
  };
  if (!refreshPromise)
    refreshPromise = (
      typeof navigator !== "undefined" && navigator.locks
        ? navigator.locks.request("evently-session", perform)
        : perform()
    ).finally(() => {
      refreshPromise = null;
    });
  return refreshPromise;
}
export async function api<T>(
  path: string,
  options: RequestInit = {},
  retry = true,
): Promise<T> {
  const res = await fetch("/api/backend" + path, {
    ...options,
    headers: { "Content-Type": "application/json", ...options.headers },
    cache: "no-store",
  });
  if (res.status === 401 && retry) {
    try {
      await refreshSession();
    } catch (error) {
      if (
        error instanceof ApiError &&
        [401, 403].includes(error.status) &&
        typeof window !== "undefined"
      )
        window.dispatchEvent(new Event("evently-auth-check"));
      throw error;
    }
    return api<T>(path, options, false);
  }
  if (!res.ok) {
    if ([401, 403].includes(res.status) && typeof window !== "undefined")
      window.dispatchEvent(new Event("evently-auth-check"));
    const body = await res.json().catch(() => ({}));
    throw new ApiError(
      res.status,
      body.error?.message ?? "Something went wrong. Please try again.",
      body.error?.code,
      body.error?.details,
    );
  }
  return res.status === 204 ? (undefined as T) : res.json();
}
export function authenticate(
  action: "login",
  values: unknown,
): Promise<Session>;
export function authenticate(
  action: "register",
  values: unknown,
): Promise<User>;
export async function authenticate(
  action: "login" | "register",
  values: unknown,
): Promise<Session | User> {
  const run = async () => {
    const res = await fetch("/api/auth/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(values),
    });
    const body = await res.json();
    if (!res.ok)
      throw new ApiError(
        res.status,
        body.error?.message ?? "Unable to sign in.",
        body.error?.code,
        body.error?.details,
      );
    if (action === "login") announceSessionChange();
    return body;
  };
  return typeof navigator !== "undefined" && navigator.locks
    ? navigator.locks.request("evently-session", run)
    : run();
}
export function announceSessionChange() {
  if (typeof BroadcastChannel !== "undefined") {
    const channel = new BroadcastChannel("evently-auth");
    channel.postMessage("changed");
    channel.close();
  }
}
