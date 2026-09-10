const id =
  "[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}";
const definitions: [string, string[]][] = [
  ["events", ["GET", "POST"]],
  [`events/${id}`, ["GET", "PATCH", "DELETE"]],
  [`events/${id}/(publish|cancel)`, ["POST"]],
  [`events/${id}/registrations`, ["GET", "POST"]],
  [`events/${id}/registrations/me`, ["GET", "DELETE"]],
  [`events/${id}/registrations/me/ticket(/qr)?`, ["GET"]],
  [`events/${id}/registrations/export`, ["GET"]],
  [`events/${id}/registrations/${id}`, ["DELETE"]],
  [`events/${id}/check-ins`, ["POST"]],
  [`events/${id}/check-ins/${id}`, ["DELETE"]],
  [`events/${id}/cover`, ["GET", "PUT", "DELETE"]],
  [`events/${id}/calendar\\.ics`, ["GET"]],
  ["organizer/events", ["GET"]],
  [`organizer/events/${id}(/summary|/cover)?`, ["GET"]],
  ["users/me", ["GET", "PATCH"]],
  ["users/me/registrations", ["GET"]],
  ["users/me/bookmarks(/status)?", ["GET"]],
  [`users/me/bookmarks/${id}`, ["PUT", "DELETE"]],
  ["users/me/notifications", ["GET"]],
  ["users/me/notifications/read-all", ["POST"]],
  [`users/me/notifications/${id}`, ["PATCH"]],
  ["users/me/notification-preferences", ["GET", "PATCH"]],
  ["users/me/organizer-requests", ["GET", "POST"]],
  ["categories", ["GET"]],
  ["admin/categories", ["GET", "POST"]],
  [`admin/categories/${id}`, ["PATCH"]],
  [
    "admin/(users|overview|organizer-requests|audit-logs|outbox|worker-status)",
    ["GET"],
  ],
  [`admin/users/${id}/(role|status)`, ["PATCH"]],
  [`admin/organizer-requests/${id}`, ["PATCH"]],
  [`admin/events/${id}/organizer`, ["PATCH"]],
  [`admin/outbox/${id}/retry`, ["POST"]],
  [
    "auth/(forgot-password|reset-password|verification/request|verification/confirm|change-password|logout-all)",
    ["POST"],
  ],
];
export function proxyAllowed(path: string, method: string) {
  return definitions.some(
    ([pattern, methods]) =>
      new RegExp(`^${pattern}$`).test(path) && methods.includes(method),
  );
}
export function publicEndpoint(path: string, method: string) {
  return (
    (method === "GET" &&
      (path === "events" ||
        path === "categories" ||
        new RegExp(`^events/${id}(/cover|/calendar\\.ics)?$`).test(path))) ||
    (method === "POST" &&
      /^auth\/(forgot-password|reset-password|verification\/request|verification\/confirm)$/.test(
        path,
      ))
  );
}
