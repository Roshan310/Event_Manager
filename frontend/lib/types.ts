export type Role = "attendee" | "organizer" | "admin";
export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  is_active: boolean;
  created_at: string;
}
export interface Event {
  id: string;
  organizer_id: string;
  title: string;
  description: string;
  location: string;
  timezone: string;
  starts_at: string;
  ends_at: string;
  capacity: number;
  status: "draft" | "published" | "cancelled" | "completed";
  confirmed_count: number;
  available_seats: number;
  created_at: string;
  updated_at: string;
}
export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
  has_more: boolean;
}
export interface Registration {
  id: string;
  event_id: string;
  attendee_id: string;
  status: "confirmed" | "waitlisted" | "cancelled";
  created_at: string;
  event?: Event;
  attendee?: User;
}
export interface Session {
  user: User | null;
  expires_at: number;
}
