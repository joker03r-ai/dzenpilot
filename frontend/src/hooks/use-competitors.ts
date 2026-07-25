'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { API_BASE, api, errorMessage } from '@/lib/api';
import type {
  CompareRequest,
  CompareResponse,
  Competitor,
  CompetitorAnalysis,
  CompetitorInput,
  CsvImportResult,
  Page,
  Publication,
  PublicationInput,
} from '@/types/api';

export const competitorKeys = {
  all: ['competitors'] as const,
  list: (projectId: string, query: string) =>
    [...competitorKeys.all, projectId, 'list', query] as const,
  detail: (projectId: string, id: string) =>
    [...competitorKeys.all, projectId, 'detail', id] as const,
  publications: (projectId: string, id: string, page: number) =>
    [...competitorKeys.all, projectId, id, 'publications', page] as const,
  analyses: (projectId: string, id: string) =>
    [...competitorKeys.all, projectId, id, 'analyses'] as const,
  groups: (projectId: string) => [...competitorKeys.all, projectId, 'groups'] as const,
};

export function useCompetitors(
  projectId: string | null,
  options: { search?: string; group?: string } = {},
) {
  const params = new URLSearchParams({ size: '100' });
  if (options.search) params.set('search', options.search);
  if (options.group) params.set('group', options.group);
  const query = params.toString();

  return useQuery({
    queryKey: competitorKeys.list(projectId ?? 'none', query),
    queryFn: () => api.get<Page<Competitor>>(`/projects/${projectId}/competitors?${query}`),
    enabled: Boolean(projectId),
  });
}

export function useCompetitor(projectId: string | null, competitorId: string) {
  return useQuery({
    queryKey: competitorKeys.detail(projectId ?? 'none', competitorId),
    queryFn: () => api.get<Competitor>(`/projects/${projectId}/competitors/${competitorId}`),
    enabled: Boolean(projectId && competitorId),
  });
}

export function useCompetitorGroups(projectId: string | null) {
  return useQuery({
    queryKey: competitorKeys.groups(projectId ?? 'none'),
    queryFn: () => api.get<string[]>(`/projects/${projectId}/competitors/groups`),
    enabled: Boolean(projectId),
  });
}

export function usePublications(projectId: string | null, competitorId: string, page = 1) {
  return useQuery({
    queryKey: competitorKeys.publications(projectId ?? 'none', competitorId, page),
    queryFn: () =>
      api.get<Page<Publication>>(
        `/projects/${projectId}/competitors/${competitorId}/publications?page=${page}&size=50`,
      ),
    enabled: Boolean(projectId && competitorId),
  });
}

export function useAnalyses(projectId: string | null, competitorId: string) {
  return useQuery({
    queryKey: competitorKeys.analyses(projectId ?? 'none', competitorId),
    queryFn: () =>
      api.get<CompetitorAnalysis[]>(
        `/projects/${projectId}/competitors/${competitorId}/analyses`,
      ),
    enabled: Boolean(projectId && competitorId),
  });
}

export function useCreateCompetitor(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: CompetitorInput) =>
      api.post<Competitor>(`/projects/${projectId}/competitors`, input, {
        idempotencyKey: crypto.randomUUID(),
      }),
    onSuccess: (competitor) => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success(`Конкурент «${competitor.name}» добавлен`);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateCompetitor(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, ...input }: Partial<CompetitorInput> & { id: string }) =>
      api.patch<Competitor>(`/projects/${projectId}/competitors/${id}`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success('Изменения сохранены');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeleteCompetitor(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${projectId}/competitors/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success('Конкурент удалён');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useAddPublication(projectId: string | null, competitorId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: PublicationInput) =>
      api.post<Publication>(
        `/projects/${projectId}/competitors/${competitorId}/publications`,
        input,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success('Публикация добавлена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDeletePublication(projectId: string | null, competitorId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (publicationId: string) =>
      api.delete(
        `/projects/${projectId}/competitors/${competitorId}/publications/${publicationId}`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success('Публикация удалена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

/** Загрузка CSV идёт через FormData, поэтому запрос собирается вручную. */
export function useImportCsv(projectId: string | null, competitorId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<CsvImportResult> => {
      const form = new FormData();
      form.append('file', file);

      const response = await fetch(
        `${API_BASE}/projects/${projectId}/competitors/${competitorId}/publications/import-csv`,
        { method: 'POST', body: form, credentials: 'include' },
      );

      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(
          payload?.error?.message ?? 'Не удалось импортировать файл. Проверьте формат CSV.',
        );
      }
      return payload as CsvImportResult;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useAnalyzeCompetitor(projectId: string | null, competitorId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () =>
      api.post<CompetitorAnalysis>(
        `/projects/${projectId}/competitors/${competitorId}/analyze`,
      ),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: competitorKeys.all });
      toast.success('Отчёт готов');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useCompare(projectId: string | null) {
  return useMutation({
    mutationFn: (input: CompareRequest) =>
      api.post<CompareResponse>(`/projects/${projectId}/competitors/compare`, input),
    onError: (error) => toast.error(errorMessage(error)),
  });
}
