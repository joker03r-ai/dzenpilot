'use client';

import Link from 'next/link';
import { useSearchParams } from 'next/navigation';
import { Suspense, useState } from 'react';

import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useLogin } from '@/hooks/use-auth';

function LoginForm() {
  const searchParams = useSearchParams();
  const nextPath = searchParams.get('next') ?? undefined;
  const login = useLogin(nextPath);

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    login.mutate({ email: email.trim(), password });
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-2xl">Вход в DzenPilot</CardTitle>
        <CardDescription>Введите почту и пароль, чтобы продолжить работу.</CardDescription>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
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
              autoFocus
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="password">Пароль</Label>
            <Input
              id="password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
            />
          </div>

          <Button type="submit" size="lg" className="w-full" loading={login.isPending}>
            Войти
          </Button>
        </form>

        <p className="mt-6 text-center text-sm text-muted-foreground">
          Ещё нет аккаунта?{' '}
          <Link href="/register" className="font-medium text-primary hover:underline">
            Зарегистрируйтесь
          </Link>
        </p>
      </CardContent>
    </Card>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<Card className="h-80 animate-pulse" />}>
      <LoginForm />
    </Suspense>
  );
}
