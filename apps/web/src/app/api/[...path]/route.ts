import { NextRequest } from "next/server";

const ALLOWED = /^(profile|settings|declarations(?:\/[a-f0-9-]{36})?|facts(?:\/[a-f0-9-]{36})?|jobs(?:\/[a-f0-9-]{36}(?:\/(?:status|events|eligibility|match|feedback))?)?|tasks(?:\/(?:extract|backup|match|discover|sheets\/(?:import|sync)))?|documents(?:\/[a-f0-9-]{36}\/download)?|candidates(?:\/[a-f0-9-]{36}\/(?:accept|reject))?|sheets\/(?:config|rows|oauth\/start)|discovery(?:\/[a-f0-9-]{36})?)$/;
async function forward(request: NextRequest, context: { params: Promise<{ path: string[] }> }) {
  const path = (await context.params).path.join("/");
  if (!ALLOWED.test(path)) return Response.json({ detail: "Not found" }, { status: 404 });
  const host = request.headers.get("host");
  let localHost = false;
  try {
    const url = new URL(`http://${host}`);
    localHost = ["127.0.0.1", "localhost", "[::1]"].includes(url.hostname) && url.host === host?.toLowerCase();
  } catch { /* Reject malformed and non-loopback hosts. */ }
  if (!localHost) return Response.json({ detail: "Localhost access only" }, { status: 403 });
  const origin = request.headers.get("origin");
  const site = request.headers.get("sec-fetch-site");
  if (site && !["same-origin", "none"].includes(site)) return Response.json({ detail: "Invalid origin" }, { status: 403 });
  if (origin) {
    let sameOrigin = false;
    // Compare against the real Host; Next may reconstruct nextUrl using localhost.
    try { const url = new URL(origin); sameOrigin = url.host === host && url.protocol === request.nextUrl.protocol; } catch { /* invalid origin */ }
    if (!sameOrigin) return Response.json({ detail: "Invalid origin" }, { status: 403 });
  } else if (!["GET", "HEAD"].includes(request.method)) {
    return Response.json({ detail: "Same-origin requests are required" }, { status: 403 });
  }
  const token = process.env.APP_ACCESS_TOKEN;
  if (!token || token.length < 32) return Response.json({ detail: "Local server access is not configured. Start the app using scripts/dev.py." }, { status: 503 });
  const limit = path === "documents" ? 7_100_000 : 1_100_000;
  if (Number(request.headers.get("content-length") ?? 0) > limit) return new Response(null, { status: 413 });
  try {
    const body = ["GET", "HEAD"].includes(request.method) ? undefined : await request.arrayBuffer();
    if (body && body.byteLength > limit) return new Response(null, { status: 413 });
    const result = await fetch(`${process.env.API_BASE_URL ?? "http://127.0.0.1:8000"}/api/${path}`, {
      method: request.method,
      headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
      body, cache: "no-store", redirect: "error", signal: AbortSignal.timeout(15000),
    });
    return new Response(result.body, { status: result.status, headers: { "Content-Type": result.headers.get("content-type") ?? "application/json", "Cache-Control": "no-store", ...(result.headers.get("content-disposition") ? { "Content-Disposition": result.headers.get("content-disposition")! } : {}) } });
  } catch {
    return Response.json({ detail: "The local API is unavailable. Check that it is running." }, { status: 502 });
  }
}
export { forward as GET, forward as POST, forward as PUT, forward as PATCH, forward as DELETE };
