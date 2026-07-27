'use client';

import * as React from 'react';

import { cn } from '@/lib/utils';

interface SliderProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  /** Заливка дорожки. Для выбора тона сюда передаётся радуга. */
  trackImage?: string;
}

/**
 * Ползунок на основе стандартного элемента.
 *
 * Нативный range доступен с клавиатуры и на сенсорных экранах без
 * дополнительных зависимостей, поэтому отдельная библиотека здесь не нужна.
 */
const Slider = React.forwardRef<HTMLInputElement, SliderProps>(
  ({ className, trackImage, style, ...props }, ref) => (
    <input
      ref={ref}
      type="range"
      className={cn(
        'h-2 w-full cursor-pointer appearance-none rounded-full border border-border bg-muted focus-ring',
        // Бегунок
        '[&::-webkit-slider-thumb]:h-5 [&::-webkit-slider-thumb]:w-5',
        '[&::-webkit-slider-thumb]:appearance-none [&::-webkit-slider-thumb]:rounded-full',
        '[&::-webkit-slider-thumb]:border-2 [&::-webkit-slider-thumb]:border-white',
        '[&::-webkit-slider-thumb]:bg-primary [&::-webkit-slider-thumb]:shadow-raised',
        '[&::-webkit-slider-thumb]:transition-transform',
        '[&::-webkit-slider-thumb]:hover:scale-110',
        '[&::-moz-range-thumb]:h-5 [&::-moz-range-thumb]:w-5',
        '[&::-moz-range-thumb]:rounded-full [&::-moz-range-thumb]:border-2',
        '[&::-moz-range-thumb]:border-white [&::-moz-range-thumb]:bg-primary',
        className,
      )}
      style={trackImage ? { backgroundImage: trackImage, ...style } : style}
      {...props}
    />
  ),
);
Slider.displayName = 'Slider';

export { Slider };
