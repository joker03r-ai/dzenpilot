'use client';

import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react';

import {
  DEFAULT_APPEARANCE,
  STORAGE_KEY,
  applyAppearance,
  readStoredAppearance,
  resolveMode,
  type AppearanceSettings,
} from '@/lib/theme';

interface AppearanceContextValue {
  settings: AppearanceSettings;
  resolvedMode: 'light' | 'dark';
  update: (patch: Partial<AppearanceSettings>) => void;
  reset: () => void;
  ready: boolean;
}

const AppearanceContext = createContext<AppearanceContextValue | null>(null);

export function AppearanceProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AppearanceSettings>(DEFAULT_APPEARANCE);
  const [resolvedMode, setResolvedMode] = useState<'light' | 'dark'>('light');
  const [ready, setReady] = useState(false);

  useEffect(() => {
    const stored = readStoredAppearance();
    setSettings(stored);
    applyAppearance(stored);
    setResolvedMode(resolveMode(stored.mode));
    setReady(true);
  }, []);

  // Системная тема может смениться, пока страница открыта
  useEffect(() => {
    if (settings.mode !== 'system' || typeof window === 'undefined') return;

    const media = window.matchMedia('(prefers-color-scheme: dark)');
    const onChange = () => {
      applyAppearance(settings);
      setResolvedMode(resolveMode(settings.mode));
    };
    media.addEventListener('change', onChange);
    return () => media.removeEventListener('change', onChange);
  }, [settings]);

  const update = useCallback((patch: Partial<AppearanceSettings>) => {
    setSettings((current) => {
      const next = { ...current, ...patch };
      applyAppearance(next);
      setResolvedMode(resolveMode(next.mode));
      try {
        window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // Приватный режим браузера может запрещать хранилище — настройки
        // применятся, но не переживут перезагрузку страницы
      }
      return next;
    });
  }, []);

  const reset = useCallback(() => {
    applyAppearance(DEFAULT_APPEARANCE);
    setSettings(DEFAULT_APPEARANCE);
    setResolvedMode(resolveMode(DEFAULT_APPEARANCE.mode));
    try {
      window.localStorage.removeItem(STORAGE_KEY);
    } catch {
      // см. выше
    }
  }, []);

  const value = useMemo(
    () => ({ settings, resolvedMode, update, reset, ready }),
    [settings, resolvedMode, update, reset, ready],
  );

  return <AppearanceContext.Provider value={value}>{children}</AppearanceContext.Provider>;
}

export function useAppearance(): AppearanceContextValue {
  const context = useContext(AppearanceContext);
  if (!context) {
    throw new Error('useAppearance используется вне AppearanceProvider');
  }
  return context;
}
