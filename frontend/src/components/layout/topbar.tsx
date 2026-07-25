'use client';

import { LogOut, Menu, Settings as SettingsIcon, User as UserIcon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { Sidebar } from '@/components/layout/sidebar';
import { Button } from '@/components/ui/button';
import { Dialog, DialogContent, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { useLogout, useMe } from '@/hooks/use-auth';
import { NAV_ITEMS } from '@/lib/nav';

export function Topbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data, isLoading } = useMe();
  const logout = useLogout();

  const current = NAV_ITEMS.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  );
  const user = data?.user;
  const initials = (user?.full_name || user?.email || '?').trim().charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-3 border-b border-border bg-card/80 px-4 backdrop-blur lg:px-8">
      {/* Меню для телефонов и планшетов */}
      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Открыть меню">
            <Menu />
          </Button>
        </DialogTrigger>
        <DialogContent className="left-0 top-0 h-full max-w-[280px] translate-x-0 translate-y-0 rounded-none p-0">
          <DialogTitle className="sr-only">Меню разделов</DialogTitle>
          <Sidebar onNavigate={() => setMobileOpen(false)} />
        </DialogContent>
      </Dialog>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{current?.label ?? 'DzenPilot'}</p>
        <p className="hidden truncate text-xs text-muted-foreground sm:block">
          {current?.description ?? 'Центр управления контентом Дзена'}
        </p>
      </div>

      {isLoading ? (
        <Skeleton className="size-10 rounded-full" />
      ) : (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex size-10 items-center justify-center rounded-full bg-accent text-sm font-semibold text-accent-foreground transition-colors hover:bg-primary hover:text-primary-foreground focus-ring"
              aria-label="Меню пользователя"
            >
              {initials}
            </button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-64">
            <DropdownMenuLabel>
              <span className="block truncate font-medium text-foreground">
                {user?.full_name || 'Без имени'}
              </span>
              <span className="block truncate">{user?.email}</span>
            </DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuItem asChild>
              <Link href="/settings">
                <UserIcon className="size-4" aria-hidden />
                Профиль
              </Link>
            </DropdownMenuItem>
            <DropdownMenuItem asChild>
              <Link href="/settings">
                <SettingsIcon className="size-4" aria-hidden />
                Настройки
              </Link>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem
              onSelect={() => logout.mutate()}
              className="text-destructive focus:bg-destructive/10"
            >
              <LogOut className="size-4" aria-hidden />
              Выйти
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      )}
    </header>
  );
}
