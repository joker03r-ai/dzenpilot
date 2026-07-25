import type { LucideIcon } from 'lucide-react';
import type { ReactNode } from 'react';

import { Card } from '@/components/ui/card';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  description: string;
  action?: ReactNode;
  secondary?: ReactNode;
}

export function EmptyState({ icon: Icon, title, description, action, secondary }: EmptyStateProps) {
  return (
    <Card className="flex flex-col items-center gap-4 px-6 py-14 text-center">
      <span className="flex size-14 items-center justify-center rounded-full bg-accent text-accent-foreground">
        <Icon className="size-6" aria-hidden />
      </span>
      <div className="max-w-md space-y-1.5">
        <h3 className="text-lg font-semibold">{title}</h3>
        <p className="text-sm text-muted-foreground">{description}</p>
      </div>
      {action ? <div className="flex flex-wrap items-center justify-center gap-3">{action}</div> : null}
      {secondary ? <div className="text-xs text-muted-foreground">{secondary}</div> : null}
    </Card>
  );
}
