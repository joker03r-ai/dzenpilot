'use client';

import { ExternalLink, FileText, Sparkles, TrendingUp } from 'lucide-react';
import Link from 'next/link';

import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { NO_DATA, formatCompact, formatDate } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Competitor, CompetitorStatus } from '@/types/api';

const STATUS_LABELS: Record<CompetitorStatus, { label: string; variant: 'default' | 'success' | 'warning' | 'destructive' }> = {
  new: { label: 'Новый', variant: 'default' },
  analyzing: { label: 'Анализируется', variant: 'warning' },
  analyzed: { label: 'Проанализирован', variant: 'success' },
  error: { label: 'Ошибка анализа', variant: 'destructive' },
};

interface CompetitorCardProps {
  competitor: Competitor;
  selected: boolean;
  onToggle: () => void;
}

export function CompetitorCard({ competitor, selected, onToggle }: CompetitorCardProps) {
  const status = STATUS_LABELS[competitor.status];

  return (
    <Card
      className={cn(
        'flex flex-col transition-shadow hover:shadow-lift',
        selected && 'ring-2 ring-primary',
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          <input
            type="checkbox"
            checked={selected}
            onChange={onToggle}
            className="mt-1 size-4 shrink-0 accent-primary"
            aria-label={`Выбрать ${competitor.name} для сравнения`}
          />

          <div className="min-w-0 flex-1">
            <Link
              href={`/competitors/${competitor.id}`}
              className="block truncate font-semibold hover:text-primary focus-ring rounded"
            >
              {competitor.name}
            </Link>
            <p className="truncate text-sm text-muted-foreground">
              {competitor.niche || 'Тематика не указана'}
            </p>
          </div>

          <Badge variant={status.variant} className="shrink-0">
            {status.label}
          </Badge>
        </div>

        {competitor.group_name ? (
          <Badge variant="outline" className="w-fit">
            {competitor.group_name}
          </Badge>
        ) : null}
      </CardHeader>

      <CardContent className="mt-auto space-y-3">
        <dl className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <dt className="text-xs text-muted-foreground">Средние просмотры</dt>
            <dd className="font-medium tabular-nums">
              {competitor.avg_views === null ? (
                <span className="text-xs font-normal text-muted-foreground">{NO_DATA}</span>
              ) : (
                formatCompact(competitor.avg_views)
              )}
            </dd>
          </div>

          <div>
            <dt className="text-xs text-muted-foreground">Подписчики</dt>
            <dd className="font-medium tabular-nums">
              {competitor.subscribers_count === null ? (
                <span className="text-xs font-normal text-muted-foreground">{NO_DATA}</span>
              ) : (
                formatCompact(competitor.subscribers_count)
              )}
            </dd>
          </div>

          <div>
            <dt className="text-xs text-muted-foreground">Публикаций сохранено</dt>
            <dd className="font-medium tabular-nums">{competitor.stored_publications}</dd>
          </div>

          <div>
            <dt className="text-xs text-muted-foreground">Раз в</dt>
            <dd className="font-medium tabular-nums">
              {competitor.avg_publish_interval_days === null ? (
                <span className="text-xs font-normal text-muted-foreground">{NO_DATA}</span>
              ) : (
                `${Number(competitor.avg_publish_interval_days).toFixed(1)} дн.`
              )}
            </dd>
          </div>
        </dl>

        <div className="flex flex-wrap items-center gap-2 border-t border-border pt-3 text-xs text-muted-foreground">
          {competitor.has_analysis ? (
            <span className="flex items-center gap-1 text-success">
              <Sparkles className="size-3.5" aria-hidden />
              Отчёт готов
            </span>
          ) : (
            <span className="flex items-center gap-1">
              <FileText className="size-3.5" aria-hidden />
              Отчёта пока нет
            </span>
          )}

          {competitor.last_analyzed_at ? (
            <span className="flex items-center gap-1">
              <TrendingUp className="size-3.5" aria-hidden />
              {formatDate(competitor.last_analyzed_at)}
            </span>
          ) : null}

          {competitor.url ? (
            <a
              href={competitor.url}
              target="_blank"
              rel="noopener noreferrer"
              className="ml-auto flex items-center gap-1 text-primary hover:underline"
            >
              Канал
              <ExternalLink className="size-3.5" aria-hidden />
            </a>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
}
