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
      <div className="flex gap-2.5">
        <Info className="mt-0.5 size-4 shrink-0 opacity-70" aria-hidden />
        <div className="min-w-0">
          <AlertTitle className="text-[13px]">{title}</AlertTitle>
          <AlertDescription className="text-[13px] leading-relaxed opacity-90">
            {children}
          </AlertDescription>
        </div>
      </div>
    </Alert>
  );
}
