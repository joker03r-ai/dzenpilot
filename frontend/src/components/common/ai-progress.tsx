'use client';

import { Sparkles } from 'lucide-react';

import { cn } from '@/lib/utils';

interface AiProgressProps {
  title?: string;
  description?: string;
  className?: string;
}

/**
 * Индикатор работы модели.
 *
 * Здесь допустимы градиент и свечение — но только пока идёт генерация.
 * В покое элемент не показывается вовсе, поэтому постоянного свечения
 * в интерфейсе не возникает.
 */
export function AiProgress({
  title = 'Модель работает',
  description = 'Обычно это занимает от 10 секунд до двух минут. Не закрывайте страницу.',
  className,
}: AiProgressProps) {
  return (
    <div
      className={cn('ai-working overflow-hidden rounded-lg border border-border bg-card', className)}
      role="status"
      aria-live="polite"
    >
      <div className="flex items-start gap-3 p-4">
        <span className="gradient-ai-mark mt-0.5 flex size-8 shrink-0 items-center justify-center rounded-md text-white">
          <Sparkles className="size-4" aria-hidden />
        </span>

        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{title}</p>
          <p className="mt-0.5 text-sm text-muted-foreground">{description}</p>
        </div>
      </div>

      {/* Бегущая полоса генерации */}
      <div className="relative h-1 w-full overflow-hidden bg-muted">
        <div className="gradient-progress absolute inset-y-0 left-0 w-1/4 animate-progress-slide rounded-full" />
      </div>
    </div>
  );
}

/** Компактный статус активной модели для шапки и карточек. */
export function AiStatusChip({ label = 'ИИ подключён' }: { label?: string }) {
  return (
    <span className="gradient-ai-status inline-flex items-center gap-1.5 rounded-md border border-border px-2 py-1 text-2xs font-medium text-foreground">
      <span className="size-1.5 rounded-full bg-ai-violet" aria-hidden />
      {label}
    </span>
  );
}
