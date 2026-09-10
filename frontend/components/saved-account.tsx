"use client";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Event, Page } from "@/lib/types";
import { useAuth } from "./providers";
import { useResource, Pager } from "./workflows";
import { Button } from "./ui/button";
import { EventCard } from "./event-card";
import { ErrorState, Loading } from "./feedback";
export function AccountSaved() {
  const { user } = useAuth();
  const [offset, setOffset] = useState(0);
  const [busy, setBusy] = useState(false);
  const query = useResource<Page<Event>>(
    `/users/me/bookmarks?limit=20&offset=${offset}`,
  );
  async function importSaved() {
    setBusy(true);
    let count = 0,
      failed = 0;
    try {
      for (const key of ["evently-saved:guest", "evently-saved:" + user!.id]) {
        const stored: unknown = JSON.parse(localStorage.getItem(key) ?? "[]");
        if (!Array.isArray(stored)) continue;
        const ids = [
          ...new Set(
            stored.filter((id): id is string => typeof id === "string"),
          ),
        ];
        for (const id of ids) {
          try {
            await api("/users/me/bookmarks/" + id, { method: "PUT" });
            const current: unknown = JSON.parse(
              localStorage.getItem(key) ?? "[]",
            );
            if (Array.isArray(current))
              localStorage.setItem(
                key,
                JSON.stringify(current.filter((value) => value !== id)),
              );
            count++;
          } catch {
            failed++;
          }
        }
      }
      toast.info(
        `${count} imported; ${failed} could not be imported and remain in this browser.`,
      );
      void query.refetch();
    } catch (e) {
      toast.error((e as Error).message);
    } finally {
      setBusy(false);
    }
  }
  return (
    <>
      <div className="page-heading">
        <h1>Saved events</h1>
        <p>Saved to your account across devices.</p>
        <Button
          variant="outline"
          disabled={busy}
          onClick={() => void importSaved()}
        >
          {busy ? "Importing…" : "Import browser saves into this account"}
        </Button>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} />
      ) : (
        <>
          {!query.data.total && <p>No saved events yet.</p>}
          <div className="event-grid">
            {query.data.items.map((event) => (
              <EventCard key={event.id} event={event} />
            ))}
          </div>
          <Pager
            offset={offset}
            setOffset={setOffset}
            more={query.data.has_more}
          />
        </>
      )}
    </>
  );
}
