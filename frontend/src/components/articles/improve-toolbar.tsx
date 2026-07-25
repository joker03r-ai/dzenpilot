'use client';

import { Wand2 } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { useImproveArticle } from '@/hooks/use-articles';
import type { ImproveAction } from '@/types/api';

/** Инструменты, меняющие текст, и инструменты, выдающие заключение. */
const REWRITE_TOOLS: { action: ImproveAction; label: string }[] = [
  { action: 'shorten', label: 'Сократить' },
  { action: 'expand', label: 'Расширить' },
  { action: 'simplify', label: 'Сделать проще' },
  { action: 'expertise', label: 'Сделать экспертнее' },
  { action: 'add_examples', label: 'Добавить примеры' },
  { action: 'remove_repeats', label: 'Убрать повторы' },
];

const ADVISORY_TOOLS: { action: ImproveAction; label: string }[] = [
  { action: 'check_structure', label: 'Проверить структуру' },
  { action: 'check_title', label: 'Проверить заголовок' },
  { action: 'check_clickability', label: 'Проверить кликабельность' },
  { action: 'check_readability', label: 'Проверить читаемость' },
  { action: 'find_unverified', label: 'Найти неподтверждённое' },
  { action: 'image_description', label: 'Описание изображений' },
  { action: 'image_prompts', label: 'Промты для картинок' },
];

interface ImproveToolbarProps {
  projectId: string;
  articleId: string;
  hasBody: boolean;
}

export function ImproveToolbar({ projectId, articleId, hasBody }: ImproveToolbarProps) {
  const improve = useImproveArticle(projectId, articleId);
  const [tone, setTone] = useState('');
  const [fragment, setFragment] = useState('');
  const [result, setResult] = useState<{ label: string; text: string } | null>(null);

  const run = (action: ImproveAction, extra: Record<string, string> = {}) => {
    improve.mutate(
      { action, ...extra },
      { onSuccess: (data) => setResult({ label: data.action_label, text: data.result }) },
    );
  };

  const busy = improve.isPending;

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle>Переписать текст</CardTitle>
          <CardDescription>
            Каждое действие меняет статью. Предыдущий вариант автоматически сохраняется
            в истории версий, поэтому откатиться можно всегда.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-2">
            {REWRITE_TOOLS.map((tool) => (
              <Button
                key={tool.action}
                variant="outline"
                size="sm"
                disabled={!hasBody || busy}
                onClick={() => run(tool.action)}
              >
                {tool.label}
              </Button>
            ))}
          </div>

          <div className="grid gap-3 sm:grid-cols-[1fr_auto] sm:items-end">
            <div className="space-y-2">
              <Label htmlFor="tone-input">Изменить тон</Label>
              <Input
                id="tone-input"
                value={tone}
                onChange={(event) => setTone(event.target.value)}
                placeholder="Например: дружелюбный и лёгкий"
                maxLength={1000}
              />
            </div>
            <Button
              variant="outline"
              disabled={!hasBody || busy || !tone.trim()}
              onClick={() => run('change_tone', { instruction: tone.trim() })}
            >
              Применить тон
            </Button>
          </div>

          <div className="space-y-2">
            <Label htmlFor="fragment-input">Переписать фрагмент</Label>
            <Textarea
              id="fragment-input"
              value={fragment}
              onChange={(event) => setFragment(event.target.value)}
              placeholder="Вставьте сюда абзац, который нужно переписать"
              className="min-h-[80px]"
              maxLength={20000}
            />
            <Button
              variant="outline"
              size="sm"
              disabled={!hasBody || busy || !fragment.trim()}
              onClick={() => run('rewrite_fragment', { fragment: fragment.trim() })}
            >
              <Wand2 aria-hidden />
              Переписать фрагмент
            </Button>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Проверить и подсказать</CardTitle>
          <CardDescription>
            Эти инструменты не меняют текст — они выдают заключение, что стоит поправить.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {ADVISORY_TOOLS.map((tool) => (
              <Button
                key={tool.action}
                variant="secondary"
                size="sm"
                disabled={!hasBody || busy}
                onClick={() => run(tool.action)}
              >
                {tool.label}
              </Button>
            ))}
          </div>
        </CardContent>
      </Card>

      {busy ? (
        <Card>
          <CardContent className="p-6 text-sm text-muted-foreground">
            Модель работает. Обычно это занимает от 10 до 60 секунд.
          </CardContent>
        </Card>
      ) : null}

      {result ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">{result.label}</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-96 overflow-auto whitespace-pre-wrap rounded-md bg-secondary p-4 text-sm">
              {result.text}
            </pre>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}
