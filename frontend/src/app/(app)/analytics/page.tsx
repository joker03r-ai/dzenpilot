import { BarChart3 } from 'lucide-react';

import { StagePlaceholder } from '@/components/common/stage-placeholder';

export const metadata = { title: 'Аналитика' };

export default function AnalyticsPage() {
  return (
    <StagePlaceholder
      title="Аналитика"
      description="Просмотры, подписчики, лучшие материалы и сравнение с конкурентами."
      icon={BarChart3}
      stage={8}
      features={[
        'Период: 7, 30, 90 дней или произвольный',
        'Динамика просмотров и подписчиков на графиках',
        'Лучшие статьи, темы и заголовки',
        'Результат по дням недели и времени публикации',
        'Ручной ввод и импорт CSV, если автоматических данных нет',
        'Выгрузка отчёта в CSV',
      ]}
    />
  );
}
