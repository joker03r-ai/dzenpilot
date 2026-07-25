'use client';

import { Sparkles } from 'lucide-react';

import { EmptyState } from '@/components/common/empty-state';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { formatDateTime } from '@/lib/format';
import type { CompetitorAnalysis } from '@/types/api';

interface AnalysisReportProps {
  analysis: CompetitorAnalysis | undefined;
  canAnalyze: boolean;
  storedPublications: number;
  onAnalyze: () => void;
  analyzing: boolean;
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
      </CardHeader>
      <CardContent>
        {items.length === 0 ? (
          <p className="text-sm text-muted-foreground">Данные недоступны</p>
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

export function AnalysisReport({
  analysis,
  canAnalyze,
  storedPublications,
  onAnalyze,
  analyzing,
}: AnalysisReportProps) {
  if (!analysis) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Отчёта пока нет"
        description={
          canAnalyze
            ? 'Нажмите кнопку — Claude разберёт публикации конкурента и объяснит, что у него работает, а что нет.'
            : `Для анализа нужно минимум 3 публикации. Сейчас сохранено: ${storedPublications}.`
        }
        action={
          <Button onClick={onAnalyze} loading={analyzing} disabled={!canAnalyze}>
            <Sparkles aria-hidden />
            Получить отчёт ИИ
          </Button>
        }
      />
    );
  }

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Краткий вывод</CardTitle>
          <CardDescription>
            {analysis.ai_model ? `Модель: ${analysis.ai_model}. ` : ''}
            Отчёт от {formatDateTime(analysis.created_at)}
            {analysis.tokens_output
              ? `. Токенов: ${analysis.tokens_input} на вход, ${analysis.tokens_output} на выход`
              : ''}
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          <p>{analysis.summary || 'Данные недоступны'}</p>

          {analysis.why_it_works ? (
            <div>
              <h3 className="mb-1 font-medium">Почему канал набирает просмотры</h3>
              <p className="text-muted-foreground">{analysis.why_it_works}</p>
            </div>
          ) : null}

          {analysis.publish_rhythm ? (
            <div>
              <h3 className="mb-1 font-medium">Ритм публикаций</h3>
              <p className="text-muted-foreground">{analysis.publish_rhythm}</p>
            </div>
          ) : null}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <ListBlock title="Какие темы работают лучше" items={analysis.working_topics} />
        <ListBlock title="Какие заголовки работают лучше" items={analysis.working_titles} />
        <ListBlock title="Что не дало результата" items={analysis.failed_posts} />
        <ListBlock title="Используемые форматы" items={analysis.formats} />
        <ListBlock title="Сильные стороны" items={analysis.strengths} />
        <ListBlock title="Слабые стороны" items={analysis.weaknesses} />
        <ListBlock title="Нераскрытые темы" items={analysis.content_gaps} />
        <ListBlock title="Как отстроиться" items={analysis.differentiation} />
      </div>

      <ListBlock
        title="Идеи, которые можно адаптировать, не копируя текст"
        items={analysis.adaptable_ideas}
      />

      <Button onClick={onAnalyze} loading={analyzing} variant="outline">
        <Sparkles aria-hidden />
        Обновить отчёт
      </Button>
    </div>
  );
}
