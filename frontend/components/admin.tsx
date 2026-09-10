"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, type ReactNode } from "react";
import {
  Activity,
  CalendarDays,
  CheckCircle2,
  ExternalLink,
  FolderKanban,
  LayoutDashboard,
  Mail,
  RefreshCw,
  ShieldCheck,
  Tags,
  Users,
  AlertTriangle,
} from "lucide-react";
import {
  useResource,
  Applications,
  ActionForm,
  Field,
  Pager,
} from "./workflows";
import { RequireAuth, Loading, ErrorState } from "./feedback";
import { Button } from "./ui/button";
import type { Page } from "@/lib/types";
import { useAuth } from "./providers";
import { cn, initials } from "@/lib/utils";
export function AdminShell({ children }: { children: ReactNode }) {
  const path = usePathname();
  const { user } = useAuth();
  const navigation = [
    { href: "/admin", label: "Overview", icon: LayoutDashboard },
    {
      href: "/admin/organizer-requests",
      label: "Organizer requests",
      icon: FolderKanban,
    },
    { href: "/admin/users", label: "People & access", icon: Users },
    { href: "/admin/events", label: "Events", icon: CalendarDays },
    { href: "/admin/categories", label: "Categories", icon: Tags },
    { href: "/admin/audit-logs", label: "Audit activity", icon: Activity },
    { href: "/admin/outbox", label: "Email operations", icon: Mail },
  ];
  return (
    <RequireAuth roles={["admin"]}>
      <div className="admin-shell">
        <a className="skip-link" href="#admin-main">
          Skip to administration content
        </a>
        <header className="admin-topbar">
          <Link href="/admin" className="admin-brand">
            <span className="admin-brand-mark">
              <ShieldCheck aria-hidden="true" />
            </span>
            <span>
              <strong>Evently</strong>
              <small>Administration</small>
            </span>
          </Link>
          <Link href="/" className="admin-public-link">
            View public site <ExternalLink size={15} aria-hidden="true" />
          </Link>
        </header>
        <div className="admin-layout">
          <aside className="admin-sidebar">
            <p className="admin-nav-label">Workspace</p>
            <nav aria-label="Administration">
              {navigation.map((item) => {
                const active =
                  item.href === "/admin"
                    ? path === item.href
                    : path.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={cn("admin-nav-item", active && "active")}
                    aria-current={active ? "page" : undefined}
                  >
                    <item.icon size={18} aria-hidden="true" />
                    {item.label}
                  </Link>
                );
              })}
            </nav>
            {user && (
              <div className="admin-profile">
                <span className="avatar">{initials(user.name)}</span>
                <span>
                  <strong>{user.name}</strong>
                  <small>Administrator</small>
                </span>
              </div>
            )}
          </aside>
          <main id="admin-main" className="admin-content">
            {children}
          </main>
        </div>
      </div>
    </RequireAuth>
  );
}
type Overview = {
  users_by_role: Record<string, number>;
  users_by_status: Record<string, number>;
  events_by_status: Record<string, number>;
  registrations_by_status: Record<string, number>;
  check_ins: number;
  pending_applications: number;
  generated_at: string;
};
type Worker = {
  healthy: boolean;
  last_seen_at: string | null;
  pending: number;
  failed: number;
};
export function WorkerHealth() {
  const query = useResource<Worker>("/admin/worker-status", true);
  return (
    <section className="admin-panel admin-worker-card">
      <div className="admin-panel-heading">
        <span
          className={cn(
            "admin-panel-icon",
            query.data?.healthy ? "healthy" : "warning",
          )}
        >
          {query.data?.healthy ? <CheckCircle2 /> : <AlertTriangle />}
        </span>
        <div>
          <h2>Email worker</h2>
          <p>Delivery queue and worker heartbeat</p>
        </div>
      </div>
      {query.error ? (
        <ErrorState error={query.error} />
      ) : query.data ? (
        <>
          <p role="status" className="admin-worker-status">
            {query.data.healthy
              ? "Healthy"
              : "Warning: worker heartbeat is stale or unavailable"}
          </p>
          <p>
            Last seen:{" "}
            {query.data.last_seen_at
              ? new Date(query.data.last_seen_at).toLocaleString()
              : "Never"}
          </p>
          <p>
            {query.data.pending} pending · {query.data.failed} failed
          </p>
        </>
      ) : (
        <Loading />
      )}
      <Button variant="outline" onClick={() => void query.refetch()}>
        <RefreshCw size={15} /> Refresh status
      </Button>
    </section>
  );
}
export function AdminOverview() {
  const query = useResource<Overview>("/admin/overview", true);
  return (
    <>
      <div className="page-heading">
        <span className="eyebrow">CONTROL CENTER</span>
        <h1>Operational overview</h1>
        <p>A live view of your community, events, and platform operations.</p>
      </div>
      {query.error ? (
        <ErrorState error={query.error} />
      ) : query.data ? (
        <>
          <section className="admin-stats-grid">
            {(
              [
                ["users_by_role", "People by role", Users],
                ["users_by_status", "Account health", ShieldCheck],
                ["events_by_status", "Event pipeline", CalendarDays],
                ["registrations_by_status", "Guest activity", CheckCircle2],
              ] as const
            ).map(([key, label, Icon]) => (
              <article className="admin-stat-card" key={key}>
                <span className="admin-stat-icon">
                  <Icon aria-hidden="true" />
                </span>
                <h2>{label}</h2>
                <dl>
                  {Object.entries(query.data[key]).map(([name, count]) => (
                    <div key={name}>
                      <dt>{name}</dt>
                      <dd>{count}</dd>
                    </div>
                  ))}
                </dl>
              </article>
            ))}
          </section>
          <section className="admin-summary-strip">
            <div>
              <strong>{query.data.check_ins}</strong>
              <span>Total check-ins</span>
            </div>
            <div>
              <strong>{query.data.pending_applications}</strong>
              <span>Requests awaiting review</span>
            </div>
            <small>
              Updated {new Date(query.data.generated_at).toLocaleString()}
            </small>
            <Button variant="outline" onClick={() => void query.refetch()}>
              <RefreshCw size={15} /> Refresh totals
            </Button>
          </section>
        </>
      ) : (
        <Loading />
      )}
      <WorkerHealth />
      <AdminActivity recent />
    </>
  );
}
export function AdminApplications() {
  return <Applications admin />;
}
type Category = { id: string; name: string; is_active: boolean };
export function AdminCategories() {
  const query = useResource<Category[]>("/admin/categories");
  return (
    <section className="account-card">
      <h1>Categories</h1>
      <ActionForm path="/admin/categories" label="Create category">
        <Field name="name" label="Category name" minLength={2} maxLength={80} />
      </ActionForm>
      {query.error ? (
        <ErrorState error={query.error} />
      ) : (
        query.data?.map((c) => (
          <article key={c.id} className="account-card">
            <ActionForm
              path={"/admin/categories/" + c.id}
              method="PATCH"
              label="Confirm category update"
            >
              <Field
                name="name"
                label="Name"
                value={c.name}
                minLength={2}
                maxLength={80}
              />
              <label>
                Status
                <select name="is_active" defaultValue={String(c.is_active)}>
                  <option value="true">Active</option>
                  <option value="false">Archived</option>
                </select>
              </label>
            </ActionForm>
          </article>
        ))
      )}
    </section>
  );
}
type Audit = {
  id: string;
  actor_id: string | null;
  action: string;
  target_id: string;
  created_at: string;
  details: Record<string, unknown>;
};
export function AdminActivity({ recent = false }: { recent?: boolean }) {
  const [offset, setOffset] = useState(0);
  const [filters, setFilters] = useState("");
  const query = useResource<Page<Audit>>(
    `/admin/audit-logs?limit=20&offset=${offset}&${filters}`,
  );
  return (
    <section className="account-card">
      <h2>{recent ? "Recent privileged actions" : "Audit activity"}</h2>
      <p>This history records privileged changes.</p>
      {!recent && (
        <form
          className="form-stack"
          onSubmit={(e) => {
            e.preventDefault();
            const params = new URLSearchParams();
            new FormData(e.currentTarget).forEach((v, k) => {
              if (v) params.set(k, String(v));
            });
            setFilters(params.toString());
            setOffset(0);
          }}
        >
          {["actor_id", "action", "target_id", "since", "until"].map((k) => (
            <label key={k}>
              {k.replaceAll("_", " ")}
              <input
                name={k}
                placeholder={
                  k === "since" || k === "until"
                    ? "2026-09-01T00:00:00Z"
                    : undefined
                }
              />
            </label>
          ))}
          <Button>Apply filters</Button>
        </form>
      )}
      {query.error ? (
        <ErrorState error={query.error} />
      ) : (
        query.data && (
          <>
            <div className="table-container">
              <table>
                <thead>
                  <tr>
                    <th>Action</th>
                    <th>Actor</th>
                    <th>Target</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {query.data.items.map((a) => (
                    <tr key={a.id}>
                      <td>{a.action}</td>
                      <td>{a.actor_id}</td>
                      <td>{a.target_id}</td>
                      <td>{new Date(a.created_at).toLocaleString()}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {!recent && (
              <Pager
                offset={offset}
                setOffset={setOffset}
                more={query.data.has_more}
              />
            )}
          </>
        )
      )}
    </section>
  );
}
type Outbox = {
  id: string;
  topic: string;
  attempts: number;
  failed_at: string | null;
  processed_at: string | null;
  last_error: string | null;
};
export function AdminOutbox() {
  const [offset, setOffset] = useState(0);
  const [failed, setFailed] = useState(false);
  const query = useResource<Page<Outbox>>(
    `/admin/outbox?limit=20&offset=${offset}&failed_only=${failed}`,
    true,
  );
  return (
    <>
      <WorkerHealth />
      <section className="account-card">
        <h1>Email operations</h1>
        <label>
          <input
            type="checkbox"
            checked={failed}
            onChange={(e) => {
              setFailed(e.target.checked);
              setOffset(0);
            }}
          />
          Failed only
        </label>
        {query.error ? (
          <ErrorState error={query.error} />
        ) : (
          query.data && (
            <>
              {query.data.items.map((m) => (
                <article key={m.id} className="account-card">
                  <h3>{m.topic}</h3>
                  <p>
                    {m.processed_at
                      ? "Delivered"
                      : m.failed_at
                        ? "Failed"
                        : "Pending"}{" "}
                    · {m.attempts} attempts
                  </p>
                  <p>{m.last_error}</p>
                  {m.failed_at && !m.topic.startsWith("account.") && (
                    <ActionForm
                      path={"/admin/outbox/" + m.id + "/retry"}
                      label="Confirm retry"
                    />
                  )}
                </article>
              ))}
              <Pager
                offset={offset}
                setOffset={setOffset}
                more={query.data.has_more}
              />
            </>
          )
        )}
      </section>
    </>
  );
}
