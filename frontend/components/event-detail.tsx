"use client";
import Link from "next/link";
import Image from "next/image";
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  ArrowLeft,
  CalendarDays,
  MapPin,
  Users,
  Heart,
  Clock3,
  ArrowUpRight,
  Check,
} from "lucide-react";
import { toast } from "sonner";
import { useEvent, useSaved } from "@/lib/events";
import { useAuth } from "./providers";
import { api, ApiError } from "@/lib/api";
import type { Page, Registration } from "@/lib/types";
import { dateLabel, timeLabel, presentation } from "@/lib/utils";
import { Button } from "./ui/button";
import { Loading, ErrorState, Empty, Confirm } from "./feedback";
export function EventDetail({ id }: { id: string }) {
  const event = useEvent(id);
  const { user } = useAuth();
  const saved = useSaved();
  const client = useQueryClient();
  const [cancel, setCancel] = useState(false);
  const registrations = useQuery({
    queryKey: ["registrations", "all", user?.id],
    enabled: !!user,
    queryFn: async () => {
      const items: Registration[] = [];
      let offset = 0;
      while (true) {
        const page = await api<Page<Registration>>(
          "/users/me/registrations?limit=100&offset=" + offset,
        );
        items.push(...page.items);
        if (!page.has_more) break;
        offset += page.limit;
      }
      return items;
    },
  });
  const current = registrations.data?.find(
    (r) => r.event_id === id && r.status !== "cancelled",
  );
  const mutation = useMutation({
    mutationFn: (remove: boolean) =>
      api<Registration | undefined>(
        "/events/" + id + "/registrations" + (remove ? "/me" : ""),
        { method: remove ? "DELETE" : "POST" },
      ),
    onSuccess: (data) => {
      toast.success(
        data
          ? data.status === "waitlisted"
            ? "You’re on the waitlist. We’ll let you know when a seat opens."
            : "You’re going! Make room for a good time."
          : "Registration cancelled.",
      );
      setCancel(false);
      void client.invalidateQueries({ queryKey: ["registrations"] });
      void client.invalidateQueries({ queryKey: ["events"] });
      void client.invalidateQueries({ queryKey: ["event", id] });
    },
    onError: (e) => {
      toast.error(e.message);
      void client.invalidateQueries({ queryKey: ["event", id] });
      void client.invalidateQueries({ queryKey: ["registrations"] });
    },
  });
  if (event.isPending) return <Loading />;
  if (event.error)
    return event.error instanceof ApiError && event.error.status === 404 ? (
      <Empty
        title="This event isn’t available"
        description="It may have been cancelled or is no longer public."
        action={
          <Button asChild>
            <Link href="/events">Explore other events</Link>
          </Button>
        }
      />
    ) : (
      <ErrorState error={event.error} retry={event.refetch} />
    );
  const e = event.data;
  const closed =
    e.status === "completed" ||
    e.status === "cancelled" ||
    new Date(e.ends_at) <= new Date();
  return (
    <>
      <Link href="/events" className="back-link">
        <ArrowLeft size={16} />
        All events
      </Link>
      <div className="detail-hero">
        <Image
          src={"/images/" + presentation(e).file + ".jpg"}
          fill
          priority
          sizes="100vw"
          alt=""
        />
        <span className="photo-caption">Illustrative event photography</span>
      </div>
      <div className="detail-layout">
        <article>
          <span className="eyebrow">
            COME FOR THE EXPERIENCE. STAY FOR THE CONNECTION.
          </span>
          <h1>{e.title}</h1>
          <div className="detail-chips">
            <span>
              <CalendarDays size={16} />
              {dateLabel(e)}
            </span>
            <span>
              <MapPin size={16} />
              {e.location}
            </span>
          </div>
          <section className="description-section">
            <h2>About this event</h2>
            <p>{e.description}</p>
          </section>
          <section className="detail-facts">
            <div>
              <CalendarDays />
              <h3>Date & time</h3>
              <p>
                {dateLabel(e)} · {timeLabel(e)}
                <br />
                {e.timezone}
              </p>
            </div>
            <div>
              <MapPin />
              <h3>Location</h3>
              <p>{e.location}</p>
            </div>
          </section>
        </article>
        <aside className="booking-card">
          <span
            className={
              "status-pill " + (closed ? "status-neutral" : "status-green")
            }
          >
            {closed
              ? "Event ended"
              : e.available_seats
                ? "Registration open"
                : "Waitlist open"}
          </span>
          <h2>{current ? "You’re part of it." : "Make it a plan."}</h2>
          <p>
            {current?.status === "confirmed"
              ? "Your place is confirmed. We’ll see you there."
              : current?.status === "waitlisted"
                ? "You’re on the waitlist. Your status updates here when a place opens."
                : "Good moments are better when you’re there."}
          </p>
          <div className="booking-info">
            <span>
              <Users size={18} />
              {e.confirmed_count} people going
            </span>
            <span>
              <Clock3 size={18} />
              {e.available_seats} of {e.capacity} spots available
            </span>
          </div>
          {!user ? (
            <Button asChild>
              <Link href={"/login?next=" + encodeURIComponent("/events/" + id)}>
                Sign in to join
                <ArrowUpRight size={16} />
              </Link>
            </Button>
          ) : user.role !== "attendee" ? (
            <p className="muted-note">
              Registration is available to attendee accounts.
            </p>
          ) : registrations.isPending ? (
            <Loading />
          ) : registrations.error ? (
            <ErrorState
              error={registrations.error}
              retry={registrations.refetch}
            />
          ) : current ? (
            <>
              <div className="registration-confirmed">
                <Check size={17} />
                {current.status === "confirmed"
                  ? "You’re going"
                  : "On the waitlist"}
              </div>
              <Button
                variant="outline"
                disabled={mutation.isPending}
                onClick={() => setCancel(true)}
              >
                Cancel registration
              </Button>
            </>
          ) : (
            <Button
              disabled={closed || mutation.isPending}
              onClick={() => mutation.mutate(false)}
            >
              {mutation.isPending
                ? "Reserving…"
                : closed
                  ? "Registration closed"
                  : e.available_seats
                    ? "Count me in"
                    : "Join the waitlist"}
              <ArrowRightIcon />
            </Button>
          )}
          <Button
            variant="ghost"
            onClick={() => {
              try {
                saved.toggle(id);
              } catch {
                toast.error("Unable to save on this browser.");
              }
            }}
          >
            <Heart
              size={17}
              fill={saved.ids.includes(id) ? "currentColor" : "none"}
            />
            {saved.ids.includes(id)
              ? "Saved on this browser"
              : "Save for later"}
          </Button>
          <small>One registration. One seat. A whole new experience.</small>
        </aside>
      </div>
      <Confirm
        open={cancel}
        onOpenChange={setCancel}
        title="Can’t make it?"
        description="Your place will be released. If there’s a waitlist, the next person will get a chance to join."
        label="Cancel registration"
        pending={mutation.isPending}
        onConfirm={() => mutation.mutate(true)}
      />
    </>
  );
}
function ArrowRightIcon() {
  return <ArrowUpRight size={17} />;
}
