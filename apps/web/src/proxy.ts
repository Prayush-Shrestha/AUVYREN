import { NextResponse, type NextRequest } from "next/server";

const SESSION_COOKIE = process.env.AUV_SESSION_COOKIE_NAME ?? "auv_session";

/**
 * Optimistic navigation guard only. The API verifies every session and the
 * workspace layout performs the authoritative server-side check.
 */
export function proxy(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasSessionCookie = request.cookies.has(SESSION_COOKIE);

  if (!hasSessionCookie) {
    const signIn = new URL("/sign-in", request.url);
    signIn.searchParams.set("reason", "signin_required");
    signIn.searchParams.set("next", `${pathname}${search}`);
    return NextResponse.redirect(signIn);
  }

  const requestHeaders = new Headers(request.headers);
  requestHeaders.set("x-auvyren-pathname", `${pathname}${search}`);
  return NextResponse.next({ request: { headers: requestHeaders } });
}

export const config = {
  matcher: ["/dashboard/:path*", "/settings/:path*"],
};
