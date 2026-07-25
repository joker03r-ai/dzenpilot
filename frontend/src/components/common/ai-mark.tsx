import { cn } from '@/lib/utils';

interface AiMarkProps {
  size?: 'sm' | 'md' | 'lg';
  /**
   * По умолчанию знак однотонный.
   *
   * Градиентный вариант включается точечно и только там, где на экране
   * нет других градиентов: правило — не больше двух на экран, а главная
   * кнопка действия уже занимает одно место.
   */
  tone?: 'solid' | 'gradient';
  className?: string;
}

export function AiMark({ size = 'md', tone = 'solid', className }: AiMarkProps) {
  const box = size === 'sm' ? 'size-7' : size === 'lg' ? 'size-10' : 'size-9';
  const glyph = size === 'sm' ? 'size-4' : size === 'lg' ? 'size-5' : 'size-[18px]';

  return (
    <span
      className={cn(
        'flex shrink-0 items-center justify-center rounded-md text-white',
        tone === 'gradient' ? 'gradient-ai-mark' : 'bg-primary',
        box,
        className,
      )}
      aria-hidden
    >
      <svg viewBox="0 0 24 24" fill="none" className={glyph}>
        <path
          d="M12 3.5 13.9 9.2 19.6 11.1 13.9 13 12 18.7 10.1 13 4.4 11.1 10.1 9.2 12 3.5Z"
          fill="currentColor"
          opacity="0.95"
        />
        <circle cx="18.4" cy="5.6" r="1.5" fill="currentColor" opacity="0.7" />
      </svg>
    </span>
  );
}
