/* eslint-disable @next/next/no-img-element -- Local authenticated cover and blob preview. */
"use client";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, CalendarDays, Lightbulb } from "lucide-react";
import { toast } from "sonner";
import { useEvent } from "@/lib/events";
import { canonicalTimeZone, wallTimeToISO, localInput } from "@/lib/utils";
import type { Event } from "@/lib/types";
import { api, ApiError } from "@/lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { RequireAuth, Loading, ErrorState } from "./feedback";
import { useResource } from "./workflows";
const schema = z.object({
  title: z
    .string()
    .trim()
    .min(3, "Give your event a name of at least 3 characters.")
    .max(200),
  description: z
    .string()
    .trim()
    .min(1, "Tell your guests what to expect.")
    .max(20000),
  location: z.string().trim().min(2, "Add a location.").max(300),
  timezone: z.string().trim().min(1, "Choose a timezone.").max(64),
  starts_at: z.string().min(1, "Choose a start time."),
  ends_at: z.string().min(1, "Choose an end time."),
  capacity: z.number().int().min(1).max(1000000),
});
type Values = z.infer<typeof schema>;
export function EventFormPage({ id }: { id?: string }) {
  return (
    <RequireAuth roles={["organizer", "admin"]}>
      {id ? <EditLoader id={id} /> : <EventForm />}
    </RequireAuth>
  );
}
function EditLoader({ id }: { id: string }) {
  const query = useEvent(id, true);
  return query.isPending ? (
    <Loading />
  ) : query.error ? (
    <ErrorState error={query.error} retry={query.refetch} />
  ) : (
    <EventForm event={query.data} />
  );
}
function EventForm({ event }: { event?: Event }) {
  const router = useRouter();
  const base = usePathname().startsWith("/admin")
    ? "/admin/events"
    : "/organizer/events";
  const [savedId, setSavedId] = useState(event?.id);
  const [category, setCategory] = useState(event?.category_id ?? "");
  const [cover, setCover] = useState<File | null>(null);
  const [preview, setPreview] = useState("");
  const [removeCover, setRemoveCover] = useState(false);
  const categories = useResource<{ id: string; name: string }[]>("/categories");
  useEffect(
    () => () => {
      if (preview) URL.revokeObjectURL(preview);
    },
    [preview],
  );
  const client = useQueryClient();
  const [error, setError] = useState("");
  const timezone = canonicalTimeZone(
    event?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone,
  );
  const {
    register,
    handleSubmit,
    setError: fieldError,
    formState: { errors, isSubmitting, isDirty },
  } = useForm<Values>({
    resolver: zodResolver(schema),
    defaultValues: event
      ? {
          title: event.title,
          description: event.description,
          location: event.location,
          timezone: event.timezone,
          starts_at: localInput(event.starts_at, event.timezone),
          ends_at: localInput(event.ends_at, event.timezone),
          capacity: event.capacity,
        }
      : { timezone, capacity: 50 },
  });
  useEffect(() => {
    const warn = (e: BeforeUnloadEvent) => {
      if (isDirty || cover) {
        e.preventDefault();
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [isDirty, cover]);
  async function submit(values: Values) {
    setError("");
    let starts_at: string, ends_at: string;
    try {
      starts_at = wallTimeToISO(values.starts_at, values.timezone);
    } catch {
      fieldError("starts_at", {
        message:
          "This time is invalid or ambiguous in this timezone. Choose another time and check the timezone.",
      });
      return;
    }
    try {
      ends_at = wallTimeToISO(values.ends_at, values.timezone);
    } catch {
      fieldError("ends_at", {
        message:
          "This time is invalid or ambiguous in this timezone. Choose another time.",
      });
      return;
    }
    if (new Date(ends_at) <= new Date(starts_at)) {
      fieldError("ends_at", { message: "The event must end after it starts." });
      return;
    }
    try {
      const saved = await api<Event>(
        "/events" + (savedId ? "/" + savedId : ""),
        {
          method: savedId ? "PATCH" : "POST",
          body: JSON.stringify({
            ...values,
            starts_at,
            ends_at,
            category_id: category || null,
          }),
        },
      );
      setSavedId(saved.id);
      if (cover) {
        const body = new FormData();
        body.append("file", cover);
        await api(`/events/${saved.id}/cover`, { method: "PUT", body });
      } else if (removeCover)
        await api(`/events/${saved.id}/cover`, { method: "DELETE" });
      toast.success(
        event
          ? "Your event has been updated."
          : "Your draft is ready. Publish it when you’re happy.",
      );
      void client.invalidateQueries({ queryKey: ["events"] });
      void client.invalidateQueries({ queryKey: ["event"] });
      router.push(base);
    } catch (e) {
      if (e instanceof ApiError && Array.isArray(e.details)) {
        const formMessages: string[] = [];
        for (const detail of e.details) {
          const name = detail.location.at(-1);
          if (name && name in values)
            fieldError(name as keyof Values, { message: detail.message });
          else formMessages.push(detail.message.replace(/^Value error, /, ""));
        }
        setError(
          formMessages.length
            ? [...new Set(formMessages)].join(" ")
            : "Please review the highlighted fields and try again.",
        );
      } else setError((e as Error).message);
    }
  }
  const field = (
    name: keyof Values,
    label: string,
    type = "text",
    placeholder = "",
  ) => (
    <div className="form-field">
      <Label htmlFor={name}>{label}</Label>
      <Input
        id={name}
        type={type}
        placeholder={placeholder}
        {...register(name, name === "capacity" ? { valueAsNumber: true } : {})}
        aria-invalid={!!errors[name]}
        aria-describedby={errors[name] ? name + "-error" : undefined}
      />
      {errors[name] && (
        <span className="field-error" id={name + "-error"}>
          {errors[name].message}
        </span>
      )}
    </div>
  );
  return (
    <>
      <Link className="back-link" href={base}>
        <ArrowLeft size={16} />
        Manage events
      </Link>
      <div className="page-heading">
        <span className="eyebrow">YOUR IDEA. THEIR NEXT GREAT MEMORY.</span>
        <h1>{event ? "Make it even better." : "Bring your event to life."}</h1>
        <p>
          {event
            ? "Update the details and keep your guests in the loop."
            : "Start with the details. The connections will follow."}
        </p>
      </div>
      <div className="editor-layout">
        <form
          className="event-form form-stack"
          onSubmit={handleSubmit(submit)}
          noValidate
        >
          <div className="form-section-heading">
            <span>01</span>
            <div>
              <h2>The big idea</h2>
              <p>Give people a reason to be there.</p>
            </div>
          </div>
          <label>
            Category
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">No category</option>
              {categories.data?.map((c) => (
                <option value={c.id} key={c.id}>
                  {c.name}
                </option>
              ))}
            </select>
          </label>
          {categories.error && <ErrorState error={categories.error} />}
          <label>
            Cover image (JPEG or PNG, up to 5 MB)
            <input
              type="file"
              accept="image/jpeg,image/png"
              onChange={(e) => {
                const file = e.target.files?.[0] ?? null;
                setCover(file);
                setPreview(file ? URL.createObjectURL(file) : "");
                setRemoveCover(false);
              }}
            />
          </label>
          {(preview || event?.cover_url) && !removeCover && (
            <img
              src={
                preview || `/api/backend/organizer/events/${event?.id}/cover`
              }
              alt="Cover preview"
              width={360}
            />
          )}
          {event?.cover_url && (
            <label>
              <input
                type="checkbox"
                checked={removeCover}
                onChange={(e) => {
                  setRemoveCover(e.target.checked);
                  setCover(null);
                  setPreview("");
                }}
              />
              Remove existing cover
            </label>
          )}
          {savedId && !event && (
            <p>
              Draft saved. If cover upload failed, retry saving to update this
              draft.
            </p>
          )}
          {field(
            "title",
            "Event name",
            "text",
            "A name worth putting on the calendar",
          )}
          <div className="form-field">
            <Label htmlFor="description">About the event</Label>
            <Textarea
              id="description"
              rows={7}
              placeholder="What’s happening? Who is it for? What should guests know?"
              {...register("description")}
              aria-invalid={!!errors.description}
            />
            {errors.description && (
              <span className="field-error">{errors.description.message}</span>
            )}
          </div>
          <div className="form-section-heading">
            <span>02</span>
            <div>
              <h2>A time and a place</h2>
              <p>Make it easy for your people to find you.</p>
            </div>
          </div>
          {field("location", "Location", "text", "Venue name and address")}
          <div className="form-field">
            <Label htmlFor="timezone">Timezone</Label>
            <Input id="timezone" list="timezones" {...register("timezone")} />
            <datalist id="timezones">
              {Array.from(
                new Set([
                  timezone,
                  "UTC",
                  ...Intl.supportedValuesOf("timeZone").map(canonicalTimeZone),
                ]),
              ).map((t) => (
                <option key={t} value={t} />
              ))}
            </datalist>
            <span className="field-hint">
              All times below are in this timezone.
            </span>
          </div>
          <div className="form-two-cols">
            {field("starts_at", "Starts", "datetime-local")}
            {field("ends_at", "Ends", "datetime-local")}
          </div>
          {field("capacity", "Guest capacity", "number")}
          <p className="field-hint">
            When your event is full, new guests automatically join the waitlist.
          </p>
          {error && (
            <div role="alert" className="form-error">
              {error}
            </div>
          )}
          <div className="form-footer">
            <Button asChild variant="outline">
              <Link href={base}>Cancel</Link>
            </Button>
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting
                ? "Saving…"
                : event
                  ? "Save changes"
                  : "Create draft"}
              <ArrowRight size={16} />
            </Button>
          </div>
        </form>
        <aside className="editor-aside">
          <span className="feature-icon">
            <Lightbulb />
          </span>
          <h2>
            Big or small,
            <br />
            make it yours.
          </h2>
          <p>The best events start with a clear idea and a warm welcome.</p>
          <ul>
            <li>Choose a name that tells a story.</li>
            <li>Include the details you’d want to know.</li>
            <li>Leave room for a new connection.</li>
          </ul>
          <div className="editor-tip">
            <CalendarDays size={21} />
            <p>
              New events start as drafts. You can review everything before going
              live.
            </p>
          </div>
        </aside>
      </div>
    </>
  );
}
