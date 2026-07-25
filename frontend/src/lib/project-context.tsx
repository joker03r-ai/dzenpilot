'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

const STORAGE_KEY = 'dzenpilot:current-project';

interface ProjectContextValue {
  projectId: string | null;
  setProjectId: (id: string | null) => void;
  ready: boolean;
}

const ProjectContext = createContext<ProjectContextValue | null>(null);

/**
 * Хранит выбранный проект между переходами и перезагрузками страницы.
 * Значение читается из localStorage только на клиенте, чтобы не ломать
 * серверный рендеринг Next.js.
 */
export function ProjectProvider({ children }: { children: React.ReactNode }) {
  const [projectId, setProjectIdState] = useState<string | null>(null);
  const [ready, setReady] = useState(false);

  useEffect(() => {
    try {
      setProjectIdState(window.localStorage.getItem(STORAGE_KEY));
    } catch {
      // Приватный режим браузера может запрещать localStorage — работаем без него
    }
    setReady(true);
  }, []);

  const setProjectId = useCallback((id: string | null) => {
    setProjectIdState(id);
    try {
      if (id) window.localStorage.setItem(STORAGE_KEY, id);
      else window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      // Значение просто не сохранится между сессиями
    }
  }, []);

  const value = useMemo(
    () => ({ projectId, setProjectId, ready }),
    [projectId, setProjectId, ready],
  );

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
}

export function useProjectContext(): ProjectContextValue {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProjectContext используется вне ProjectProvider');
  }
  return context;
}
