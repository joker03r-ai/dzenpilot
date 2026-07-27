/**
 * Настройки внешнего вида.
 *
 * Весь интерфейс построен на переменных CSS в формате HSL, поэтому смена
 * темы, акцента, фона и цвета текста сводится к подмене нескольких значений
 * на корневом элементе. Пересборка стилей не требуется.
 */

export type ThemeMode = 'light' | 'dark' | 'system';
export type TextContrast = 'auto' | 'black' | 'white';

export interface AppearanceSettings {
  mode: ThemeMode;
  /** Тон акцента, 0–360 по цветовому кругу */
  accentHue: number;
  /** Насыщенность акцента, 45–95 % */
  accentSaturation: number;
  /** Идентификатор фона из BACKGROUNDS */
  background: string;
  textContrast: TextContrast;
}

export const DEFAULT_APPEARANCE: AppearanceSettings = {
  mode: 'light',
  accentHue: 221,
  accentSaturation: 83,
  background: 'cool',
  textContrast: 'auto',
};

export const STORAGE_KEY = 'dzenpilot:appearance';

/** Готовые акценты — быстрый выбор без ползунка. */
export const ACCENT_PRESETS: { name: string; hue: number; saturation: number }[] = [
  { name: 'Синий', hue: 221, saturation: 83 },
  { name: 'Индиго', hue: 243, saturation: 72 },
  { name: 'Фиолетовый', hue: 262, saturation: 68 },
  { name: 'Голубой', hue: 197, saturation: 84 },
  { name: 'Бирюзовый', hue: 174, saturation: 62 },
  { name: 'Зелёный', hue: 152, saturation: 55 },
  { name: 'Графит', hue: 220, saturation: 12 },
];

interface BackgroundOption {
  id: string;
  name: string;
  description: string;
  light: { background: string; surface: string; card: string };
  dark: { background: string; surface: string; card: string };
}

/** Фоны рабочей области. Все однотонные — градиентов здесь нет. */
export const BACKGROUNDS: BackgroundOption[] = [
  {
    id: 'cool',
    name: 'Холодный серый',
    description: 'Основной вариант: спокойный, не утомляет при долгой работе',
    light: { background: '220 33% 97%', surface: '220 30% 98%', card: '0 0% 100%' },
    dark: { background: '222 40% 9%', surface: '222 36% 12%', card: '222 36% 12%' },
  },
  {
    id: 'white',
    name: 'Чистый белый',
    description: 'Максимум света, карточки отделяются только границей',
    light: { background: '0 0% 100%', surface: '220 25% 98%', card: '0 0% 100%' },
    dark: { background: '222 44% 7%', surface: '222 38% 10%', card: '222 38% 11%' },
  },
  {
    id: 'warm',
    name: 'Тёплый песочный',
    description: 'Мягче для глаз при жёлтом освещении',
    light: { background: '40 24% 97%', surface: '40 22% 98%', card: '0 0% 100%' },
    dark: { background: '30 14% 10%', surface: '30 12% 13%', card: '30 12% 13%' },
  },
  {
    id: 'blue',
    name: 'Глубокий синий',
    description: 'Заметнее фирменный оттенок, подходит для тёмной темы',
    light: { background: '215 40% 96%', surface: '215 36% 97%', card: '0 0% 100%' },
    dark: { background: '220 48% 8%', surface: '220 42% 11%', card: '220 42% 12%' },
  },
];

/** Разбирает строку вида "220 33% 97%" в компоненты HSL. */
function parseHsl(value: string): { h: number; s: number; l: number } {
  const [h, s, l] = value.split(' ');
  return {
    h: Number.parseFloat(h),
    s: Number.parseFloat(s),
    l: Number.parseFloat(l),
  };
}

/** Относительная яркость по формуле WCAG. */
function luminance(h: number, s: number, l: number): number {
  const sat = s / 100;
  const light = l / 100;
  const c = (1 - Math.abs(2 * light - 1)) * sat;
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
  const m = light - c / 2;

  let rgb: [number, number, number];
  if (h < 60) rgb = [c, x, 0];
  else if (h < 120) rgb = [x, c, 0];
  else if (h < 180) rgb = [0, c, x];
  else if (h < 240) rgb = [0, x, c];
  else if (h < 300) rgb = [x, 0, c];
  else rgb = [c, 0, x];

  const channels = rgb.map((value) => {
    const v = value + m;
    return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4;
  });

  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2];
}

