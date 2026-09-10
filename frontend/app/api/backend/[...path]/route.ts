import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import {
  clearSession,
  failure,
  originAllowed,
  upstream,
  boundedBody,
} from "@/lib/server";
import { proxyAllowed, publicEndpoint } from "@/lib/proxy-contract";
async function handler(
  request: Request,
  { params }: { params: Promise<{ path: string[] }> },
) {
  const path = (await params).path.join("/");
  if (!proxyAllowed(path, request.method)) return failure("Not found.", 404);
  if (request.method !== "GET" && !originAllowed(request))
    return failure("Invalid request origin.", 403);
  const token = (await cookies()).get("evently_access")?.value;
  const isPublic = publicEndpoint(path, request.method);
  if (!isPublic && !token) return failure("Please sign in.", 401);
  try {
    const headers = new Headers();
    const contentType = request.headers.get("content-type");
    if (contentType) headers.set("Content-Type", contentType);
    if (token && !isPublic) headers.set("Authorization", `Bearer ${token}`);
    const body =
      request.method === "GET"
        ? undefined
        : await boundedBody(
            request,
            path.endsWith("/cover") ? 6 * 1024 * 1024 : 65536,
          );
    const res = await upstream("/" + path + new URL(request.url).search, {
      method: request.method,
      headers,
      body,
    });
    const outgoing = new Headers({
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    });
    for (const key of [
      "content-type",
      "content-disposition",
      "x-request-id",
      "retry-after",
      "x-ratelimit-limit",
      "x-ratelimit-remaining",
      "x-ratelimit-reset",
    ]) {
      const value = res.headers.get(key);
      if (value) outgoing.set(key, value);
    }
    if (res.ok && ["auth/change-password", "auth/logout-all"].includes(path))
      await clearSession();
    return new NextResponse(res.status === 204 ? null : res.body, {
      status: res.status,
      headers: outgoing,
    });
  } catch (error) {
    return error instanceof RangeError
      ? failure("Request body is too large.", 413)
      : failure();
  }
}
export {
  handler as GET,
  handler as POST,
  handler as PATCH,
  handler as DELETE,
  handler as PUT,
};
