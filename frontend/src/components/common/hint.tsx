import { Info } from 'lucide-react';
import type { ReactNode } from 'react';

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';

interface HintProps {
  title?: string;
  children: ReactNode;
}

/** Подсказка «Что здесь можно сделать» — показывается на сложных экранах. */
export function Hint({ title = 'Что здесь можно сделать', children }: HintProps) {
  return (
    <Alert variant="info">
      <div className="flex gap-3">
        <Info className="mt-0.5 size-4 shrink-0" aria-hidden />
        <div>
          <AlertTitle>{title}</AlertTitle>
          <AlertDescription>{children}</AlertDescription>
        </div>
      </div>
    </Alert>
  );
}
