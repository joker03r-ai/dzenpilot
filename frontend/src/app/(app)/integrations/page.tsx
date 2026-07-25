'use client';

import {
  CheckCircle2,
  KeyRound,
  Plug,
  RefreshCw,
  ShieldCheck,
  Trash2,
  XCircle,
} from 'lucide-react';
import { useState } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import {
  useConnectIntegration,
  useDeleteIntegration,
  useIntegrations,
  useTestIntegration,
} from '@/hooks/use-integrations';
import { formatDateTime } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';
import type { IntegrationKind } from '@/types/api';

interface CatalogItem {
  kind: IntegrationKind;
  title: string;
  description: string;
  needsKey: boolean;
  keyPlaceholder?: string;
  helpUrl?: string;
}

const CATALOG: CatalogItem[] = [
  {
    kind: 'anthropic',
    title: 'Anthropic Claude',
    description: 'Основная модель: анализ конкурентов, подбор тем и написание статей.',
    needsKey: true,
    keyPlaceholder: 'sk-ant-…',
    helpUrl: 'https://console.anthropic.com/settings/keys',
  },
  {
    kind: 'openai',
    title: 'OpenAI',
    description: 'Запасная модель. Подключается по желанию.',
    needsKey: true,
    keyPlaceholder: 'sk-…',
  },
  {
    kind: 'gemini',
    title: 'Google Gemini',
    description: 'Ещё одна запасная модель.',
    needsKey: true,
    keyPlaceholder: 'AIza…',
  },
  {
    kind: 'dzen_channel',
    title: 'Канал Яндекс Дзена',
    description: 'Ссылка на ваш канал. Публикация выполняется официальным способом или экспортом.',
    needsKey: false,
  },
  {
    kind: 'yandex_metrika',
    title: 'Яндекс Метрика',
    description: 'Статистика переходов, если счётчик установлен.',
    needsKey: true,
    keyPlaceholder: 'OAuth-токен',
  },
  {
    kind: 'telegram',
    title: 'Telegram',
    description: 'Уведомления о готовых статьях и времени публикации.',
    needsKey: true,
    keyPlaceholder: 'Токен бота',
  },
  {
    kind: 'webhook',
    title: 'Webhook',
    description: 'Отправка событий в вашу систему.',
    needsKey: false,
  },
  {
    kind: 'storage',
    title: 'Хранилище изображений',
    description: 'Загрузка обложек и иллюстраций в облако.',
    needsKey: true,
    keyPlaceholder: 'Ключ доступа',
  },
];

