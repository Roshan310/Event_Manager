"use client";
import {
  createContext,
  useContext,
  useState,
  useEffect,
  type ReactNode,
} from "react";
import {
  QueryClient,
  QueryClientProvider,
  useQuery,
  useQueryClient,
} from "@tanstack/react-query";
import { MotionConfig } from "motion/react";
import { Toaster, toast } from "sonner";
import { api, ApiError, announceSessionChange } from "@/lib/api";
import type { Session, User } from "@/lib/types";
const AuthContext = createContext<{
  user: User | null;
  loading: boolean;
  error: Error | null;
  logout: () => Promise<void>;
  reload: () => Promise<unknown>;
}>({
  user: null,
  loading: true,
  error: null,
  logout: async () => {},
  reload: async () => {},
});
function AuthProvider({ children }: { children: ReactNode }) {
  const client = useQueryClient();
  const query = useQuery({
    queryKey: ["session"],
    queryFn: async () => {
      const res = await fetch("/api/session", { cache: "no-store" });
      if (!res.ok) throw new Error("Unable to connect. Please try again.");
      const data: Session & { can_refresh: boolean } = await res.json();
      if (!data.user && data.can_refresh) {
        try {
          const user = await api<User>("/users/me");
          return { user, expires_at: 0 };
        } catch (error) {
          if (error instanceof ApiError && [401, 403].includes(error.status))
            return { user: null, expires_at: 0 };
          throw error;
        }
      }
      return data;
    },
    retry: false,
    staleTime: 60000,
  });
  useEffect(() => {
    const recheck = () => {
      void client.invalidateQueries({ queryKey: ["session"] });
    };
    const channel =
      typeof BroadcastChannel !== "undefined"
        ? new BroadcastChannel("evently-auth")
        : null;
    if (channel)
      channel.onmessage = () => {
        client.removeQueries({ predicate: (q) => q.queryKey[0] !== "session" });
        recheck();
      };
    window.addEventListener("evently-auth-check", recheck);
    return () => {
      channel?.close();
      window.removeEventListener("evently-auth-check", recheck);
    };
  }, [client]);
  async function logout() {
    const run = async () => {
      const res = await fetch("/api/auth/logout", { method: "POST" });
      if (!res.ok) throw new Error("Unable to sign out. Please try again.");
      const data = await res.json();
      await client.cancelQueries();
      announceSessionChange();
      if (data.warning) toast.warning(data.warning);
      // A document navigation discards all account state without racing route guards.
      window.location.replace(new URL("/", window.location.origin).href);
    };
    try {
      if (navigator.locks)
        await navigator.locks.request("evently-session", run);
      else await run();
    } catch (e) {
      toast.error((e as Error).message);
    }
  }
  return (
    <AuthContext.Provider
      value={{
        user: query.data?.user ?? null,
        loading: query.isPending,
        error: query.error,
        logout,
        reload: () => query.refetch(),
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
export function useAuth() {
  return useContext(AuthContext);
}
export function Providers({ children }: { children: ReactNode }) {
  const [client] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: { staleTime: 30000, retry: 1 },
          mutations: { retry: false },
        },
      }),
  );
  return (
    <QueryClientProvider client={client}>
      <MotionConfig reducedMotion="user">
        <AuthProvider>{children}</AuthProvider>
        <Toaster position="bottom-right" richColors closeButton />
      </MotionConfig>
    </QueryClientProvider>
  );
}
