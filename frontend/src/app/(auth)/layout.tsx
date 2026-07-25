import { CalendarCheck2, LineChart, Sparkles, Users } from 'lucide-react';

import { AiMark } from '@/components/common/ai-mark';

const POINTS = [
  { icon: Users, text: 'Разбор конкурентов и понятный отчёт, что у них работает' },
  { icon: Sparkles, text: 'Темы с оценкой перспективности от 0 до 100' },
  { icon: LineChart, text: 'Статьи по шагам, без выдуманных фактов' },
  { icon: CalendarCheck2, text: 'Календарь публикаций с часовыми поясами' },
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col lg:grid lg:grid-cols-[1.05fr_1fr]">
      {/* Однотонная тёмно-синяя панель. Единственный градиент здесь —
          декоративный элемент в правом верхнем углу. */}
      <aside className="relative hidden flex-col justify-between overflow-hidden bg-sidebar p-12 lg:flex">
        <div
          className="gradient-hero-orb pointer-events-none absolute -right-24 -top-24 size-80 rounded-full opacity-60"
          aria-hidden
        />

        <div className="relative flex items-center gap-2.5">
          <AiMark size="sm" />
          <span className="text-[15px] font-semibold text-white">DzenPilot</span>
        </div>

        <div className="relative max-w-md space-y-8">
          <h1 className="text-3xl font-semibold leading-tight text-white">
            Ваш центр управления контентом Дзена
          </h1>

          <ul className="space-y-4">
            {POINTS.map((point) => {
              const Icon = point.icon;
              return (
                <li key={point.text} className="flex items-start gap-3">
                  <span className="mt-0.5 flex size-7 shrink-0 items-center justify-center rounded-md border border-sidebar-border bg-white/6">
                    <Icon className="size-3.5 text-white" aria-hidden />
                  </span>
                  <span className="text-sm leading-relaxed text-sidebar-foreground">
                    {point.text}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>

        <p className="relative max-w-sm text-2xs leading-relaxed text-sidebar-muted">
          Ключи хранятся на сервере в зашифрованном виде. Публикация всегда требует
          вашего подтверждения.
        </p>
      </aside>

      <main className="flex flex-1 items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-[400px]">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <AiMark size="sm" />
            <span className="text-[15px] font-semibold">DzenPilot</span>
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}
