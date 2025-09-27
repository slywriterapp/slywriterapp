import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

export function middleware(request: NextRequest) {
  // DISABLED - Auth is handled client-side with localStorage
  // This middleware was interfering with the auth flow
  return NextResponse.next()

  /* Original middleware code - kept for reference
  const { pathname } = request.nextUrl

  // Allow access to login page, auth-redirect page, API routes, and static files
  if (
    pathname.startsWith('/login') ||
    pathname.startsWith('/auth-redirect') ||
    pathname.startsWith('/api') ||
    pathname.startsWith('/_next') ||
    pathname.startsWith('/favicon') ||
    pathname.includes('.')
  ) {
    return NextResponse.next()
  }

  // Check for auth token in cookies
  const token = request.cookies.get('auth_token')?.value

  // If no token and trying to access protected routes, redirect to login
  if (!token && pathname !== '/login') {
    return NextResponse.redirect(new URL('/login', request.url))
  }

  return NextResponse.next()
  */
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - api (API routes)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    '/((?!api|_next/static|_next/image|favicon.ico).*)',
  ],
}