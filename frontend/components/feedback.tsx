"use client";
import {
  CalendarDays,
  RefreshCw,
  ArrowRight,
  LoaderCircle,
} from "lucide-react";
import Link from "next/link";
import { useEffect, type ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuth } from "./providers";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
import type { Role } from "@/lib/types";
export function Empty({
  title = "Your next great experience is on its way",
  description = "There are no upcoming events yet. Check back soon for something worth getting together for.",
  action,
}: {
  title?: string;
  description?: string;
  action?: ReactNode;
}) {
  return (
    <div className="empty-state">
      <span className="empty-icon">
        <CalendarDays size={27} />
      </span>
      <h3>{title}</h3>
      <p>{description}</p>
      {action}
    </div>
  );
}
export function ErrorState({
  error,
  retry,
}: {
  error: Error;
  retry?: () => unknown;
}) {
  return (
    <div className="error-state" role="alert">
      <h3>Let’s try that again</h3>
      <p>{error.message}</p>
      {retry && (
        <Button variant="outline" onClick={() => retry()}>
          <RefreshCw size={15} />
          Try again
        </Button>
      )}
    </div>
  );
}
export function Loading({ cards = false }: { cards?: boolean }) {
  return cards ? (
    <div className="event-grid">
      {[1, 2, 3].map((n) => (
        <div key={n} className="skeleton-card">
          <div />
          <span />
          <span />
          <span />
        </div>
      ))}
    </div>
  ) : (
    <div className="loading-state" role="status">
      <LoaderCircle className="spin" size={22} />
      <span>Getting things ready…</span>
    </div>
  );
}
export function RequireAuth({
  children,
  roles,
}: {
  children: ReactNode;
  roles?: Role[];
}) {
  const { user, loading, error, reload } = useAuth();
  const router = useRouter();
  const path = usePathname();
  useEffect(() => {
    if (!loading && !error && !user)
      router.replace("/login?next=" + encodeURIComponent(path));
  }, [loading, error, user, path, router]);
  if (loading) return <Loading />;
  if (error) return <ErrorState error={error} retry={reload} />;
  if (!user) return <Loading />;
  if (roles && !roles.includes(user.role))
    return (
      <Empty
        title="A different kind of access"
        description="This area is available to event organizers and administrators. Your current account doesn’t have access."
        action={
          <Button asChild>
            <Link href="/">
              Explore events
              <ArrowRight size={15} />
            </Link>
          </Button>
        }
      />
    );
  return children;
}
export function Confirm({
  open,
  onOpenChange,
  title,
  description,
  onConfirm,
  pending,
  label = "Confirm",
}: {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description: string;
  onConfirm: () => void;
  pending?: boolean;
  label?: string;
}) {
  return (
    <Dialog open={open} onOpenChange={pending ? undefined : onOpenChange}>
      <DialogContent>
        <DialogTitle className="dialog-title">{title}</DialogTitle>
        <DialogDescription className="dialog-description">
          {description}
        </DialogDescription>
        <div className="dialog-actions">
          <Button
            variant="outline"
            disabled={pending}
            onClick={() => onOpenChange(false)}
          >
            Keep it
          </Button>
          <Button variant="destructive" disabled={pending} onClick={onConfirm}>
            {pending ? "Working…" : label}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