export default function IntegrationsPage() {
  const { projectId } = useProjectContext();
  const { data: integrations, isLoading } = useIntegrations(projectId);
  const connect = useConnectIntegration(projectId);
  const test = useTestIntegration(projectId);
  const remove = useDeleteIntegration(projectId);

  const [selected, setSelected] = useState<CatalogItem | null>(null);
  const [apiKey, setApiKey] = useState('');
  const [configValue, setConfigValue] = useState('');

  const connected = integrations ?? [];
  const byKind = new Map(connected.map((item) => [item.kind, item]));

  const handleConnect = (event: React.FormEvent) => {
    event.preventDefault();
    if (!selected) return;

    const config: Record<string, unknown> = {};
    if (selected.kind === 'dzen_channel' && configValue) config.channel_url = configValue.trim();
    if (selected.kind === 'webhook' && configValue) config.url = configValue.trim();

    connect.mutate(
      {
        kind: selected.kind,
        title: 'Основное',
        api_key: apiKey.trim() || undefined,
        config,
      },
      {
        onSuccess: () => {
          setSelected(null);
          setApiKey('');
          setConfigValue('');
        },
      },
    );
  };

  if (!projectId) {
    return (
      <EmptyState
        icon={Plug}
        title="Сначала создайте проект"
        description="Подключения хранятся отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Интеграции"
        description="Подключите модель ИИ и канал — после этого станут доступны анализ конкурентов, подбор тем и генерация статей."
      />

      <Hint>
        Ключи вводятся один раз и сразу шифруются на сервере. Обратно они не отдаются —
        в интерфейсе вы видите только маску вида <code>sk-ant-…a1b2</code>. Если ключ
        потерялся, создайте новый в личном кабинете провайдера и подключите заново.
      </Hint>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {[0, 1, 2, 3].map((index) => (
            <Skeleton key={index} className="h-40" />
          ))}
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {CATALOG.map((item) => {
            const existing = byKind.get(item.kind);

            return (
              <Card key={item.kind} className="flex flex-col">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0 space-y-1">
                      <CardTitle className="text-base">{item.title}</CardTitle>
                      <CardDescription>{item.description}</CardDescription>
                    </div>
                    <Badge variant={existing ? 'success' : 'outline'} className="shrink-0">
                      {existing ? 'Подключено' : 'Не подключено'}
                    </Badge>
                  </div>
                </CardHeader>

                <CardContent className="mt-auto space-y-3">
                  {existing ? (
                    <>
                      <div className="flex items-center gap-2 rounded-md bg-secondary px-3 py-2 text-sm">
                        <KeyRound className="size-4 shrink-0 text-muted-foreground" aria-hidden />
                        <span className="truncate font-mono text-xs">{existing.key_mask}</span>
                      </div>

                      {existing.last_check_result ? (
                        <p className="flex items-start gap-2 text-xs text-muted-foreground">
                          {existing.last_check_result.includes('не') ? (
                            <XCircle className="mt-px size-3.5 shrink-0 text-destructive" aria-hidden />
                          ) : (
                            <CheckCircle2 className="mt-px size-3.5 shrink-0 text-success" aria-hidden />
                          )}
                          <span>
                            {existing.last_check_result}
                            {existing.last_check_at
                              ? ` · ${formatDateTime(existing.last_check_at)}`
                              : ''}
                          </span>
                        </p>
                      ) : null}

                      <div className="flex flex-wrap gap-2">
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => test.mutate(existing.id)}
                          loading={test.isPending && test.variables === existing.id}
                        >
                          <RefreshCw aria-hidden />
                          Проверить
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          className="text-destructive hover:bg-destructive/10"
                          onClick={() => remove.mutate(existing.id)}
                        >
                          <Trash2 aria-hidden />
                          Отключить
                        </Button>
                      </div>
                    </>
                  ) : (
                    <Button
                      className="w-full"
                      onClick={() => {
                        setSelected(item);
                        setApiKey('');
                        setConfigValue('');
                      }}
                    >
                      <Plug aria-hidden />
                      Подключить
                    </Button>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      <Dialog open={Boolean(selected)} onOpenChange={(open) => !open && setSelected(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Подключение: {selected?.title}</DialogTitle>
            <DialogDescription>{selected?.description}</DialogDescription>
          </DialogHeader>

          <form onSubmit={handleConnect} className="space-y-4">
            {selected?.needsKey ? (
              <div className="space-y-2">
                <Label htmlFor="api-key">Секретный ключ</Label>
                <Input
                  id="api-key"
                  type="password"
                  value={apiKey}
                  onChange={(event) => setApiKey(event.target.value)}
                  placeholder={selected.keyPlaceholder}
                  autoComplete="off"
                  required
                  autoFocus
                />
                {selected.helpUrl ? (
                  <p className="text-xs text-muted-foreground">
                    Где взять ключ:{' '}
                    <a
                      href={selected.helpUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-primary hover:underline"
                    >
                      личный кабинет Anthropic
                    </a>
                  </p>
                ) : null}
              </div>
            ) : null}

            {selected?.kind === 'dzen_channel' ? (
              <div className="space-y-2">
                <Label htmlFor="channel-url">Ссылка на канал</Label>
                <Input
                  id="channel-url"
                  value={configValue}
                  onChange={(event) => setConfigValue(event.target.value)}
                  placeholder="https://dzen.ru/ваш_канал"
                  required
                  autoFocus
                />
              </div>
            ) : null}

            {selected?.kind === 'webhook' ? (
              <div className="space-y-2">
                <Label htmlFor="webhook-url">Адрес webhook</Label>
                <Input
                  id="webhook-url"
                  value={configValue}
                  onChange={(event) => setConfigValue(event.target.value)}
                  placeholder="https://example.ru/hooks/dzenpilot"
                  required
                  autoFocus
                />
              </div>
            ) : null}

            <p className="flex items-start gap-2 rounded-md bg-accent p-3 text-xs text-accent-foreground">
              <ShieldCheck className="mt-px size-4 shrink-0" aria-hidden />
              <span>
                Значение шифруется на сервере и никогда не передаётся обратно в браузер.
                В журнал действий сам ключ не попадает.
              </span>
            </p>

            <DialogFooter>
              <Button type="button" variant="ghost" onClick={() => setSelected(null)}>
                Отмена
              </Button>
              <Button type="submit" loading={connect.isPending}>
                Сохранить и подключить
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}
