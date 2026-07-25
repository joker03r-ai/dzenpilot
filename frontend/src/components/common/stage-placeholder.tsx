import type { LucideIcon } from 'lucide-react';
import Link from 'next/link';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Button } from '@/components/ui/button';

interface StagePlaceholderProps {
  title: string;
  description: string;
  icon: LucideIcon;
  stage: number;
  /** Что появится в этом разделе */
  features: string[];
}

/**
 * Экран раздела, который включается на следующем этапе разработки.
 * Пользователь сразу видит, что здесь будет и что можно сделать сейчас.
 */
export function StagePlaceholder({
  title,
  description,
  icon,
  stage,
  features,
}: StagePlaceholderProps) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={description} />

      <Hint>
        Раздел подключается на этапе {stage} разработки. Основа проекта уже готова: работают
        регистрация, проекты, интеграции и главная страница.
      </Hint>

      <EmptyState
        icon={icon}
        title="Раздел скоро откроется"
        description="Здесь появятся следующие возможности:"
        action={
          <Button asChild>
            <Link href="/dashboard">Вернуться на главную</Link>
          </Button>
        }
        secondary={
          <ul className="mx-auto mt-2 max-w-md space-y-1 text-left">
            {features.map((feature) => (
              <li key={feature}>• {feature}</li>
            ))}
          </ul>
        }
      />
    </div>
  );
}
