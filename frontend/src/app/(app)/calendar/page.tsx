'use client';

import { CalendarDays, ChevronLeft, ChevronRight, Plus, Sparkles } from 'lucide-react';
import { useState } from 'react';

import { ScheduleChip } from '@/components/calendar/schedule-chip';
import { ScheduleDialog } from '@/components/calendar/schedule-dialog';
import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useCalendar, useCalendarOptions, useUpdateSchedule } from '@/hooks/use-calendar';
import { useProject } from '@/hooks/use-projects';
import { formatDate } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';
import { cn } from '@/lib/utils';
import type { CalendarView, ScheduleItem } from '@/types/api';

const VIEWS: { value: CalendarView; label: string }[] = [
  { value: 'day', label: 'День' },
  { value: 'week', label: 'Неделя' },
  { value: 'month', label: 'Месяц' },
  { value: 'list', label: 'Список' },
];

const WEEKDAYS = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'];

function toIsoDate(value: Date): string {
  return value.toISOString().slice(0, 10);
}

function shiftAnchor(anchor: string, view: CalendarView, direction: number): string {
  const date = new Date(`${anchor}T12:00:00`);
  if (view === 'day') date.setDate(date.getDate() + direction);
  else if (view === 'week') date.setDate(date.getDate() + 7 * direction);
  else if (view === 'month') date.setMonth(date.getMonth() + direction);
  else date.setDate(date.getDate() + 30 * direction);
  return toIsoDate(date);
}

/** Дни для сетки месяца: с понедельника первой недели по воскресенье последней. */
function monthGrid(periodStart: string, periodEnd: string): string[] {
  const start = new Date(`${periodStart}T12:00:00`);
  const end = new Date(`${periodEnd}T12:00:00`);

  const gridStart = new Date(start);
  gridStart.setDate(gridStart.getDate() - ((start.getDay() + 6) % 7));

  const gridEnd = new Date(end);
  gridEnd.setDate(gridEnd.getDate() + (7 - ((end.getDay() + 6) % 7) - 1));

  const days: string[] = [];
  const cursor = new Date(gridStart);
  while (cursor <= gridEnd) {
    days.push(toIsoDate(cursor));
    cursor.setDate(cursor.getDate() + 1);
  }
  return days;
}

