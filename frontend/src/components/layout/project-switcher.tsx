'use client';

import { Check, ChevronsUpDown, FolderPlus } from 'lucide-react';
import { useEffect } from 'react';

import { CreateProjectDialog } from '@/components/layout/create-project-dialog';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Skeleton } from '@/components/ui/skeleton';
import { useProjects } from '@/hooks/use-projects';
import { useProjectContext } from '@/lib/project-context';

export function ProjectSwitcher() {
  const { projectId, setProjectId, ready } = useProjectContext();
  const { data, isLoading } = useProjects();

  const projects = data?.items ?? [];
  const current = projects.find((project) => project.id === projectId);

  // Если сохранённого проекта больше нет, выбираем первый доступный
  useEffect(() => {
    if (!ready || isLoading || projects.length === 0) return;
    if (!projectId || !projects.some((project) => project.id === projectId)) {
      setProjectId(projects[0].id);
    }
  }, [ready, isLoading, projects, projectId, setProjectId]);

  if (isLoading) {
    return <Skeleton className="h-14 w-full" />;
  }

  return (
    <div className="space-y-2">
      <DropdownMenu>
        <DropdownMenuTrigger asChild>
          <button
            type="button"
            className="flex w-full items-center gap-2 rounded-md border border-border bg-background px-3 py-2.5 text-left transition-colors hover:bg-secondary focus-ring"
          >
            <span className="min-w-0 flex-1">
              <span className="block text-[11px] uppercase tracking-wide text-muted-foreground">
                Проект
              </span>
              <span className="block truncate text-sm font-medium">
                {current?.name ?? 'Проект не выбран'}
              </span>
            </span>
            <ChevronsUpDown className="size-4 shrink-0 text-muted-foreground" aria-hidden />
          </button>
        </DropdownMenuTrigger>

        <DropdownMenuContent align="start" className="w-[248px]">
          <DropdownMenuLabel>Ваши проекты</DropdownMenuLabel>
          {projects.length === 0 ? (
            <p className="px-2.5 py-2 text-sm text-muted-foreground">
              Пока ни одного проекта
            </p>
          ) : (
            projects.map((project) => (
              <DropdownMenuItem key={project.id} onSelect={() => setProjectId(project.id)}>
                <Check
                  className={
                    project.id === projectId ? 'size-4 text-primary' : 'size-4 opacity-0'
                  }
                  aria-hidden
                />
                <span className="truncate">{project.name}</span>
              </DropdownMenuItem>
            ))
          )}
          <DropdownMenuSeparator />
          <CreateProjectDialog
            trigger={
              <DropdownMenuItem onSelect={(event) => event.preventDefault()}>
                <FolderPlus className="size-4" aria-hidden />
                Создать проект
              </DropdownMenuItem>
            }
          />
        </DropdownMenuContent>
      </DropdownMenu>

      {projects.length === 0 ? (
        <CreateProjectDialog
          trigger={
            <Button size="sm" className="w-full">
              <FolderPlus aria-hidden />
              Создать первый проект
            </Button>
          }
        />
      ) : null}
    </div>
  );
}
