import { NextResponse, type NextRequest } from 'next/server';

const PUBLIC_PATHS = new Set(['/login', '/_next', '/favicon.ico']);

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (process.env.NEXT_PUBLIC_DISABLE_AUTH === '1') {
    return NextResponse.next();
  }
  if ([...PUBLIC_PATHS].some((p) => pathname === p || pathname.startsWith(p + '/'))) {
    return NextResponse.next();
  }
  // Si pas d'access token côté client, on s'appuie sur le refresh côté route API lors des appels.
  // Ici on vérifie seulement la présence du refresh_token httpOnly.
  const refresh = req.cookies.get('refresh_token')?.value;
  if (!refresh && pathname !== '/login') {
    const url = req.nextUrl.clone();
    url.pathname = '/login';
    url.searchParams.set('next', pathname);
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!api).*)'],
};
