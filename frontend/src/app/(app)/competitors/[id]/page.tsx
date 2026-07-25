'use client';

import {
  ArrowLeft,
  ExternalLink,
  FileUp,
  Plus,
  Sparkles,
  Trash2,
} from 'lucide-react';
import Link from 'next/link';
import { useParams, useRouter } from 'next/navigation';
import { useRef, useState } from 'react';

import { AddPublicationDialog } from '@/components/competitors/add-publication-dialog';
import { AnalysisReport } from '@/components/competitors/analysis-report';
import { PublicationsTable } from '@/components/competitors/publications-table';
import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useAnalyses,
  useAnalyzeCompetitor,
  useCompetitor,
  useDeleteCompetitor,
  useImportCsv,
  usePublications,
} from '@/hooks/use-competitors';
import { NO_DATA, formatDate, formatNumber } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';

export default function CompetitorPage() {
  const params = useParams<{ id: string }>();
  const router = useRouter();
  const { projectId } = useProjectContext();
  const fileInput = useRef<HTMLInputElement>(null);
  const [page, setPage] = useState(1);

  const competitorId = params.id;
  const { data: competitor, isLoading } = useCompetitor(projectId, competitorId);
  const { data: publications } = usePublications(projectId, competitorId, page);
  const { data: analyses } = useAnalyses(projectId, competitorId);

  const analyze = useAnalyzeCompetitor(projectId, competitorId);
  const importCsv = useImportCsv(projectId, competitorId);
  const removeCompetitor = useDeleteCompetitor(projectId);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  if (!competitor) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Конкурент не найден"
        description="Возможно, он был удалён."
        action={
          <Button asChild>
            <Link href="/competitors">К списку конкурентов</Link>
          </Button>
        }
      />
    );
  }

  const stored = competitor.stored_publications;
  const canAnalyze = stored >= 3;
  const latestAnalysis = analyses?.[0];

  const metrics: { label: string; value: string }[] = [
    { label: 'Подписчики', value: competitor.subscribers_count === null ? NO_DATA : formatNumber(competitor.subscribers_count) },
    { label: 'Публикаций сохранено', value: formatNumber(stored) },
    { label: 'Средние просмотры', value: competitor.avg_views === null ? NO_DATA : formatNumber(competitor.avg_views) },
    { label: 'Максимум просмотров', value: competitor.max_views === null ? NO_DATA : formatNumber(competitor.max_views) },
    { label: 'Минимум просмотров', value: competitor.min_views === null ? NO_DATA : formatNumber(competitor.min_views) },
    { label: 'Вовлечённость', value: competitor.avg_engagement_rate === null ? NO_DATA : `${Number(competitor.avg_engagement_rate).toFixed(2)}%` },
    { label: 'Средняя длина статьи', value: competitor.avg_article_length === null ? NO_DATA : `${formatNumber(competitor.avg_article_length)} знаков` },
    { label: 'Частота публикаций', value: competitor.avg_publish_interval_days === null ? NO_DATA : `раз в ${Number(competitor.avg_publish_interval_days).toFixed(1)} дн.` },
    { label: 'Последний анализ', value: competitor.last_analyzed_at ? formatDate(competitor.last_analyzed_at) : 'Ещё не проводился' },
  ];

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/competitors">
          <ArrowLeft aria-hidden />
          К списку конкурентов
        </Link>
      </Button>

      <PageHeader
        title={competitor.name}
        description={
          competitor.description ||
          `${competitor.niche || 'Тематика не указана'}. Здесь собраны публикации конкурента и отчёт ИИ.`
        }
        action={
          <Button
            size="lg"
            onClick={() => analyze.mutate()}
            loading={analyze.isPending}
            disabled={!canAnalyze}
            title={canAnalyze ? undefined : 'Нужно минимум 3 публикации'}
          >
            <Sparkles aria-hidden />
            {latestAnalysis ? 'Обновить отчёт' : 'Получить отчёт ИИ'}
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-2">
        {competitor.group_name ? <Badge variant="outline">{competitor.group_name}</Badge> : null}
        {competitor.url ? (
          <a
            href={competitor.url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-1 text-sm text-primary hover:underline"
          >
            Открыть канал
            <ExternalLink className="size-3.5" aria-hidden />
          </a>
        ) : null}
      </div>

      {!canAnalyze ? (
        <Hint title="Как получить отчёт">
          Для анализа нужно минимум 3 публикации конкурента — сейчас сохранено {stored}.
          Добавьте их вручную кнопкой ниже или загрузите файлом CSV. Чем больше публикаций
          с просмотрами, тем точнее выводы.
        </Hint>
      ) : null}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {metrics.map((metric) => (
          <Card key={metric.label} className="p-4">
            <p className="text-xs text-muted-foreground">{metric.label}</p>
            <p
              className={
                metric.value === NO_DATA
                  ? 'mt-1 text-sm text-muted-foreground'
                  : 'mt-1 text-lg font-semibold tabular-nums'
              }
            >
              {metric.value}
            </p>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="publications">
        <TabsList>
          <TabsTrigger value="publications">Публикации ({stored})</TabsTrigger>
          <TabsTrigger value="report">Отчёт ИИ</TabsTrigger>
          <TabsTrigger value="details">Подробности</TabsTrigger>
        </TabsList>

        <TabsContent value="publications" className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <AddPublicationDialog
              projectId={projectId!}
              competitorId={competitorId}
              trigger={
                <Button>
                  <Plus aria-hidden />
                  Добавить публикацию
                </Button>
              }
            />

            <Button
              variant="outline"
              onClick={() => fileInput.current?.click()}
              loading={importCsv.isPending}
            >
              <FileUp aria-hidden />
              Импорт CSV
            </Button>
            <input
              ref={fileInput}
              type="file"
              accept=".csv,text/csv"
              className="hidden"
              onChange={(event) => {
                const file = event.target.files?.[0];
                if (file) importCsv.mutate(file);
                event.target.value = '';
              }}
            />
          </div>

          <Hint title="Формат файла CSV">
            Обязательная колонка одна — «Заголовок». Дополнительно распознаются
            «Ссылка», «Дата», «Просмотры», «Реакции», «Комментарии», «Тема», «Формат».
            Подойдёт файл, сохранённый из Excel или Google Таблиц.
          </Hint>

          <PublicationsTable
            projectId={projectId!}
            competitorId={competitorId}
            publications={publications?.items ?? []}
            page={page}
            pages={publications?.pages ?? 0}
            onPageChange={setPage}
          />
        </TabsContent>

        <TabsContent value="report">
          <AnalysisReport
            analysis={latestAnalysis}
            canAnalyze={canAnalyze}
            storedPublications={stored}
            onAnalyze={() => analyze.mutate()}
            analyzing={analyze.isPending}
          />
        </TabsContent>

        <TabsContent value="details" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Заметки</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="whitespace-pre-wrap text-sm text-muted-foreground">
                {competitor.notes || 'Заметок пока нет.'}
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Частые слова в заголовках</CardTitle>
            </CardHeader>
            <CardContent>
              {competitor.popular_title_words.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  Появятся, когда будет добавлено больше публикаций.
                </p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {competitor.popular_title_words.map((item) => (
                    <Badge key={item.word} variant="secondary">
                      {item.word} · {item.count}
                    </Badge>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Изображения и видео</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-sm text-muted-foreground">
                Требуется ручной импорт. Автоматически получить эти показатели
                законным способом нельзя — сервис не обходит защиту площадки.
              </p>
            </CardContent>
          </Card>

          <Card className="border-destructive/25">
            <CardHeader>
              <CardTitle className="text-destructive">Удаление</CardTitle>
            </CardHeader>
            <CardContent>
              <p className="mb-3 text-sm text-muted-foreground">
                Конкурент и все его публикации будут удалены из проекта.
              </p>
              <Button
                variant="outline"
                className="text-destructive hover:bg-destructive/10"
                onClick={() =>
                  removeCompetitor.mutate(competitorId, {
                    onSuccess: () => router.push('/competitors'),
                  })
                }
                loading={removeCompetitor.isPending}
              >
                <Trash2 aria-hidden />
                Удалить конкурента
              </Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
