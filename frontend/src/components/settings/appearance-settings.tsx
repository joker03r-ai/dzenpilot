'use client';

import { Check, Monitor, Moon, RotateCcw, Sun, TriangleAlert } from 'lucide-react';

import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { useAppearance } from '@/lib/appearance-context';
import {
  ACCENT_PRESETS,
  BACKGROUNDS,
  backgroundFor,
  contrastRatio,
  contrastVerdict,
  foregroundFor,
  type TextContrast,
  type ThemeMode,
} from '@/lib/theme';
import { cn } from '@/lib/utils';

const MODES: { value: ThemeMode; label: string; hint: string; icon: typeof Sun }[] = [
  { value: 'light', label: 'Светлая', hint: 'Основной вариант', icon: Sun },
  { value: 'dark', label: 'Тёмная', hint: 'Для работы вечером', icon: Moon },
  { value: 'system', label: 'Как в системе', hint: 'Меняется сама', icon: Monitor },
];

const TEXT_MODES: { value: TextContrast; label: string; hint: string }[] = [
  { value: 'auto', label: 'Автоматически', hint: 'Подбирается под фон' },
  { value: 'black', label: 'Чёрный', hint: 'Для светлого фона' },
  { value: 'white', label: 'Белый', hint: 'Для тёмного фона' },
];

/** Радуга на дорожке ползунка тона — видно, что именно выбираешь. */
const HUE_TRACK =
  'linear-gradient(90deg, hsl(0 80% 55%), hsl(60 80% 55%), hsl(120 80% 55%), hsl(180 80% 55%), hsl(240 80% 55%), hsl(300 80% 55%), hsl(360 80% 55%))';

