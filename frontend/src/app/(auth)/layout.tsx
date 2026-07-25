import { Compass } from 'lucide-react';

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col lg:grid lg:grid-cols-2">
      {/* Левая колонка с описанием — только на широких экранах */}
      <aside className="hidden flex-col justify-between bg-primary p-12 text-primary-foreground lg:flex">
        <div className="flex items-center gap-3">
          <span className="flex size-10 items-center justify-center rounded-lg bg-primary-foreground/15">
            <Compass className="size-6" aria-hidden />
          </span>
          <span className="text-xl font-semibold">DzenPilot</span>
        </div>

        <div className="max-w-md space-y-6">
          <h1 className="text-3xl font-semibold leading-tight">
            Ваш центр управления контентом Дзена
          </h1>
          <ul className="space-y-3 text-primary-foreground/85">
            <li>Разбор конкурентов и понятный отчёт, что у них работает.</li>
            <li>Поиск тем с оценкой перспективности от 0 до 100.</li>
            <li>Создание статей с помощью Claude — по шагам, без выдуманных фактов.</li>
            <li>Календарь публикаций с часовыми поясами от Калининграда до Владивостока.</li>
          </ul>
        </div>

        <p className="text-sm text-primary-foreground/70">
          Ключи хранятся на сервере в зашифрованном виде. Публикация всегда требует
          вашего подтверждения.
        </p>
      </aside>

      <main className="flex flex-1 items-center justify-center px-4 py-10 sm:px-8">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-2.5 lg:hidden">
            <span className="flex size-9 items-center justify-center rounded-lg bg-primary text-primary-foreground">
              <Compass className="size-5" aria-hidden />
            </span>
            <span className="text-lg font-semibold">DzenPilot</span>
          </div>
          {children}
        </div>
      </main>
    </div>
  );
}
