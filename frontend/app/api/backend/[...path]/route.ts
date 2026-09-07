import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { failure, originAllowed, upstream } from "@/lib/server";
const uuid = "[0-9a-fA-F-]{36}";
const routes: [RegExp, string[]][] = [
  [/^events$/, ["GET", "POST"]],
  [new RegExp(`^events/${uuid}$`), ["GET", "PATCH", "DELETE"]],
  [new RegExp(`^events/${uuid}/(publish|cancel)$`), ["POST"]],
  [new RegExp(`^events/${uuid}/registrations$`), ["GET", "POST"]],
  [new RegExp(`^events/${uuid}/registrations/me$`), ["DELETE"]],
  [/^organizer\/events$/, ["GET"]],
  [new RegExp(`^organizer/events/${uuid}$`), ["GET"]],
  [/^users\/me(\/registrations)?$/, ["GET"]],
  [/^admin\/users$/, ["GET"]],
  [new RegExp(`^admin/users/${uuid}/role$`), ["PATCH"]],
];
async function handler(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const path = (await params).path.join("/");
  if (
    !routes.some(
      ([pattern, methods]) =>
        pattern.test(path) && methods.includes(request.method),
    )
  )
    return failure("Not found.", 404);
  if (request.method !== "GET" && !originAllowed(request))
    return failure("Invalid request origin.", 403);
  const token = (await cookies()).get("evently_access")?.value;
  const publicRead =
    request.method === "GET" &&
    (path === "events" || new RegExp(`^events/${uuid}$`).test(path));
  if (!publicRead && !token) return failure("Please sign in.", 401);
  try {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
    };
    if (token && !publicRead) headers.Authorization = `Bearer ${token}`;
    const res = await upstream("/" + path + new URL(request.url).search, {
      method: request.method,
      headers,
      body: ["POST", "PATCH"].includes(request.method)
        ? await request.text()
        : undefined,
    });
    return new NextResponse(res.status === 204 ? null : await res.text(), {
      status: res.status,
      headers: {
        "Content-Type": "application/json",
        "Cache-Control": "no-store",
      },
    });
  } catch {
    return failure();
  }
}
export { handler as GET, handler as POST, handler as PATCH, handler as DELETE };
