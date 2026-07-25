'use client';

import { BarChart3, Download, FileUp, Sparkles } from 'lucide-react';
import { useRef, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { StatCard } from '@/components/common/stat-card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  downloadAnalyticsCsv,
  useComparison,
  useHourStats,
  useImportAnalyticsCsv,
  useOverview,
  useTimeseries,
  useTopContent,
  useWeekdayStats,
} from '@/hooks/use-analytics';
import { NO_DATA, formatDate, formatNumber } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';
import type { AnalyticsPeriod, MetricValue } from '@/types/api';

const PERIODS: { value: AnalyticsPeriod; label: string }[] = [
  { value: '7d', label: '7 дней' },
  { value: '30d', label: '30 дней' },
  { value: '90d', label: '90 дней' },
  { value: 'custom', label: 'Произвольный' },
];

const GRID = 'hsl(220 14% 90%)';
const AXIS = 'hsl(220 10% 45%)';
const TOOLTIP_STYLE = { borderRadius: 12, border: `1px solid ${GRID}` };

function metricText(metric: MetricValue | undefined, suffix = ''): string {
  if (!metric || !metric.available || metric.value === null) return NO_DATA;
  return `${formatNumber(Number(metric.value))}${suffix}`;
}

function metricHint(metric: MetricValue | undefined): string {
  if (!metric?.available) return 'Введите данные вручную или импортируйте CSV';
  if (metric.change_percent === null) return 'Не с чем сравнить';
  const sign = metric.change_percent > 0 ? '+' : '';
  return `${sign}${metric.change_percent}% к прошлому периоду`;
}

