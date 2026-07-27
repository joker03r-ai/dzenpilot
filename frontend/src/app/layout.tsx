import type { Metadata, Viewport } from 'next';

import { Providers } from '@/components/providers';

import './globals.css';

export const metadata: Metadata = {
  title: {
    default: 'DzenPilot — центр управления контентом Дзена',
    template: '%s — DzenPilot',
  },
  description:
    'Анализ конкурентов, поиск прибыльных тем, создание статей с помощью ИИ и планирование публикаций для авторов Яндекс Дзена.',
  robots: { index: false, follow: false },
};

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  themeColor: '#ffffff',
};

/**
 * Настройки внешнего вида применяются до первой отрисовки.
 * Без этого страница на мгновение показалась бы в теме по умолчанию.
 */
const APPLY_THEME_EARLY = `
(function () {
  try {
    var raw = localStorage.getItem('dzenpilot:appearance');
    if (!raw) return;
    var s = JSON.parse(raw);
    var mode = s.mode === 'system'
      ? (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')
      : (s.mode || 'light');
    var root = document.documentElement;
    root.setAttribute('data-theme', mode);
    if (s.accentHue != null) {
      var l = mode === 'dark' ? 60 : 53;
      var sat = s.accentSaturation != null ? s.accentSaturation : 83;
      root.style.setProperty('--primary', s.accentHue + ' ' + sat + '% ' + l + '%');
      root.style.setProperty('--ring', s.accentHue + ' ' + sat + '% ' + l + '%');
    }
  } catch (e) {}
})();
`;

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: APPLY_THEME_EARLY }} />
      </head>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
