"use client";
import Link from "next/link";
import { useState } from "react";
import { useInfiniteQuery, useQueries } from "@tanstack/react-query";
import { ArrowRight, Bookmark, LogOut, Mail, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import type { Event, Page, Registration } from "@/lib/types";
import { dateLabel, timeLabel, initials } from "@/lib/utils";
import { useSaved } from "@/lib/events";
import { useAuth } from "./providers";
import { EventCard } from "./event-card";
import { Empty, ErrorState, Loading, RequireAuth } from "./feedback";
import { Button } from "./ui/button";
export function Saved() {
  const saved = useSaved();
  const queries = useQueries({
    queries: saved.ids.map((id) => ({
      queryKey: ["event", id, false],
      queryFn: () => api<Event>("/events/" + id),
      retry: false,
    })),
  });
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">FOR ANOTHER DAY. OR THIS WEEKEND.</span>
        <h1>A few things to look forward to.</h1>
        <p>Your saved events, all in one place. Saved on this browser.</p>
      </div>
      {!saved.ids.length ? (
        <Empty
          title="Keep a little inspiration close"
          description="Tap the heart on an event to save it here. Your next good plan is waiting."
          action={
            <Button asChild>
              <Link href="/events">
                Find an event
                <ArrowRight size={16} />
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="event-grid">
          {queries.map((q, i) =>
            q.isPending ? (
              <div className="skeleton-card" key={saved.ids[i]}>
                <div />
                <span />
                <span />
              </div>
            ) : q.data ? (
              <EventCard key={q.data.id} event={q.data} />
            ) : (
              <div className="unavailable-card" key={saved.ids[i]}>
                <Bookmark />
                <h3>Event unavailable</h3>
                <p>
                  This event may no longer be public, or the service couldn’t be
                  reached.
                </p>
                <Button variant="outline" onClick={() => void q.refetch()}>
                  Try again
                </Button>
                <Button
                  variant="ghost"
                  onClick={() => {
                    try {
                      saved.toggle(saved.ids[i]);
                    } catch {
                      toast.error("Unable to update saved events.");
                    }
                  }}
                >
                  Remove saved event
                </Button>
              </div>
            ),
          )}
        </div>
      )}
    </>
  );
}
export function MyEvents() {
  return (
    <RequireAuth>
      <Registrations />
    </RequireAuth>
  );
}
function Registrations() {
  const { user } = useAuth();
  const [tab, setTab] = useState("upcoming");
  const query = useInfiniteQuery({
    queryKey: ["registrations", "mine", user?.id],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api<Page<Registration>>(
        "/users/me/registrations?limit=24&offset=" + pageParam,
      ),
    getNextPageParam: (last) =>
      last.has_more ? last.offset + last.limit : undefined,
  });
  const rows = query.data?.pages.flatMap((p) => p.items) ?? [];
  const filtered = rows.filter((r) =>
    tab === "cancelled"
      ? r.status === "cancelled"
      : tab === "waitlisted"
        ? r.status === "waitlisted"
        : tab === "past"
          ? r.status !== "cancelled" &&
            r.event &&
            new Date(r.event.ends_at) <= new Date()
          : r.status === "confirmed" &&
            r.event &&
            new Date(r.event.ends_at) > new Date(),
  );
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">PLANS TO LOOK FORWARD TO</span>
        <h1>My Events</h1>
        <p>A calendar full of possibilities. Here’s what you’re part of.</p>
      </div>
      <div className="tab-bar" role="group" aria-label="Registration status">
        {["upcoming", "waitlisted", "past", "cancelled"].map((t) => (
          <button
            key={t}
            aria-pressed={tab === t}
            className={tab === t ? "active" : ""}
            onClick={() => setTab(t)}
          >
            {t}
          </button>
        ))}
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={query.refetch} />
      ) : !filtered.length ? (
        <Empty
          title="Make your next plan a good one"
          description="No registrations in this view. Explore the lineup or load more of your history."
          action={
            <Button asChild>
              <Link href="/events">
                Explore events
                <ArrowRight size={15} />
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="registration-list">
          {filtered.map((r) => (
            <article key={r.id} className="registration-row">
              <div className="registration-date">
                {r.event && (
                  <>
                    <small>{dateLabel(r.event, { month: "short" })}</small>
                    <strong>{dateLabel(r.event, { day: "numeric" })}</strong>
                  </>
                )}
              </div>
              <div>
                <span
                  className={
                    "status-pill " +
                    (r.status === "confirmed"
                      ? "status-green"
                      : r.status === "waitlisted"
                        ? "status-amber"
                        : "status-neutral")
                  }
                >
                  {r.status}
                </span>
                <h3>{r.event?.title ?? "Event"}</h3>
                <p>
                  {r.event &&
                    `${dateLabel(r.event)} · ${timeLabel(r.event)} · ${r.event.location}`}
                </p>
              </div>
              <Button variant="outline" asChild>
                <Link href={"/events/" + r.event_id}>
                  View event
                  <ArrowRight size={15} />
                </Link>
              </Button>
            </article>
          ))}
        </div>
      )}
      {query.hasNextPage && (
        <div className="pagination-footer">
          <Button
            variant="outline"
            disabled={query.isFetchingNextPage}
            onClick={() => void query.fetchNextPage()}
          >
            Load more registrations
          </Button>
        </div>
      )}
    </>
  );
}
export function Account() {
  const { user, logout } = useAuth();
  return (
    <RequireAuth>
      <div className="page-heading">
        <span className="eyebrow">A LITTLE ABOUT YOU</span>
        <h1>Your account</h1>
        <p>Your place in the Evently community.</p>
      </div>
      {user && (
        <section className="account-card">
          <div className="account-identity">
            <span className="avatar large-avatar">{initials(user.name)}</span>
            <div>
              <h2>{user.name}</h2>
              <p>
                Member since{" "}
                {new Date(user.created_at).toLocaleDateString("en-US", {
                  month: "long",
                  year: "numeric",
                })}
              </p>
            </div>
          </div>
          <dl>
            <div>
              <dt>
                <Mail size={17} />
                Email address
              </dt>
              <dd>{user.email}</dd>
            </div>
            <div>
              <dt>
                <ShieldCheck size={17} />
                Account role
              </dt>
              <dd className="capitalize">{user.role}</dd>
            </div>
          </dl>
          <p className="muted-note">
            Profile editing is coming soon. Contact your administrator for
            account assistance.
          </p>
          <Button variant="outline" onClick={() => void logout()}>
            <LogOut size={16} />
            Sign out
          </Button>
        </section>
      )}
    </RequireAuth>
  );
}
