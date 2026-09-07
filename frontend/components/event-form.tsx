"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, ArrowRight, CalendarDays, Lightbulb } from "lucide-react";
import { toast } from "sonner";
import { useEvent } from "@/lib/events";
import { wallTimeToISO, localInput } from "@/lib/utils";
import type { Event } from "@/lib/types";
import { api, ApiError } from "@/lib/api";
import { Button } from "./ui/button";
import { Input } from "./ui/input";
import { Textarea } from "./ui/textarea";
import { Label } from "./ui/label";
import { RequireAuth, Loading, ErrorState } from "./feedback";
const schema = z.object({
  title: z
    .string()
    .min(3, "Give your event a name of at least 3 characters.")
    .max(200),
  description: z.string().min(1, "Tell your guests what to expect.").max(20000),
  location: z.string().min(2, "Add a location.").max(300),
  timezone: z.string().min(1, "Choose a timezone."),
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
  const client = useQueryClient();
  const [error, setError] = useState("");
  const timezone =
    event?.timezone ?? Intl.DateTimeFormat().resolvedOptions().timeZone;
  const {
    register,
    handleSubmit,
    setError: fieldError,
    formState: { errors, isSubmitting },
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
      await api<Event>("/events" + (event ? "/" + event.id : ""), {
        method: event ? "PATCH" : "POST",
        body: JSON.stringify({ ...values, starts_at, ends_at }),
      });
      toast.success(
        event
          ? "Your event has been updated."
          : "Your draft is ready. Publish it when you’re happy.",
      );
      void client.invalidateQueries({ queryKey: ["events"] });
      void client.invalidateQueries({ queryKey: ["event"] });
      router.push("/organizer/events");
    } catch (e) {
      setError((e as Error).message);
      if (e instanceof ApiError && Array.isArray(e.details))
        for (const detail of e.details) {
          const name = detail.location.at(-1);
          if (name && name in values)
            fieldError(name as keyof Values, { message: detail.message });
        }
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
      <Link className="back-link" href="/organizer/events">
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
                  ...Intl.supportedValuesOf("timeZone"),
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
              <Link href="/organizer/events">Cancel</Link>
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
