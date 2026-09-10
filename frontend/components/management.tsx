"use client";
import Link from "next/link";
import { useState } from "react";
import {
  useInfiniteQuery,
  useMutation,
  useQueryClient,
} from "@tanstack/react-query";
import {
  Plus,
  ArrowRight,
  ArrowLeft,
  Pencil,
  Users,
  Send,
  Ban,
  Trash2,
  CalendarDays,
} from "lucide-react";
import { toast } from "sonner";
import { useEvents, useEvent } from "@/lib/events";
import { api } from "@/lib/api";
import type { Event, Page, Registration, User, Role } from "@/lib/types";
import { dateLabel, initials } from "@/lib/utils";
import { useAuth } from "./providers";
import { Button } from "./ui/button";
import { RequireAuth, Loading, ErrorState, Empty, Confirm } from "./feedback";
import { usePathname } from "next/navigation";
import { useResource, ActionForm, Field } from "./workflows";
export function ManagedEvents() {
  return (
    <RequireAuth roles={["organizer", "admin"]}>
      <ManagedList />
    </RequireAuth>
  );
}
function ManagedList() {
  const base = usePathname().startsWith("/admin")
    ? "/admin/events"
    : "/organizer/events";
  const { user } = useAuth();
  const [tab, setTab] = useState("all");
  const [search, setSearch] = useState("");
  const query = useEvents(
    true,
    new URLSearchParams({
      ...(tab !== "all" ? { status: tab } : {}),
      ...(search ? { q: search } : {}),
    }).toString(),
  );
  const [action, setAction] = useState<{ event: Event; type: string } | null>(
    null,
  );
  const client = useQueryClient();
  const rows = query.data?.pages.flatMap((p) => p.items) ?? [];
  const filtered = rows.filter((e) => tab === "all" || e.status === tab);
  const mutation = useMutation({
    mutationFn: () =>
      api(
        "/events/" +
          action!.event.id +
          (action!.type === "delete" ? "" : "/" + action!.type),
        { method: action!.type === "delete" ? "DELETE" : "POST" },
      ),
    onSuccess: () => {
      toast.success(
        action?.type === "publish"
          ? "Your event is live. Let the connections begin."
          : action?.type === "cancel"
            ? "Event cancelled."
            : "Draft deleted.",
      );
      setAction(null);
      void client.invalidateQueries({ queryKey: ["events"] });
      void client.invalidateQueries({ queryKey: ["event"] });
      void client.invalidateQueries({ queryKey: ["registrations"] });
    },
    onError: (e) => toast.error(e.message),
  });
  return (
    <>
      <div className="page-heading heading-with-action">
        <div>
          <span className="eyebrow">BRING PEOPLE TOGETHER</span>
          <h1>
            {user?.role === "admin"
              ? "All events"
              : "Your events, your community."}
          </h1>
          <p>From your first idea to the last good conversation.</p>
        </div>
        <Button asChild>
          <Link href={base + "/new"}>
            <Plus size={18} />
            Create Event
          </Link>
        </Button>
      </div>
      <label>
        Search events
        <input value={search} onChange={(e) => setSearch(e.target.value)} />
      </label>
      <div className="tab-bar" role="group" aria-label="Event status">
        {["all", "draft", "published", "completed", "cancelled"].map((t) => (
          <button
            key={t}
            className={tab === t ? "active" : ""}
            aria-pressed={tab === t}
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
          title="Something great starts with an idea"
          description="There are no events in this view. Create an event or load more to see the rest."
          action={
            <Button asChild>
              <Link href={base + "/new"}>
                <Plus size={16} />
                Create your event
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="managed-list">
          {filtered.map((e) => (
            <article key={e.id} className="managed-card">
              <div className="managed-card-main">
                <span className="managed-icon">
                  <CalendarDays size={24} />
                </span>
                <div>
                  <span
                    className={
                      "status-pill " +
                      (e.status === "published"
                        ? "status-green"
                        : e.status === "draft"
                          ? "status-amber"
                          : "status-neutral")
                    }
                  >
                    {e.status}
                  </span>
                  <h3>{e.title}</h3>
                  <p>
                    {dateLabel(e)} · {e.location}
                  </p>
                  <p>
                    {e.confirmed_count} registered · {e.available_seats} spots
                    left
                  </p>
                </div>
              </div>
              <div className="managed-actions">
                {e.status !== "cancelled" && e.status !== "completed" && (
                  <Button size="sm" variant="outline" asChild>
                    <Link href={base + "/" + e.id + "/edit"}>
                      <Pencil size={14} />
                      Edit
                    </Link>
                  </Button>
                )}
                <Button size="sm" variant="outline" asChild>
                  <Link href={base + "/" + e.id + "/registrations"}>
                    <Users size={14} />
                    Attendees
                  </Link>
                </Button>
                {e.status === "draft" && (
                  <>
                    <Button
                      size="sm"
                      onClick={() => setAction({ event: e, type: "publish" })}
                    >
                      <Send size={14} />
                      Publish
                    </Button>
                    <Button
                      size="icon"
                      variant="ghost"
                      aria-label={"Delete " + e.title}
                      onClick={() => setAction({ event: e, type: "delete" })}
                    >
                      <Trash2 size={16} />
                    </Button>
                  </>
                )}
                {e.status === "published" && (
                  <>
                    <Button
                      variant="ghost"
                      size="icon"
                      aria-label={"Cancel " + e.title}
                      onClick={() => setAction({ event: e, type: "cancel" })}
                    >
                      <Ban size={16} />
                    </Button>
                    <Button size="sm" variant="ghost" asChild>
                      <Link href={"/events/" + e.id}>
                        View
                        <ArrowRight size={14} />
                      </Link>
                    </Button>
                  </>
                )}
              </div>
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
            Load more events
          </Button>
        </div>
      )}
      <Confirm
        open={!!action}
        onOpenChange={(open) => {
          if (!open) setAction(null);
        }}
        title={
          action?.type === "publish"
            ? "Ready to bring people together?"
            : action?.type === "cancel"
              ? "Cancel this event?"
              : "Delete this draft?"
        }
        description={
          action?.type === "publish"
            ? "Your event will become publicly visible and attendees can register."
            : action?.type === "cancel"
              ? "All registrations will be cancelled and email notifications queued. This cannot be undone."
              : "This draft will be permanently deleted."
        }
        label={
          action?.type === "publish"
            ? "Publish event"
            : action?.type === "cancel"
              ? "Cancel event"
              : "Delete draft"
        }
        pending={mutation.isPending}
        onConfirm={() => mutation.mutate()}
      />
    </>
  );
}
export function Roster({ id }: { id: string }) {
  return (
    <RequireAuth roles={["organizer", "admin"]}>
      <RosterContent id={id} />
    </RequireAuth>
  );
}
function RosterContent({ id }: { id: string }) {
  const event = useEvent(id, true);
  const { user } = useAuth();
  const base = usePathname().startsWith("/admin")
    ? "/admin/events"
    : "/organizer/events";
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const summary = useResource<Record<string, number>>(
    `/organizer/events/${id}/summary`,
  );
  const query = useInfiniteQuery({
    queryKey: ["roster", user?.id, id, search, status],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api<Page<Registration>>(
        `/events/${id}/registrations?limit=24&offset=${pageParam}&include_cancelled=true&${new URLSearchParams({ ...(search ? { q: search } : {}), ...(status ? { status } : {}) })}`,
      ),
    getNextPageParam: (last) =>
      last.has_more ? last.offset + last.limit : undefined,
  });
  return (
    <>
      <Link href={base} className="back-link">
        <ArrowLeft size={16} />
        Manage events
      </Link>
      <div className="page-heading">
        <span className="eyebrow">THE PEOPLE MAKE IT</span>
        <h1>Guest list</h1>
        <p>{event.data?.title ?? "Your event attendees"}</p>
        <Link href={`${base}/${id}/check-in`}>Open check-in scanner</Link>
        <a href={`/api/backend/events/${id}/registrations/export`} download>
          Export CSV
        </a>
        {summary.error ? (
          <ErrorState error={summary.error} />
        ) : (
          summary.data && (
            <p>
              {Object.entries(summary.data)
                .filter(([k]) => k !== "event_id")
                .map(([k, v]) => `${k.replaceAll("_", " ")}: ${v}`)
                .join(" · ")}
            </p>
          )
        )}
        <label>
          Search guests
          <input value={search} onChange={(e) => setSearch(e.target.value)} />
        </label>
        <label>
          Status
          <select value={status} onChange={(e) => setStatus(e.target.value)}>
            {["", "confirmed", "waitlisted", "cancelled"].map((s) => (
              <option key={s} value={s}>
                {s || "All"}
              </option>
            ))}
          </select>
        </label>
        {user?.role === "admin" && (
          <ActionForm
            path={`/admin/events/${id}/organizer`}
            method="PATCH"
            label="Confirm ownership transfer"
          >
            <Field name="organizer_id" label="New organizer account ID" />
          </ActionForm>
        )}
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={query.refetch} />
      ) : !query.data.pages[0].total ? (
        <Empty
          title="Your first guest is just around the corner"
          description="Confirmed attendees and waitlisted guests will appear here."
        />
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Guest</th>
                <th>Email</th>
                <th>Status</th>
                <th>Registered</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {query.data.pages
                .flatMap((p) => p.items)
                .map((r) => (
                  <tr key={r.id}>
                    <td>
                      <span className="table-person">
                        <span className="avatar">
                          {initials(r.attendee?.name ?? "?")}
                        </span>
                        {r.attendee?.name}
                      </span>
                    </td>
                    <td>{r.attendee?.email}</td>
                    <td>
                      <span
                        className={
                          "status-pill " +
                          (r.status === "confirmed"
                            ? "status-green"
                            : "status-amber")
                        }
                      >
                        {r.status}
                      </span>
                    </td>
                    <td>
                      {new Date(r.created_at).toLocaleDateString("en-US")}
                    </td>
                    <td>
                      {r.status === "confirmed" && !r.checked_in_at && (
                        <ActionForm
                          path={`/events/${id}/check-ins`}
                          label="Confirm check-in"
                        >
                          <input
                            type="hidden"
                            name="registration_id"
                            value={r.id}
                          />
                        </ActionForm>
                      )}
                      {r.checked_in_at && (
                        <ReasonAction
                          path={`/events/${id}/check-ins/${r.id}`}
                          label="Undo check-in"
                        />
                      )}
                      {r.status !== "cancelled" && (
                        <ReasonAction
                          path={`/events/${id}/registrations/${r.id}`}
                          label="Remove attendee"
                        />
                      )}
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
      {query.hasNextPage && (
        <div className="pagination-footer">
          <Button
            variant="outline"
            disabled={query.isFetchingNextPage}
            onClick={() => void query.fetchNextPage()}
          >
            Load more guests
          </Button>
        </div>
      )}
    </>
  );
}
export function AdminUsers() {
  return (
    <RequireAuth roles={["admin"]}>
      <UserList />
    </RequireAuth>
  );
}
function UserList() {
  const { user, reload } = useAuth();
  const client = useQueryClient();
  const [q, setQ] = useState("");
  const [role, setRole] = useState("");
  const [active, setActive] = useState("");
  const [change, setChange] = useState<{ user: User; role: Role } | null>(null);
  const query = useInfiniteQuery({
    queryKey: ["admin-users", user?.id, q, role, active],
    initialPageParam: 0,
    queryFn: ({ pageParam }) =>
      api<Page<User>>(
        "/admin/users?limit=24&offset=" +
          pageParam +
          "&" +
          new URLSearchParams({
            ...(q ? { q } : {}),
            ...(role ? { role } : {}),
            ...(active ? { is_active: active } : {}),
          }),
      ),
    getNextPageParam: (last) =>
      last.has_more ? last.offset + last.limit : undefined,
  });
  const mutation = useMutation({
    mutationFn: () =>
      api("/admin/users/" + change!.user.id + "/role", {
        method: "PATCH",
        body: JSON.stringify({ role: change!.role }),
      }),
    onSuccess: () => {
      toast.success("Account role updated.");
      setChange(null);
      void client.invalidateQueries({
        queryKey: ["admin-users", user?.id, q, role, active],
      });
      void reload();
    },
    onError: (e) => toast.error(e.message),
  });
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">COMMUNITY, WELL LOOKED AFTER</span>
        <h1>People & permissions</h1>
        <p>Manage who attends, who organizes, and who keeps things running.</p>
        <label>
          Search name or email
          <input value={q} onChange={(e) => setQ(e.target.value)} />
        </label>
        <label>
          Role
          <select value={role} onChange={(e) => setRole(e.target.value)}>
            {["", "attendee", "organizer", "admin"].map((r) => (
              <option key={r} value={r}>
                {r || "All"}
              </option>
            ))}
          </select>
        </label>
        <label>
          Status
          <select value={active} onChange={(e) => setActive(e.target.value)}>
            <option value="">All</option>
            <option value="true">Active</option>
            <option value="false">Suspended</option>
          </select>
        </label>
      </div>
      {query.isPending ? (
        <Loading />
      ) : query.error ? (
        <ErrorState error={query.error} retry={query.refetch} />
      ) : (
        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Person</th>
                <th>Email</th>
                <th>Account</th>
                <th>Role</th>
              </tr>
            </thead>
            <tbody>
              {query.data.pages
                .flatMap((p) => p.items)
                .map((u) => (
                  <tr key={u.id}>
                    <td>
                      <span className="table-person">
                        <span className="avatar">{initials(u.name)}</span>
                        {u.name}
                        {u.id === user?.id && <small>(you)</small>}
                      </span>
                    </td>
                    <td>{u.email}</td>
                    <td>
                      <span
                        className={
                          "status-pill " +
                          (u.is_active ? "status-green" : "status-neutral")
                        }
                      >
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                      {u.id !== user?.id && (
                        <ActionForm
                          path={"/admin/users/" + u.id + "/status"}
                          method="PATCH"
                          label={
                            u.is_active
                              ? "Confirm suspension"
                              : "Confirm reactivation"
                          }
                        >
                          <input
                            type="hidden"
                            name="is_active"
                            value={String(!u.is_active)}
                          />
                        </ActionForm>
                      )}
                    </td>
                    <td>
                      <select
                        aria-label={"Role for " + u.name}
                        value={u.role}
                        disabled={u.id === user?.id}
                        onChange={(e) =>
                          setChange({ user: u, role: e.target.value as Role })
                        }
                      >
                        <option value="attendee">Attendee</option>
                        <option value="organizer">Organizer</option>
                        <option value="admin">Administrator</option>
                      </select>
                    </td>
                  </tr>
                ))}
            </tbody>
          </table>
        </div>
      )}
      {query.hasNextPage && (
        <div className="pagination-footer">
          <Button
            variant="outline"
            disabled={query.isFetchingNextPage}
            onClick={() => void query.fetchNextPage()}
          >
            Load more people
          </Button>
        </div>
      )}
      <Confirm
        open={!!change}
        onOpenChange={(open) => {
          if (!open) setChange(null);
        }}
        title="Update account permissions?"
        description={`${change?.user.name} will have ${change?.role} access. This changes the actions they can perform in Evently.`}
        label="Update role"
        pending={mutation.isPending}
        onConfirm={() => mutation.mutate()}
      />
    </>
  );
}

function ReasonAction({ path, label }: { path: string; label: string }) {
  const [reason, setReason] = useState("");
  return (
    <div>
      <label>
        Reason
        <input
          minLength={3}
          maxLength={500}
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />
      </label>
      {reason.trim().length >= 3 && (
        <ActionForm
          path={path + "?" + new URLSearchParams({ reason })}
          method="DELETE"
          label={"Confirm " + label.toLowerCase()}
        />
      )}
    </div>
  );
}
