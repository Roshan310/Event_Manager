"use client";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useCallback, useSyncExternalStore } from "react";
import { api } from "./api";
import type { Event, Page } from "./types";
import { useAuth } from "@/components/providers";
export function useEvents(managed = false) {
  return useInfiniteQuery({
    queryKey: ["events", managed ? "managed" : "public"],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api<Page<Event>>(
        `${managed ? "/organizer" : ""}/events?limit=24&offset=${pageParam}`,
      ),
    getNextPageParam: (last) =>
      last.has_more ? last.offset + last.limit : undefined,
  });
}
export function useEvent(id: string, managed = false) {
  return useQuery({
    queryKey: ["event", id, managed],
    queryFn: () => api<Event>(`${managed ? "/organizer" : ""}/events/${id}`),
    enabled: !!id,
  });
}
const emptySaved = "[]";
function subscribe(callback: () => void) {
  window.addEventListener("storage", callback);
  window.addEventListener("evently-saved", callback);
  return () => {
    window.removeEventListener("storage", callback);
    window.removeEventListener("evently-saved", callback);
  };
}
export function useSaved() {
  const { user } = useAuth();
  const key = "evently-saved:" + (user?.id ?? "guest");
  const snapshot = useCallback(() => {
    try {
      return localStorage.getItem(key) ?? emptySaved;
    } catch {
      return emptySaved;
    }
  }, [key]);
  const raw = useSyncExternalStore(subscribe, snapshot, () => emptySaved);
  let ids: string[];
  try {
    const parsed: unknown = JSON.parse(raw);
    ids = Array.isArray(parsed)
      ? parsed.filter((v): v is string => typeof v === "string")
      : [];
  } catch {
    ids = [];
  }
  function toggle(id: string) {
    const next = ids.includes(id) ? ids.filter((x) => x !== id) : [...ids, id];
    localStorage.setItem(key, JSON.stringify(next));
    window.dispatchEvent(new window.Event("evently-saved"));
  }
  return { ids, toggle };
}
