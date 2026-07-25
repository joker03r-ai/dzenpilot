'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import { useProjectContext } from '@/lib/project-context';
import type { Dashboard, Page, Project, TimezoneOption } from '@/types/api';

export const projectKeys = {
  all: ['projects'] as const,
  list: () => [...projectKeys.all, 'list'] as const,
  detail: (id: string) => [...projectKeys.all, 'detail', id] as const,
  dashboard: (id: string) => [...projectKeys.all, 'dashboard', id] as const,
  timezones: (id: string) => [...projectKeys.all, 'timezones', id] as const,
};

export function useProjects() {
  return useQuery({
    queryKey: projectKeys.list(),
    queryFn: () => api.get<Page<Project>>('/projects?size=100'),
  });
}

export function useProject(projectId: string | null) {
  return useQuery({
    queryKey: projectKeys.detail(projectId ?? 'none'),
    queryFn: () => api.get<Project>(`/projects/${projectId}`),
    enabled: Boolean(projectId),
  });
}

export function useDashboard(projectId: string | null) {
  return useQuery({
    queryKey: projectKeys.dashboard(projectId ?? 'none'),
    queryFn: () => api.get<Dashboard>(`/projects/${projectId}/dashboard`),
    enabled: Boolean(projectId),
  });
}

export function useTimezones(projectId: string | null) {
  return useQuery({
    queryKey: projectKeys.timezones(projectId ?? 'none'),
    queryFn: () => api.get<TimezoneOption[]>(`/projects/${projectId}/timezones`),
    enabled: Boolean(projectId),
    staleTime: 60 * 60 * 1000,
  });
}

export interface ProjectInput {
  name: string;
  description?: string | null;
  niche?: string | null;
  target_audience?: string | null;
  tone_of_voice?: string | null;
  region?: string | null;
  timezone?: string;
  dzen_channel_url?: string | null;
}

export function useCreateProject() {
  const queryClient = useQueryClient();
  const { setProjectId } = useProjectContext();

  return useMutation({
    mutationFn: (input: ProjectInput) =>
      // Ключ идемпотентности защищает от двойного нажатия кнопки
      api.post<Project>('/projects', input, { idempotencyKey: crypto.randomUUID() }),
    onSuccess: (project) => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
      setProjectId(project.id);
      toast.success(`Проект «${project.name}» создан`);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateProject(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: Partial<ProjectInput>) =>
      api.patch<Project>(`/projects/${projectId}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: projectKeys.all });
      toast.success('Настройки проекта сохранены');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
