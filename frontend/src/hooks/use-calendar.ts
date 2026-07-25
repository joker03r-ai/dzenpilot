'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { toast } from 'sonner';

import { api, errorMessage } from '@/lib/api';
import type {
  CalendarOptions,
  CalendarResponse,
  CalendarView,
  ScheduleCreateInput,
  ScheduleItem,
} from '@/types/api';

export const calendarKeys = {
  all: ['calendar'] as const,
  view: (projectId: string, query: string) =>
    [...calendarKeys.all, projectId, query] as const,
  options: (projectId: string) => [...calendarKeys.all, projectId, 'options'] as const,
};

export function useCalendar(
  projectId: string | null,
  view: CalendarView,
  anchor: string,
  timezone: string,
) {
  const query = new URLSearchParams({ view, anchor, timezone }).toString();

  return useQuery({
    queryKey: calendarKeys.view(projectId ?? 'none', query),
    queryFn: () => api.get<CalendarResponse>(`/projects/${projectId}/calendar?${query}`),
    enabled: Boolean(projectId),
  });
}

export function useCalendarOptions(projectId: string | null) {
  return useQuery({
    queryKey: calendarKeys.options(projectId ?? 'none'),
    queryFn: () => api.get<CalendarOptions>(`/projects/${projectId}/calendar/timezones`),
    enabled: Boolean(projectId),
    staleTime: 60 * 60 * 1000,
  });
}

export function useCreateSchedule(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (input: ScheduleCreateInput) =>
      api.post<ScheduleItem[]>(`/projects/${projectId}/calendar`, input),
    onSuccess: (items) => {
      queryClient.invalidateQueries({ queryKey: calendarKeys.all });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      toast.success(
        items.length > 1
          ? `Создано записей: ${items.length}`
          : 'Публикация запланирована. Не забудьте подтвердить её.',
      );
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useUpdateSchedule(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      id,
      ...input
    }: {
      id: string;
      local_datetime?: string;
      timezone?: string;
      note?: string | null;
      confirmed_by_user?: boolean;
    }) => api.patch<ScheduleItem>(`/projects/${projectId}/calendar/${id}`, input),
    onSuccess: (item) => {
      queryClient.invalidateQueries({ queryKey: calendarKeys.all });
      toast.success(
        item.confirmed_by_user
          ? 'Публикация подтверждена'
          : `Перенесено на ${item.local_date} в ${item.local_time}`,
      );
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useDuplicateSchedule(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) =>
      api.post<ScheduleItem>(`/projects/${projectId}/calendar/${id}/duplicate?days_offset=7`),
    onSuccess: (item) => {
      queryClient.invalidateQueries({ queryKey: calendarKeys.all });
      toast.success(`Копия создана на ${item.local_date}`);
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}

export function useCancelSchedule(projectId: string | null) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (id: string) => api.delete(`/projects/${projectId}/calendar/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: calendarKeys.all });
      queryClient.invalidateQueries({ queryKey: ['articles'] });
      toast.success('Публикация отменена');
    },
    onError: (error) => toast.error(errorMessage(error)),
  });
}
