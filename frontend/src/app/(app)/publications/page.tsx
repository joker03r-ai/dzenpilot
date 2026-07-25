'use client';

import {
  AlertTriangle,
  ArrowLeft,
  CheckCircle2,
  Copy,
  Download,
  MinusCircle,
  Send,
  Sparkles,
} from 'lucide-react';
import Link from 'next/link';
import { useState } from 'react';
import { toast } from 'sonner';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { useCalendar } from '@/hooks/use-calendar';
import { useProject } from '@/hooks/use-projects';
import {
  useConfirmPublication,
  usePreflight,
  usePublicationLogs,
  usePublish,
} from '@/hooks/use-publications';
import { formatDateTime } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';
import type { PublicationMethod, PublishResponse } from '@/types/api';

const METHODS: { value: PublicationMethod; label: string; hint: string }[] = [
  {
    value: 'manual_export',
    label: 'Ручной экспорт',
    hint: 'Готовит файлы Markdown и HTML для вставки в редактор Дзена',
  },
  {
    value: 'copy_formatted',
    label: 'Копирование текста',
    hint: 'Отформатированный текст, который можно вставить сразу',
  },
  {
    value: 'reminder',
    label: 'Напоминание',
    hint: 'Сервис напомнит, когда придёт время публиковать вручную',
  },
  {
    value: 'official_api',
    label: 'Официальное API',
    hint: 'Доступно, если вы подключили официальный доступ к каналу',
  },
];

const RESULT_ICONS = {
  success: CheckCircle2,
  error: AlertTriangle,
  skipped: MinusCircle,
};

