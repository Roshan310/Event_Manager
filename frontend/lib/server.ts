import "server-only";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
export const baseURL =
  process.env.API_BASE_URL ?? "http://127.0.0.1:8000/api/v1";
export const cookieOptions = {
  httpOnly: true,
  sameSite: "lax" as const,
  secure: process.env.NODE_ENV === "production",
  path: "/",
};
export async function upstream(path: string, init: RequestInit = {}) {
  return fetch(baseURL + path, {
    ...init,
    cache: "no-store",
    signal: AbortSignal.timeout(15000),
  });
}
export function originAllowed(request: Request) {
  const origin = request.headers.get("origin");
  const protocol =
    request.headers.get("x-forwarded-proto") ??
    new URL(request.url).protocol.replace(":", "");
  const expected =
    process.env.APP_ORIGIN ?? `${protocol}://${request.headers.get("host")}`;
  return !!origin && origin === expected;
}
export function failure(
  message = "The event service is unavailable. Please try again.",
  status = 503,
) {
  return NextResponse.json({ error: { message } }, { status });
}
export async function clearSession() {
  const jar = await cookies();
  for (const name of ["evently_access", "evently_refresh", "evently_expiry"])
    jar.set(name, "", { ...cookieOptions, maxAge: 0 });
}
export async function setSession(pair: {
  access_token: string;
  refresh_token: string;
  expires_in: number;
  refresh_expires_in: number;
}) {
  const jar = await cookies();
  jar.set("evently_access", pair.access_token, {
    ...cookieOptions,
    maxAge: pair.expires_in,
  });
  jar.set("evently_refresh", pair.refresh_token, {
    ...cookieOptions,
    maxAge: pair.refresh_expires_in,
  });
  jar.set("evently_expiry", String(Date.now() + pair.expires_in * 1000), {
    ...cookieOptions,
    maxAge: pair.refresh_expires_in,
  });
}

export async function boundedBody(
  request: Request,
  limit = 65536,
): Promise<ArrayBuffer> {
  if (Number(request.headers.get("content-length")) > limit)
    throw new RangeError("body");
  const reader = request.body?.getReader();
  if (!reader) return new ArrayBuffer(0);
  const chunks: Uint8Array[] = [];
  let size = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      size += value.byteLength;
      if (size > limit) {
        await reader.cancel();
        throw new RangeError("body");
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const result = new Uint8Array(size);
  let offset = 0;
  for (const chunk of chunks) {
    result.set(chunk, offset);
    offset += chunk.byteLength;
  }
  return result.buffer;
}