export default function AnalyticsPage() {
  const { projectId } = useProjectContext();
  const fileInput = useRef<HTMLInputElement>(null);

  const [period, setPeriod] = useState<AnalyticsPeriod>('30d');
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');

  const { data: overview, isLoading } = useOverview(projectId, period, start, end);
  const { data: series } = useTimeseries(projectId, period, start, end);
  const { data: weekdays } = useWeekdayStats(projectId, period, start, end);
  const { data: hours } = useHourStats(projectId, period, start, end);
  const { data: top } = useTopContent(projectId, period, start, end);
  const { data: comparison } = useComparison(projectId, period, start, end);
  const importCsv = useImportAnalyticsCsv(projectId);

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Аналитика ведётся отдельно для каждого проекта."
      />
    );
  }

  // Для графика по часам показываем только те часы, когда что-то публиковалось
  const activeHours = (hours ?? []).filter((item) => item.published > 0);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Аналитика"
        description="Показатели проекта, динамика и сравнение с конкурентами."
        action={
          <div className="flex flex-wrap gap-2">
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

            <Button onClick={() => downloadAnalyticsCsv(projectId, period, start, end)}>
              <Download aria-hidden />
              Выгрузить CSV
            </Button>
          </div>
        }
      />

      <Hint>
        Дзен не отдаёт статистику сторонним сервисам без официального доступа, поэтому
        сервис её не собирает автоматически. Выгрузите данные из личного кабинета и
        загрузите файлом — нужна одна обязательная колонка «Дата».
      </Hint>

      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="mb-1 block text-xs text-muted-foreground">Период</label>
          <Select
            value={period}
            onChange={(event) => setPeriod(event.target.value as AnalyticsPeriod)}
            className="w-48"
          >
            {PERIODS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        </div>

        {period === 'custom' ? (
          <>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">С</label>
              <Input
                type="date"
                value={start}
                onChange={(event) => setStart(event.target.value)}
                className="w-44"
              />
            </div>
            <div>
              <label className="mb-1 block text-xs text-muted-foreground">По</label>
              <Input
                type="date"
                value={end}
                onChange={(event) => setEnd(event.target.value)}
                className="w-44"
              />
            </div>
          </>
        ) : null}

        {overview ? (
          <Badge variant="secondary">
            {formatDate(overview.period_start)} — {formatDate(overview.period_end)}
          </Badge>
        ) : null}
      </div>

      {overview?.data_source_note ? (
        <Alert variant="info">
          <AlertDescription>{overview.data_source_note}</AlertDescription>
        </Alert>
      ) : null}

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {[0, 1, 2, 3, 4, 5].map((index) => (
            <Skeleton key={index} className="h-32" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <StatCard
            label="Опубликовано статей"
            value={metricText(overview?.published_articles)}
            hint={metricHint(overview?.published_articles)}
            icon={BarChart3}
          />
          <StatCard
            label="Всего просмотров"
            value={metricText(overview?.total_views)}
            hint={metricHint(overview?.total_views)}
            icon={BarChart3}
          />
          <StatCard
            label="Средние просмотры"
            value={metricText(overview?.avg_views)}
            hint={metricHint(overview?.avg_views)}
            icon={BarChart3}
          />
          <StatCard
            label="Подписчики"
            value={metricText(overview?.subscribers)}
            hint={metricHint(overview?.subscribers)}
            icon={BarChart3}
          />
          <StatCard
            label="Вовлечённость"
            value={
              overview?.avg_engagement.available
                ? `${overview.avg_engagement.value}%`
                : NO_DATA
            }
            hint={metricHint(overview?.avg_engagement)}
            icon={BarChart3}
          />
          <StatCard
            label="Статей в неделю"
            value={metricText(overview?.publish_frequency)}
            hint="Частота публикаций за период"
            icon={BarChart3}
          />
        </div>
      )}

      <Card>
        <CardHeader>
          <CardTitle>Динамика</CardTitle>
          <CardDescription>{series?.note}</CardDescription>
        </CardHeader>
        <CardContent>
          {!series?.has_data ? (
            <p className="py-12 text-center text-sm text-muted-foreground">
              Данных для графика пока нет. Загрузите статистику файлом CSV.
            </p>
          ) : (
            <div className="h-72 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={series.points}>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                  <XAxis dataKey="day" tick={{ fontSize: 11 }} stroke={AXIS} tickLine={false} />
                  <YAxis tick={{ fontSize: 11 }} stroke={AXIS} tickLine={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Line
                    type="monotone"
                    dataKey="views"
                    name="Просмотры"
                    stroke="#4f5bd5"
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />
                  <Line
                    type="monotone"
                    dataKey="subscribers"
                    name="Подписчики"
                    stroke="#12a67a"
                    strokeWidth={2}
                    dot={false}
                    connectNulls
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          )}
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle>Результат по дням недели</CardTitle>
            <CardDescription>Когда публикации набирают больше просмотров.</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-64 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekdays ?? []}>
                  <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 10 }}
                    stroke={AXIS}
                    tickLine={false}
                    tickFormatter={(value: string) => value.slice(0, 2)}
                  />
                  <YAxis tick={{ fontSize: 11 }} stroke={AXIS} tickLine={false} />
                  <Tooltip contentStyle={TOOLTIP_STYLE} />
                  <Bar dataKey="avg_views" name="Средние просмотры" radius={[6, 6, 0, 0]}>
                    {(weekdays ?? []).map((item) => (
                      <Cell key={item.weekday} fill={item.published ? '#4f5bd5' : '#d6dae5'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Результат по времени публикации</CardTitle>
            <CardDescription>
              {activeHours.length === 0
                ? 'Показывается только время, когда были публикации.'
                : `Активных часов: ${activeHours.length}.`}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {activeHours.length === 0 ? (
              <p className="py-16 text-center text-sm text-muted-foreground">
                Публикаций за период не было.
              </p>
            ) : (
              <div className="h-64 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={activeHours}>
                    <CartesianGrid strokeDasharray="3 3" stroke={GRID} vertical={false} />
                    <XAxis dataKey="label" tick={{ fontSize: 10 }} stroke={AXIS} tickLine={false} />
                    <YAxis tick={{ fontSize: 11 }} stroke={AXIS} tickLine={false} />
                    <Tooltip contentStyle={TOOLTIP_STYLE} />
                    <Bar
                      dataKey="avg_views"
                      name="Средние просмотры"
                      fill="#12a67a"
                      radius={[6, 6, 0, 0]}
                    />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Сравнение с конкурентами</CardTitle>
          <CardDescription>{comparison?.note}</CardDescription>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <table className="w-full min-w-[520px] text-sm">
              <thead className="border-y border-border bg-secondary/50">
                <tr className="text-left">
                  <th className="px-4 py-3 font-medium">Канал</th>
                  <th className="px-4 py-3 text-right font-medium">Публикаций</th>
                  <th className="px-4 py-3 text-right font-medium">Средние просмотры</th>
                </tr>
              </thead>
              <tbody>
                {(comparison?.rows ?? []).map((row) => (
                  <tr
                    key={row.name}
                    className={row.is_you ? 'bg-accent/50 font-medium' : undefined}
                  >
                    <td className="px-4 py-3">{row.name}</td>
                    <td className="px-4 py-3 text-right tabular-nums">{row.publications}</td>
                    <td className="px-4 py-3 text-right tabular-nums">
                      {row.avg_views === null ? (
                        <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                      ) : (
                        formatNumber(row.avg_views)
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Лучшие статьи</CardTitle>
            <CardDescription>{top?.note}</CardDescription>
          </CardHeader>
          <CardContent>
            {!top?.articles.length ? (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Опубликованных статей за период нет.
              </p>
            ) : (
              <ol className="space-y-2">
                {top.articles.map((item, index) => (
                  <li key={item.article_id} className="flex items-start gap-3 text-sm">
                    <span className="w-5 shrink-0 text-muted-foreground tabular-nums">
                      {index + 1}.
                    </span>
                    <span className="min-w-0 flex-1 truncate">{item.title}</span>
                    <span className="shrink-0 tabular-nums">
                      {item.views === null ? (
                        <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                      ) : (
                        formatNumber(item.views)
                      )}
                    </span>
                  </li>
                ))}
              </ol>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Частые слова в заголовках</CardTitle>
          </CardHeader>
          <CardContent>
            {!top?.title_words.length ? (
              <p className="text-sm text-muted-foreground">Появятся после публикаций.</p>
            ) : (
              <div className="flex flex-wrap gap-2">
                {top.title_words.map((item) => (
                  <Badge key={item.word} variant="secondary">
                    {item.word} · {item.count}
                  </Badge>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