export default function PublicationsPage() {
  const { projectId } = useProjectContext();
  const { data: project } = useProject(projectId);
  const timezone = project?.timezone ?? 'Europe/Moscow';

  const today = new Date().toISOString().slice(0, 10);
  const { data: calendar } = useCalendar(projectId, 'list', today, timezone);
  const { data: logs, isLoading } = usePublicationLogs(projectId);

  const preflight = usePreflight(projectId);
  const confirmPublication = useConfirmPublication(projectId);
  const publish = usePublish(projectId);

  const [selected, setSelected] = useState<string | null>(null);
  const [method, setMethod] = useState<PublicationMethod>('manual_export');
  const [output, setOutput] = useState<PublishResponse | null>(null);

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Журнал публикаций ведётся отдельно для каждого проекта."
      />
    );
  }

  const pending = (calendar?.items ?? []).filter(
    (item) => item.status === 'planned' || item.status === 'ready' || item.status === 'failed',
  );

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast.success('Текст скопирован в буфер обмена');
    } catch {
      toast.error('Браузер не разрешил доступ к буферу обмена. Скопируйте текст вручную.');
    }
  };

  const downloadFile = (content: string, filename: string) => {
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/calendar">
          <ArrowLeft aria-hidden />
          К календарю
        </Link>
      </Button>

      <PageHeader
        title="Публикация и журнал"
        description="Проверьте статью, подтвердите публикацию и выберите способ. Журнал хранит все попытки."
      />

      <Hint>
        Сервис не публикует материалы автоматически и не использует обходные способы
        доступа к платформе. Доступны только законные пути: экспорт файла, копирование
        готового текста, напоминание и официальное API, если вы его подключили.
      </Hint>

      <Card>
        <CardHeader>
          <CardTitle>Готовые к публикации</CardTitle>
          <CardDescription>
            Записи календаря, которые ждут действия. Время указано в поясе «
            {calendar?.timezone_label ?? 'Москва, UTC+3'}».
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-3">
          {pending.length === 0 ? (
            <p className="py-6 text-center text-sm text-muted-foreground">
              Ничего не запланировано. Добавьте статью в календарь.
            </p>
          ) : (
            pending.map((item) => (
              <div
                key={item.id}
                className="rounded-md border border-border p-3 transition-colors hover:bg-secondary/40"
              >
                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                  <div className="min-w-0">
                    <p className="truncate font-medium">{item.article_title}</p>
                    <p className="text-xs text-muted-foreground">
                      {item.local_date} в {item.local_time} · {item.timezone_label} ·{' '}
                      {item.status_label}
                    </p>
                  </div>

                  <div className="flex shrink-0 flex-wrap gap-2">
                    {!item.confirmed_by_user ? (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => confirmPublication.mutate(item.id)}
                        loading={confirmPublication.isPending}
                      >
                        Подтвердить
                      </Button>
                    ) : (
                      <Badge variant="success">Подтверждено</Badge>
                    )}

                    <Button
                      size="sm"
                      variant="secondary"
                      onClick={() => {
                        setSelected(item.id);
                        setOutput(null);
                        preflight.mutate(item.id);
                      }}
                    >
                      Проверить
                    </Button>
                  </div>
                </div>

                {selected === item.id && preflight.data ? (
                  <div className="mt-3 space-y-3 border-t border-border pt-3">
                    <ul className="space-y-1.5">
                      {preflight.data.checks.map((check) => (
                        <li key={check.code} className="flex gap-2 text-sm">
                          {check.passed ? (
                            <CheckCircle2
                              className="mt-0.5 size-4 shrink-0 text-success"
                              aria-hidden
                            />
                          ) : (
                            <AlertTriangle
                              className="mt-0.5 size-4 shrink-0 text-warning-foreground"
                              aria-hidden
                            />
                          )}
                          <span>
                            <span className="font-medium">{check.label}.</span>{' '}
                            <span className="text-muted-foreground">{check.detail}</span>
                          </span>
                        </li>
                      ))}
                    </ul>

                    <div className="flex flex-wrap items-end gap-2">
                      <div className="min-w-[220px] flex-1">
                        <label className="mb-1 block text-xs text-muted-foreground">
                          Способ публикации
                        </label>
                        <Select
                          value={method}
                          onChange={(event) =>
                            setMethod(event.target.value as PublicationMethod)
                          }
                        >
                          {METHODS.map((option) => (
                            <option key={option.value} value={option.value}>
                              {option.label}
                            </option>
                          ))}
                        </Select>
                        <p className="mt-1 text-xs text-muted-foreground">
                          {METHODS.find((option) => option.value === method)?.hint}
                        </p>
                      </div>

                      <Button
                        disabled={!preflight.data.ready}
                        loading={publish.isPending}
                        onClick={() =>
                          publish.mutate(
                            { scheduleId: item.id, method },
                            { onSuccess: (data) => setOutput(data) },
                          )
                        }
                        title={
                          preflight.data.ready ? undefined : 'Сначала выполните все проверки'
                        }
                      >
                        <Send aria-hidden />
                        Опубликовать
                      </Button>
                    </div>
                  </div>
                ) : null}
              </div>
            ))
          )}
        </CardContent>
      </Card>

      {output ? (
        <Card>
          <CardHeader>
            <CardTitle>{output.method_label}</CardTitle>
            <CardDescription>{output.next_step || output.message}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {output.payload.markdown ? (
              <div className="flex flex-wrap gap-2">
                <Button
                  variant="outline"
                  onClick={() =>
                    downloadFile(
                      output.payload.markdown,
                      output.payload.filename_markdown || 'article.md',
                    )
                  }
                >
                  <Download aria-hidden />
                  Скачать Markdown
                </Button>
                <Button
                  variant="outline"
                  onClick={() =>
                    downloadFile(
                      output.payload.html,
                      output.payload.filename_html || 'article.html',
                    )
                  }
                >
                  <Download aria-hidden />
                  Скачать HTML
                </Button>
              </div>
            ) : null}

            {output.payload.plain ? (
              <>
                <Button variant="outline" onClick={() => copyToClipboard(output.payload.plain)}>
                  <Copy aria-hidden />
                  Скопировать текст
                </Button>
                <pre className="max-h-72 overflow-auto whitespace-pre-wrap rounded-md bg-secondary p-4 text-sm">
                  {output.payload.plain}
                </pre>
              </>
            ) : null}

            {output.error_message ? (
              <p className="rounded-md bg-warning/10 p-3 text-sm text-warning-foreground">
                {output.error_message}
              </p>
            ) : null}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Журнал публикаций</CardTitle>
          <CardDescription>Все попытки с результатом и ответом сервиса.</CardDescription>
        </CardHeader>

        <CardContent className="p-0">
          {isLoading ? (
            <div className="space-y-2 p-4">
              {[0, 1, 2].map((index) => (
                <Skeleton key={index} className="h-16" />
              ))}
            </div>
          ) : !logs || logs.length === 0 ? (
            <p className="py-10 text-center text-sm text-muted-foreground">
              Записей пока нет. Здесь появятся все попытки публикации.
            </p>
          ) : (
            <ul className="divide-y divide-border">
              {logs.map((log) => {
                const Icon = RESULT_ICONS[log.result];
                return (
                  <li key={log.id} className="flex gap-3 p-4">
                    <Icon
                      className={
                        log.result === 'success'
                          ? 'mt-0.5 size-4 shrink-0 text-success'
                          : log.result === 'error'
                            ? 'mt-0.5 size-4 shrink-0 text-destructive'
                            : 'mt-0.5 size-4 shrink-0 text-muted-foreground'
                      }
                      aria-hidden
                    />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium">{log.article_title}</p>
                      <p className="text-xs text-muted-foreground">
                        {log.method_label} · {log.result_label} · попытка {log.attempt_number} ·{' '}
                        {formatDateTime(log.finished_at ?? log.created_at)}
                      </p>
                      {log.error_message ? (
                        <p className="mt-1 text-xs text-destructive">{log.error_message}</p>
                      ) : null}
                      {log.published_url ? (
                        <a
                          href={log.published_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="mt-1 inline-block text-xs text-primary hover:underline"
                        >
                          Открыть публикацию
                        </a>
                      ) : null}
                    </div>
                  </li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
