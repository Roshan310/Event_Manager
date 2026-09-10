"use client";
import { useEffect, useRef, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useEvent } from "@/lib/events";
import { Button } from "./ui/button";
import { RequireAuth, ErrorState } from "./feedback";
import { Roster } from "./management";
export function CheckIn({ id }: { id: string }) {
  return (
    <RequireAuth roles={["organizer", "admin"]}>
      <Scanner id={id} />
      <Roster id={id} />
    </RequireAuth>
  );
}
function Scanner({ id }: { id: string }) {
  const event = useEvent(id, true);
  const client = useQueryClient();
  const [camera, setCamera] = useState(false);
  const [message, setMessage] = useState("");
  const [pending, setPending] = useState(false);
  const video = useRef<HTMLVideoElement>(null);
  const busy = useRef(false);
  async function check(token: string) {
    if (busy.current) return;
    busy.current = true;
    setPending(true);
    try {
      await api(`/events/${id}/check-ins`, {
        method: "POST",
        body: JSON.stringify({ token }),
      });
      setMessage("Check-in confirmed by the server.");
      void client.invalidateQueries();
    } catch (e) {
      setMessage((e as Error).message);
    } finally {
      busy.current = false;
      setPending(false);
    }
  }
  const checkRef = useRef(check);
  useEffect(() => {
    checkRef.current = check;
  });
  useEffect(() => {
    if (!camera) return;
    let disposed = false;
    let controls: { stop: () => void } | undefined;
    const element = video.current;
    let stream: MediaStream | undefined;
    void (async () => {
      try {
        const { BrowserQRCodeReader } = await import("@zxing/browser");
        if (disposed) return;
        stream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: "environment" },
          audio: false,
        });
        if (disposed) {
          stream.getTracks().forEach((t) => t.stop());
          return;
        }
        controls = await new BrowserQRCodeReader().decodeFromStream(
          stream,
          element!,
          (result, _error, control) => {
            if (result && !disposed) {
              control.stop();
              setCamera(false);
              void checkRef.current(result.getText());
            }
          },
        );
        if (disposed) controls.stop();
      } catch {
        if (!disposed) {
          setMessage(
            "Camera unavailable or permission denied. Use a pasted code or roster lookup.",
          );
          setCamera(false);
        }
      }
    })();
    return () => {
      disposed = true;
      controls?.stop();
      stream?.getTracks().forEach((t) => t.stop());
      if (element) element.srcObject = null;
    };
  }, [camera]);
  return (
    <section className="account-card">
      <h1>Check-in</h1>
      <p>{event.data?.title}</p>
      <p>
        Check-in opens one hour before the event starts and closes at its end.
      </p>
      {event.error && <ErrorState error={event.error} />}
      <Button
        variant="outline"
        disabled={pending}
        onClick={() => setCamera(!camera)}
      >
        {camera ? "Stop camera" : "Start camera"}
      </Button>
      {camera && (
        <video
          ref={video}
          muted
          playsInline
          style={{ width: "100%", maxWidth: 480 }}
        />
      )}
      <form
        className="form-stack"
        onSubmit={(e) => {
          e.preventDefault();
          const form = e.currentTarget;
          void check(String(new FormData(form).get("token")));
          form.reset();
        }}
      >
        <label>
          Paste ticket code
          <input
            name="token"
            required
            minLength={32}
            maxLength={256}
            autoComplete="off"
          />
        </label>
        <Button disabled={pending}>Check in</Button>
      </form>
      <p role="status">{message}</p>
    </section>
  );
}
