'use client';

import { Lightbulb, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { TopicCard } from '@/components/topics/topic-card';
import { TopicSearchForm } from '@/components/topics/topic-search-form';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useProject } from '@/hooks/use-projects';
import { useSearchTopics, useTopics } from '@/hooks/use-topics';
import { useProjectContext } from '@/lib/project-context';
import type { TopicStatus } from '@/types/api';

const STATUS_FILTERS: { value: string; label: string }[] = [
  { value: '', label: 'Все темы' },
  { value: 'suggested', label: 'Предложенные' },
  { value: 'saved', label: 'Сохранённые' },
  { value: 'planned', label: 'В плане' },
  { value: 'hidden', label: 'Скрытые' },
];

export default function TopicsPage() {
  const { projectId } = useProjectContext();
  const { data: project } = useProject(projectId);

  const [showForm, setShowForm] = useState(false);
  const [status, setStatus] = useState('');
  const [minScore, setMinScore] = useState('');

  const searchTopics = useSearchTopics(projectId);
  const { data, isLoading } = useTopics(projectId, {
    status: (status || undefined) as TopicStatus | undefined,
    minScore: minScore ? Number(minScore) : undefined,
  });

  const topics = data?.items ?? [];

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Темы хранятся отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Поиск тем"
        description="Сервис предложит темы и объяснит, из чего сложилась оценка каждой — от 0 до 100."
        action={
          <Button size="lg" onClick={() => setShowForm((current) => !current)}>
            <Sparkles aria-hidden />
            {showForm ? 'Свернуть форму' : 'Найти темы'}
          </Button>
        }
      />

      <Hint>
        Оценка складывается из десяти составляющих. Смысловые оценки даёт Claude,
        а успешность у конкурентов считается по вашим реальным данным. Итог считает
        обычный код, поэтому одна и та же тема всегда получает один и тот же балл.
      </Hint>

      {showForm ? (
        <TopicSearchForm
          defaultNiche={project?.niche ?? ''}
          defaultAudience={project?.target_audience ?? ''}
          loading={searchTopics.isPending}
          onSubmit={(request) =>
            searchTopics.mutate(request, { onSuccess: () => setShowForm(false) })
          }
        />
      ) : null}

      {searchTopics.data?.sources_note ? (
        <Alert variant="info">
          <AlertDescription>{searchTopics.data.sources_note}</AlertDescription>
        </Alert>
      ) : null}

      {topics.length > 0 ? (
        <div className="flex flex-col gap-3 sm:flex-row">
          <Select
            value={status}
            onChange={(event) => setStatus(event.target.value)}
            className="sm:w-56"
            aria-label="Статус темы"
          >
            {STATUS_FILTERS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>

          <Select
            value={minScore}
            onChange={(event) => setMinScore(event.target.value)}
            className="sm:w-56"
            aria-label="Минимальная оценка"
          >
            <option value="">Любая оценка</option>
            <option value="80">Только от 80</option>
            <option value="65">Только от 65</option>
            <option value="50">Только от 50</option>
          </Select>
        </div>
      ) : null}

      {isLoading || searchTopics.isPending ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((index) => (
            <Skeleton key={index} className="h-72" />
          ))}
        </div>
      ) : topics.length === 0 ? (
        <EmptyState
          icon={Lightbulb}
          title={status || minScore ? 'Ничего не найдено' : 'Тем пока нет'}
          description={
            status || minScore
              ? 'Попробуйте изменить фильтры.'
              : 'Опишите нишу и аудиторию — сервис подберёт темы, объяснит их перспективность и предложит варианты заголовков.'
          }
          action={
            <Button onClick={() => setShowForm(true)}>
              <Sparkles aria-hidden />
              Найти темы
            </Button>
          }
          secondary="Совет: сначала добавьте нескольких конкурентов с публикациями — тогда оценки будут точнее."
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {topics.map((topic) => (
            <TopicCard key={topic.id} projectId={projectId} topic={topic} />
          ))}
        </div>
      )}
    </div>
  );
}
