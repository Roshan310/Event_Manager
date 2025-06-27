"use client"

import { useState } from "react"
import Link from "next/link"
import { logout } from "@/lib/auth"
import { Bell, Calendar, LogOut, Menu, Plus, Search, User } from "lucide-react"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Input } from "@/components/ui/input"
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet"

export function Navbar() {
  const [isSearchOpen, setIsSearchOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-2 md:gap-4">
          {/* Mobile menu */}
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="ghost" size="icon" className="md:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle menu</span>
              </Button>
            </SheetTrigger>
            <SheetContent side="left" className="w-[240px] sm:w-[300px]">
              <nav className="flex flex-col gap-4 pt-4">
                <Link
                  href="/dashboard"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
                >
                  Dashboard
                </Link>
                <Link
                  href="/dashboard/events"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
                >
                  My Events
                </Link>
                <Link
                  href="/dashboard/calendar"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
                >
                  Calendar
                </Link>
                <Link
                  href="/dashboard/profile"
                  className="flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
                >
                  Profile
                </Link>
                <Button className="mt-2 w-full gap-2" size="sm">
                  <Plus className="h-4 w-4" />
                  Create Event
                </Button>
              </nav>
            </SheetContent>
          </Sheet>

          {/* Logo */}
          <Link href="/dashboard" className="flex items-center gap-2 font-semibold">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary text-primary-foreground">
              <Calendar className="h-5 w-5" />
            </div>
            <span className="hidden md:inline-block">EveX</span>
          </Link>

          {/* Desktop navigation */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              href="/dashboard"
              className="rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
            >
              Dashboard
            </Link>
            <Link
              href="/dashboard/events"
              className="rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
            >
              My Events
            </Link>
            <Link
              href="/dashboard/calendar"
              className="rounded-md px-3 py-2 text-sm font-medium hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
            >
              Calendar
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-2">
          {/* Search */}
          <div className="relative hidden md:block">
            {isSearchOpen ? (
              <div className="absolute right-0 top-0 w-60 animate-in fade-in slide-in-from-right-5 duration-300">
                <Input
                  type="search"
                  placeholder="Search events..."
                  className="pr-8"
                  autoFocus
                  onBlur={() => setIsSearchOpen(false)}
                />
                <Search className="absolute right-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              </div>
            ) : (
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsSearchOpen(true)}
                className="hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
              >
                <Search className="h-5 w-5" />
                <span className="sr-only">Search</span>
              </Button>
            )}
          </div>

          {/* Create Event Button */}
          <Button className="hidden md:flex gap-1" size="sm">
            <Plus className="h-4 w-4" />
            Create Event
          </Button>

          {/* Notifications */}
          <Button
            variant="ghost"
            size="icon"
            className="hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
          >
            <Bell className="h-5 w-5" />
            <span className="sr-only">Notifications</span>
            <span className="absolute right-1 top-1 h-2 w-2 rounded-full bg-rose-500" />
          </Button>

          {/* User menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="rounded-full h-8 w-8 border border-border hover:bg-rose-50 hover:text-rose-600 dark:hover:bg-rose-950/20 dark:hover:text-rose-400"
              >
                <User className="h-4 w-4" />
                <span className="sr-only">User menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col">
                  <span>{}</span>
                  <span className="text-xs text-muted-foreground">john@example.com</span>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem asChild>
                <Link href="/dashboard/profile" className="cursor-pointer">
                  <User className="mr-2 h-4 w-4" />
                  Profile
                </Link>
              </DropdownMenuItem>
              <DropdownMenuItem asChild>
                <Link href="/dashboard/settings" className="cursor-pointer">
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="mr-2 h-4 w-4"
                  >
                    <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
                    <circle cx="12" cy="12" r="3" />
                  </svg>
                  Settings
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={logout} className="text-rose-600 dark:text-rose-400 focus:text-rose-700 dark:focus:text-rose-300 cursor-pointer">
                <LogOut className="mr-2 h-4 w-4" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  )
}