export function AppearanceSettings() {
  const { settings, resolvedMode, update, reset, ready } = useAppearance();

  if (!ready) {
    return <div className="h-96 animate-pulse rounded-lg bg-muted" />;
  }

  const surfaces = backgroundFor(settings, resolvedMode);
  const foreground = foregroundFor(settings, resolvedMode);
  const ratio = contrastRatio(surfaces.card, foreground);
  const verdict = contrastVerdict(ratio);

  const accentColor = `hsl(${settings.accentHue} ${settings.accentSaturation}% ${
    resolvedMode === 'dark' ? 60 : 53
  }%)`;

  return (
    <div className="space-y-4">
      {/* Тема */}
      <Card>
        <CardHeader>
          <CardTitle>Тема</CardTitle>
          <CardDescription>
            Настройки сохраняются в этом браузере и применяются сразу, без перезагрузки.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-3">
            {MODES.map((mode) => {
              const Icon = mode.icon;
              const active = settings.mode === mode.value;
              return (
                <button
                  key={mode.value}
                  type="button"
                  onClick={() => update({ mode: mode.value })}
                  aria-pressed={active}
                  className={cn(
                    'flex items-start gap-3 rounded-md border p-3 text-left transition-colors focus-ring',
                    active
                      ? 'border-primary bg-accent'
                      : 'border-border bg-surface hover:border-border-strong',
                  )}
                >
                  <Icon
                    className={cn('mt-0.5 size-4 shrink-0', active ? 'text-primary' : 'text-muted-foreground')}
                    aria-hidden
                  />
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{mode.label}</span>
                    <span className="block text-2xs text-muted-foreground">{mode.hint}</span>
                  </span>
                  {active ? <Check className="ml-auto size-4 shrink-0 text-primary" aria-hidden /> : null}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Акцент */}
      <Card>
        <CardHeader>
          <CardTitle>Цвет кнопок и акцентов</CardTitle>
          <CardDescription>
            Задаёт цвет главных кнопок, ссылок, активного пункта меню и рамки фокуса.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {ACCENT_PRESETS.map((preset) => {
              const active =
                settings.accentHue === preset.hue && settings.accentSaturation === preset.saturation;
              return (
                <button
                  key={preset.name}
                  type="button"
                  title={preset.name}
                  aria-label={preset.name}
                  aria-pressed={active}
                  onClick={() =>
                    update({ accentHue: preset.hue, accentSaturation: preset.saturation })
                  }
                  className={cn(
                    'flex size-9 items-center justify-center rounded-md border transition-transform focus-ring',
                    active ? 'border-foreground scale-105' : 'border-border hover:scale-105',
                  )}
                  style={{
                    backgroundColor: `hsl(${preset.hue} ${preset.saturation}% ${
                      resolvedMode === 'dark' ? 60 : 53
                    }%)`,
                  }}
                >
                  {active ? <Check className="size-4 text-white" aria-hidden /> : null}
                </button>
              );
            })}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="accent-hue">Тон</Label>
              <span className="text-2xs tabular-nums text-muted-foreground">
                {Math.round(settings.accentHue)}°
              </span>
            </div>
            <Slider
              id="accent-hue"
              min={0}
              max={360}
              step={1}
              value={settings.accentHue}
              trackImage={HUE_TRACK}
              onChange={(event) => update({ accentHue: Number(event.target.value) })}
            />
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <Label htmlFor="accent-saturation">Насыщенность</Label>
              <span className="text-2xs tabular-nums text-muted-foreground">
                {Math.round(settings.accentSaturation)}%
              </span>
            </div>
            <Slider
              id="accent-saturation"
              min={10}
              max={95}
              step={1}
              value={settings.accentSaturation}
              trackImage={`linear-gradient(90deg, hsl(${settings.accentHue} 8% 60%), hsl(${settings.accentHue} 95% 53%))`}
              onChange={(event) => update({ accentSaturation: Number(event.target.value) })}
            />
            <p className="text-2xs text-muted-foreground">
              Ниже — строже и спокойнее, выше — ярче и заметнее.
            </p>
          </div>

          {/* Живой пример: сразу видно, как выглядят кнопки */}
          <div className="rounded-md border border-border bg-surface p-4">
            <p className="mb-3 text-2xs uppercase tracking-wide text-muted-foreground">
              Как это выглядит
            </p>
            <div className="flex flex-wrap items-center gap-2">
              <Button size="sm">Главная кнопка</Button>
              <Button size="sm" variant="solid">
                Однотонная
              </Button>
              <Button size="sm" variant="outline">
                Обычная
              </Button>
              <Badge>Метка</Badge>
              <span className="text-sm" style={{ color: accentColor }}>
                Ссылка
              </span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Фон */}
      <Card>
        <CardHeader>
          <CardTitle>Фон рабочей области</CardTitle>
          <CardDescription>Все варианты однотонные — рабочая область не отвлекает.</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2">
            {BACKGROUNDS.map((option) => {
              const active = settings.background === option.id;
              const preview = resolvedMode === 'dark' ? option.dark : option.light;
              return (
                <button
                  key={option.id}
                  type="button"
                  aria-pressed={active}
                  onClick={() => update({ background: option.id })}
                  className={cn(
                    'flex items-start gap-3 rounded-md border p-3 text-left transition-colors focus-ring',
                    active ? 'border-primary' : 'border-border hover:border-border-strong',
                  )}
                >
                  <span
                    className="mt-0.5 flex size-9 shrink-0 items-center justify-center rounded-md border border-border"
                    style={{ backgroundColor: `hsl(${preview.background})` }}
                  >
                    <span
                      className="size-4 rounded-sm border border-border"
                      style={{ backgroundColor: `hsl(${preview.card})` }}
                    />
                  </span>
                  <span className="min-w-0">
                    <span className="block text-sm font-medium">{option.name}</span>
                    <span className="block text-2xs leading-relaxed text-muted-foreground">
                      {option.description}
                    </span>
                  </span>
                  {active ? (
                    <Check className="ml-auto size-4 shrink-0 text-primary" aria-hidden />
                  ) : null}
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Цвет текста */}
      <Card>
        <CardHeader>
          <CardTitle>Цвет текста</CardTitle>
          <CardDescription>
            Рядом показан контраст с фоном карточек. Значение ниже 4,5 означает, что мелкий
            текст будет читаться с трудом.
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="grid gap-3 sm:grid-cols-3">
            {TEXT_MODES.map((option) => {
              const active = settings.textContrast === option.value;
              return (
                <button
                  key={option.value}
                  type="button"
                  aria-pressed={active}
                  onClick={() => update({ textContrast: option.value })}
                  className={cn(
                    'rounded-md border p-3 text-left transition-colors focus-ring',
                    active
                      ? 'border-primary bg-accent'
                      : 'border-border bg-surface hover:border-border-strong',
                  )}
                >
                  <span className="block text-sm font-medium">{option.label}</span>
                  <span className="block text-2xs text-muted-foreground">{option.hint}</span>
                </button>
              );
            })}
          </div>

          <div
            className={cn(
              'flex items-start gap-2.5 rounded-md border p-3',
              verdict.tone === 'good' && 'border-success/20 bg-success/8',
              verdict.tone === 'ok' && 'border-warning/25 bg-warning/8',
              verdict.tone === 'bad' && 'border-destructive/25 bg-destructive/8',
            )}
          >
            {verdict.tone === 'good' ? (
              <Check className="mt-0.5 size-4 shrink-0 text-success" aria-hidden />
            ) : (
              <TriangleAlert
                className={cn(
                  'mt-0.5 size-4 shrink-0',
                  verdict.tone === 'ok' ? 'text-warning' : 'text-destructive',
                )}
                aria-hidden
              />
            )}
            <div className="min-w-0 text-sm">
              <p className="font-medium">
                Контраст {ratio.toFixed(1)} к 1 — {verdict.label.toLowerCase()}
              </p>
              <p className="mt-0.5 text-2xs text-muted-foreground">
                Для обычного текста нужно не меньше 4,5. Для крупных заголовков достаточно 3.
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="flex justify-end">
        <Button variant="outline" onClick={reset}>
          <RotateCcw aria-hidden />
          Вернуть стандартный вид
        </Button>
      </div>
    </div>
  );
}
