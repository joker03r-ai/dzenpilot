'use client';

import { ArrowRight, Sparkles } from 'lucide-react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Suspense, useEffect, useState } from 'react';

import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Textarea } from '@/components/ui/textarea';
import { useCreateArticle } from '@/hooks/use-articles';
import { useProject } from '@/hooks/use-projects';
import { useTopic } from '@/hooks/use-topics';
import { useProjectContext } from '@/lib/project-context';

/** Строка вида «а, б, в» превращается в список. */
function splitList(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

function NewArticleForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { projectId } = useProjectContext();

  const topicId = searchParams.get('topic');
  const { data: project } = useProject(projectId);
  const { data: topic } = useTopic(projectId, topicId ?? '');
  const createArticle = useCreateArticle(projectId);

  const [form, setForm] = useState({
    title: '',
    goal: '',
    audience: '',
    tone: '',
    target_length: 7000,
    keywords: '',
    region: '',
    required_facts: '',
    source_links: '',
    products: '',
    forbidden_words: '',
    cta: '',
  });

  // Данные из проекта и выбранной темы подставляются автоматически
  useEffect(() => {
    setForm((current) => ({
      ...current,
      title: current.title || topic?.title || '',
      audience: current.audience || topic?.audience || project?.target_audience || '',
      tone: current.tone || project?.tone_of_voice || '',
      region: current.region || project?.region || '',
      target_length: topic?.recommended_length || current.target_length,
    }));
  }, [topic, project]);

  if (!projectId) {
    return (
      <EmptyState
        icon={Sparkles}
        title="Сначала создайте проект"
        description="Статьи хранятся отдельно для каждого проекта. Создайте проект в меню слева."
      />
    );
  }

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.title.trim()) return;

    createArticle.mutate(
      {
        title: form.title.trim(),
        topic_id: topicId,
        goal: form.goal.trim() || null,
        audience: form.audience.trim() || null,
        tone: form.tone.trim() || null,
        target_length: form.target_length,
        keywords: splitList(form.keywords),
        region: form.region.trim() || null,
        required_facts: splitList(form.required_facts),
        source_links: splitList(form.source_links),
        products: splitList(form.products),
        forbidden_words: splitList(form.forbidden_words),
        cta: form.cta.trim() || null,
      },
      { onSuccess: (article) => router.push(`/articles/${article.id}`) },
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Новая статья"
        description="Шаг 1 из 5. Расскажите о статье — на следующем шаге сервис предложит структуру."
      />

      <Hint>
        Обязательное поле одно — тема. Остальное влияет на качество: чем точнее опишете
        аудиторию и обязательные факты, тем меньше придётся править потом.
      </Hint>

      {topic ? (
        <Card className="border-primary/25 bg-accent">
          <CardContent className="flex items-center gap-3 p-4 text-sm">
            <Sparkles className="size-4 shrink-0 text-primary" aria-hidden />
            <span>
              Статья создаётся по теме «{topic.title}»
              {topic.score ? ` с оценкой ${topic.score.total_score} из 100` : ''}.
            </span>
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>Основные данные</CardTitle>
          <CardDescription>Эти сведения получит модель при генерации текста.</CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="title">Тема статьи</Label>
              <Input
                id="title"
                value={form.title}
                onChange={(event) => setForm({ ...form, title: event.target.value })}
                placeholder="Сколько стоила жизнь в 1900 году"
                maxLength={500}
                required
                autoFocus
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="goal">Цель статьи</Label>
                <Input
                  id="goal"
                  value={form.goal}
                  onChange={(event) => setForm({ ...form, goal: event.target.value })}
                  placeholder="Дать понятную картину жизни горожан"
                  maxLength={500}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="tone">Тон общения</Label>
                <Input
                  id="tone"
                  value={form.tone}
                  onChange={(event) => setForm({ ...form, tone: event.target.value })}
                  placeholder="Живой рассказ без канцелярита"
                  maxLength={120}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="audience">Целевая аудитория</Label>
              <Textarea
                id="audience"
                value={form.audience}
                onChange={(event) => setForm({ ...form, audience: event.target.value })}
                placeholder="Взрослые 35–60 лет, интересуются историей быта"
                maxLength={500}
                className="min-h-[72px]"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="length">Примерный объём, знаков</Label>
                <Input
                  id="length"
                  type="number"
                  min={500}
                  max={50000}
                  step={500}
                  value={form.target_length}
                  onChange={(event) =>
                    setForm({ ...form, target_length: Number(event.target.value) })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="region">Регион</Label>
                <Input
                  id="region"
                  value={form.region}
                  onChange={(event) => setForm({ ...form, region: event.target.value })}
                  maxLength={120}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="keywords">Ключевые слова</Label>
              <Input
                id="keywords"
                value={form.keywords}
                onChange={(event) => setForm({ ...form, keywords: event.target.value })}
                placeholder="история быта, цены 1900, зарплаты"
              />
              <p className="text-xs text-muted-foreground">
                Через запятую. Модель вставит их естественно, не более двух раз каждое.
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="facts">Факты, которые нужно использовать</Label>
              <Textarea
                id="facts"
                value={form.required_facts}
                onChange={(event) => setForm({ ...form, required_facts: event.target.value })}
                placeholder="Каждый факт с новой строки"
                className="min-h-[72px]"
              />
              <p className="text-xs text-muted-foreground">
                Модель не выдумывает цифры. Всё, что не указано здесь и требует проверки,
                она пометит строкой «Требуется проверка факта».
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="sources">Ссылки на источники</Label>
              <Textarea
                id="sources"
                value={form.source_links}
                onChange={(event) => setForm({ ...form, source_links: event.target.value })}
                placeholder="Каждая ссылка с новой строки"
                className="min-h-[64px]"
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <div className="space-y-2">
                <Label htmlFor="products">Товары или услуги для упоминания</Label>
                <Input
                  id="products"
                  value={form.products}
                  onChange={(event) => setForm({ ...form, products: event.target.value })}
                  placeholder="через запятую"
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="forbidden">Запрещённые слова</Label>
                <Input
                  id="forbidden"
                  value={form.forbidden_words}
                  onChange={(event) => setForm({ ...form, forbidden_words: event.target.value })}
                  placeholder="через запятую"
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="cta">Призыв к действию</Label>
              <Input
                id="cta"
                value={form.cta}
                onChange={(event) => setForm({ ...form, cta: event.target.value })}
                placeholder="Подпишитесь, если хотите продолжение серии"
                maxLength={500}
              />
            </div>

            <Button type="submit" size="lg" loading={createArticle.isPending}>
              Дальше: структура
              <ArrowRight aria-hidden />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function NewArticlePage() {
  return (
    <Suspense fallback={<Skeleton className="h-96 w-full" />}>
      <NewArticleForm />
    </Suspense>
  );
}
