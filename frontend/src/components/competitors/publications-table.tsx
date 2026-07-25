'use client';

import { ExternalLink, FileText, Trash2 } from 'lucide-react';

import { EmptyState } from '@/components/common/empty-state';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { useDeletePublication } from '@/hooks/use-competitors';
import { NO_DATA, formatDate, formatNumber } from '@/lib/format';
import type { Publication } from '@/types/api';

interface PublicationsTableProps {
  projectId: string;
  competitorId: string;
  publications: Publication[];
  page: number;
  pages: number;
  onPageChange: (page: number) => void;
}

export function PublicationsTable({
  projectId,
  competitorId,
  publications,
  page,
  pages,
  onPageChange,
}: PublicationsTableProps) {
  const deletePublication = useDeletePublication(projectId, competitorId);

  if (publications.length === 0) {
    return (
      <EmptyState
        icon={FileText}
        title="Публикаций пока нет"
        description="Добавьте несколько публикаций конкурента вручную или загрузите файл CSV — после этого станут доступны показатели и отчёт ИИ."
      />
    );
  }

  return (
    <Card className="overflow-hidden">
      {/* Таблица прокручивается по горизонтали, чтобы страница не разъезжалась на телефоне */}
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] text-sm">
          <thead className="border-b border-border bg-secondary/50">
            <tr className="text-left">
              <th className="px-4 py-3 font-medium">Заголовок</th>
              <th className="px-4 py-3 font-medium">Дата</th>
              <th className="px-4 py-3 text-right font-medium">Просмотры</th>
              <th className="px-4 py-3 text-right font-medium">Реакции</th>
              <th className="px-4 py-3 font-medium">Разбор заголовка</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>

          <tbody>
            {publications.map((publication) => (
              <tr key={publication.id} className="border-b border-border last:border-0">
                <td className="max-w-md px-4 py-3">
                  <div className="flex items-start gap-2">
                    <span className="line-clamp-2">{publication.title}</span>
                    {publication.url ? (
                      <a
                        href={publication.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="mt-0.5 shrink-0 text-primary"
                        aria-label="Открыть публикацию"
                      >
                        <ExternalLink className="size-3.5" aria-hidden />
                      </a>
                    ) : null}
                  </div>
                  {publication.topic_guess ? (
                    <span className="mt-1 block text-xs text-muted-foreground">
                      {publication.topic_guess}
                    </span>
                  ) : null}
                </td>

                <td className="whitespace-nowrap px-4 py-3 text-muted-foreground">
                  {publication.published_at ? formatDate(publication.published_at) : NO_DATA}
                </td>

                <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums">
                  {publication.views === null ? (
                    <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                  ) : (
                    formatNumber(publication.views)
                  )}
                </td>

                <td className="whitespace-nowrap px-4 py-3 text-right tabular-nums">
                  {publication.reactions === null ? (
                    <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                  ) : (
                    formatNumber(publication.reactions)
                  )}
                </td>

                <td className="px-4 py-3">
                  <div className="flex flex-wrap gap-1">
                    {publication.has_numbers ? <Badge variant="secondary">числа</Badge> : null}
                    {publication.has_question ? <Badge variant="secondary">вопрос</Badge> : null}
                    {publication.has_cta ? <Badge variant="secondary">призыв</Badge> : null}
                    {publication.title_emotionality !== null ? (
                      <Badge
                        variant={publication.title_emotionality > 50 ? 'warning' : 'outline'}
                      >
                        эмоции {publication.title_emotionality}
                      </Badge>
                    ) : null}
                  </div>
                </td>

                <td className="px-4 py-3 text-right">
                  <Button
                    variant="ghost"
                    size="icon"
                    className="text-muted-foreground hover:text-destructive"
                    onClick={() => deletePublication.mutate(publication.id)}
                    aria-label="Удалить публикацию"
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {pages > 1 ? (
        <div className="flex items-center justify-between border-t border-border px-4 py-3">
          <span className="text-sm text-muted-foreground">
            Страница {page} из {pages}
          </span>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              disabled={page <= 1}
              onClick={() => onPageChange(page - 1)}
            >
              Назад
            </Button>
            <Button
              variant="outline"
              size="sm"
              disabled={page >= pages}
              onClick={() => onPageChange(page + 1)}
            >
              Вперёд
            </Button>
          </div>
        </div>
      ) : null}
    </Card>
  );
}
