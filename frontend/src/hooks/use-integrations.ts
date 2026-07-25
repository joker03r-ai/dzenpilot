'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import type {
  AISettings,
  Integration,
  IntegrationKind,
  IntegrationTestResult,
  ProviderInfo,
} from '@/types/api';

export const integrationKeys = {
  all: ['integrations'] as const,
  list: (projectId: string) => [...integrationKeys.all, projectId] as const,
  providers: ['ai', 'providers'] as const,
  aiSettings: (projectId: string) => ['ai', 'settings', projectId] as const,
};

export function useIntegrations(projectId: string | null) {
  return useQuery({
    queryKey: integrationKeys.list(projectId ?? 'none'),
    queryFn: () => api.get<Integration[]>(`/projects/${projectId}/integrations`),
    enabled: Boolean(projectId),
  });
}

export function useAiProviders() {
  return useQuery({
    queryKey: integrationKeys.providers,
    queryFn: () => api.get<ProviderInfo[]>('/ai/providers'),
    staleTime: 60 * 60 * 1000,
  });
}

export function useAiSettings(projectId: string | null) {
  return useQuery({
    queryKey: integrationKeys.aiSettings(projectId ?? 'none'),
    queryFn: () => api.get<AISettings>(`/ai/settings?project_id=${projectId}`),
    enabled: Boolean(projectId),
  });
}

interface ConnectInput {
  kind: IntegrationKind;
  title?: string;
  api_key?: string;
  config?: Record<string, unknown>;
}

export function useConnectIntegration(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ConnectInput) =>
      api.post<Integration>(`/projects/${projectId}/integrations`, input),
    onSuccess: (integration) => {
      queryClient.invalidateQueries({ queryKey: integrationKeys.all });
      queryClient.invalidateQueries({ queryKey: ['ai'] });
      toast.success(`${integration.kind_label} подключён`);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateIntegration(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...input }: { id: string; api_key?: string; is_active?: boolean }) =>
      api.patch<Integration>(`/projects/${projectId}/integrations/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationKeys.all });
      toast.success('Подключение обновлено');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeleteIntegration(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${projectId}/integrations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: integrationKeys.all });
      toast.success('Подключение удалено');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useTestIntegration(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<IntegrationTestResult>(`/projects/${projectId}/integrations/${id}/test`),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: integrationKeys.all });
      if (result.ok) toast.success(result.message);
      else toast.error(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useSaveAiSettings(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: { provider: string; model: string; temperature: number; max_tokens: number }) =>
      api.put<AISettings>(`/ai/settings?project_id=${projectId}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['ai'] });
      toast.success('Модель сохранена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
