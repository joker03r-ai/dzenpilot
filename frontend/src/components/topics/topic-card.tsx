'use client';

import { CalendarPlus, Bookmark, EyeOff, PenSquare } from 'lucide-react';
import Link from 'next/link';

import { ScoreBadge } from '@/components/topics/score-badge';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader } from '@/components/ui/card';
import { useUpdateTopic } from '@/hooks/use-topics';
import type { CompetitionLevel, Topic } from '@/types/api';

const COMPETITION_LABELS: Record<CompetitionLevel, string> = {
  low: 'Конкуренция низкая',
  medium: 'Конкуренция средняя',
  high: 'Конкуренция высокая',
};

export function TopicCard({ projectId, topic }: { projectId: string; topic: Topic }) {
  const updateTopic = useUpdateTopic(projectId);

  return (
    <Card className="flex flex-col transition-shadow hover:shadow-lift">
      <CardHeader className="pb-3">
        <div className="flex items-start gap-3">
          {topic.score ? (
            <ScoreBadge score={topic.score.total_score} />
          ) : (
            <span className="flex size-11 shrink-0 items-center justify-center rounded-full bg-muted text-xs text-muted-foreground">
              —
            </span>
          )}

          <div className="min-w-0 flex-1">
            <Link
              href={`/topics/${topic.id}`}
              className="block font-semibold leading-snug hover:text-primary focus-ring rounded"
            >
              {topic.title}
            </Link>
            {topic.score ? (
              <p className="mt-0.5 text-xs text-muted-foreground">{topic.score.verdict}</p>
            ) : null}
          </div>
        </div>
      </CardHeader>

      <CardContent className="mt-auto space-y-3">
        {topic.description ? (
          <p className="line-clamp-3 text-sm text-muted-foreground">{topic.description}</p>
        ) : null}

        <div className="flex flex-wrap gap-1.5">
          {topic.competition_level ? (
            <Badge variant="outline">{COMPETITION_LABELS[topic.competition_level]}</Badge>
          ) : null}
          {topic.format ? <Badge variant="secondary">{topic.format}</Badge> : null}
          {topic.recommended_length ? (
            <Badge variant="outline">≈ {topic.recommended_length} знаков</Badge>
          ) : null}
          {topic.status === 'saved' ? <Badge variant="success">Сохранена</Badge> : null}
          {topic.status === 'planned' ? <Badge variant="success">В плане</Badge> : null}
        </div>

        <div className="flex flex-wrap gap-2 border-t border-border pt-3">
          <Button asChild size="sm">
            <Link href={`/articles/new?topic=${topic.id}`}>
              <PenSquare aria-hidden />
              Создать статью
            </Link>
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={() => updateTopic.mutate({ id: topic.id, status: 'planned' })}
          >
            <CalendarPlus aria-hidden />
            В план
          </Button>

          <Button
            variant="ghost"
            size="sm"
            onClick={() => updateTopic.mutate({ id: topic.id, status: 'saved' })}
          >
            <Bookmark aria-hidden />
            Сохранить
          </Button>

          <Button
            variant="ghost"
            size="sm"
            className="text-muted-foreground"
            onClick={() => updateTopic.mutate({ id: topic.id, status: 'hidden' })}
          >
            <EyeOff aria-hidden />
            Скрыть
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
