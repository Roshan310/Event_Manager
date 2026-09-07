"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState } from "react";
import {
  Home,
  Search,
  Tickets,
  Bookmark,
  Bell,
  Music2,
  BriefcaseBusiness,
  Palette,
  Heart,
  Utensils,
  Trophy,
  GraduationCap,
  Users,
  CalendarDays,
  MapPin,
  ChevronDown,
  Menu,
  X,
  ArrowUpRight,
  LogOut,
  Settings,
  ShieldCheck,
} from "lucide-react";
import { Dialog as Primitive, DropdownMenu } from "radix-ui";
import { useAuth } from "./providers";
import { initials, cn } from "@/lib/utils";
import { Button } from "./ui/button";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "./ui/dialog";
const topics = [
  { label: "Music", term: "music", icon: Music2 },
  { label: "Tech & Business", term: "workshop", icon: BriefcaseBusiness },
  { label: "Arts & Culture", term: "art", icon: Palette },
  { label: "Health & Wellness", term: "wellness", icon: Heart },
  { label: "Food & Drink", term: "food", icon: Utensils },
  { label: "Sports", term: "sport", icon: Trophy },
  { label: "Education", term: "education", icon: GraduationCap },
  { label: "Community", term: "community", icon: Users },
];
export function Logo() {
  return (
    <Link href="/" className="logo" aria-label="Evently home">
      <svg viewBox="0 0 32 36" aria-hidden="true">
        <g fill="currentColor">
          <ellipse cx="12" cy="9" rx="5" ry="8" transform="rotate(-24 12 9)" />
          <ellipse
            cx="22"
            cy="10"
            rx="5"
            ry="8"
            transform="rotate(45 22 10)"
            opacity=".75"
          />
          <ellipse
            cx="23"
            cy="21"
            rx="5"
            ry="8"
            transform="rotate(100 23 21)"
          />
          <ellipse
            cx="16"
            cy="28"
            rx="5"
            ry="8"
            transform="rotate(150 16 28)"
            opacity=".65"
          />
          <ellipse
            cx="7"
            cy="23"
            rx="5"
            ry="8"
            transform="rotate(45 7 23)"
            opacity=".8"
          />
        </g>
        <circle cx="15" cy="18" r="4" fill="#bbb5ff" />
      </svg>
      <span>Evently</span>
    </Link>
  );
}
export function Shell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { user, loading, logout } = useAuth();
  const [menu, setMenu] = useState(false);
  const [notice, setNotice] = useState(false);
  const [organize, setOrganize] = useState(false);
  const [search, setSearch] = useState("");
  const nav = [
    { href: "/", label: "Home", icon: Home },
    { href: "/events", label: "Explore Events", icon: Search },
    { href: "/my-events", label: "My Events", icon: Tickets },
    { href: "/saved", label: "Saved", icon: Bookmark },
  ];
  function sidebar() {
    return (
      <>
        <div className="sidebar-logo">
          <Logo />
        </div>
        <nav aria-label="Main navigation">
          {nav.map((item) => (
            <Link
              key={item.href}
              onClick={() => setMenu(false)}
              href={item.href}
              className={cn(
                "nav-item",
                (item.href === "/"
                  ? path === "/"
                  : path.startsWith(item.href)) && "active",
              )}
            >
              <item.icon size={20} />
              {item.label}
            </Link>
          ))}
          <button className="nav-item" onClick={() => setNotice(true)}>
            <Bell size={20} />
            Notifications
            <span className="soon-dot" />
          </button>
          {user && user.role !== "attendee" && (
            <Link
              className={cn(
                "nav-item",
                path.startsWith("/organizer") && "active",
              )}
              href="/organizer/events"
              onClick={() => setMenu(false)}
            >
              <CalendarDays size={20} />
              Manage Events
            </Link>
          )}
          {user?.role === "admin" && (
            <Link
              className={cn("nav-item", path.startsWith("/admin") && "active")}
              href="/admin/users"
              onClick={() => setMenu(false)}
            >
              <ShieldCheck size={20} />
              Administration
            </Link>
          )}
        </nav>
        <div className="topic-nav">
          <p>Browse by Topic</p>
          {topics.map((t) => (
            <Link
              className="nav-item"
              href={"/events?topic=" + t.term}
              key={t.term}
              onClick={() => setMenu(false)}
            >
              <t.icon size={20} />
              {t.label}
            </Link>
          ))}
        </div>
        <div className="organize-card">
          <CalendarDays size={24} />
          <h3>Organizing an event?</h3>
          <p>Bring people together. Create and manage your events with ease.</p>
          {user && user.role !== "attendee" ? (
            <Button asChild>
              <Link href="/organizer/events/new">Create Event</Link>
            </Button>
          ) : (
            <Button onClick={() => setOrganize(true)}>Create Event</Button>
          )}
        </div>
      </>
    );
  }
  return (
    <div className="app-shell">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <aside className="sidebar">{sidebar()}</aside>
      <Primitive.Root open={menu} onOpenChange={setMenu}>
        <Primitive.Portal>
          <Primitive.Overlay className="dialog-overlay" />
          <Primitive.Content className="mobile-sidebar">
            <Primitive.Title className="sr-only">Navigation</Primitive.Title>
            <Primitive.Description className="sr-only">
              Explore Evently
            </Primitive.Description>
            <Primitive.Close
              className="mobile-close"
              aria-label="Close navigation"
            >
              <X />
            </Primitive.Close>
            {sidebar()}
          </Primitive.Content>
        </Primitive.Portal>
      </Primitive.Root>
      <div className="app-body">
        <header className="topbar">
          <button
            className="mobile-menu icon-button"
            aria-label="Open navigation"
            onClick={() => setMenu(true)}
          >
            <Menu size={23} />
          </button>
          <form
            className="header-search"
            onSubmit={(e) => {
              e.preventDefault();
              router.push("/events?q=" + encodeURIComponent(search));
            }}
          >
            <Search size={19} />
            <input
              aria-label="Search events"
              placeholder="Search events, topics, or locations..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
            />
          </form>
          <div className="header-actions">
            <Link className="location-control" href="/events#filters">
              <MapPin size={17} />
              <span>Find your next event</span>
              <ChevronDown size={14} />
            </Link>
            <button
              className="icon-button notification-button"
              aria-label="Notifications — coming soon"
              onClick={() => setNotice(true)}
            >
              <Bell size={20} />
            </button>
            <div className="header-divider" />
            {loading ? (
              <span className="avatar avatar-loading" />
            ) : user ? (
              <DropdownMenu.Root>
                <DropdownMenu.Trigger className="profile-control">
                  <span className="avatar">{initials(user.name)}</span>
                  <span className="profile-copy">
                    <strong>{user.name}</strong>
                    <small>{user.role}</small>
                  </span>
                  <ChevronDown size={15} />
                </DropdownMenu.Trigger>
                <DropdownMenu.Portal>
                  <DropdownMenu.Content
                    className="dropdown-content"
                    align="end"
                    sideOffset={12}
                  >
                    <DropdownMenu.Item asChild>
                      <Link href="/account">
                        <Settings size={16} />
                        Your account
                      </Link>
                    </DropdownMenu.Item>
                    <DropdownMenu.Item onSelect={() => void logout()}>
                      <LogOut size={16} />
                      Sign out
                    </DropdownMenu.Item>
                  </DropdownMenu.Content>
                </DropdownMenu.Portal>
              </DropdownMenu.Root>
            ) : (
              <Button asChild size="sm">
                <Link href="/login">
                  Sign in
                  <ArrowUpRight size={15} />
                </Link>
              </Button>
            )}
          </div>
        </header>
        <main id="main" className="main-content">
          {children}
        </main>
        <footer className="site-footer">
          <span>Good events. Better connections.</span>
          <span>© {new Date().getFullYear()} Evently</span>
        </footer>
      </div>
      <Dialog open={notice} onOpenChange={setNotice}>
        <DialogContent>
          <span className="feature-icon">
            <Bell />
          </span>
          <DialogTitle className="dialog-title">
            A little heads-up, soon.
          </DialogTitle>
          <DialogDescription className="dialog-description">
            An in-app notification inbox is on the way. For now, visit My Events
            to check your registration status. Event emails are sent when the
            organizer’s email service is configured.
          </DialogDescription>
          <Button asChild onClick={() => setNotice(false)}>
            <Link href="/my-events">Go to My Events</Link>
          </Button>
        </DialogContent>
      </Dialog>
      <Dialog open={organize} onOpenChange={setOrganize}>
        <DialogContent>
          <span className="feature-icon">
            <CalendarDays />
          </span>
          <DialogTitle className="dialog-title">
            Make something worth attending.
          </DialogTitle>
          <DialogDescription className="dialog-description">
            Event creation is available to organizer accounts.{" "}
            {user
              ? "Ask your administrator to enable organizer access for your account."
              : "Create an account, then ask your administrator for organizer access."}
          </DialogDescription>
          {!user && (
            <Button asChild>
              <Link href="/register">Create an account</Link>
            </Button>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}
