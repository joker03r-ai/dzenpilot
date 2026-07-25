'use client';

import { Clock, FileText, PenSquare, Sparkles } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useArticles } from '@/hooks/use-articles';
import { formatDateTime, formatNumber } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';
import type { ArticleStatus } from '@/types/api';

const TABS: { value: string; label: string }[] = [
  { value: 'all', label: 'Все' },
  { value: 'draft', label: 'Черновики' },
  { value: 'review', label: 'На проверке' },
  { value: 'ready', label: 'Готовы' },
  { value: 'scheduled', label: 'Запланированы' },
  { value: 'published', label: 'Опубликованы' },
  { value: 'failed', label: 'Ошибка' },
  { value: 'archived', label: 'Архив' },
];

const STATUS_VARIANTS: Record<ArticleStatus, 'default' | 'secondary' | 'success' | 'warning' | 'destructive' | 'outline'> = {
  draft: 'secondary',
  review: 'warning',
  ready: 'success',
  scheduled: 'default',
  published: 'success',
  failed: 'destructive',
  archived: 'outline',
};

export default function ArticlesPage() {
  const { projectId } = useProjectContext();
  const [tab, setTab] = useState('all');

  const { data, isLoading } = useArticles(
    projectId,
    tab === 'all' ? undefined : (tab as ArticleStatus),
  );
  const articles = data?.items ?? [];

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Статьи хранятся отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Статьи"
        description="Все материалы проекта: от черновика до опубликованной статьи."
        action={
          <Button asChild size="lg">
            <Link href="/articles/new">
              <PenSquare aria-hidden />
              Создать статью
            </Link>
          </Button>
        }
      />

      <Tabs value={tab} onValueChange={setTab}>
        <TabsList className="flex-wrap">
          {TABS.map((item) => (
            <TabsTrigger key={item.value} value={item.value}>
              {item.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </Tabs>

      {isLoading ? (
        <div className="space-y-3">
          {[0, 1, 2].map((index) => (
            <Skeleton key={index} className="h-24" />
          ))}
        </div>
      ) : articles.length === 0 ? (
        <EmptyState
          icon={FileText}
          title={tab === 'all' ? 'Статей пока нет' : 'В этом разделе пусто'}
          description={
            tab === 'all'
              ? 'Мастер проведёт по пяти шагам: тема, структура, текст, доработка и проверка перед публикацией.'
              : 'Попробуйте другую вкладку или создайте новую статью.'
          }
          action={
            <Button asChild>
              <Link href="/articles/new">
                <PenSquare aria-hidden />
                Создать статью
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {articles.map((article) => (
            <Card key={article.id} className="p-4 transition-colors hover:border-border-strong">
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div className="min-w-0 flex-1">
                  <Link
                    href={`/articles/${article.id}`}
                    className="block truncate font-medium hover:text-primary focus-ring rounded"
                  >
                    {article.title}
                  </Link>

                  <div className="mt-1.5 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
                    <Badge variant={STATUS_VARIANTS[article.status]}>
                      {article.status_label}
                    </Badge>

                    {article.word_count ? (
                      <span>{formatNumber(article.word_count)} слов</span>
                    ) : null}

                    {article.reading_time_min ? (
                      <span className="flex items-center gap-1">
                        <Clock className="size-3" aria-hidden />
                        {article.reading_time_min} мин чтения
                      </span>
                    ) : null}

                    <span>Изменена {formatDateTime(article.updated_at)}</span>
                  </div>
                </div>

                <Button asChild variant="outline" size="sm" className="shrink-0">
                  <Link href={`/articles/${article.id}`}>Открыть</Link>
                </Button>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
