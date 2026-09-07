import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
import { Temporal } from "@js-temporal/polyfill";
import type { Event } from "./types";
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
export function dateLabel(
  event: Event,
  options: Intl.DateTimeFormatOptions = {
    month: "short",
    day: "numeric",
    year: "numeric",
  },
) {
  return new Intl.DateTimeFormat("en-US", {
    ...options,
    timeZone: event.timezone,
  }).format(new Date(event.starts_at));
}
export function timeLabel(event: Event) {
  return dateLabel(event, { hour: "numeric", minute: "2-digit" });
}
export function wallTimeToISO(value: string, timezone: string) {
  return Temporal.PlainDateTime.from(value)
    .toZonedDateTime(timezone, { disambiguation: "reject" })
    .toInstant()
    .toString();
}
export function localInput(iso: string, timezone: string) {
  return Temporal.Instant.from(iso)
    .toZonedDateTimeISO(timezone)
    .toPlainDateTime()
    .toString()
    .slice(0, 16);
}
const themes = [
  { name: "Music", file: "music", re: /music|concert|festival|jazz|dj\b/i },
  {
    name: "Technology",
    file: "workshop",
    re: /tech|business|design|workshop|\bai\b|conference/i,
  },
  { name: "Arts & Culture", file: "art", re: /art|culture|gallery|museum/i },
  { name: "Outdoors", file: "hiking", re: /hik|outdoor|mountain|adventure/i },
  {
    name: "Wellness",
    file: "wellness",
    re: /wellness|health|yoga|fitness|park/i,
  },
  { name: "Community", file: "community", re: /./ },
];
export function presentation(event: Pick<Event, "title" | "description">) {
  return (
    themes.find((t) => t.re.test(event.title + " " + event.description)) ??
    themes[5]
  );
}
export function initials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((n) => n[0])
    .join("")
    .toUpperCase();
}

export function eventDateKey(event: Event) {
  return Temporal.Instant.from(event.starts_at)
    .toZonedDateTimeISO(event.timezone)
    .toPlainDate()
    .toString();
}
