'use client';

import { AlertTriangle } from 'lucide-react';
import { useEffect } from 'react';

import { Button } from '@/components/ui/button';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error('Ошибка интерфейса:', error);
  }, [error]);

  return (
    <div className="flex min-h-[60vh] items-center justify-center px-4">
      <div className="max-w-md space-y-4 text-center">
        <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-destructive/10 text-destructive">
          <AlertTriangle className="size-6" aria-hidden />
        </span>
        <h1 className="text-2xl font-semibold">Что-то пошло не так</h1>
        <p className="text-sm text-muted-foreground">
          Страница не смогла загрузиться. Попробуйте обновить — если ошибка повторяется,
          проверьте, запущен ли сервер, на странице http://localhost:8000/health
        </p>
        <div className="flex justify-center gap-3">
          <Button onClick={reset}>Попробовать снова</Button>
          <Button variant="outline" onClick={() => window.location.reload()}>
            Обновить страницу
          </Button>
        </div>
      </div>
    </div>
  );
}
