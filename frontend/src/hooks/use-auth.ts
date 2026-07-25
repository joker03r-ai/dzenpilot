'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter } from 'next/navigation';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import { useProjectContext } from '@/lib/project-context';
import type { AuthResponse, MessageResponse } from '@/types/api';

export const authKeys = {
  me: ['auth', 'me'] as const,
};

export function useMe(enabled = true) {
  return useQuery({
    queryKey: authKeys.me,
    queryFn: () => api.get<AuthResponse>('/auth/me'),
    enabled,
    retry: false,
  });
}

interface LoginInput {
  email: string;
  password: string;
}

export function useLogin(nextPath?: string) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setProjectId } = useProjectContext();

  return useMutation({
    mutationFn: (input: LoginInput) => api.post<AuthResponse>('/auth/login', input),
    onSuccess: (data) => {
      queryClient.setQueryData(authKeys.me, data);
      if (data.default_project_id) setProjectId(data.default_project_id);
      toast.success('Вход выполнен');
      router.replace(nextPath || '/dashboard');
      router.refresh();
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

interface RegisterInput {
  email: string;
  password: string;
  full_name?: string;
  project_name: string;
}

export function useRegister() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setProjectId } = useProjectContext();

  return useMutation({
    mutationFn: (input: RegisterInput) => api.post<AuthResponse>('/auth/register', input),
    onSuccess: (data) => {
      queryClient.setQueryData(authKeys.me, data);
      if (data.default_project_id) setProjectId(data.default_project_id);
      toast.success('Аккаунт создан. Добро пожаловать в DzenPilot');
      router.replace('/dashboard');
      router.refresh();
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setProjectId } = useProjectContext();

  return useMutation({
    mutationFn: () => api.post<MessageResponse>('/auth/logout'),
    onSuccess: () => {
      setProjectId(null);
      queryClient.clear();
      router.replace('/login');
      router.refresh();
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

interface ChangePasswordInput {
  current_password: string;
  new_password: string;
}

export function useChangePassword() {
  return useMutation({
    mutationFn: (input: ChangePasswordInput) =>
      api.post<MessageResponse>('/auth/change-password', input),
    onSuccess: (data) => toast.success(data.message),
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateProfile() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: { full_name: string }) => api.patch('/auth/me', input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.me });
      toast.success('Профиль обновлён');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
