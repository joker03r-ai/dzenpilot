'use client';

import { BarChart3, Plus, Search, Sparkles, Users } from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';

import { AddCompetitorDialog } from '@/components/competitors/add-competitor-dialog';
import { CompetitorCard } from '@/components/competitors/competitor-card';
import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useCompetitorGroups, useCompetitors } from '@/hooks/use-competitors';
import { useProjectContext } from '@/lib/project-context';

export default function CompetitorsPage() {
  const { projectId } = useProjectContext();
  const [search, setSearch] = useState('');
  const [group, setGroup] = useState('');
  const [selected, setSelected] = useState<string[]>([]);

  const { data, isLoading } = useCompetitors(projectId, { search, group });
  const { data: groups } = useCompetitorGroups(projectId);

  const competitors = data?.items ?? [];

  const toggleSelected = (id: string) => {
    setSelected((current) =>
      current.includes(id) ? current.filter((item) => item !== id) : [...current, id],
    );
  };

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Конкуренты хранятся отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Конкуренты"
        description="Добавьте каналы вашей тематики, сохраните их публикации — и сервис покажет, какие темы и заголовки у них работают."
        action={
          <AddCompetitorDialog
            projectId={projectId}
            trigger={
              <Button size="lg">
                <Plus aria-hidden />
                Добавить конкурента
              </Button>
            }
          />
        }
      />

      <Hint>
        Показатели считаются только по тем публикациям, которые вы добавили вручную или
        загрузили файлом CSV. Если данных о просмотрах нет, сервис честно пишет
        «Данные недоступны» и не подставляет выдуманные цифры.
      </Hint>

      {competitors.length > 0 || search || group ? (
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <Search
              className="pointer-events-none absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground"
              aria-hidden
            />
            <Input
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              placeholder="Поиск по названию"
              className="pl-9"
            />
          </div>

          <Select
            value={group}
            onChange={(event) => setGroup(event.target.value)}
            className="sm:w-56"
            aria-label="Группа конкурентов"
          >
            <option value="">Все группы</option>
            {groups?.map((item) => (
              <option key={item} value={item}>
                {item}
              </option>
            ))}
          </Select>

          <Button
            variant="outline"
            disabled={selected.length < 2}
            asChild={selected.length >= 2}
            title={selected.length < 2 ? 'Выберите минимум двух конкурентов' : undefined}
          >
            {selected.length >= 2 ? (
              <Link href={`/competitors/compare?ids=${selected.join(',')}`}>
                <BarChart3 aria-hidden />
                Сравнить ({selected.length})
              </Link>
            ) : (
              <span>
                <BarChart3 aria-hidden />
                Сравнить
              </span>
            )}
          </Button>
        </div>
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2].map((index) => (
            <Skeleton key={index} className="h-64" />
          ))}
        </div>
      ) : competitors.length === 0 ? (
        <EmptyState
          icon={Users}
          title={search || group ? 'Ничего не найдено' : 'Пока ни одного конкурента'}
          description={
            search || group
              ? 'Попробуйте изменить условия поиска или выбрать другую группу.'
              : 'Добавьте 3–5 каналов вашей тематики. Достаточно ссылки или названия — остальное можно заполнить позже.'
          }
          action={
            <AddCompetitorDialog
              projectId={projectId}
              trigger={
                <Button>
                  <Plus aria-hidden />
                  Добавить конкурента
                </Button>
              }
            />
          }
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {competitors.map((competitor) => (
            <CompetitorCard
              key={competitor.id}
              competitor={competitor}
              selected={selected.includes(competitor.id)}
              onToggle={() => toggleSelected(competitor.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}
