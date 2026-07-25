'use client';

import { Compass } from 'lucide-react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { ProjectSwitcher } from '@/components/layout/project-switcher';
import { Badge } from '@/components/ui/badge';
import { NAV_ITEMS } from '@/lib/nav';
import { cn } from '@/lib/utils';

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();

  return (
    <div className="flex h-full flex-col gap-6 border-r border-border bg-card px-4 py-6">
      <Link
        href="/dashboard"
        onClick={onNavigate}
        className="flex items-center gap-2.5 px-2 focus-ring rounded-md"
      >
        <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
          <Compass className="size-5" aria-hidden />
        </span>
        <span className="text-lg font-semibold tracking-tight">DzenPilot</span>
      </Link>

      <ProjectSwitcher />

      <nav className="flex-1 space-y-1" aria-label="Основное меню">
        {NAV_ITEMS.map((item) => {
          const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
          const Icon = item.icon;

          return (
            <Link
              key={item.href}
              href={item.href}
              onClick={onNavigate}
              aria-current={active ? 'page' : undefined}
              className={cn(
                'group flex items-center gap-3 rounded-md px-3 py-2.5 text-sm font-medium transition-colors focus-ring',
                active
                  ? 'bg-accent text-accent-foreground'
                  : 'text-muted-foreground hover:bg-secondary hover:text-foreground',
              )}
            >
              <Icon className="size-[18px] shrink-0" aria-hidden />
              <span className="flex-1 truncate">{item.label}</span>
              {item.stage ? (
                <Badge variant="outline" className="shrink-0 text-[10px]">
                  этап {item.stage}
                </Badge>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <p className="px-3 text-xs leading-relaxed text-muted-foreground">
        Публикация всегда требует вашего подтверждения. Сервис ничего не отправляет сам.
      </p>
    </div>
  );
}
