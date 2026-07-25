'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { API_BASE, api, errorMessage } from '@/lib/api';
import type {
  AnalyticsComparison,
  AnalyticsOverview,
  AnalyticsTop,
  CsvImportSummary,
  HourStat,
  TimeseriesResponse,
  WeekdayStat,
} from '@/types/api';

export const analyticsKeys = {
  all: ['analytics'] as const,
  section: (projectId: string, section: string, query: string) =>
    [...analyticsKeys.all, projectId, section, query] as const,
};

function buildQuery(period: string, start?: string, end?: string): string {
  const params = new URLSearchParams({ period });
  if (period === 'custom' && start && end) {
    params.set('start', start);
    params.set('end', end);
  }
  return params.toString();
}

function useSection<T>(
  projectId: string | null,
  section: string,
  period: string,
  start?: string,
  end?: string,
) {
  const query = buildQuery(period, start, end);
  const ready = period !== 'custom' || Boolean(start && end);

  return useQuery({
    queryKey: analyticsKeys.section(projectId ?? 'none', section, query),
    queryFn: () => api.get<T>(`/projects/${projectId}/analytics/${section}?${query}`),
    enabled: Boolean(projectId) && ready,
  });
}

export function useOverview(projectId: string | null, period: string, start?: string, end?: string) {
  return useSection<AnalyticsOverview>(projectId, 'overview', period, start, end);
}

export function useTimeseries(projectId: string | null, period: string, start?: string, end?: string) {
  return useSection<TimeseriesResponse>(projectId, 'timeseries', period, start, end);
}

export function useWeekdayStats(projectId: string | null, period: string, start?: string, end?: string) {
  return useSection<WeekdayStat[]>(projectId, 'by-weekday', period, start, end);
}

export function useHourStats(projectId: string | null, period: string, start?: string, end?: string) {
  return useSection<HourStat[]>(projectId, 'by-hour', period, start, end);
}

export function useTopContent(projectId: string | null, period: string, start?: string, end?: string) {
  return useSection<AnalyticsTop>(projectId, 'top', period, start, end);
}

export function useComparison(projectId: string | null, period: string, start?: string, end?: string) {
  return useSection<AnalyticsComparison>(projectId, 'comparison', period, start, end);
}

export function useAddManualStat(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: {
      article_id?: string | null;
      captured_for: string;
      views?: number | null;
      subscribers?: number | null;
      reactions?: number | null;
      comments_count?: number | null;
    }) => api.post(`/projects/${projectId}/analytics/manual`, input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: analyticsKeys.all });
      toast.success('Данные сохранены');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useImportAnalyticsCsv(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (file: File): Promise<CsvImportSummary> => {
      const form = new FormData();
      form.append('file', file);

      const response = await fetch(`${API_BASE}/projects/${projectId}/analytics/import-csv`, {
        method: 'POST',
        body: form,
        credentials: 'include',
      });

      const payload = await response.json().catch(() => null);
      if (!response.ok) {
        throw new Error(payload?.error?.message ?? 'Не удалось импортировать файл.');
      }
      return payload as CsvImportSummary;
    },
    onSuccess: (result) => {
      queryClient.invalidateQueries({ queryKey: analyticsKeys.all });
      toast.success(result.message);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

/** Выгрузка CSV скачивается напрямую, минуя React Query. */
export async function downloadAnalyticsCsv(
  projectId: string,
  period: string,
  start?: string,
  end?: string,
): Promise<void> {
  const query = buildQuery(period, start, end);
  const response = await fetch(`${API_BASE}/projects/${projectId}/analytics/export?${query}`, {
    credentials: 'include',
  });

  if (!response.ok) {
    toast.error('Не удалось выгрузить файл');
    return;
  }

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `analytics-${period}.csv`;
  link.click();
  URL.revokeObjectURL(url);
  toast.success('Файл выгружен');
}
