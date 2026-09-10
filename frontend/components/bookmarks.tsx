"use client";
import {
  useCallback,
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "./providers";
const Context = createContext<{
  ids: string[];
  watch: (id: string) => () => void;
  toggle: (id: string) => Promise<void>;
  ready: boolean;
}>({ ids: [], watch: () => () => {}, toggle: async () => {}, ready: false });
export function BookmarkProvider({ children }: { children: ReactNode }) {
  const { user } = useAuth();
  const client = useQueryClient();
  const [visible, setVisible] = useState<Record<string, number>>({});
  const ids = Object.keys(visible)
    .filter((id) => visible[id] > 0)
    .sort();
  const query = useQuery({
    queryKey: ["bookmarks", user?.id, ids],
    enabled: !!user && ids.length > 0,
    queryFn: async ({ signal }) => {
      const result: string[] = [];
      for (let i = 0; i < ids.length; i += 100) {
        const params = new URLSearchParams();
        ids.slice(i, i + 100).forEach((id) => params.append("event_ids", id));
        result.push(
          ...(await api<string[]>("/users/me/bookmarks/status?" + params, {
            signal,
          })),
        );
      }
      return result;
    },
  });
  const watch = useCallback((id: string) => {
    setVisible((v) => ({ ...v, [id]: (v[id] ?? 0) + 1 }));
    return () =>
      setVisible((v) => ({ ...v, [id]: Math.max(0, (v[id] ?? 0) - 1) }));
  }, []);
  return (
    <Context.Provider
      value={{
        ids: query.data ?? [],
        ready: !query.isFetching && !query.isError,
        watch,
        toggle: async (id) => {
          await api("/users/me/bookmarks/" + id, {
            method: query.data?.includes(id) ? "DELETE" : "PUT",
          });
          await client.invalidateQueries({ queryKey: ["bookmarks"] });
          await client.invalidateQueries({ queryKey: ["resource"] });
        },
      }}
    >
      {children}
    </Context.Provider>
  );
}
export function useAccountBookmark(id?: string) {
  const context = useContext(Context);
  const watch = context.watch;
  useEffect(() => {
    if (id) return watch(id);
  }, [id, watch]);
  return context;
}
