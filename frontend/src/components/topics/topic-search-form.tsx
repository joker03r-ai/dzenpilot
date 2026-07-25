'use client';

import { Search } from 'lucide-react';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import type { TopicSearchRequest } from '@/types/api';

interface TopicSearchFormProps {
  defaultNiche?: string;
  defaultAudience?: string;
  loading: boolean;
  onSubmit: (request: TopicSearchRequest) => void;
}

const GOALS = [
  { value: 'views', label: 'Просмотры' },
  { value: 'subscribers', label: 'Подписчики' },
  { value: 'leads', label: 'Заявки' },
  { value: 'income', label: 'Доход' },
] as const;

const PERIODS = [
  { value: 30, label: '30 дней' },
  { value: 90, label: '90 дней' },
  { value: 180, label: 'Полгода' },
  { value: 365, label: 'Год' },
];

export function TopicSearchForm({
  defaultNiche = '',
  defaultAudience = '',
  loading,
  onSubmit,
}: TopicSearchFormProps) {
  const [niche, setNiche] = useState(defaultNiche);
  const [audience, setAudience] = useState(defaultAudience);
  const [region, setRegion] = useState('Россия');
  const [format, setFormat] = useState('');
  const [periodDays, setPeriodDays] = useState(90);
  const [forbidden, setForbidden] = useState('');
  const [competition, setCompetition] = useState('');
  const [goal, setGoal] = useState<TopicSearchRequest['goal']>('views');
  const [count, setCount] = useState(8);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    if (!niche.trim()) return;

    onSubmit({
      niche: niche.trim(),
      audience: audience.trim() || null,
      region: region.trim() || null,
      format: format.trim() || null,
      period_days: periodDays,
      forbidden_topics: forbidden
        .split(',')
        .map((item) => item.trim())
        .filter(Boolean),
      competition_level: (competition || null) as TopicSearchRequest['competition_level'],
      goal,
      count,
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Параметры подбора</CardTitle>
        <CardDescription>
          Чем точнее опишете нишу и читателей, тем полезнее будут темы. Обязательное поле одно — ниша.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="niche">Ниша или тематика</Label>
            <Input
              id="niche"
              value={niche}
              onChange={(event) => setNiche(event.target.value)}
              placeholder="История быта, здоровье после 40, личные финансы"
              maxLength={255}
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="audience">Кто ваши читатели</Label>
            <Textarea
              id="audience"
              value={audience}
              onChange={(event) => setAudience(event.target.value)}
              placeholder="Взрослые 35–60 лет, читают с телефона, любят конкретику и цифры"
              maxLength={1000}
              className="min-h-[72px]"
            />
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <Label htmlFor="region">Регион</Label>
              <Input
                id="region"
                value={region}
                onChange={(event) => setRegion(event.target.value)}
                maxLength={120}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="format">Желаемый формат</Label>
              <Input
                id="format"
                value={format}
                onChange={(event) => setFormat(event.target.value)}
                placeholder="Разбор, подборка, личная история"
                maxLength={120}
              />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <Label htmlFor="goal">Цель</Label>
              <Select
                id="goal"
                value={goal}
                onChange={(event) => setGoal(event.target.value as TopicSearchRequest['goal'])}
              >
                {GOALS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="competition">Конкуренция</Label>
              <Select
                id="competition"
                value={competition}
                onChange={(event) => setCompetition(event.target.value)}
              >
                <option value="">Любая</option>
                <option value="low">Низкая</option>
                <option value="medium">Средняя</option>
                <option value="high">Высокая</option>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="period">Период анализа</Label>
              <Select
                id="period"
                value={String(periodDays)}
                onChange={(event) => setPeriodDays(Number(event.target.value))}
              >
                {PERIODS.map((item) => (
                  <option key={item.value} value={item.value}>
                    {item.label}
                  </option>
                ))}
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="count">Сколько тем</Label>
              <Input
                id="count"
                type="number"
                min={3}
                max={15}
                value={count}
                onChange={(event) => setCount(Number(event.target.value))}
              />
            </div>
          </div>

          <div className="space-y-2">
            <Label htmlFor="forbidden">Запрещённые темы</Label>
            <Input
              id="forbidden"
              value={forbidden}
              onChange={(event) => setForbidden(event.target.value)}
              placeholder="политика, криптовалюта, медицина"
            />
            <p className="text-xs text-muted-foreground">
              Через запятую. Темы с этими словами предлагаться не будут.
            </p>
          </div>

          <Button type="submit" size="lg" loading={loading}>
            <Search aria-hidden />
            Найти темы
          </Button>
        </form>
      </CardContent>
    </Card>
  );
}