/** Коэффициент контраста между двумя цветами HSL. */
export function contrastRatio(colorA: string, colorB: string): number {
  const a = parseHsl(colorA);
  const b = parseHsl(colorB);
  const la = luminance(a.h, a.s, a.l);
  const lb = luminance(b.h, b.s, b.l);
  const lighter = Math.max(la, lb);
  const darker = Math.min(la, lb);
  return (lighter + 0.05) / (darker + 0.05);
}

export function contrastVerdict(ratio: number): { label: string; tone: 'good' | 'ok' | 'bad' } {
  if (ratio >= 7) return { label: 'Отличный контраст', tone: 'good' };
  if (ratio >= 4.5) return { label: 'Достаточный контраст', tone: 'good' };
  if (ratio >= 3) return { label: 'Слабый контраст, мелкий текст читается плохо', tone: 'ok' };
  return { label: 'Текст почти нечитаем, выберите другое сочетание', tone: 'bad' };
}

export function resolveMode(mode: ThemeMode): 'light' | 'dark' {
  if (mode !== 'system') return mode;
  if (typeof window === 'undefined') return 'light';
  return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

/** Цвет текста для выбранного режима контраста. */
export function foregroundFor(settings: AppearanceSettings, resolved: 'light' | 'dark'): string {
  if (settings.textContrast === 'black') return '0 0% 6%';
  if (settings.textContrast === 'white') return '0 0% 100%';
  return resolved === 'dark' ? '213 30% 93%' : '222 44% 13%';
}

export function backgroundFor(settings: AppearanceSettings, resolved: 'light' | 'dark') {
  const option = BACKGROUNDS.find((item) => item.id === settings.background) ?? BACKGROUNDS[0];
  return resolved === 'dark' ? option.dark : option.light;
}

/**
 * Применяет настройки к корневому элементу.
 * Вызывается и при загрузке страницы, и при каждом изменении в настройках.
 */
export function applyAppearance(settings: AppearanceSettings): void {
  if (typeof document === 'undefined') return;

  const root = document.documentElement;
  const resolved = resolveMode(settings.mode);
  const surfaces = backgroundFor(settings, resolved);
  const foreground = foregroundFor(settings, resolved);

  root.setAttribute('data-theme', resolved);

  const hue = Math.round(settings.accentHue);
  const saturation = Math.round(settings.accentSaturation);
  const lightness = resolved === 'dark' ? 60 : 53;

  root.style.setProperty('--primary', `${hue} ${saturation}% ${lightness}%`);
  root.style.setProperty('--primary-hover', `${hue} ${saturation}% ${lightness - 6}%`);
  root.style.setProperty('--ring', `${hue} ${saturation}% ${lightness}%`);
  root.style.setProperty(
    '--accent',
    resolved === 'dark' ? `${hue} 40% 18%` : `${hue} 90% 97%`,
  );
  root.style.setProperty(
    '--accent-foreground',
    resolved === 'dark' ? `${hue} 90% 78%` : `${hue} 76% 42%`,
  );

  root.style.setProperty('--background', surfaces.background);
  root.style.setProperty('--surface', surfaces.surface);
  root.style.setProperty('--card', surfaces.card);
  root.style.setProperty('--popover', surfaces.card);

  root.style.setProperty('--foreground', foreground);
  root.style.setProperty('--card-foreground', foreground);
  root.style.setProperty('--popover-foreground', foreground);
}

export function readStoredAppearance(): AppearanceSettings {
  if (typeof window === 'undefined') return DEFAULT_APPEARANCE;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_APPEARANCE;
    const parsed = JSON.parse(raw) as Partial<AppearanceSettings>;
    return { ...DEFAULT_APPEARANCE, ...parsed };
  } catch {
    return DEFAULT_APPEARANCE;
  }
}