export default function CalendarPage() {
  const { projectId } = useProjectContext();
  const { data: project } = useProject(projectId);
  const { data: options } = useCalendarOptions(projectId);

  const [view, setView] = useState<CalendarView>('month');
  const [anchor, setAnchor] = useState(toIsoDate(new Date()));
  const [timezone, setTimezone] = useState('');

  const activeTimezone = timezone || project?.timezone || 'Europe/Moscow';
  const { data, isLoading } = useCalendar(projectId, view, anchor, activeTimezone);
  const updateSchedule = useUpdateSchedule(projectId);

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Календарь хранится отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  const items = data?.items ?? [];
  const byDate = new Map<string, ScheduleItem[]>();
  for (const item of items) {
    byDate.set(item.local_date, [...(byDate.get(item.local_date) ?? []), item]);
  }

  /** Перенос мышью: меняется только дата, время остаётся прежним. */
  const handleDrop = (event: React.DragEvent, targetDate: string) => {
    event.preventDefault();
    const id = event.dataTransfer.getData('text/plain');
    const item = items.find((candidate) => candidate.id === id);
    if (!item || item.local_date === targetDate) return;

    updateSchedule.mutate({
      id,
      local_datetime: `${targetDate}T${item.local_time}`,
      timezone: item.timezone,
    });
  };

  const today = toIsoDate(new Date());

  return (
    <div className="space-y-6">
      <PageHeader
        title="Контент-календарь"
        description="План публикаций по датам. Записи переносятся мышью — просто перетащите на другой день."
        action={
          <ScheduleDialog
            projectId={projectId}
            defaultDate={anchor}
            defaultTimezone={activeTimezone}
            trigger={
              <Button size="lg">
                <Plus aria-hidden />
                Запланировать публикацию
              </Button>
            }
          />
        }
      />

      <Hint>
        Всё время показано в поясе «{data?.timezone_label ?? 'Москва, UTC+3'}». Сервис
        никогда не публикует сам: у каждой записи должна стоять ваша отметка
        «Подтверждено», и только после этого публикация уходит в работу.
      </Hint>

      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
        <Tabs value={view} onValueChange={(value) => setView(value as CalendarView)}>
          <TabsList>
            {VIEWS.map((item) => (
              <TabsTrigger key={item.value} value={item.value}>
                {item.label}
              </TabsTrigger>
            ))}
          </TabsList>
        </Tabs>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            variant="outline"
            size="icon"
            onClick={() => setAnchor(shiftAnchor(anchor, view, -1))}
            aria-label="Предыдущий период"
          >
            <ChevronLeft />
          </Button>

          <Button variant="outline" size="sm" onClick={() => setAnchor(today)}>
            Сегодня
          </Button>

          <Button
            variant="outline"
            size="icon"
            onClick={() => setAnchor(shiftAnchor(anchor, view, 1))}
            aria-label="Следующий период"
          >
            <ChevronRight />
          </Button>

          <Select
            value={activeTimezone}
            onChange={(event) => setTimezone(event.target.value)}
            className="w-56"
            aria-label="Часовой пояс"
          >
            {options?.popular.map((item) => (
              <option key={item.label} value={item.value}>
                {item.label}
              </option>
            ))}
            <optgroup label="Все остальные">
              {options?.all.map((zone) => (
                <option key={zone} value={zone}>
                  {zone}
                </option>
              ))}
            </optgroup>
          </Select>
        </div>
      </div>

      {data ? (
        <div className="flex flex-wrap items-center gap-2 text-sm text-muted-foreground">
          <Badge variant="secondary">{data.timezone_label}</Badge>
          <span>
            {formatDate(data.period_start)} — {formatDate(data.period_end)}
          </span>
        </div>
      ) : null}

      {data?.note ? (
        <Alert variant="info">
          <AlertDescription>{data.note}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <Skeleton className="h-[520px] w-full" />
      ) : view === 'month' ? (
        <Card className="overflow-hidden">
          <div className="grid grid-cols-7 border-b border-border bg-secondary/50">
            {WEEKDAYS.map((day) => (
              <div key={day} className="px-2 py-2 text-center text-xs font-medium">
                {day}
              </div>
            ))}
          </div>

          <div className="grid grid-cols-7">
            {monthGrid(data!.period_start, data!.period_end).map((day) => {
              const inPeriod = day >= data!.period_start && day <= data!.period_end;
              const dayItems = byDate.get(day) ?? [];

              return (
                <div
                  key={day}
                  onDragOver={(event) => event.preventDefault()}
                  onDrop={(event) => handleDrop(event, day)}
                  className={cn(
                    'min-h-[110px] space-y-1 border-b border-r border-border p-1.5 transition-colors',
                    !inPeriod && 'bg-muted/40',
                    day === today && 'bg-accent/40',
                  )}
                >
                  <div className="flex items-center justify-between">
                    <span
                      className={cn(
                        'text-xs tabular-nums',
                        day === today ? 'font-semibold text-primary' : 'text-muted-foreground',
                      )}
                    >
                      {Number(day.slice(8, 10))}
                    </span>
                  </div>

                  {dayItems.map((item) => (
                    <ScheduleChip key={item.id} projectId={projectId} item={item} compact />
                  ))}
                </div>
              );
            })}
          </div>
        </Card>
      ) : view === 'week' ? (
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-7">
          {monthGrid(data!.period_start, data!.period_end)
            .filter((day) => day >= data!.period_start && day <= data!.period_end)
            .map((day) => (
              <Card
                key={day}
                onDragOver={(event) => event.preventDefault()}
                onDrop={(event) => handleDrop(event, day)}
                className={cn('min-h-[200px] p-2', day === today && 'ring-1 ring-primary')}
              >
                <p className="mb-2 text-xs font-medium text-muted-foreground">
                  {formatDate(day)}
                </p>
                <div className="space-y-2">
                  {(byDate.get(day) ?? []).map((item) => (
                    <ScheduleChip key={item.id} projectId={projectId} item={item} compact />
                  ))}
                </div>
              </Card>
            ))}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={CalendarDays}
          title="На этот период ничего не запланировано"
          description="Выберите статью, дату и время — сервис напомнит о публикации и подготовит материал к выгрузке."
          action={
            <ScheduleDialog
              projectId={projectId}
              defaultDate={anchor}
              defaultTimezone={activeTimezone}
              trigger={
                <Button>
                  <Plus aria-hidden />
                  Запланировать публикацию
                </Button>
              }
            />
          }
        />
      ) : (
        <Card>
          <CardContent className="space-y-3 p-4">
            {items.map((item) => (
              <div key={item.id} className="flex flex-col gap-2 sm:flex-row sm:items-start">
                <div className="w-40 shrink-0 text-sm">
                  <p className="font-medium">{formatDate(item.local_date)}</p>
                  <p className="text-xs text-muted-foreground">
                    {item.local_time} · {item.timezone_label}
                  </p>
                </div>
                <div className="flex-1">
                  <ScheduleChip projectId={projectId} item={item} />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
