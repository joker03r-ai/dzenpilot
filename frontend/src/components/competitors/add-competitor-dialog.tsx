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
import { Textarea } from '@/components/ui/textarea';
import { useCreateCompetitor } from '@/hooks/use-competitors';

interface AddCompetitorDialogProps {
  projectId: string;
  trigger: ReactNode;
}

export function AddCompetitorDialog({ projectId, trigger }: AddCompetitorDialogProps) {
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({
    name: '',
    url: '',
    niche: '',
    group_name: '',
    notes: '',
  });

  const createCompetitor = useCreateCompetitor(projectId);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!form.name.trim()) return;

    createCompetitor.mutate(
      {
        name: form.name.trim(),
        url: form.url.trim() || null,
        niche: form.niche.trim() || null,
        group_name: form.group_name.trim() || null,
        notes: form.notes.trim() || null,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setForm({ name: '', url: '', niche: '', group_name: '', notes: '' });
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Новый конкурент</DialogTitle>
          <DialogDescription>
            Достаточно названия. Ссылку и остальное можно заполнить позже.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="competitor-name">Название канала</Label>
            <Input
              id="competitor-name"
              value={form.name}
              onChange={(event) => setForm({ ...form, name: event.target.value })}
              placeholder="Хроники прошлого"
              maxLength={255}
              required
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="competitor-url">Ссылка на канал</Label>
            <Input
              id="competitor-url"
              value={form.url}
              onChange={(event) => setForm({ ...form, url: event.target.value })}
              placeholder="dzen.ru/nazvanie_kanala"
              maxLength={500}
            />
            <p className="text-xs text-muted-foreground">
              Можно без «https://» — сервис добавит сам.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="competitor-niche">Тематика</Label>
              <Input
                id="competitor-niche"
                value={form.niche}
                onChange={(event) => setForm({ ...form, niche: event.target.value })}
                placeholder="История"
                maxLength={255}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="competitor-group">Группа</Label>
              <Input
                id="competitor-group"
                value={form.group_name}
                onChange={(event) => setForm({ ...form, group_name: event.target.value })}
                placeholder="Основные конкуренты"
                maxLength={120}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="competitor-notes">Заметки</Label>
            <Textarea
              id="competitor-notes"
              value={form.notes}
              onChange={(event) => setForm({ ...form, notes: event.target.value })}
              placeholder="Что заметили: ритм публикаций, сильные заголовки, форматы"
              maxLength={4000}
              className="min-h-[72px]"
            />
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" loading={createCompetitor.isPending}>
              Добавить конкурента
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
