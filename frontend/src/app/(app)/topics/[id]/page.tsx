'use client';

import { ArrowLeft, Bookmark, CalendarPlus, EyeOff, Lightbulb, PenSquare } from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';

import { EmptyState } from '@/components/common/empty-state';
import { PageHeader } from '@/components/common/page-header';
import { ScoreBadge } from '@/components/topics/score-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useTopic, useUpdateTopic } from '@/hooks/use-topics';
import { useProjectContext } from '@/lib/project-context';
import type { CompetitionLevel, ScoreBreakdown } from '@/types/api';

const COMPETITION_LABELS: Record<CompetitionLevel, string> = {
  low: 'Низкая',
  medium: 'Средняя',
  high: 'Высокая',
};

/** Подписи составляющих оценки. Инвертированные названы так, как их видит пользователь. */
const BREAKDOWN_LABELS: { key: keyof ScoreBreakdown; label: string; inverted?: boolean }[] = [
  { key: 'interest', label: 'Интерес аудитории' },
  { key: 'growth', label: 'Рост темы' },
  { key: 'competition', label: 'Свободная ниша' },
  { key: 'seasonality', label: 'Устойчивость по сезонам' },
  { key: 'competitor_success', label: 'Успех у конкурентов' },
  { key: 'series_potential', label: 'Потенциал серии материалов' },
  { key: 'commercial', label: 'Коммерческий потенциал' },
  { key: 'difficulty', label: 'Простота подготовки', inverted: true },
  { key: 'decay_risk', label: 'Долгий срок жизни', inverted: true },
  { key: 'audience_fit', label: 'Соответствие вашей аудитории' },
];

function ListCard({ title, items, empty }: { title: string; items: string[]; empty: string }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">{empty}</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {items.map((item, index) => (
              <li key={`${title}-${index}`} className="flex gap-2">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" aria-hidden />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}

export default function TopicPage() {
  const params = useParams<{ id: string }>();
  const { projectId } = useProjectContext();
  const { data: topic, isLoading } = useTopic(projectId, params.id);
  const updateTopic = useUpdateTopic(projectId);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  if (!topic) {
    return (
      <EmptyState
        icon={Lightbulb}
        title="Тема не найдена"
        description="Возможно, она была удалена."
        action={
          <Button asChild>
            <Link href="/topics">К списку тем</Link>
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/topics">
          <ArrowLeft aria-hidden />
          К списку тем
        </Link>
      </Button>

      <PageHeader
        title={topic.title}
        description={topic.description ?? undefined}
        action={
          <Button asChild size="lg">
            <Link href={`/articles/new?topic=${topic.id}`}>
              <PenSquare aria-hidden />
              Создать статью
            </Link>
          </Button>
        }
      />

      <div className="flex flex-wrap gap-2">
        <Button
          variant="outline"
          size="sm"
          onClick={() => updateTopic.mutate({ id: topic.id, status: 'planned' })}
        >
          <CalendarPlus aria-hidden />
          Добавить в план
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={() => updateTopic.mutate({ id: topic.id, status: 'saved' })}
        >
          <Bookmark aria-hidden />
          Сохранить тему
        </Button>
        <Button
          variant="ghost"
          size="sm"
          className="text-muted-foreground"
          onClick={() => updateTopic.mutate({ id: topic.id, status: 'hidden' })}
        >
          <EyeOff aria-hidden />
          Скрыть тему
        </Button>
      </div>

      {topic.score ? (
        <Card>
          <CardHeader>
            <div className="flex flex-wrap items-center gap-4">
              <ScoreBadge score={topic.score.total_score} size="lg" />
              <div>
                <CardTitle>{topic.score.verdict}</CardTitle>
                <CardDescription>Формула версии {topic.score.formula_version}</CardDescription>
              </div>
            </div>
          </CardHeader>

          <CardContent className="space-y-5">
            <p className="rounded-md bg-accent p-4 text-sm text-accent-foreground">
              {topic.score.explanation}
            </p>

            <div>
              <h3 className="mb-3 text-sm font-medium">Из чего сложилась оценка</h3>
              <div className="grid gap-x-8 gap-y-3 sm:grid-cols-2">
                {BREAKDOWN_LABELS.map((item) => {
                  const raw = topic.score!.breakdown[item.key];
                  // Для инвертированных показываем «полезное» значение, а не сырое
                  const shown = item.inverted ? 100 - raw : raw;
                  return (
                    <div key={item.key} className="space-y-1">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">{item.label}</span>
                        <span className="font-medium tabular-nums">{shown}</span>
                      </div>
                      <Progress value={shown} className="h-1.5" />
                    </div>
                  );
                })}
              </div>
            </div>
          </CardContent>
        </Card>
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Аудитория</p>
          <p className="mt-1 text-sm font-medium">{topic.audience || 'Не указана'}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Конкуренция</p>
          <p className="mt-1 text-sm font-medium">
            {topic.competition_level ? COMPETITION_LABELS[topic.competition_level] : 'Не оценена'}
          </p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Сезонность</p>
          <p className="mt-1 text-sm font-medium">{topic.seasonality || 'Не указана'}</p>
        </Card>
        <Card className="p-4">
          <p className="text-xs text-muted-foreground">Рекомендуемый объём</p>
          <p className="mt-1 text-sm font-medium">
            {topic.recommended_length ? `${topic.recommended_length} знаков` : 'Не указан'}
          </p>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <ListCard
          title="Варианты заголовков"
          items={topic.title_variants}
          empty="Заголовки появятся после подбора темы через поиск."
        />
        <ListCard
          title="Вопросы читателей"
          items={topic.reader_questions}
          empty="Данные недоступны"
        />
        <ListCard
          title="Идеи для серии статей"
          items={topic.series_ideas}
          empty="Данные недоступны"
        />
        <ListCard
          title="Способы монетизации"
          items={topic.monetization}
          empty="Данные недоступны"
        />
        <ListCard title="Риски" items={topic.risks} empty="Существенных рисков не отмечено" />
        <ListCard
          title="На чём основан вывод"
          items={topic.sources}
          empty="Тема добавлена вручную"
        />
      </div>

      <div className="flex flex-wrap gap-2">
        {topic.format ? <Badge variant="secondary">{topic.format}</Badge> : null}
        {topic.region ? <Badge variant="outline">{topic.region}</Badge> : null}
        {topic.niche ? <Badge variant="outline">{topic.niche}</Badge> : null}
      </div>
    </div>
  );
}
