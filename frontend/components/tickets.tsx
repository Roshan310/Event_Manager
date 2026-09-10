/* eslint-disable @next/next/no-img-element -- Authenticated QR responses must bypass shared image caching. */
"use client";
import { useState } from "react";
import { useResource } from "./workflows";
import { Button } from "./ui/button";
import { ErrorState, Loading } from "./feedback";
export function Ticket({ id }: { id: string }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <Button variant="outline" onClick={() => setOpen(!open)}>
        {open ? "Close ticket" : "Show ticket"}
      </Button>
      {open && <TicketContent id={id} />}
      <a href={`/api/backend/events/${id}/calendar.ics`} download>
        Add to calendar
      </a>
    </>
  );
}
function TicketContent({ id }: { id: string }) {
  const query = useResource<{
    qr_payload: string;
    checked_in_at: string | null;
  }>(`/events/${id}/registrations/me/ticket`);
  return query.error ? (
    <ErrorState error={query.error} />
  ) : query.isPending ? (
    <Loading />
  ) : (
    <div>
      <p>{query.data.checked_in_at ? "Checked in" : "Ready for check-in"}</p>
      {/* The authenticated image URL contains only the event ID. */}
      <img
        src={`/api/backend/events/${id}/registrations/me/ticket/qr`}
        width={240}
        height={240}
        alt="Your admission QR code"
      />
      <a
        href={`/api/backend/events/${id}/registrations/me/ticket/qr`}
        download="ticket.png"
      >
        Download QR image
      </a>
    </div>
  );
}
