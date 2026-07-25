import { FileText } from 'lucide-react';

import { StagePlaceholder } from '@/components/common/stage-placeholder';

export const metadata = { title: 'Статьи' };

export default function ArticlesPage() {
  return (
    <StagePlaceholder
      title="Статьи"
      description="Библиотека материалов и пошаговый мастер создания статьи."
      icon={FileText}
      stage={5}
      features={[
        'Статусы: черновик, на проверке, готова, запланирована, опубликована, архив',
        'Мастер из пяти шагов: данные, структура, текст, улучшение, проверка',
        'Пометки «Требуется проверка факта» вместо выдуманных данных',
        'Инструменты: сократить, расширить, проще, экспертнее, убрать повторы',
        'Автосохранение и восстановление предыдущих версий',
        'Учёт токенов и стоимости генерации',
      ]}
    />
  );
}
