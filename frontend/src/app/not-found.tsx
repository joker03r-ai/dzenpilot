import { FileQuestion } from 'lucide-react';
import Link from 'next/link';

import { Button } from '@/components/ui/button';

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center px-4">
      <div className="max-w-md space-y-4 text-center">
        <span className="mx-auto flex size-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
          <FileQuestion className="size-6" aria-hidden />
        </span>
        <h1 className="text-2xl font-semibold">Страница не найдена</h1>
        <p className="text-sm text-muted-foreground">
          Возможно, ссылка устарела или раздел ещё не открыт. Вернитесь на главную —
          оттуда доступны все разделы сервиса.
        </p>
        <Button asChild>
          <Link href="/dashboard">На главную</Link>
        </Button>
      </div>
    </div>
  );
}
