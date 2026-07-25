'use client';

import { useState, type ReactNode } from 'react';

import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useAddPublication } from '@/hooks/use-competitors';

interface AddPublicationDialogProps {
  projectId: string;
  competitorId: string;
  trigger: ReactNode;
}

const EMPTY = {
  title: '',
  url: '',
  published_at: '',
  views: '',
  reactions: '',
  comments_count: '',
  topic_guess: '',
  format: '',
};

export function AddPublicationDialog({
  projectId,
  competitorId,
  trigger,
}: AddPublicationDialogProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState(EMPTY);

  const addPublication = useAddPublication(projectId, competitorId);

  const toNumber = (value: string) => (value.trim() === '' ? null : Number(value));

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.title.trim()) return;

    addPublication.mutate(
      {
        title: form.title.trim(),
        url: form.url.trim() || null,
        published_at: form.published_at ? new Date(form.published_at).toISOString() : null,
        views: toNumber(form.views),
        reactions: toNumber(form.reactions),
        comments_count: toNumber(form.comments_count),
        topic_guess: form.topic_guess.trim() || null,
        format: form.format.trim() || null,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setForm(EMPTY);
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Публикация конкурента</DialogTitle>
          <DialogDescription>
            Обязателен только заголовок. Числовые поля оставьте пустыми, если данных нет —
            сервис не будет их выдумывать.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="pub-title">Заголовок</Label>
            <Input
              id="pub-title"
              value={form.title}
              onChange={(event) => setForm({ ...form, title: event.target.value })}
              maxLength={500}
              required
              autoFocus
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="pub-url">Ссылка</Label>
              <Input
                id="pub-url"
                value={form.url}
                onChange={(event) => setForm({ ...form, url: event.target.value })}
                maxLength={700}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pub-date">Дата публикации</Label>
              <Input
                id="pub-date"
                type="date"
                value={form.published_at}
                onChange={(event) => setForm({ ...form, published_at: event.target.value })}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-3">
            <div className="space-y-2">
              <Label htmlFor="pub-views">Просмотры</Label>
              <Input
                id="pub-views"
                type="number"
                min={0}
                value={form.views}
                onChange={(event) => setForm({ ...form, views: event.target.value })}
                placeholder="нет данных"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pub-reactions">Реакции</Label>
              <Input
                id="pub-reactions"
                type="number"
                min={0}
                value={form.reactions}
                onChange={(event) => setForm({ ...form, reactions: event.target.value })}
                placeholder="нет данных"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pub-comments">Комментарии</Label>
              <Input
                id="pub-comments"
                type="number"
                min={0}
                value={form.comments_count}
                onChange={(event) => setForm({ ...form, comments_count: event.target.value })}
                placeholder="нет данных"
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="pub-topic">Тема</Label>
              <Input
                id="pub-topic"
                value={form.topic_guess}
                onChange={(event) => setForm({ ...form, topic_guess: event.target.value })}
                placeholder="Быт и повседневность"
                maxLength={255}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="pub-format">Формат</Label>
              <Input
                id="pub-format"
                value={form.format}
                onChange={(event) => setForm({ ...form, format: event.target.value })}
                placeholder="Разбор, подборка, история"
                maxLength={120}
              />
            </div>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" loading={addPublication.isPending}>
              Добавить
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
