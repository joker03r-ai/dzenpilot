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
import { useCreateProject } from '@/hooks/use-projects';

const TIMEZONES = [
  { value: 'Europe/Moscow', label: 'Москва, UTC+3' },
  { value: 'Europe/Kaliningrad', label: 'Калининград, UTC+2' },
  { value: 'Asia/Yekaterinburg', label: 'Екатеринбург, UTC+5' },
  { value: 'Asia/Novosibirsk', label: 'Новосибирск, UTC+7' },
  { value: 'Asia/Irkutsk', label: 'Иркутск и Улан-Удэ, UTC+8' },
  { value: 'Asia/Vladivostok', label: 'Владивосток, UTC+10' },
  { value: 'Europe/Berlin', label: 'Берлин, UTC+1' },
];

export function CreateProjectDialog({ trigger }: { trigger: ReactNode }) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');
  const [niche, setNiche] = useState('');
  const [audience, setAudience] = useState('');
  const [timezone, setTimezone] = useState('Europe/Moscow');

  const createProject = useCreateProject();

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!name.trim()) return;

    createProject.mutate(
      {
        name: name.trim(),
        niche: niche.trim() || null,
        target_audience: audience.trim() || null,
        timezone,
      },
      {
        onSuccess: () => {
          setOpen(false);
          setName('');
          setNiche('');
          setAudience('');
          setTimezone('Europe/Moscow');
        },
      },
    );
  };

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger asChild>{trigger}</DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Новый проект</DialogTitle>
          <DialogDescription>
            Проект — это один канал Дзена. У каждого свои конкуренты, темы, статьи и календарь.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="project-name">Название проекта</Label>
            <Input
              id="project-name"
              value={name}
              onChange={(event) => setName(event.target.value)}
              placeholder="Например: Канал про историю"
              maxLength={255}
              required
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-niche">Тематика</Label>
            <Input
              id="project-niche"
              value={niche}
              onChange={(event) => setNiche(event.target.value)}
              placeholder="История, здоровье, путешествия…"
              maxLength={255}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-audience">Кто ваши читатели</Label>
            <Textarea
              id="project-audience"
              value={audience}
              onChange={(event) => setAudience(event.target.value)}
              placeholder="Взрослые 30–60 лет, интересуются историей быта"
              maxLength={2000}
              className="min-h-[72px]"
            />
            <p className="text-xs text-muted-foreground">
              Это описание ИИ использует при подборе тем и написании статей.
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-timezone">Часовой пояс публикаций</Label>
            <Select
              id="project-timezone"
              value={timezone}
              onChange={(event) => setTimezone(event.target.value)}
            >
              {TIMEZONES.map((option) => (
                <option key={option.label} value={option.value}>
                  {option.label}
                </option>
              ))}
            </Select>
          </div>

          <DialogFooter>
            <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
              Отмена
            </Button>
            <Button type="submit" loading={createProject.isPending}>
              Создать проект
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}
