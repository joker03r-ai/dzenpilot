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
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { useArticles } from '@/hooks/use-articles';
import { useCalendarOptions, useCreateSchedule } from '@/hooks/use-calendar';
import type { RepeatRule } from '@/types/api';

interface ScheduleDialogProps {
  projectId: string;
  defaultDate?: string;
  defaultTimezone: string;
  trigger: ReactNode;
}

export function ScheduleDialog({
  projectId,
  defaultDate,
  defaultTimezone,
  trigger,
}: ScheduleDialogProps) {
  const [open, setOpen] = useState(false);
  const { data: articles } = useArticles(projectId);
  const { data: options } = useCalendarOptions(projectId);
  const createSchedule = useCreateSchedule(projectId);

  const [articleId, setArticleId] = useState('');
  const [day, setDay] = useState(defaultDate ?? new Date().toISOString().slice(0, 10));
  const [time, setTime] = useState('10:00');
  const [timezone, setTimezone] = useState(defaultTimezone);
  const [repeat, setRepeat] = useState<RepeatRule>('none');
  const [repeatCount, setRepeatCount] = useState(4);
  const [note, setNote] = useState('');

  // В календарь можно ставить всё, кроме архива
  const available = (articles?.items ?? []).filter((item) => item.status !== 'archived');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!articleId) return;

    createSchedule.mutate(
      {
        article_id: articleId,
        local_datetime: `${day}T${time}`,
        timezone,
        repeat_rule: repeat,
        repeat_count: repeat === 'none' ? 1 : repeatCount,
        note: note.trim() || null,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setArticleId('');
          setNote('');
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Запланировать публикацию</DialogTitle>
          <DialogDescription>
            Время указывается в выбранном часовом поясе. Публикация не выполнится,
            пока вы её не подтвердите.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="schedule-article">Статья</Label>
            <Select
              id="schedule-article"
              value={articleId}
              onChange={(event) => setArticleId(event.target.value)}
              required
            >
              <option value="">Выберите статью</option>
              {available.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title} — {item.status_label}
                </option>
              ))}
            </Select>
            {available.length === 0 ? (
              <p className="text-xs text-muted-foreground">
                Статей пока нет. Сначала создайте статью в разделе «Статьи».
              </p>
            ) : null}
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="schedule-day">Дата</Label>
              <Input
                id="schedule-day"
                type="date"
                value={day}
                onChange={(event) => setDay(event.target.value)}
                required
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="schedule-time">Время</Label>
              <Input
                id="schedule-time"
                type="time"
                value={time}
                onChange={(event) => setTime(event.target.value)}
                required
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="schedule-timezone">Часовой пояс</Label>
            <Select
              id="schedule-timezone"
              value={timezone}
              onChange={(event) => setTimezone(event.target.value)}
            >
              {options?.popular.map((item) => (
                <option key={item.label} value={item.value}>
                  {item.label}
                </option>
              ))}
              <optgroup label="Все остальные">
                {options?.all.map((zone) => (
                  <option key={zone} value={zone}>
                    {zone}
                  </option>
                ))}
              </optgroup>
            </Select>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="schedule-repeat">Повторение</Label>
              <Select
                id="schedule-repeat"
                value={repeat}
                onChange={(event) => setRepeat(event.target.value as RepeatRule)}
              >
                {options?.repeat_rules.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>
            </div>

            {repeat !== 'none' ? (
              <div className="space-y-2">
                <Label htmlFor="schedule-count">Сколько публикаций</Label>
                <Input
                  id="schedule-count"
                  type="number"
                  min={1}
                  max={52}
                  value={repeatCount}
                  onChange={(event) => setRepeatCount(Number(event.target.value))}
                />
              </div>
            ) : null}
          </div>

          <div className="space-y-2">
            <Label htmlFor="schedule-note">Заметка</Label>
            <Textarea
              id="schedule-note"
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Например: выложить после утреннего пика"
              className="min-h-[64px]"
              maxLength={2000}
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" loading={createSchedule.isPending} disabled={!articleId}>
              Запланировать
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
