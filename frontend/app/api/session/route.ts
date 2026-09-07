import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { failure, upstream } from "@/lib/server";
export async function GET() {
  const jar = await cookies();
  const access = jar.get("evently_access")?.value;
  const empty = {
    user: null,
    expires_at: 0,
    can_refresh: !!jar.get("evently_refresh")?.value,
  };
  if (!access)
    return NextResponse.json(empty, {
      headers: { "Cache-Control": "no-store" },
    });
  try {
    const res = await upstream("/users/me", {
      headers: { Authorization: `Bearer ${access}` },
    });
    if (res.status === 401 || res.status === 403)
      return NextResponse.json(empty);
    if (!res.ok) return failure();
    return NextResponse.json(
      {
        user: await res.json(),
        expires_at: Number(jar.get("evently_expiry")?.value ?? 0),
        can_refresh: true,
      },
      { headers: { "Cache-Control": "no-store" } },
    );
  } catch {
    return failure();
  }
}
