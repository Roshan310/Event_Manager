import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  clearSession,
  failure,
  originAllowed,
  setSession,
  upstream,
} from "@/lib/server";
export async function POST(
  request: Request,
  { params }: { params: Promise<{ action: string }> },
) {
  if (!originAllowed(request)) return failure("Invalid request origin.", 403);
  const { action } = await params;
  if (!["login", "register", "refresh", "logout"].includes(action))
    return failure("Not found.", 404);
  try {
    const jar = await cookies();
    let payload;
    if (action === "refresh" || action === "logout") {
      const token = jar.get("evently_refresh")?.value;
      if (!token) {
        await clearSession();
        return action === "logout"
          ? NextResponse.json({ user: null })
          : failure("Please sign in again.", 401);
      }
      payload = { refresh_token: token };
    } else {
      try {
        payload = await request.json();
      } catch {
        return failure("Invalid request.", 400);
      }
    }
    const res = await upstream("/auth/" + action, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (action === "logout") {
      await clearSession();
      return NextResponse.json({ user: null });
    }
    const body = await res.json();
    if (!res.ok) {
      if (action === "refresh" && [401, 403].includes(res.status))
        await clearSession();
      return NextResponse.json(body, { status: res.status });
    }
    if (action === "register") return NextResponse.json(body, { status: 201 });
    await setSession(body);
    return NextResponse.json(
      { user: body.user, expires_at: Date.now() + body.expires_in * 1000 },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    if (action === "logout") {
      await clearSession();
      return NextResponse.json({
        user: null,
        warning:
          "Signed out here. The server could not be reached to revoke the session.",
      });
    }
    return failure();
  }
}
