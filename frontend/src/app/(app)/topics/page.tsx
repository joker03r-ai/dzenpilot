import { Lightbulb } from 'lucide-react';

import { StagePlaceholder } from '@/components/common/stage-placeholder';

export const metadata = { title: 'Поиск тем' };

export default function TopicsPage() {
  return (
    <StagePlaceholder
      title="Поиск тем"
      description="Перспективные темы с оценкой от 0 до 100 и объяснением, почему они работают."
      icon={Lightbulb}
      stage={4}
      features={[
        'Форма поиска: ниша, аудитория, регион, формат, период, цель',
        'Оценка темы из десяти составляющих с расшифровкой',
        'Карточка темы: заголовки, вопросы читателей, идеи серии, риски',
        'Кнопки «Создать статью», «Добавить в план», «Сохранить», «Скрыть»',
        'Источники, на которых основан вывод',
      ]}
    />
  );
}
