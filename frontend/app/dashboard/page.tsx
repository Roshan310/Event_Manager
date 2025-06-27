"use client"
import { useEffect, useState } from "react"
import { Calendar, Clock, MapPin, Users } from "lucide-react"
import { useRouter } from "next/navigation"
import { getCurrentUser, logout } from "@/lib/auth"
import { Button } from "@/components/ui/button"
import { capitalizeFirstLetter } from "@/utils/format"
import { Navbar } from "@/components/navbar"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
const upcomingEvents = [
    {
      id: 1,
      title: "Team Building Workshop",
      date: "June 15, 2025",
      time: "10:00 AM - 2:00 PM",
      location: "Conference Room A",
      attendees: 12,
    },
    {
      id: 2,
      title: "Product Launch",
      date: "June 20, 2025",
      time: "6:00 PM - 9:00 PM",
      location: "Grand Ballroom",
      attendees: 85,
    },
    {
      id: 3,
      title: "Quarterly Review",
      date: "June 30, 2025",
      time: "1:00 PM - 3:00 PM",
      location: "Meeting Room B",
      attendees: 8,
    },
  ]


export default function DashboardPage() {
  const [user, setUser] = useState(null)
  const router = useRouter()

  useEffect(() => {
    getCurrentUser().then((u) => {
      if (!u) {
        router.push("/login")
      } else {
        console.log("User fetched successfully:", u)
        setUser(u)
      }
    })
  }, [])

  if (!user) {
    return <div>Loading...</div>
  }

  return (
    <div className="min-h-screen flex flex-col bg-gray-50 dark:bg-gray-950">
      <Navbar />
      <main className="flex-1 container py-8">
        <div className="flex flex-col gap-8">
          {/* Welcome section */}
          <section className="flex flex-col gap-2">
            <h1 className="text-3xl font-bold tracking-tight">Welcome back, {capitalizeFirstLetter(user.name)}!</h1>
            <p className="text-muted-foreground">Here's what's happening with your events today.</p>
          </section>

          {/* Stats overview */}
          <section className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Events</CardTitle>
                <Calendar className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">12</div>
                <p className="text-xs text-muted-foreground">+2 from last month</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Upcoming Events</CardTitle>
                <Clock className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">3</div>
                <p className="text-xs text-muted-foreground">Next event in 6 days</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Total Attendees</CardTitle>
                <Users className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">248</div>
                <p className="text-xs text-muted-foreground">+24% from last month</p>
              </CardContent>
            </Card>
            <Card>
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium">Locations</CardTitle>
                <MapPin className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">5</div>
                <p className="text-xs text-muted-foreground">Across 3 cities</p>
              </CardContent>
            </Card>
          </section>

          {/* Upcoming events */}
          <section className="flex flex-col gap-4">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold tracking-tight">Upcoming Events</h2>
              <Button variant="outline" size="sm" className="gap-1">
                <Calendar className="h-4 w-4" />
                View Calendar
              </Button>
            </div>
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
              {upcomingEvents.map((event) => (
                <Card key={event.id} className="overflow-hidden transition-all duration-200 hover:shadow-md">
                  <CardHeader className="p-4 pb-2">
                    <CardTitle className="text-lg">{event.title}</CardTitle>
                    <CardDescription className="flex items-center gap-1">
                      <Calendar className="h-3.5 w-3.5 text-rose-500" />
                      {event.date}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="p-4 pt-2 space-y-2">
                    <div className="flex items-center gap-2 text-sm">
                      <Clock className="h-3.5 w-3.5 text-muted-foreground" />
                      <span>{event.time}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <MapPin className="h-3.5 w-3.5 text-muted-foreground" />
                      <span>{event.location}</span>
                    </div>
                    <div className="flex items-center gap-2 text-sm">
                      <Users className="h-3.5 w-3.5 text-muted-foreground" />
                      <span>{event.attendees} attendees</span>
                    </div>
                  </CardContent>
                  <CardFooter className="p-4 pt-0 flex gap-2">
                    <Button variant="outline" size="sm" className="w-full">
                      View Details
                    </Button>
                    <Button size="sm" variant="ghost" className="w-full">
                      Edit
                    </Button>
                  </CardFooter>
                </Card>
              ))}
            </div>
          </section>
        </div>
      </main>
    </div>
  )
}
