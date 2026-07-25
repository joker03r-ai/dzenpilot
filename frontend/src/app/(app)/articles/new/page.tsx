import { PenSquare } from 'lucide-react';

import { StagePlaceholder } from '@/components/common/stage-placeholder';

export const metadata = { title: 'Новая статья' };

export default function NewArticlePage() {
  return (
    <StagePlaceholder
      title="Новая статья"
      description="Мастер проведёт по пяти шагам: от темы до проверки перед публикацией."
      icon={PenSquare}
      stage={5}
      features={[
        'Шаг 1 — тема, цель, аудитория, тон, объём, ключевые слова, факты',
        'Шаг 2 — десять вариантов заголовка, лид, план и тезисы',
        'Шаг 3 — генерация текста моделью Claude',
        'Шаг 4 — доработка: тон, примеры, повторы, читаемость',
        'Шаг 5 — чек-лист перед публикацией',
      ]}
    />
  );
}
