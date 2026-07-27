'use client';

import { Bot, Save, ShieldCheck, Sparkles, User as UserIcon } from 'lucide-react';
import { useEffect, useState } from 'react';
import { toast } from 'sonner';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { AppearanceSettings } from '@/components/settings/appearance-settings';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import { useChangePassword, useMe, useUpdateProfile } from '@/hooks/use-auth';
import { useAiProviders, useAiSettings, useSaveAiSettings } from '@/hooks/use-integrations';
import { useProject, useTimezones, useUpdateProject } from '@/hooks/use-projects';
import { useProjectContext } from '@/lib/project-context';

export default function SettingsPage() {
  const { projectId } = useProjectContext();

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Настройки хранятся отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Настройки"
        description="Профиль, параметры проекта, модель ИИ и безопасность. Каждая вкладка сохраняется отдельно."
      />

      <Tabs defaultValue="project">
        <TabsList className="flex-wrap">
          <TabsTrigger value="project">Проект</TabsTrigger>
          <TabsTrigger value="appearance">Внешний вид</TabsTrigger>
          <TabsTrigger value="ai">Модель ИИ</TabsTrigger>
          <TabsTrigger value="profile">Профиль</TabsTrigger>
          <TabsTrigger value="security">Безопасность</TabsTrigger>
        </TabsList>

        <TabsContent value="project">
          <ProjectSettings projectId={projectId} />
        </TabsContent>
        <TabsContent value="appearance">
          <AppearanceSettings />
        </TabsContent>
        <TabsContent value="ai">
          <AiSettings projectId={projectId} />
        </TabsContent>
        <TabsContent value="profile">
          <ProfileSettings />
        </TabsContent>
        <TabsContent value="security">
          <SecuritySettings />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function ProjectSettings({ projectId }: { projectId: string }) {
  const { data: project, isLoading } = useProject(projectId);
  const { data: timezones } = useTimezones(projectId);
  const updateProject = useUpdateProject(projectId);

  const [form, setForm] = useState({
    name: '',
    niche: '',
    target_audience: '',
    tone_of_voice: '',
    region: '',
    timezone: 'Europe/Moscow',
    dzen_channel_url: '',
  });

  useEffect(() => {
    if (!project) return;
    setForm({
      name: project.name,
      niche: project.niche ?? '',
      target_audience: project.target_audience ?? '',
      tone_of_voice: project.tone_of_voice ?? '',
      region: project.region ?? '',
      timezone: project.timezone,
      dzen_channel_url: project.dzen_channel_url ?? '',
    });
  }, [project]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    updateProject.mutate({
      name: form.name.trim(),
      niche: form.niche.trim() || null,
      target_audience: form.target_audience.trim() || null,
      tone_of_voice: form.tone_of_voice.trim() || null,
      region: form.region.trim() || null,
      timezone: form.timezone,
      dzen_channel_url: form.dzen_channel_url.trim() || null,
    });
  };

  const options = timezones ?? [{ value: 'Europe/Moscow', label: 'Москва, UTC+3', offset: '+03:00' }];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Параметры проекта</CardTitle>
        <CardDescription>
          Эти данные ИИ использует при подборе тем и написании статей — чем точнее
          описание, тем ближе результат к вашему стилю.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="name">Название проекта</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(event) => setForm({ ...form, name: event.target.value })}
                maxLength={255}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="niche">Тематика</Label>
              <Input
                id="niche"
                value={form.niche}
                onChange={(event) => setForm({ ...form, niche: event.target.value })}
                placeholder="История, здоровье, финансы…"
                maxLength={255}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience">Кто ваши читатели</Label>
            <Textarea
              id="audience"
              value={form.target_audience}
              onChange={(event) => setForm({ ...form, target_audience: event.target.value })}
              placeholder="Взрослые 30–60 лет, интересуются историей быта, читают с телефона"
              maxLength={2000}
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="tone">Тон общения</Label>
              <Input
                id="tone"
                value={form.tone_of_voice}
                onChange={(event) => setForm({ ...form, tone_of_voice: event.target.value })}
                placeholder="Живой рассказ без канцелярита"
                maxLength={255}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="region">Регион</Label>
              <Input
                id="region"
                value={form.region}
                onChange={(event) => setForm({ ...form, region: event.target.value })}
                placeholder="Россия"
                maxLength={120}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="timezone">Часовой пояс публикаций</Label>
              <Select
                id="timezone"
                value={form.timezone}
                onChange={(event) => setForm({ ...form, timezone: event.target.value })}
              >
                {options.map((option) => (
                  <option key={option.label} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </Select>
              <p className="text-xs text-muted-foreground">
                Время в календаре показывается в этом поясе.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="channel">Ссылка на канал Дзена</Label>
              <Input
                id="channel"
                value={form.dzen_channel_url}
                onChange={(event) => setForm({ ...form, dzen_channel_url: event.target.value })}
                placeholder="https://dzen.ru/ваш_канал"
                maxLength={500}
              />
            </div>
          </div>

          <Button type="submit" loading={updateProject.isPending}>
            <Save aria-hidden />
            Сохранить настройки
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function AiSettings({ projectId }: { projectId: string }) {
  const { data: providers, isLoading: providersLoading } = useAiProviders();
  const { data: settings, isLoading: settingsLoading } = useAiSettings(projectId);
  const saveSettings = useSaveAiSettings(projectId);

  const [provider, setProvider] = useState('anthropic');
  const [model, setModel] = useState('claude-sonnet-5');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(4096);

  useEffect(() => {
    if (!settings) return;
    setProvider(settings.provider);
    setModel(settings.model);
    setTemperature(Number(settings.temperature));
    setMaxTokens(settings.max_tokens);
  }, [settings]);

  if (providersLoading || settingsLoading) return <Skeleton className="h-96 w-full" />;

  const currentProvider = providers?.find((item) => item.provider === provider);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    saveSettings.mutate({ provider, model, temperature, max_tokens: maxTokens });
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <CardTitle>Модель ИИ</CardTitle>
            <CardDescription>
              Модель можно менять в любой момент — код сервиса переписывать не нужно.
            </CardDescription>
          </div>
          <Badge variant={settings?.key_configured ? 'success' : 'warning'}>
            {settings?.key_configured ? 'Ключ подключён' : 'Ключ не задан'}
          </Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {!settings?.key_configured ? (
          <Hint title="Нужен ключ">
            Выбранная модель не заработает, пока не подключён ключ. Откройте раздел
            «Интеграции» и добавьте его — там же можно проверить соединение.
          </Hint>
        ) : null}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="provider">Провайдер</Label>
              <Select
                id="provider"
                value={provider}
                onChange={(event) => {
                  const next = event.target.value;
                  setProvider(next);
                  const first = providers?.find((item) => item.provider === next)?.models[0];
                  if (first) setModel(first.id);
                }}
              >
                {providers?.map((item) => (
                  <option key={item.provider} value={item.provider}>
                    {item.title}
                  </option>
                ))}
              </Select>
              {currentProvider ? (
                <p className="text-xs text-muted-foreground">{currentProvider.description}</p>
              ) : null}
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">Модель</Label>
              <Select
                id="model"
                value={model}
                onChange={(event) => setModel(event.target.value)}
              >
                {currentProvider?.models.map((item) => (
                  <option key={item.id} value={item.id}>
                    {item.title}
                    {item.recommended ? ' — рекомендуем' : ''}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="temperature">Творческость: {temperature.toFixed(1)}</Label>
              <Slider
                id="temperature"
                min={0}
                max={1}
                step={0.1}
                value={temperature}
                onChange={(event) => setTemperature(Number(event.target.value))}
              />
              <p className="text-xs text-muted-foreground">
                Ниже — строже и предсказуемее, выше — живее и разнообразнее.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="max-tokens">Максимальная длина ответа</Label>
              <Input
                id="max-tokens"
                type="number"
                min={256}
                max={64000}
                step={256}
                value={maxTokens}
                onChange={(event) => setMaxTokens(Number(event.target.value))}
              />
              <p className="text-xs text-muted-foreground">
                4096 хватает на статью примерно на 8–10 тысяч знаков.
              </p>
            </div>
          </div>

          <Button type="submit" loading={saveSettings.isPending}>
            <Bot aria-hidden />
            Сохранить модель
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function ProfileSettings() {
  const { data, isLoading } = useMe();
  const updateProfile = useUpdateProfile();
  const [fullName, setFullName] = useState('');

  useEffect(() => {
    if (data?.user) setFullName(data.user.full_name ?? '');
  }, [data]);

  if (isLoading) return <Skeleton className="h-64 w-full" />;

  return (
    <Card>
      <CardHeader>
        <CardTitle>Профиль</CardTitle>
        <CardDescription>Имя показывается на главной странице и в меню.</CardDescription>
      </CardHeader>

      <CardContent>
        <form
          onSubmit={(event) => {
            event.preventDefault();
            updateProfile.mutate({ full_name: fullName.trim() });
          }}
          className="space-y-4"
        >
          <div className="space-y-2">
            <Label htmlFor="full-name">Имя</Label>
            <Input
              id="full-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              maxLength={255}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="user-email">Электронная почта</Label>
            <Input id="user-email" value={data?.user.email ?? ''} disabled />
            <p className="text-xs text-muted-foreground">
              Почта используется для входа и пока не меняется.
            </p>
          </div>

          <Button type="submit" loading={updateProfile.isPending}>
            <UserIcon aria-hidden />
            Сохранить профиль
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}

function SecuritySettings() {
  const changePassword = useChangePassword();
  const [current, setCurrent] = useState('');
  const [next, setNext] = useState('');
  const [repeat, setRepeat] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (next.length < 8) {
      toast.error('Новый пароль должен быть не короче 8 символов');
      return;
    }
    if (next !== repeat) {
      toast.error('Пароли не совпадают');
      return;
    }

    changePassword.mutate(
      { current_password: current, new_password: next },
      {
        onSuccess: () => {
          setCurrent('');
          setNext('');
          setRepeat('');
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Смена пароля</CardTitle>
          <CardDescription>
            Пароль хранится только в виде необратимого хеша — восстановить его невозможно
            ни нам, ни кому-либо ещё.
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="max-w-md space-y-4">
            <div className="space-y-2">
              <Label htmlFor="current-password">Текущий пароль</Label>
              <Input
                id="current-password"
                type="password"
                value={current}
                onChange={(event) => setCurrent(event.target.value)}
                autoComplete="current-password"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="new-password">Новый пароль</Label>
              <Input
                id="new-password"
                type="password"
                value={next}
                onChange={(event) => setNext(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="repeat-password">Повторите новый пароль</Label>
              <Input
                id="repeat-password"
                type="password"
                value={repeat}
                onChange={(event) => setRepeat(event.target.value)}
                autoComplete="new-password"
                required
              />
            </div>

            <Button type="submit" loading={changePassword.isPending}>
              <ShieldCheck aria-hidden />
              Сменить пароль
            </Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Как защищены ваши данные</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="space-y-2 text-sm text-muted-foreground">
            <li>Токен сессии лежит в защищённой cookie и недоступен из JavaScript.</li>
            <li>Ключи интеграций шифруются на сервере и не передаются в браузер.</li>
            <li>Все важные действия записываются в журнал: вход, изменения, публикации.</li>
            <li>Запросы к базе параметризованы — внедрение SQL невозможно.</li>
            <li>Частота запросов ограничена, подбор пароля перебором не сработает.</li>
            <li>Публикация статьи всегда требует вашего подтверждения.</li>
          </ul>
        </CardContent>
      </Card>
    </div>
  );
}
