'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import type {
  Page,
  Topic,
  TopicSearchRequest,
  TopicSearchResponse,
  TopicStatus,
} from '@/types/api';

export const topicKeys = {
  all: ['topics'] as const,
  list: (projectId: string, query: string) =>
    [...topicKeys.all, projectId, 'list', query] as const,
  detail: (projectId: string, id: string) =>
    [...topicKeys.all, projectId, 'detail', id] as const,
};

export function useTopics(
  projectId: string | null,
  options: { status?: TopicStatus; minScore?: number; search?: string } = {},
) {
  const params = new URLSearchParams({ size: '100' });
  if (options.status) params.set('status', options.status);
  if (options.minScore !== undefined) params.set('min_score', String(options.minScore));
  if (options.search) params.set('search', options.search);
  const query = params.toString();

  return useQuery({
    queryKey: topicKeys.list(projectId ?? 'none', query),
    queryFn: () => api.get<Page<Topic>>(`/projects/${projectId}/topics?${query}`),
    enabled: Boolean(projectId),
  });
}

export function useTopic(projectId: string | null, topicId: string) {
  return useQuery({
    queryKey: topicKeys.detail(projectId ?? 'none', topicId),
    queryFn: () => api.get<Topic>(`/projects/${projectId}/topics/${topicId}`),
    enabled: Boolean(projectId && topicId),
  });
}

export function useSearchTopics(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: TopicSearchRequest) =>
      api.post<TopicSearchResponse>(`/projects/${projectId}/topics/search`, input),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.all });
      if (result.created > 0) toast.success(result.message);
      else toast.warning(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateTopic(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...input }: { id: string; status?: TopicStatus; title?: string }) =>
      api.patch<Topic>(`/projects/${projectId}/topics/${id}`, input),
    onSuccess: (topic) => {
      queryClient.invalidateQueries({ queryKey: topicKeys.all });
      const messages: Partial<Record<TopicStatus, string>> = {
        saved: 'Тема сохранена',
        planned: 'Тема добавлена в план',
        hidden: 'Тема скрыта',
        in_progress: 'Тема взята в работу',
      };
      toast.success(messages[topic.status] ?? 'Изменения сохранены');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeleteTopic(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${projectId}/topics/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: topicKeys.all });
      toast.success('Тема удалена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
