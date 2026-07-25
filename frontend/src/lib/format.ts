/** Форматирование чисел и дат для русского интерфейса. */

export const NO_DATA = 'Данные недоступны';
export const NEEDS_IMPORT = 'Требуется ручной импорт';

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return NO_DATA;
  return new Intl.NumberFormat('ru-RU').format(value);
}

export function formatCompact(value: number | null | undefined): string {
  if (value === null || value === undefined) return NO_DATA;
  return new Intl.NumberFormat('ru-RU', { notation: 'compact', maximumFractionDigits: 1 }).format(
    value,
  );
}

export function formatDate(value: string | Date | null | undefined, timeZone?: string): string {
  if (!value) return NO_DATA;
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return NO_DATA;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'long',
    year: 'numeric',
    timeZone,
  }).format(date);
}

export function formatDateTime(value: string | Date | null | undefined, timeZone?: string): string {
  if (!value) return NO_DATA;
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return NO_DATA;
  return new Intl.DateTimeFormat('ru-RU', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    timeZone,
  }).format(date);
}

export function formatRelative(value: string | Date | null | undefined): string {
  if (!value) return '';
  const date = typeof value === 'string' ? new Date(value) : value;
  if (Number.isNaN(date.getTime())) return '';

  const diffMs = date.getTime() - Date.now();
  const minutes = Math.round(diffMs / 60000);
  const formatter = new Intl.RelativeTimeFormat('ru-RU', { numeric: 'auto' });

  if (Math.abs(minutes) < 60) return formatter.format(minutes, 'minute');
  const hours = Math.round(minutes / 60);
  if (Math.abs(hours) < 24) return formatter.format(hours, 'hour');
  const days = Math.round(hours / 24);
  if (Math.abs(days) < 30) return formatter.format(days, 'day');
  return formatDate(date);
}

/** Склонение: 1 статья, 2 статьи, 5 статей */
export function plural(count: number, forms: [string, string, string]): string {
  const abs = Math.abs(count) % 100;
  const tail = abs % 10;
  if (abs > 10 && abs < 20) return forms[2];
  if (tail > 1 && tail < 5) return forms[1];
  if (tail === 1) return forms[0];
  return forms[2];
}
