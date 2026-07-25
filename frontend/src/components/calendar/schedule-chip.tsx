'use client';

import { CheckCircle2, Copy, Clock, X } from 'lucide-react';

import { Button } from '@/components/ui/button';
import { useCancelSchedule, useDuplicateSchedule, useUpdateSchedule } from '@/hooks/use-calendar';
import { cn } from '@/lib/utils';
import type { ScheduleItem } from '@/types/api';

const STATUS_TONE: Record<string, string> = {
  planned: 'border-primary/30 bg-primary/5',
  ready: 'border-success/30 bg-success/5',
  publishing: 'border-warning/40 bg-warning/10',
  published: 'border-success/40 bg-success/10',
  failed: 'border-destructive/40 bg-destructive/10',
  cancelled: 'border-border bg-muted opacity-60',
};

interface ScheduleChipProps {
  projectId: string;
  item: ScheduleItem;
  compact?: boolean;
}

export function ScheduleChip({ projectId, item, compact = false }: ScheduleChipProps) {
  const updateSchedule = useUpdateSchedule(projectId);
  const duplicateSchedule = useDuplicateSchedule(projectId);
  const cancelSchedule = useCancelSchedule(projectId);

  const draggable = item.status === 'planned' || item.status === 'ready';

  return (
    <div
      draggable={draggable}
      onDragStart={(event) => {
        event.dataTransfer.setData('text/plain', item.id);
        event.dataTransfer.effectAllowed = 'move';
      }}
      className={cn(
        'rounded-md border p-2 text-left text-xs transition-shadow',
        STATUS_TONE[item.status] ?? STATUS_TONE.planned,
        draggable && 'cursor-grab active:cursor-grabbing hover:shadow-card',
      )}
      title={draggable ? 'Перетащите на другой день, чтобы перенести' : undefined}
    >
      <div className="flex items-start gap-1.5">
        <Clock className="mt-0.5 size-3 shrink-0 text-muted-foreground" aria-hidden />
        <span className="font-medium tabular-nums">{item.local_time}</span>
        {item.confirmed_by_user ? (
          <CheckCircle2 className="ml-auto size-3 shrink-0 text-success" aria-hidden />
        ) : null}
      </div>

      <p className={cn('mt-1 font-medium', compact ? 'line-clamp-1' : 'line-clamp-2')}>
        {item.article_title}
      </p>

      {!compact ? (
        <>
          <p className="mt-0.5 text-muted-foreground">{item.status_label}</p>
          {item.note ? (
            <p className="mt-1 line-clamp-2 text-muted-foreground">{item.note}</p>
          ) : null}

          {item.status !== 'cancelled' && item.status !== 'published' ? (
            <div className="mt-2 flex flex-wrap gap-1">
              {!item.confirmed_by_user ? (
                <Button
                  size="sm"
                  variant="outline"
                  className="h-7 px-2 text-[11px]"
                  onClick={() =>
                    updateSchedule.mutate({ id: item.id, confirmed_by_user: true })
                  }
                >
                  Подтвердить
                </Button>
              ) : null}

              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-[11px]"
                onClick={() => duplicateSchedule.mutate(item.id)}
              >
                <Copy className="size-3" aria-hidden />
                Копия
              </Button>

              <Button
                size="sm"
                variant="ghost"
                className="h-7 px-2 text-[11px] text-destructive hover:bg-destructive/10"
                onClick={() => cancelSchedule.mutate(item.id)}
              >
                <X className="size-3" aria-hidden />
                Отменить
              </Button>
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
