'use client';

import Link from 'next/link';
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useRegister } from '@/hooks/use-auth';

export default function RegisterPage() {
  const register = useRegister();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [projectName, setProjectName] = useState('Мой канал');
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();

    if (password.length < 8) {
      setPasswordError('Пароль должен быть не короче 8 символов');
      return;
    }
    setPasswordError(null);

    register.mutate({
      email: email.trim(),
      password,
      full_name: fullName.trim() || undefined,
      project_name: projectName.trim() || 'Мой канал',
    });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Регистрация</CardTitle>
        <CardDescription>
          Создадим аккаунт и сразу первый проект — это займёт меньше минуты.
        </CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="full-name">Как вас зовут</Label>
            <Input
              id="full-name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Иван"
              autoComplete="name"
              maxLength={255}
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="email">Электронная почта</Label>
            <Input
              id="email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="autor@example.ru"
              autoComplete="email"
              required
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="new-password"
              aria-invalid={Boolean(passwordError)}
              required
            />
            <p className={passwordError ? 'text-xs text-destructive' : 'text-xs text-muted-foreground'}>
              {passwordError ?? 'Не короче 8 символов'}
            </p>
          </div>

          <div className="space-y-2">
            <Label htmlFor="project-name">Название вашего канала</Label>
            <Input
              id="project-name"
              value={projectName}
              onChange={(event) => setProjectName(event.target.value)}
              placeholder="Канал про историю"
              maxLength={255}
            />
            <p className="text-xs text-muted-foreground">
              Позже можно переименовать и добавить сколько угодно проектов.
            </p>
          </div>

          <Button type="submit" size="lg" className="w-full" loading={register.isPending}>
            Создать аккаунт
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Уже зарегистрированы?{' '}
          <Link href="/login" className="font-medium text-primary hover:underline">
            Войдите
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}
