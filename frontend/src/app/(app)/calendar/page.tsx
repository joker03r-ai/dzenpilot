import { CalendarDays } from 'lucide-react';

import { StagePlaceholder } from '@/components/common/stage-placeholder';

export const metadata = { title: 'Контент-календарь' };

export default function CalendarPage() {
  return (
    <StagePlaceholder
      title="Контент-календарь"
      description="План публикаций по датам, времени и часовым поясам."
      icon={CalendarDays}
      stage={6}
      features={[
        'Виды: день, неделя, месяц, список',
        'Перетаскивание статей мышью и перенос даты',
        'Копирование, перенос, отмена и повторение публикаций',
        'Часовой пояс по умолчанию — Москва, UTC+3',
        'Калининград, Екатеринбург, Новосибирск, Иркутск, Владивосток, Берлин и любой другой',
        'Выбранный пояс всегда виден рядом с датой',
      ]}
    />
  );
}
