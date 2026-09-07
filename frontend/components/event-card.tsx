"use client";
import Link from "next/link";
import Image from "next/image";
import { Heart, Clock3, MapPin, Users } from "lucide-react";
import { motion } from "motion/react";
import { toast } from "sonner";
import type { Event } from "@/lib/types";
import { dateLabel, timeLabel, presentation } from "@/lib/utils";
import { useSaved } from "@/lib/events";
export function EventCard({
  event,
  compact = false,
  featured = false,
  index = 0,
}: {
  event: Event;
  compact?: boolean;
  featured?: boolean;
  index?: number;
}) {
  const { ids, toggle } = useSaved();
  const saved = ids.includes(event.id);
  const visual = presentation(event);
  const full = event.available_seats === 0;
  return (
    <motion.article
      className={"event-card " + (compact ? "compact-card" : "")}
      initial={{ opacity: 0, y: 9 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.22, delay: Math.min(index, 4) * 0.035 }}
    >
      <div className="event-image">
        <Link href={"/events/" + event.id} tabIndex={-1} aria-hidden="true">
          <Image
            src={"/images/" + visual.file + ".jpg"}
            fill
            sizes="(max-width: 600px) 100vw, (max-width: 1000px) 50vw, 25vw"
            alt=""
          />
        </Link>
        {featured && <span className="featured-pill">Discover</span>}
        {compact && (
          <span className="date-stamp">
            <small>{dateLabel(event, { month: "short" })}</small>
            <strong>{dateLabel(event, { day: "numeric" })}</strong>
          </span>
        )}
        {!compact && (
          <button
            className={"save-button " + (saved ? "is-saved" : "")}
            aria-label={(saved ? "Unsave " : "Save ") + event.title}
            aria-pressed={saved}
            onClick={() => {
              try {
                toggle(event.id);
                toast.success(
                  saved ? "Removed from saved events" : "Saved on this browser",
                );
              } catch {
                toast.error("Your browser could not save this event.");
              }
            }}
          >
            <Heart size={22} fill={saved ? "currentColor" : "none"} />
          </button>
        )}
      </div>
      <div className="event-card-body">
        <div className="event-title-row">
          <h3>
            <Link href={"/events/" + event.id}>{event.title}</Link>
          </h3>
          {compact && (
            <span
              className={
                "status-pill " +
                (full
                  ? "status-rose"
                  : event.available_seats <= 5
                    ? "status-amber"
                    : "status-green")
              }
            >
              {full
                ? "Waitlist"
                : event.available_seats <= 5
                  ? "Few left"
                  : "Open"}
            </span>
          )}
        </div>
        <p className="event-meta">
          <Clock3 />
          {dateLabel(event)} <span className="meta-dot">·</span>{" "}
          {timeLabel(event)}
        </p>
        <p className="event-meta">
          <MapPin />
          {event.location}
        </p>
        {!compact && (
          <>
            <p className="event-meta">
              <Users />
              {event.confirmed_count} going <span className="meta-dot">·</span>{" "}
              {event.available_seats} spots left
            </p>
            <div className="event-tags">
              <Link
                href={
                  "/events?topic=" +
                  encodeURIComponent(visual.name.toLowerCase())
                }
              >
                {visual.name}
              </Link>
              <span>In person</span>
            </div>
          </>
        )}
      </div>
    </motion.article>
  );
}
export function MiniEvent({ event }: { event: Event }) {
  return (
    <Link className="mini-event" href={"/events/" + event.id}>
      <div className="mini-image">
        <Image
          src={"/images/" + presentation(event).file + ".jpg"}
          fill
          sizes="72px"
          alt=""
        />
      </div>
      <div>
        <h3>{event.title}</h3>
        <p>
          <Clock3 size={12} />
          {dateLabel(event, { month: "short", day: "numeric" })} ·{" "}
          {timeLabel(event)}
        </p>
        <p>
          <MapPin size={12} />
          {event.location}
        </p>
      </div>
    </Link>
  );
}
