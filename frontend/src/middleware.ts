/* eslint-disable @typescript-eslint/no-unused-vars */
import { NextResponse } from "next/server";
import type { NextRequest } from "next/server";

/**
 * Next.js middleware — protects routes that require authentication.
 *
 * Protected prefix: /dashboard (and any future /app/* routes).
 * Public routes: /login, /register, /api/*, and static assets.
 *
 * When an unauthenticated request hits a protected route, the user is
 * redirected to /login?next=<original-path> so they can return after
 * signing in.
 *
 * Note: localStorage is not accessible in middleware (Edge Runtime).
 * We use a cookie ``docassistiq_has_session`` as a lightweight signal.
 * The cookie is set by the login page after receiving the JWT and is
 * cleared on logout. The JWT itself is stored in localStorage (client-
 * side only) for XSS isolation; the cookie is not HttpOnly so JS can
 * manage it. The real authoritative check happens server-side on /me.
 */

const PROTECTED_PREFIXES = ["/dashboard"];

function isProtected(pathname: string): boolean {
  return PROTECTED_PREFIXES.some((prefix) => pathname.startsWith(prefix));
}

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl;

  if (!isProtected(pathname)) {
    return NextResponse.next();
  }

  const hasSession = request.cookies.get("docassistiq_has_session")?.value === "1";

  if (!hasSession) {
    const loginUrl = request.nextUrl.clone();
    loginUrl.pathname = "/login";
    loginUrl.searchParams.set("next", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths EXCEPT:
     * - _next/static (static files)
     * - _next/image (image optimisation)
     * - favicon.ico
     * - api routes
     */
    "/((?!_next/static|_next/image|favicon.ico|api/).*)",
  ],
};
