import { cn } from '@/lib/utils';

interface ScoreBadgeProps {
  score: number;
  verdict?: string;
  size?: 'sm' | 'lg';
}

/** Кружок с оценкой темы. Цвет подсказывает качество без чтения текста. */
export function ScoreBadge({ score, verdict, size = 'sm' }: ScoreBadgeProps) {
  const tone =
    score >= 80
      ? 'bg-success/12 text-success ring-success/25'
      : score >= 65
        ? 'bg-primary/10 text-primary ring-primary/25'
        : score >= 50
          ? 'bg-warning/15 text-warning-foreground ring-warning/30'
          : 'bg-muted text-muted-foreground ring-border';

  return (
    <div className="flex items-center gap-2">
      <span
        className={cn(
          'flex shrink-0 items-center justify-center rounded-full font-semibold tabular-nums ring-1',
          tone,
          size === 'lg' ? 'size-16 text-xl' : 'size-11 text-sm',
        )}
        aria-label={`Оценка ${score} из 100`}
      >
        {score}
      </span>
      {verdict ? (
        <span className={size === 'lg' ? 'text-sm font-medium' : 'text-xs text-muted-foreground'}>
          {verdict}
        </span>
      ) : null}
    </div>
  );
}
