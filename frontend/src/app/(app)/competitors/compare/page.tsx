'use client';

import { ArrowLeft, BarChart3 } from 'lucide-react';
import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useCompare } from '@/hooks/use-competitors';
import { NO_DATA, formatNumber } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';

const PERIODS = [
  { value: 30, label: 'За 30 дней' },
  { value: 90, label: 'За 90 дней' },
  { value: 180, label: 'За полгода' },
  { value: 365, label: 'За год' },
];

const BAR_COLORS = ['#4f5bd5', '#12a67a', '#e8a33d', '#d9534f', '#7b61ff'];

function CompareContent() {
  const searchParams = useSearchParams();
  const { projectId } = useProjectContext();
  const [period, setPeriod] = useState(90);

  const ids = (searchParams.get('ids') ?? '').split(',').filter(Boolean);
  const compare = useCompare(projectId);
  const { mutate } = compare;

  useEffect(() => {
    if (projectId && ids.length >= 2) {
      mutate({ competitor_ids: ids, period_days: period });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId, searchParams, period]);

  if (ids.length < 2) {
    return (
      <EmptyState
        icon={BarChart3}
        title="Выберите конкурентов"
        description="Отметьте галочками от 2 до 10 каналов в списке конкурентов и нажмите «Сравнить»."
        action={
          <Button asChild>
            <Link href="/competitors">К списку конкурентов</Link>
          </Button>
        }
      />
    );
  }

  const data = compare.data;

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/competitors">
          <ArrowLeft aria-hidden />
          К списку конкурентов
        </Link>
      </Button>

      <PageHeader
        title="Сравнение конкурентов"
        description="Кто активнее публикуется, у кого выше просмотры и вовлечённость, какие темы работают."
        action={
          <Select
            value={String(period)}
            onChange={(event) => setPeriod(Number(event.target.value))}
            className="w-48"
            aria-label="Период сравнения"
          >
            {PERIODS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </Select>
        }
      />

      {compare.isPending ? (
        <div className="space-y-4">
          <Skeleton className="h-72 w-full" />
          <Skeleton className="h-64 w-full" />
        </div>
      ) : !data ? (
        <EmptyState
          icon={BarChart3}
          title="Не удалось построить сравнение"
          description="Попробуйте выбрать другой период или вернитесь к списку конкурентов."
        />
      ) : (
        <>
          <Hint>{data.note}</Hint>

          <Card>
            <CardHeader>
              <CardTitle>Средние просмотры</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-72 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={data.chart} margin={{ top: 8, right: 8, left: 8, bottom: 8 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="hsl(220 14% 90%)" vertical={false} />
                    <XAxis
                      dataKey="name"
                      tick={{ fontSize: 12 }}
                      stroke="hsl(220 10% 45%)"
                      tickLine={false}
                    />
                    <YAxis tick={{ fontSize: 12 }} stroke="hsl(220 10% 45%)" tickLine={false} />
                    <Tooltip
                      formatter={(value) =>
                        typeof value === 'number' ? formatNumber(value) : NO_DATA
                      }
                      labelStyle={{ fontWeight: 600 }}
                      contentStyle={{ borderRadius: 12, border: '1px solid hsl(220 14% 90%)' }}
                    />
                    <Bar dataKey="avg_views" name="Средние просмотры" radius={[6, 6, 0, 0]}>
                      {data.chart.map((entry, index) => (
                        <Cell key={entry.name} fill={BAR_COLORS[index % BAR_COLORS.length]} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          <Card className="overflow-hidden">
            <CardHeader>
              <CardTitle>Таблица сравнения</CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              <div className="overflow-x-auto">
                <table className="w-full min-w-[1000px] text-sm">
                  <thead className="border-y border-border bg-secondary/50">
                    <tr className="text-left">
                      <th className="px-4 py-3 font-medium">Место</th>
                      <th className="px-4 py-3 font-medium">Канал</th>
                      <th className="px-4 py-3 text-right font-medium">Публикаций</th>
                      <th className="px-4 py-3 text-right font-medium">Раз в дней</th>
                      <th className="px-4 py-3 text-right font-medium">Ср. просмотры</th>
                      <th className="px-4 py-3 text-right font-medium">Вовлечённость</th>
                      <th className="px-4 py-3 text-right font-medium">Динамика</th>
                      <th className="px-4 py-3 font-medium">Лучшие темы</th>
                      <th className="px-4 py-3 font-medium">Стиль заголовков</th>
                    </tr>
                  </thead>

                  <tbody>
                    {data.rows.map((row, index) => (
                      <tr key={row.competitor_id} className="border-b border-border last:border-0">
                        <td className="px-4 py-3">
                          <Badge variant={index === 0 ? 'success' : 'outline'}>
                            {index + 1} · {row.rating}
                          </Badge>
                        </td>

                        <td className="px-4 py-3">
                          <Link
                            href={`/competitors/${row.competitor_id}`}
                            className="font-medium hover:text-primary"
                          >
                            {row.name}
                          </Link>
                          <span className="mt-0.5 block max-w-xs text-xs text-muted-foreground">
                            {row.rating_reason}
                          </span>
                        </td>

                        <td className="px-4 py-3 text-right tabular-nums">
                          {row.publications_in_period}
                        </td>

                        <td className="px-4 py-3 text-right tabular-nums">
                          {row.publish_interval_days === null
                            ? NO_DATA
                            : row.publish_interval_days.toFixed(1)}
                        </td>

                        <td className="px-4 py-3 text-right tabular-nums">
                          {row.avg_views === null ? (
                            <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                          ) : (
                            formatNumber(row.avg_views)
                          )}
                        </td>

                        <td className="px-4 py-3 text-right tabular-nums">
                          {row.avg_engagement_rate === null
                            ? NO_DATA
                            : `${row.avg_engagement_rate}%`}
                        </td>

                        <td className="px-4 py-3 text-right tabular-nums">
                          {row.dynamics_percent === null ? (
                            <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                          ) : (
                            <span
                              className={
                                row.dynamics_percent >= 0 ? 'text-success' : 'text-destructive'
                              }
                            >
                              {row.dynamics_percent > 0 ? '+' : ''}
                              {row.dynamics_percent}%
                            </span>
                          )}
                        </td>

                        <td className="px-4 py-3">
                          {row.best_topics.length === 0 ? (
                            <span className="text-xs text-muted-foreground">{NO_DATA}</span>
                          ) : (
                            <div className="flex flex-wrap gap-1">
                              {row.best_topics.map((topic) => (
                                <Badge key={topic} variant="secondary">
                                  {topic}
                                </Badge>
                              ))}
                            </div>
                          )}
                        </td>

                        <td className="max-w-xs px-4 py-3 text-xs text-muted-foreground">
                          {row.title_style}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}

export default function ComparePage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <CompareContent />
    </Suspense>
  );
}
