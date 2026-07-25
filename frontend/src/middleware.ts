import { NextResponse, type NextRequest } from 'next/server';

const ACCESS_COOKIE = 'dp_access';
const PUBLIC_PATHS = ['/login', '/register'];

/**
 * Ранняя проверка доступа: если cookie сессии нет, пользователь сразу
 * попадает на страницу входа и не видит пустой интерфейс.
 * Настоящая проверка прав выполняется на сервере при каждом запросе к API.
 */
export function middleware(request: NextRequest) {
  const { pathname, search } = request.nextUrl;
  const hasSession = Boolean(request.cookies.get(ACCESS_COOKIE)?.value);
  const isPublic = PUBLIC_PATHS.some((path) => pathname.startsWith(path));

  if (!hasSession && !isPublic) {
    const url = request.nextUrl.clone();
    url.pathname = '/login';
    url.search = `?next=${encodeURIComponent(pathname + search)}`;
    return NextResponse.redirect(url);
  }

  if (hasSession && isPublic) {
    const url = request.nextUrl.clone();
    url.pathname = '/dashboard';
    url.search = '';
    return NextResponse.redirect(url);
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|webp|ico)$).*)'],
};
