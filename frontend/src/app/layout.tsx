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

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ru" suppressHydrationWarning>
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
