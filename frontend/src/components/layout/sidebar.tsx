'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

import { AiMark } from '@/components/common/ai-mark';
import { ProjectSwitcher } from '@/components/layout/project-switcher';
import { NAV_ITEMS } from '@/lib/nav';
import { cn } from '@/lib/utils';

interface SidebarProps {
  onNavigate?: () => void;
}

export function Sidebar({ onNavigate }: SidebarProps) {
  const pathname = usePathname();

  return (
    // Однотонная тёмно-синяя панель. Градиента по высоте нет.
    <div className="sidebar-scroll flex h-full flex-col gap-6 overflow-y-auto bg-sidebar px-3 py-5">
      <Link
        href="/dashboard"
        onClick={onNavigate}
        className="flex items-center gap-2.5 rounded-md px-2 py-1 focus-ring"
      >
        <AiMark size="sm" />
        <span className="text-[15px] font-semibold tracking-tight text-white">DzenPilot</span>
      </Link>

      <ProjectSwitcher />

      <nav className="flex-1 space-y-0.5" aria-label="Основное меню">
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
                'group flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors focus-ring',
                active
                  ? 'bg-sidebar-active font-medium text-sidebar-active-foreground'
                  : 'text-sidebar-foreground hover:bg-white/6 hover:text-white',
              )}
            >
              <Icon
                className={cn(
                  'size-[18px] shrink-0',
                  active ? 'text-white' : 'text-sidebar-muted group-hover:text-white',
                )}
                aria-hidden
              />
              <span className="flex-1 truncate">{item.label}</span>
              {item.stage ? (
                <span className="shrink-0 rounded border border-sidebar-border px-1.5 py-0.5 text-2xs text-sidebar-muted">
                  этап {item.stage}
                </span>
              ) : null}
            </Link>
          );
        })}
      </nav>

      <p className="border-t border-sidebar-border px-3 pt-4 text-2xs leading-relaxed text-sidebar-muted">
        Публикация всегда требует вашего подтверждения. Сервис ничего не отправляет сам.
      </p>
    </div>
  );
}
