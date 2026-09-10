"use client";
import Link from "next/link";
import { useEffect, useState, useRef, type ReactNode } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { api, announceSessionChange } from "@/lib/api";
import type { Page } from "@/lib/types";
import { useAuth } from "./providers";
import { Button } from "./ui/button";
import { Loading, ErrorState } from "./feedback";
export function useResource<T>(path: string, refresh = false) {
  const { user } = useAuth();
  return useQuery({
    queryKey: ["resource", user?.id, path],
    queryFn: ({ signal }) => api<T>(path, { signal }),
    gcTime: path.endsWith("/ticket") ? 0 : 300000,
    refetchInterval: refresh ? 60000 : false,
    refetchIntervalInBackground: false,
  });
}
export function ActionForm({
  path,
  method = "POST",
  children,
  label = "Save",
  after,
}: {
  path: string;
  method?: string;
  children?: ReactNode;
  label?: string;
  after?: () => void;
}) {
  const client = useQueryClient();
  const mutation = useMutation({
    mutationFn: (values: Record<string, unknown>) =>
      api(path, { method, body: JSON.stringify(values) }),
    onSuccess: () => {
      toast.success("Saved.");
      void client.invalidateQueries();
      after?.();
    },
    onError: () => {
      void client.invalidateQueries();
    },
  });
  return (
    <form
      className="form-stack"
      onSubmit={(e) => {
        e.preventDefault();
        const values: Record<string, unknown> = {};
        new FormData(e.currentTarget).forEach((v, k) => {
          if (v !== "")
            values[k] = ["is_active", "is_read"].includes(k) ? v === "true" : v;
        });
        mutation.mutate(values);
      }}
    >
      {children}
      {mutation.error && (
        <p role="alert" className="form-error">
          {mutation.error.message}
        </p>
      )}
      <Button disabled={mutation.isPending}>
        {mutation.isPending ? "Working…" : label}
      </Button>
    </form>
  );
}
export function Field({
  name,
  label,
  type = "text",
  minLength,
  maxLength,
  value,
}: {
  name: string;
  label: string;
  type?: string;
  minLength?: number;
  maxLength?: number;
  value?: string;
}) {
  return (
    <label>
      {label}
      <input
        name={name}
        type={type}
        required
        minLength={minLength}
        maxLength={maxLength}
        defaultValue={value}
        autoComplete={type === "password" ? "new-password" : undefined}
      />
    </label>
  );
}
type Application = {
  id: string;
  user_id: string;
  organization: string;
  intent: string;
  status: string;
  feedback: string | null;
  created_at: string;
  reviewed_at: string | null;
};
export function Applications({ admin = false }: { admin?: boolean }) {
  const [offset, setOffset] = useState(0);
  const [status, setStatus] = useState("");
  const [q, setQ] = useState("");
  const query = useResource<Page<Application>>(
    `${admin ? "/admin" : "/users/me"}/organizer-requests?limit=20&offset=${offset}${admin ? `&${new URLSearchParams({ ...(status ? { status } : {}), ...(q ? { q } : {}) })}` : ""}`,
  );
  const { user } = useAuth();
  return (
    <section className="account-card">
      <h2>Organizer applications</h2>
      {admin ? (
        <div className="form-stack">
          <label>
            Search applicants
            <input
              value={q}
              onChange={(e) => {
                setQ(e.target.value);
                setOffset(0);
              }}
            />
          </label>
          <label>
            Status
            <select
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setOffset(0);
              }}
            >
              {["", "pending", "approved", "rejected"].map((s) => (
                <option key={s} value={s}>
                  {s || "All"}
                </option>
              ))}
            </select>
          </label>
        </div>
      ) : (
        user?.role === "attendee" && (
          <>
            <p>Verify your email, then tell us what you would like to host.</p>
            {user.email_verified &&
              !query.data?.items.some((a) => a.status === "pending") && (
                <ActionForm
                  path="/users/me/organizer-requests"
                  label="Submit application"
                >
                  <Field
                    name="organization"
                    label="Organization or display name"
                    minLength={2}
                    maxLength={120}
                  />
                  <label>
                    Event-hosting intent
                    <textarea
                      name="intent"
                      required
                      minLength={20}
                      maxLength={2000}
                    />
                  </label>
                </ActionForm>
              )}
          </>
        )
      )}
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} />
      ) : (
        <>
          {!query.data.items.length && <p>No applications yet.</p>}
          {query.data.items.map((a) => (
            <article key={a.id} className="account-card">
              <h3>{a.organization}</h3>
              <p>{a.intent}</p>
              <p>
                {a.status} · {new Date(a.created_at).toLocaleString()}
              </p>
              {admin && <p>Applicant: {a.user_id}</p>}
              {a.feedback && <p>Review feedback: {a.feedback}</p>}
              {admin && a.status === "pending" && (
                <ActionForm
                  path={"/admin/organizer-requests/" + a.id}
                  method="PATCH"
                  label="Confirm decision"
                >
                  <label>
                    Decision
                    <select name="status">
                      <option value="approved">
                        Approve and grant hosting access
                      </option>
                      <option value="rejected">Reject</option>
                    </select>
                  </label>
                  <Field
                    name="feedback"
                    label="Review feedback"
                    minLength={3}
                    maxLength={500}
                  />
                </ActionForm>
              )}
            </article>
          ))}
          <Pager
            offset={offset}
            setOffset={setOffset}
            more={query.data.has_more}
          />
        </>
      )}
    </section>
  );
}
export function Pager({
  offset,
  setOffset,
  more,
}: {
  offset: number;
  setOffset: (n: number) => void;
  more: boolean;
}) {
  return (
    <div className="pagination-footer">
      <Button
        variant="outline"
        disabled={!offset}
        onClick={() => setOffset(Math.max(0, offset - 20))}
      >
        Previous
      </Button>
      <span>Page {offset / 20 + 1}</span>
      <Button
        variant="outline"
        disabled={!more}
        onClick={() => setOffset(offset + 20)}
      >
        Next
      </Button>
    </div>
  );
}
export function AccountSettings() {
  const { user, reload } = useAuth();
  const prefs = useResource<{ reminder_emails: boolean }>(
    "/users/me/notification-preferences",
  );
  const [cooldown, setCooldown] = useState(false);
  const invalidateSession = () => {
    announceSessionChange();
    window.location.replace("/login");
  };
  if (!user) return null;
  return (
    <>
      <section className="account-card">
        <h2>Profile and security</h2>
        <ActionForm path="/users/me" method="PATCH" after={() => void reload()}>
          <Field
            name="name"
            label="Name"
            minLength={2}
            maxLength={120}
            value={user.name}
          />
        </ActionForm>
        <p>
          Email: {user.email} ·{" "}
          {user.email_verified ? "Verified" : "Verification needed"}
        </p>
        {!user.email_verified && (
          <>
            <Button
              disabled={cooldown}
              onClick={async () => {
                setCooldown(true);
                try {
                  await api("/auth/verification/request", {
                    method: "POST",
                    body: JSON.stringify({ email: user.email }),
                  });
                  toast.success("Check your email for a verification token.");
                } catch (e) {
                  toast.error((e as Error).message);
                }
                setTimeout(() => setCooldown(false), 60000);
              }}
            >
              Resend verification email
            </Button>
            <Link href="/verify">Enter verification token</Link>
          </>
        )}
        <h3>Change password</h3>
        <ActionForm
          path="/auth/change-password"
          after={invalidateSession}
          label="Change password and sign out"
        >
          <Field
            name="current_password"
            label="Current password"
            type="password"
            maxLength={128}
          />
          <Field
            name="password"
            label="New password"
            type="password"
            minLength={10}
            maxLength={128}
          />
        </ActionForm>
        <ActionForm
          path="/auth/logout-all"
          after={invalidateSession}
          label="Sign out all devices"
        />
        <h3>Reminders</h3>
        {prefs.error ? (
          <ErrorState error={prefs.error} />
        ) : (
          prefs.data && (
            <Button
              variant="outline"
              onClick={async () => {
                try {
                  await api("/users/me/notification-preferences", {
                    method: "PATCH",
                    body: JSON.stringify({
                      reminder_emails: !prefs.data.reminder_emails,
                    }),
                  });
                  void prefs.refetch();
                } catch (e) {
                  toast.error((e as Error).message);
                }
              }}
            >
              {prefs.data.reminder_emails ? "Disable" : "Enable"} reminder
              emails
            </Button>
          )
        )}
      </section>
      <Applications />
    </>
  );
}
export function Recovery({ mode }: { mode: "verify" | "reset" | "forgot" }) {
  const tokenInput = useRef<HTMLInputElement>(null);
  useEffect(() => {
    const token = new URLSearchParams(window.location.hash.slice(1)).get(
      "token",
    );
    if (token) {
      if (tokenInput.current) tokenInput.current.value = token;
      window.history.replaceState(
        null,
        "",
        window.location.pathname + window.location.search,
      );
    }
  }, []);
  return (
    <main className="account-card">
      <h1>
        {mode === "verify"
          ? "Verify your email"
          : mode === "reset"
            ? "Reset password"
            : "Forgot password"}
      </h1>
      <ActionForm
        path={
          mode === "verify"
            ? "/auth/verification/confirm"
            : `/auth/${mode === "reset" ? "reset" : "forgot"}-password`
        }
        label="Continue"
        after={() => {
          if (mode !== "forgot") {
            announceSessionChange();
            window.location.replace(mode === "verify" ? "/account" : "/login");
          }
        }}
      >
        {mode === "forgot" ? (
          <Field name="email" label="Email address" type="email" />
        ) : (
          <label>
            Single-use token
            <input name="token" required ref={tokenInput} autoComplete="off" />
          </label>
        )}
        {mode === "reset" && (
          <Field
            name="password"
            label="New password"
            type="password"
            minLength={10}
            maxLength={128}
          />
        )}
      </ActionForm>
      <p>
        Expired or used token? Request a new email from{" "}
        {mode === "verify" ? (
          <Link href="/account">your account</Link>
        ) : (
          <Link href="/forgot-password">password recovery</Link>
        )}
        .
      </p>
      <Link href="/login">Back to sign in</Link>
    </main>
  );
}
export type Notice = {
  id: string;
  event_id: string | null;
  message: string;
  read_at: string | null;
  created_at: string;
};
export function Notifications() {
  const [offset, setOffset] = useState(0);
  const [unread, setUnread] = useState(false);
  const query = useResource<Page<Notice>>(
    `/users/me/notifications?limit=20&offset=${offset}&unread_only=${unread}`,
    true,
  );
  return (
    <section className="account-card">
      <h1>Notifications</h1>
      <label>
        <input
          type="checkbox"
          checked={unread}
          onChange={(e) => {
            setUnread(e.target.checked);
            setOffset(0);
          }}
        />
        Unread only
      </label>
      <ActionForm
        path="/users/me/notifications/read-all"
        label="Mark all read"
      />
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} />
      ) : (
        <>
          {query.data.items.map((n) => (
            <article className="account-card" key={n.id}>
              <p>{n.message}</p>
              <small>{new Date(n.created_at).toLocaleString()}</small>
              {n.event_id && (
                <Link href={"/events/" + n.event_id}>View event</Link>
              )}
              {!n.read_at && (
                <ActionForm
                  path={"/users/me/notifications/" + n.id}
                  method="PATCH"
                  label="Mark read"
                >
                  <input type="hidden" name="is_read" value="true" />
                </ActionForm>
              )}
            </article>
          ))}
          {!query.data.total && <p>No notifications in this view.</p>}
          <Pager
            offset={offset}
            setOffset={setOffset}
            more={query.data.has_more}
          />
        </>
      )}
    </section>
  );
}
