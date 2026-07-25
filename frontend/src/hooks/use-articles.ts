'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import type {
  Article,
  ArticleCreateInput,
  ArticleListItem,
  ArticleStatus,
  ArticleVersion,
  ChecklistResponse,
  ImproveAction,
  ImproveResponse,
  OutlineResponse,
  Page,
} from '@/types/api';

export const articleKeys = {
  all: ['articles'] as const,
  list: (projectId: string, status: string) =>
    [...articleKeys.all, projectId, 'list', status] as const,
  detail: (projectId: string, id: string) =>
    [...articleKeys.all, projectId, 'detail', id] as const,
  versions: (projectId: string, id: string) =>
    [...articleKeys.all, projectId, id, 'versions'] as const,
  checklist: (projectId: string, id: string) =>
    [...articleKeys.all, projectId, id, 'checklist'] as const,
};

export function useArticles(projectId: string | null, status?: ArticleStatus) {
  const query = status ? `status=${status}&size=100` : 'size=100';

  return useQuery({
    queryKey: articleKeys.list(projectId ?? 'none', status ?? 'all'),
    queryFn: () => api.get<Page<ArticleListItem>>(`/projects/${projectId}/articles?${query}`),
    enabled: Boolean(projectId),
  });
}

export function useArticle(projectId: string | null, articleId: string) {
  return useQuery({
    queryKey: articleKeys.detail(projectId ?? 'none', articleId),
    queryFn: () => api.get<Article>(`/projects/${projectId}/articles/${articleId}`),
    enabled: Boolean(projectId && articleId),
  });
}

export function useArticleVersions(projectId: string | null, articleId: string) {
  return useQuery({
    queryKey: articleKeys.versions(projectId ?? 'none', articleId),
    queryFn: () =>
      api.get<ArticleVersion[]>(`/projects/${projectId}/articles/${articleId}/versions`),
    enabled: Boolean(projectId && articleId),
  });
}

export function useChecklist(projectId: string | null, articleId: string) {
  return useQuery({
    queryKey: articleKeys.checklist(projectId ?? 'none', articleId),
    queryFn: () =>
      api.get<ChecklistResponse>(`/projects/${projectId}/articles/${articleId}/checklist`),
    enabled: Boolean(projectId && articleId),
  });
}

export function useCreateArticle(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ArticleCreateInput) =>
      api.post<Article>(`/projects/${projectId}/articles`, input, {
        idempotencyKey: crypto.randomUUID(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

interface UpdateInput {
  title?: string;
  lead?: string | null;
  body_markdown?: string;
  cta?: string | null;
  status?: ArticleStatus;
  outline?: { heading: string; points: string[] }[];
  change_note?: string;
  save_version?: boolean;
}

export function useUpdateArticle(projectId: string | null, articleId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: UpdateInput) =>
      api.patch<Article>(`/projects/${projectId}/articles/${articleId}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useGenerateOutline(projectId: string | null, articleId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post<OutlineResponse>(`/projects/${projectId}/articles/${articleId}/outline`),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
      toast.success(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useGenerateBody(projectId: string | null, articleId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: { use_outline: boolean; extra_instructions?: string | null }) =>
      api.post<Article>(`/projects/${projectId}/articles/${articleId}/generate`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
      toast.success('Статья написана. Проверьте текст и доработайте при необходимости.');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useImproveArticle(projectId: string | null, articleId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      action: ImproveAction;
      fragment?: string | null;
      instruction?: string | null;
    }) => api.post<ImproveResponse>(`/projects/${projectId}/articles/${articleId}/improve`, input),
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
      toast.success(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useRestoreVersion(projectId: string | null, articleId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (versionId: string) =>
      api.post<Article>(
        `/projects/${projectId}/articles/${articleId}/versions/${versionId}/restore`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
      toast.success('Версия восстановлена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeleteArticle(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (articleId: string) => api.delete(`/projects/${projectId}/articles/${articleId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: articleKeys.all });
      toast.success('Статья перенесена в архив');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
