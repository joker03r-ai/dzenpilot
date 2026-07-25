'use client';

import {
  AlertTriangle,
  ArrowRight,
  CalendarClock,
  CheckCircle2,
  FileText,
  Lightbulb,
  PenSquare,
  Sparkles,
  Users,
} from 'lucide-react';
import Link from 'next/link';

import { EmptyState } from '@/components/common/empty-state';
import { StatCard } from '@/components/common/stat-card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useDashboard } from '@/hooks/use-projects';
import { errorMessage } from '@/lib/api';
import { formatNumber, formatRelative } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';
import { cn } from '@/lib/utils';
import type { ActivityItem } from '@/types/api';

const ACTIVITY_STYLES: Record<string, string> = {
  success: 'bg-success/10 text-success',
  error: 'bg-destructive/10 text-destructive',
  warning: 'bg-warning/12 text-warning-foreground',
  info: 'bg-secondary text-muted-foreground',
};

function activityIcon(item: ActivityItem) {
  switch (item.kind) {
    case 'topic':
      return Lightbulb;
    case 'article':
      return FileText;
    case 'competitor_publication':
      return Users;
    case 'publication_error':
      return AlertTriangle;
    default:
      return CalendarClock;
  }
}

export default function DashboardPage() {
  const { projectId, ready } = useProjectContext();
  const { data, isLoading, isError, error, refetch } = useDashboard(projectId);

  if (!ready || (isLoading && projectId)) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-32 w-full" />
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          {[0, 1, 2, 3].map((index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-72 w-full" />
      </div>
    );
  }

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Создайте первый проект"
        description="Проект — это один канал Дзена со своими конкурентами, темами и календарём. Кнопка создания находится в меню слева."
      />
    );
  }

  if (isError) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="Не удалось загрузить данные"
        description={errorMessage(error)}
        action={<Button onClick={() => refetch()}>Повторить</Button>}
      />
    );
  }

  if (!data) return null;

  const { counters, steps, activity, setup_progress: setupProgress } = data;
  const doneSteps = steps.filter((step) => step.done).length;

  return (
    <div className="space-y-6">
      {/* Приветственный блок. Единственный градиент на экране —
          декоративный элемент справа. */}
      <Card className="relative overflow-hidden">
        <div
          className="gradient-hero-orb pointer-events-none absolute -right-16 -top-20 hidden size-64 rounded-full opacity-25 sm:block"
          aria-hidden
        />

        <div className="relative flex flex-col gap-6 p-6 lg:flex-row lg:items-end lg:justify-between lg:p-8">
          <div className="max-w-2xl space-y-3">
            <Badge variant="secondary">{data.project_name}</Badge>
            <h1 className="text-2xl font-semibold sm:text-[28px]">{data.greeting}</h1>
            <p className="max-w-xl text-sm leading-relaxed text-muted-foreground">
              {data.user_name ? `${data.user_name}, здесь` : 'Здесь'} видно всё сразу: конкуренты,
              найденные темы, статьи и план публикаций. Начните с одного шага — сервис подскажет,
              с какого именно.
            </p>

            <div className="max-w-xs space-y-2 pt-2">
              <div className="flex items-center justify-between text-[13px]">
                <span className="text-muted-foreground">Настройка сервиса</span>
                <span className="font-medium tabular-nums">{setupProgress}%</span>
              </div>
              <Progress value={setupProgress} />
              <p className="text-2xs text-muted-foreground">
                Выполнено {doneSteps} из {steps.length} шагов
              </p>
            </div>
          </div>

          <Button asChild size="lg" className="shrink-0">
            <Link href="/articles/new">
              <PenSquare aria-hidden />
              Создать новую статью
            </Link>
          </Button>
        </div>
      </Card>

      {/* Показатели */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard
          label="Конкуренты"
          value={formatNumber(counters.competitors)}
          hint="Каналы под наблюдением"
          icon={Users}
        />
        <StatCard
          label="Найденные темы"
          value={formatNumber(counters.topics)}
          hint="С оценкой перспективности"
          icon={Lightbulb}
        />
        <StatCard
          label="Созданные статьи"
          value={formatNumber(counters.articles)}
          hint={`Опубликовано: ${formatNumber(counters.published)}`}
          icon={FileText}
        />
        <StatCard
          label="Запланировано"
          value={formatNumber(counters.scheduled)}
          hint="Ждут подтверждения публикации"
          icon={CalendarClock}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-5">
        {/* Что сделать сейчас */}
        <Card className="lg:col-span-3">
          <CardHeader>
            <CardTitle>Что сделать сейчас</CardTitle>
            <CardDescription>
              Пять шагов, после которых сервис работает в полную силу. Порядок можно менять.
            </CardDescription>
          </CardHeader>

          <CardContent className="space-y-3">
            {steps.map((step) => (
              <div
                key={step.code}
                className={cn(
                  'rounded-md border p-4 transition-colors',
                  step.done ? 'border-success/20 bg-success/5' : 'border-border bg-surface',
                )}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                  <div className="min-w-0 flex-1 space-y-1.5">
                    <div className="flex items-center gap-2">
                      {step.done ? (
                        <CheckCircle2 className="size-4 shrink-0 text-success" aria-hidden />
                      ) : (
                        <span
                          className="size-4 shrink-0 rounded-full border-2 border-muted-foreground/40"
                          aria-hidden
                        />
                      )}
                      <h3 className="truncate text-sm font-medium">{step.title}</h3>
                      <Badge variant={step.done ? 'success' : 'outline'} className="shrink-0">
                        {step.done ? 'Готово' : 'Не начато'}
                      </Badge>
                    </div>

                    <p className="text-sm text-muted-foreground">{step.description}</p>
                    <Progress value={step.progress} className="h-1.5 max-w-xs" />
                  </div>

                  <Button
                    asChild
                    variant={step.done ? 'ghost' : 'outline'}
                    size="sm"
                    className="shrink-0"
                  >
                    <Link href={step.action_href}>
                      {step.action_label}
                      <ArrowRight aria-hidden />
                    </Link>
                  </Button>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Последняя активность */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Последняя активность</CardTitle>
            <CardDescription>Темы, статьи, публикации конкурентов и ошибки.</CardDescription>
          </CardHeader>

          <CardContent>
            {activity.length === 0 ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Пока пусто. Как только появятся конкуренты, темы или статьи, события
                будут показаны здесь.
              </p>
            ) : (
              <ul className="space-y-1">
                {activity.map((item, index) => {
                  const Icon = activityIcon(item);
                  const content = (
                    <div className="flex gap-3 rounded-md p-2.5 transition-colors hover:bg-secondary">
                      <span
                        className={cn(
                          'flex size-8 shrink-0 items-center justify-center rounded-md',
                          ACTIVITY_STYLES[item.level] ?? ACTIVITY_STYLES.info,
                        )}
                      >
                        <Icon className="size-4" aria-hidden />
                      </span>
                      <div className="min-w-0 flex-1">
                        <p className="truncate text-sm font-medium">{item.title}</p>
                        {item.subtitle ? (
                          <p className="truncate text-xs text-muted-foreground">{item.subtitle}</p>
                        ) : null}
                        {item.happened_at ? (
                          <p className="text-xs text-muted-foreground/70">
                            {formatRelative(item.happened_at)}
                          </p>
                        ) : null}
                      </div>
                    </div>
                  );

                  return (
                    <li key={`${item.kind}-${item.entity_id ?? index}`}>
                      {item.href ? <Link href={item.href}>{content}</Link> : content}
                    </li>
                  );
                })}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
