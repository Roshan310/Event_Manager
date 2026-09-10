"use client";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { useRouter, useSearchParams } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import {
  Search,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  CalendarDays,
  Sprout,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { useAuth } from "./providers";
import { useEvents } from "@/lib/events";
import { api } from "@/lib/api";
import type { Page, Registration, Event } from "@/lib/types";

import { EventCard, MiniEvent } from "./event-card";
import { Button } from "./ui/button";
import { Empty, ErrorState, Loading } from "./feedback";
export function Discovery({ home = false }: { home?: boolean }) {
  const { user } = useAuth();
  const params = useSearchParams();
  const router = useRouter();
  const backendFilters = new URLSearchParams();
  for (const key of [
    "q",
    "location",
    "category_id",
    "sort",
    "available_only",
  ]) {
    const value = params.get(key);
    if (value) backendFilters.set(key, value);
  }
  if (!backendFilters.has("q") && params.get("topic"))
    backendFilters.set("q", params.get("topic")!);
  for (const [key, apiKey] of [
    ["date", "starts_after"],
    ["until", "starts_before"],
  ]) {
    const value = params.get(key);
    if (value) {
      const boundary = new Date(value + "T00:00:00");
      if (key === "until") boundary.setDate(boundary.getDate() + 1);
      if (Number.isFinite(boundary.getTime()))
        backendFilters.set(
          apiKey,
          new Date(
            boundary.getTime() - (key === "until" ? 1 : 0),
          ).toISOString(),
        );
    }
  }
  const events = useEvents(false, backendFilters.toString());
  const categories = useQuery({
    queryKey: ["categories"],
    queryFn: () => api<{ id: string; name: string }[]>("/categories"),
  });
  const [heroSearch, setHeroSearch] = useState("");
  const [slide, setSlide] = useState(0);
  const registrations = useQuery({
    queryKey: ["registrations", "rail", user?.id],
    queryFn: () =>
      api<Page<Registration>>(
        "/users/me/registrations?limit=3&status=confirmed&period=upcoming&sort=starts_at",
      ),
    enabled: !!user,
  });
  const rows = events.data?.pages.flatMap((p) => p.items) ?? [];
  const total = events.data?.pages[0]?.total ?? 0;
  const q = params.get("q") ?? "";

  const topic = params.get("topic") ?? "";
  const location = params.get("location") ?? "";
  const date = params.get("date") ?? "";
  const sort = params.get("sort") ?? "starts_at";
  function filter(key: string, value: string) {
    const next = new URLSearchParams(params.toString());
    if (value) next.set(key, value);
    else next.delete(key);
    router.push(
      (home ? "/" : "/events") + (next.size ? "?" + next.toString() : ""),
      { scroll: false },
    );
  }
  const filtered = rows;
  const personal = (registrations.data?.items ?? [])
    .filter(
      (r) =>
        r.status !== "cancelled" &&
        r.event &&
        new Date(r.event.ends_at) > new Date(),
    )
    .map((r) => r.event as Event)
    .sort((a, b) => a.starts_at.localeCompare(b.starts_at));
  const rail = !!user ? personal.slice(0, 3) : rows.slice(0, 3);
  const filters = (
    <div className="discovery-filters" id="filters">
      <label className="select-wrap">
        <span className="sr-only">Location</span>
        <input
          aria-label="Location"
          placeholder="Location"
          value={location}
          onChange={(e) => filter("location", e.target.value)}
        />
      </label>
      <label className="date-filter">
        <CalendarDays size={15} />
        <span className="sr-only">Event date</span>
        <input
          aria-label="Event date"
          type="date"
          disabled={events.isPending}
          value={date}
          onChange={(e) => filter("date", e.target.value)}
        />
      </label>
      <label className="select-wrap">
        <span className="sr-only">Sort events</span>
        <select
          disabled={events.isPending}
          value={sort}
          onChange={(e) => filter("sort", e.target.value)}
        >
          <option value="starts_at">Sort by: Soonest</option>
          <option value="title">Sort by: Name</option>
          <option value="newest">Sort by: Newest</option>
        </select>
      </label>
      <label>
        Through
        <input
          type="date"
          value={params.get("until") ?? ""}
          onChange={(e) => filter("until", e.target.value)}
        />
      </label>
      <label>
        Category
        <select
          value={params.get("category_id") ?? ""}
          onChange={(e) => filter("category_id", e.target.value)}
        >
          <option value="">All categories</option>
          {categories.data?.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
      </label>
      <label>
        <input
          type="checkbox"
          checked={params.get("available_only") === "true"}
          onChange={(e) =>
            filter("available_only", e.target.checked ? "true" : "")
          }
        />
        Available seats
      </label>
    </div>
  );
  return (
    <>
      {home ? (
        <div className="home-top">
          <div className="home-primary">
            <section className="hero">
              <Image
                src="/images/hero.jpg"
                fill
                priority
                sizes="(max-width: 1000px) 100vw, 65vw"
                alt="A crowd sharing an evening of live music"
              />
              <div className="hero-shade" />
              <div className="hero-content">
                <p className="hero-greeting">
                  {user
                    ? "Good to see you, " + user.name.split(" ")[0]
                    : "A little more together."}
                </p>
                <h1>
                  Events bring
                  <br />
                  people closer.
                </h1>
                <p className="hero-description">
                  Discover amazing events, meet new people,
                  <br className="desktop-break" /> and be part of something
                  great.
                </p>
                <form
                  className="hero-search"
                  onSubmit={(e) => {
                    e.preventDefault();
                    router.push("/events?q=" + encodeURIComponent(heroSearch));
                  }}
                >
                  <Search size={20} />
                  <input
                    aria-label="Find an event"
                    placeholder="Search events, topics, or locations..."
                    value={heroSearch}
                    onChange={(e) => setHeroSearch(e.target.value)}
                  />
                  <Button type="submit">Search</Button>
                </form>
              </div>
              <div className="hero-note" aria-hidden="true">
                Good
                <br />
                <span>Events</span>
                <br />
                Brighter
                <br />
                <span>People</span>
                <i>✧</i>
              </div>
            </section>
            <section className="featured-section">
              <div className="section-heading">
                <div>
                  <h2>Discover something great</h2>
                  <p>Good plans start with a little inspiration</p>
                </div>
                <div className="section-actions">
                  <Link href="/events">View all</Link>
                  <button
                    className="round-button"
                    disabled={slide === 0}
                    onClick={() => setSlide(Math.max(0, slide - 3))}
                    aria-label="Previous events"
                  >
                    <ChevronLeft size={18} />
                  </button>
                  <button
                    className="round-button"
                    disabled={slide + 3 >= rows.length}
                    onClick={() => setSlide(slide + 3)}
                    aria-label="Next events"
                  >
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
              {events.isPending ? (
                <Loading cards />
              ) : events.error ? (
                <ErrorState error={events.error} retry={events.refetch} />
              ) : rows.length ? (
                <div className="featured-grid">
                  {rows.slice(slide, slide + 3).map((event, i) => (
                    <EventCard
                      key={event.id}
                      event={event}
                      featured={i === 0}
                      index={i}
                    />
                  ))}
                </div>
              ) : (
                <Empty />
              )}
            </section>
          </div>
          <aside className="right-rail">
            <div className="connection-card">
              <span className="feature-icon">
                <CalendarDays size={23} />
              </span>
              <h2>
                Small events.
                <br />
                Big connections.
              </h2>
              <p>
                Find your next favorite
                <br />
                experience.
              </p>
              <div className="abstract-one" />
              <div className="abstract-two" />
              <span className="card-rays" aria-hidden="true">
                ╲│╱
              </span>
            </div>
            <section className="upcoming-panel">
              <div className="rail-heading">
                <h2>{!!user ? "Your next plans" : "Coming up soon"}</h2>
                <Link href={!!user ? "/my-events" : "/events"}>View all</Link>
              </div>
              {registrations.isError && !!user ? (
                <ErrorState
                  error={registrations.error}
                  retry={registrations.refetch}
                />
              ) : rail.length ? (
                rail.map((e) => <MiniEvent key={e.id} event={e} />)
              ) : (
                <p className="rail-empty">
                  {!!user
                    ? "Your next great plan belongs here. Find an event and make it yours."
                    : "A fresh lineup is on its way. Come back soon."}
                </p>
              )}
            </section>
            <div className="welcome-card">
              <span className="feature-icon mint">
                <Sprout size={25} />
              </span>
              <h2>New here?</h2>
              <p>
                Explore events, save your favorites,
                <br />
                and never miss out.
              </p>
              <Link href="/events">
                Find your people <ArrowRight size={14} />
              </Link>
            </div>
          </aside>
        </div>
      ) : (
        <div className="page-heading">
          <span className="eyebrow">GOOD PLANS START HERE</span>
          <h1>Find your next experience.</h1>
          <p>A new interest. A familiar face. A reason to get out there.</p>
        </div>
      )}
      <section className="upcoming-section">
        <div className="section-heading upcoming-heading">
          <div>
            <h2>{home ? "Upcoming Events" : "Explore Events"}</h2>
            <p>
              {home
                ? "Make room for something good"
                : "Real experiences. Real connections."}
            </p>
          </div>
          {filters}
        </div>
        {!home && (
          <form
            className="explore-search"
            onSubmit={(e) => {
              e.preventDefault();
              filter("q", String(new FormData(e.currentTarget).get("q") ?? ""));
            }}
          >
            <Search size={19} />
            <input
              aria-label="Search events"
              name="q"
              key={q}
              placeholder="Search events, topics, or locations…"
              defaultValue={q}
            />
            <Button type="submit" size="sm">
              <SlidersHorizontal size={16} />
              Search
            </Button>
          </form>
        )}
        {(q || topic || location || date) && (
          <div className="filter-summary">
            <span>
              Searching {rows.length} of {total} events
              {topic ? ` · Topic search: ${topic}` : ""}
            </span>
            <button
              onClick={() =>
                router.replace(home ? "/" : "/events", { scroll: false })
              }
            >
              Clear filters
              <X size={13} />
            </button>
          </div>
        )}
        {!home && events.isPending ? (
          <Loading cards />
        ) : !home && events.error ? (
          <ErrorState error={events.error} retry={events.refetch} />
        ) : filtered.length ? (
          <div className={home ? "upcoming-grid" : "event-grid"}>
            {(home ? filtered.slice(0, 4) : filtered).map((event, i) => (
              <EventCard
                key={event.id}
                event={event}
                compact={home}
                index={i}
              />
            ))}
          </div>
        ) : (
          !events.isPending &&
          !events.error && (
            <Empty
              title={
                rows.length
                  ? "No matches in these events"
                  : "Your calendar has room for something good"
              }
              description={
                rows.length
                  ? "Try another search or load more events to explore the rest of the lineup."
                  : "New experiences will appear here as organizers publish them."
              }
            />
          )
        )}
        <div className="pagination-footer">
          {home && filtered.length > 4 && (
            <Button variant="outline" asChild>
              <Link href="/events">
                View all events
                <ArrowRight size={16} />
              </Link>
            </Button>
          )}
          {total > 0 && (
            <span>
              {rows.length} of {total} events loaded
            </span>
          )}
          {events.hasNextPage && (
            <Button
              variant="outline"
              disabled={events.isFetchingNextPage}
              onClick={() => void events.fetchNextPage()}
            >
              {events.isFetchingNextPage ? "Loading…" : "Load more events"}
              <ArrowRight size={16} />
            </Button>
          )}
          {events.isFetchNextPageError && (
            <p role="alert">Could not load more events. Please try again.</p>
          )}
        </div>
      </section>
    </>
  );
}
