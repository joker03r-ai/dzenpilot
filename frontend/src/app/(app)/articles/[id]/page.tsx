'use client';

import {
  ArrowLeft,
  CheckCircle2,
  Circle,
  Clock,
  FileText,
  History,
  ListOrdered,
  RotateCcw,
  Save,
  Sparkles,
} from 'lucide-react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { toast } from 'sonner';

import { ImproveToolbar } from '@/components/articles/improve-toolbar';
import { EmptyState } from '@/components/common/empty-state';
import { Hint } from '@/components/common/hint';
import { PageHeader } from '@/components/common/page-header';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Textarea } from '@/components/ui/textarea';
import {
  useArticle,
  useArticleVersions,
  useChecklist,
  useGenerateBody,
  useGenerateOutline,
  useRestoreVersion,
  useUpdateArticle,
} from '@/hooks/use-articles';
import { formatDateTime, formatNumber } from '@/lib/format';
import { useProjectContext } from '@/lib/project-context';

const AUTOSAVE_DELAY = 3000;

export default function ArticleEditorPage() {
  const params = useParams<{ id: string }>();
  const { projectId } = useProjectContext();
  const articleId = params.id;

  const { data: article, isLoading } = useArticle(projectId, articleId);
  const { data: versions } = useArticleVersions(projectId, articleId);
  const { data: checklist } = useChecklist(projectId, articleId);

  const updateArticle = useUpdateArticle(projectId, articleId);
  const generateOutline = useGenerateOutline(projectId, articleId);
  const generateBody = useGenerateBody(projectId, articleId);
  const restoreVersion = useRestoreVersion(projectId, articleId);

  const [title, setTitle] = useState('');
  const [lead, setLead] = useState('');
  const [body, setBody] = useState('');
  const [dirty, setDirty] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    if (!article) return;
    setTitle(article.title);
    setLead(article.lead ?? '');
    setBody(article.body_markdown ?? '');
    setDirty(false);
  }, [article?.id, article?.updated_at]);

  // Автосохранение: правки уходят на сервер через три секунды после последнего ввода
  useEffect(() => {
    if (!dirty) return;
    if (timer.current) clearTimeout(timer.current);

    timer.current = setTimeout(() => {
      updateArticle.mutate(
        { title, lead, body_markdown: body },
        {
          onSuccess: () => {
            setSavedAt(new Date());
            setDirty(false);
          },
        },
      );
    }, AUTOSAVE_DELAY);

    return () => {
      if (timer.current) clearTimeout(timer.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [title, lead, body, dirty]);

  if (isLoading) return <Skeleton className="h-96 w-full" />;

  if (!article) {
    return (
      <EmptyState
        icon={FileText}
        title="Статья не найдена"
        description="Возможно, она была перенесена в архив."
        action={
          <Button asChild>
            <Link href="/articles">К списку статей</Link>
          </Button>
        }
      />
    );
  }

  const outline = generateOutline.data;
  const titleVariants = (article.generation_input?.title_variants as string[]) ?? [];

  const saveNow = () => {
    updateArticle.mutate(
      { title, lead, body_markdown: body, save_version: true, change_note: 'Ручное сохранение' },
      {
        onSuccess: () => {
          setSavedAt(new Date());
          setDirty(false);
          toast.success('Сохранено, версия добавлена в историю');
        },
      },
    );
  };

  return (
    <div className="space-y-6">
      <Button asChild variant="ghost" size="sm" className="-ml-2">
        <Link href="/articles">
          <ArrowLeft aria-hidden />
          К списку статей
        </Link>
      </Button>

      <PageHeader
        title={article.title}
        description="Шаги 2–5 мастера. Правки сохраняются автоматически."
        action={
          <Button size="lg" onClick={saveNow} loading={updateArticle.isPending}>
            <Save aria-hidden />
            Сохранить версию
          </Button>
        }
      />

      <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        <Badge variant="secondary">{article.status_label}</Badge>
        {article.word_count ? <span>{formatNumber(article.word_count)} слов</span> : null}
        {article.reading_time_min ? (
          <span className="flex items-center gap-1">
            <Clock className="size-3" aria-hidden />
            {article.reading_time_min} мин чтения
          </span>
        ) : null}
        {article.ai_model ? <span>Модель: {article.ai_model}</span> : null}
        {article.tokens_output ? (
          <span>Токенов: {formatNumber((article.tokens_input ?? 0) + article.tokens_output)}</span>
        ) : null}
        <span className={dirty ? 'text-warning-foreground' : ''}>
          {dirty
            ? 'Есть несохранённые правки…'
            : savedAt
              ? `Сохранено в ${savedAt.toLocaleTimeString('ru-RU')}`
              : 'Все правки сохранены'}
        </span>
      </div>

      <Tabs defaultValue="editor">
        <TabsList className="flex-wrap">
          <TabsTrigger value="outline">2. Структура</TabsTrigger>
          <TabsTrigger value="editor">3. Текст</TabsTrigger>
          <TabsTrigger value="improve">4. Доработка</TabsTrigger>
          <TabsTrigger value="checklist">5. Проверка</TabsTrigger>
          <TabsTrigger value="versions">Версии ({article.versions_count})</TabsTrigger>
        </TabsList>

        {/* Шаг 2 */}
        <TabsContent value="outline" className="space-y-4">
          <Hint>
            Сервис предложит десять вариантов заголовка и план из разделов. План можно
            отредактировать до того, как будет написан полный текст.
          </Hint>

          <Button onClick={() => generateOutline.mutate()} loading={generateOutline.isPending}>
            <ListOrdered aria-hidden />
            {article.outline.length ? 'Создать структуру заново' : 'Создать структуру'}
          </Button>

          {titleVariants.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Варианты заголовка</CardTitle>
                <CardDescription>Нажмите, чтобы подставить заголовок в статью.</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {titleVariants.map((variant, index) => (
                    <li key={index}>
                      <button
                        type="button"
                        onClick={() => {
                          setTitle(variant);
                          setDirty(true);
                        }}
                        className="w-full rounded-md border border-border px-3 py-2 text-left text-sm transition-colors hover:bg-secondary focus-ring"
                      >
                        {variant}
                      </button>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}

          {article.outline.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>План статьи</CardTitle>
              </CardHeader>
              <CardContent>
                <ol className="space-y-4">
                  {article.outline.map((section, index) => (
                    <li key={index}>
                      <p className="font-medium">
                        {index + 1}. {section.heading}
                      </p>
                      {section.points?.length ? (
                        <ul className="mt-1 space-y-1 pl-5 text-sm text-muted-foreground">
                          {section.points.map((point, pointIndex) => (
                            <li key={pointIndex} className="list-disc">
                              {point}
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </li>
                  ))}
                </ol>
              </CardContent>
            </Card>
          ) : outline ? null : (
            <EmptyState
              icon={ListOrdered}
              title="Структуры пока нет"
              description="Нажмите «Создать структуру» — сервис предложит заголовки, вступление и план разделов."
            />
          )}
        </TabsContent>

        {/* Шаг 3 */}
        <TabsContent value="editor" className="space-y-4">
          <div className="flex flex-wrap gap-2">
            <Button
              onClick={() => generateBody.mutate({ use_outline: article.outline.length > 0 })}
              loading={generateBody.isPending}
            >
              <Sparkles aria-hidden />
              {article.body_markdown ? 'Сгенерировать заново' : 'Сгенерировать статью'}
            </Button>
          </div>

          {generateBody.isPending ? (
            <Hint title="Идёт генерация">
              Модель пишет статью. Это занимает от 30 секунд до двух минут — не закрывайте страницу.
            </Hint>
          ) : null}

          <Card>
            <CardContent className="space-y-4 pt-6">
              <div className="space-y-2">
                <Label htmlFor="article-title">Заголовок</Label>
                <Input
                  id="article-title"
                  value={title}
                  onChange={(event) => {
                    setTitle(event.target.value);
                    setDirty(true);
                  }}
                  maxLength={500}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="article-lead">Вступление</Label>
                <Textarea
                  id="article-lead"
                  value={lead}
                  onChange={(event) => {
                    setLead(event.target.value);
                    setDirty(true);
                  }}
                  className="min-h-[80px]"
                  maxLength={4000}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="article-body">Текст статьи</Label>
                <Textarea
                  id="article-body"
                  value={body}
                  onChange={(event) => {
                    setBody(event.target.value);
                    setDirty(true);
                  }}
                  className="min-h-[520px] font-mono text-sm leading-relaxed"
                  placeholder="Здесь появится текст после генерации. Можно писать и вручную — разметка Markdown."
                />
                <p className="text-xs text-muted-foreground">
                  Подзаголовки обозначаются двумя решётками: ## Заголовок раздела
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Шаг 4 */}
        <TabsContent value="improve">
          <ImproveToolbar
            projectId={projectId!}
            articleId={articleId}
            hasBody={Boolean(article.body_markdown)}
          />
        </TabsContent>

        {/* Шаг 5 */}
        <TabsContent value="checklist" className="space-y-4">
          <Hint>
            Статья не публикуется автоматически. Даже когда все пункты выполнены,
            публикацию нужно подтвердить вручную.
          </Hint>

          {checklist ? (
            <Card>
              <CardHeader>
                <CardTitle>{checklist.ready ? 'Всё готово' : 'Перед публикацией'}</CardTitle>
                <CardDescription>{checklist.message}</CardDescription>
              </CardHeader>
              <CardContent>
                <ul className="space-y-3">
                  {checklist.items.map((item) => (
                    <li key={item.code} className="flex gap-3">
                      {item.done ? (
                        <CheckCircle2 className="mt-0.5 size-4 shrink-0 text-success" aria-hidden />
                      ) : (
                        <Circle className="mt-0.5 size-4 shrink-0 text-muted-foreground" aria-hidden />
                      )}
                      <div>
                        <p className="text-sm font-medium">{item.label}</p>
                        <p className="text-xs text-muted-foreground">{item.hint}</p>
                      </div>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : (
            <Skeleton className="h-72 w-full" />
          )}

          <div className="flex flex-wrap gap-2">
            <Button
              variant="outline"
              onClick={() => updateArticle.mutate({ status: 'review' })}
            >
              Отправить на проверку
            </Button>
            <Button
              onClick={() => updateArticle.mutate({ status: 'ready' })}
              disabled={!checklist?.ready}
              title={checklist?.ready ? undefined : 'Сначала выполните все пункты'}
            >
              Отметить готовой
            </Button>
          </div>
        </TabsContent>

        {/* Версии */}
        <TabsContent value="versions">
          {!versions || versions.length === 0 ? (
            <EmptyState
              icon={History}
              title="Версий пока нет"
              description="Версия сохраняется автоматически перед каждой генерацией и доработкой, а также по кнопке «Сохранить версию»."
            />
          ) : (
            <Card>
              <CardContent className="p-0">
                <ul className="divide-y divide-border">
                  {versions.map((version) => (
                    <li
                      key={version.id}
                      className="flex flex-col gap-2 p-4 sm:flex-row sm:items-center sm:justify-between"
                    >
                      <div className="min-w-0">
                        <p className="text-sm font-medium">
                          Версия {version.version_number}
                          {version.change_note ? ` · ${version.change_note}` : ''}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {formatDateTime(version.created_at)}
                          {version.title ? ` · ${version.title}` : ''}
                        </p>
                      </div>

                      <Button
                        variant="outline"
                        size="sm"
                        className="shrink-0"
                        onClick={() => restoreVersion.mutate(version.id)}
                        loading={restoreVersion.isPending}
                      >
                        <RotateCcw aria-hidden />
                        Восстановить
                      </Button>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
