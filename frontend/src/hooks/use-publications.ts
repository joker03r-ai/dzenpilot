'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import type {
  ExportResponse,
  PreflightResponse,
  PublicationLogItem,
  PublishResponse,
} from '@/types/api';

export const publicationKeys = {
  all: ['publications'] as const,
  logs: (projectId: string) => [...publicationKeys.all, projectId, 'logs'] as const,
  preflight: (projectId: string, scheduleId: string) =>
    [...publicationKeys.all, projectId, scheduleId, 'preflight'] as const,
};

export function usePublicationLogs(projectId: string | null) {
  return useQuery({
    queryKey: publicationKeys.logs(projectId ?? 'none'),
    queryFn: () =>
      api.get<PublicationLogItem[]>(`/projects/${projectId}/publications/logs?limit=100`),
    enabled: Boolean(projectId),
  });
}

export function usePreflight(projectId: string | null) {
  return useMutation({
    mutationFn: (scheduleId: string) =>
      api.post<PreflightResponse>(
        `/projects/${projectId}/publications/${scheduleId}/preflight`,
      ),
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useConfirmPublication(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (scheduleId: string) =>
      api.post<PreflightResponse>(`/projects/${projectId}/publications/${scheduleId}/confirm`, {
        confirmed: true,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
      toast.success('Публикация подтверждена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function usePublish(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      scheduleId,
      method,
      force = false,
    }: {
      scheduleId: string;
      method: string;
      force?: boolean;
    }) =>
      api.post<PublishResponse>(`/projects/${projectId}/publications/${scheduleId}/publish`, {
        method,
        force,
      }),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: publicationKeys.all });
      queryClient.invalidateQueries({ queryKey: ['calendar'] });
      queryClient.invalidateQueries({ queryKey: ['articles'] });

      if (result.result === 'success') toast.success(result.message);
      else if (result.result === 'skipped') toast.warning(result.message);
      else toast.error(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useExportArticle(projectId: string | null) {
  return useMutation({
    mutationFn: ({ articleId, format }: { articleId: string; format: string }) =>
      api.get<ExportResponse>(
        `/projects/${projectId}/articles/${articleId}/export?format=${format}`,
      ),
    onSuccess: (result) => {
      // Файл скачивается прямо из браузера, без обращения к серверу
      const blob = new Blob([result.content], { type: 'text/plain;charset=utf-8' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = result.filename;
      link.click();
      URL.revokeObjectURL(url);
      toast.success(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
