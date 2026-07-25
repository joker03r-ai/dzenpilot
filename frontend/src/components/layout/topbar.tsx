'use client';

import { LogOut, Menu, Settings as SettingsIcon, User as UserIcon } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState } from 'react';

import { AiStatusChip } from '@/components/common/ai-progress';
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
import { useAiSettings } from '@/hooks/use-integrations';
import { useLogout, useMe } from '@/hooks/use-auth';
import { NAV_ITEMS } from '@/lib/nav';
import { useProjectContext } from '@/lib/project-context';

export function Topbar() {
  const pathname = usePathname();
  const [mobileOpen, setMobileOpen] = useState(false);
  const { data, isLoading } = useMe();
  const { projectId } = useProjectContext();
  const { data: aiSettings } = useAiSettings(projectId);
  const logout = useLogout();

  const current = NAV_ITEMS.find(
    (item) => pathname === item.href || pathname.startsWith(`${item.href}/`),
  );
  const user = data?.user;
  const initials = (user?.full_name || user?.email || '?').trim().charAt(0).toUpperCase();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-3 border-b border-border bg-card px-4 lg:px-8">
      {/* Меню для телефонов и планшетов */}
      <Dialog open={mobileOpen} onOpenChange={setMobileOpen}>
        <DialogTrigger asChild>
          <Button variant="ghost" size="icon" className="lg:hidden" aria-label="Открыть меню">
            <Menu />
          </Button>
        </DialogTrigger>
        <DialogContent className="left-0 top-0 h-full max-h-full w-[264px] max-w-[264px] translate-x-0 translate-y-0 overflow-hidden rounded-none border-0 p-0">
          <DialogTitle className="sr-only">Меню разделов</DialogTitle>
          <Sidebar onNavigate={() => setMobileOpen(false)} />
        </DialogContent>
      </Dialog>

      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium">{current?.label ?? 'DzenPilot'}</p>
      </div>

      {aiSettings?.key_configured ? (
        <div className="hidden sm:block">
          <AiStatusChip label={aiSettings.model} />
        </div>
      ) : null}

      {isLoading ? (
        <Skeleton className="size-9 rounded-full" />
      ) : (
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <button
              type="button"
              className="flex size-9 items-center justify-center rounded-full bg-secondary text-sm font-medium text-secondary-foreground transition-colors hover:bg-border focus-ring"
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
              <span className="block truncate font-normal">{user?.email}</span>
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
              className="text-destructive focus:bg-destructive/8"
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
