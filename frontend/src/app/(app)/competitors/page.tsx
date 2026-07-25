import { Users } from 'lucide-react';

import { StagePlaceholder } from '@/components/common/stage-placeholder';

export const metadata = { title: 'Конкуренты' };

export default function CompetitorsPage() {
  return (
    <StagePlaceholder
      title="Конкуренты"
      description="Каналы вашей тематики: их публикации, показатели и разбор от ИИ."
      icon={Users}
      stage={3}
      features={[
        'Добавление конкурента по ссылке или названию',
        'Группы, заметки, редактирование и удаление',
        'Импорт публикаций из CSV и ручное добавление',
        'Разбор заголовков: длина, эмоциональность, числа, вопрос, призыв',
        'Отчёт Claude: что работает, слабые места, нераскрытые темы',
        'Сравнение от 2 до 10 конкурентов в таблице с графиками',
      ]}
    />
  );
}
