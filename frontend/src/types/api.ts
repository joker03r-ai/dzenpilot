/** Типы данных, которые отдаёт backend. */

export type ProjectStatus = 'active' | 'paused' | 'archived';
export type UserRole = 'owner' | 'editor' | 'author' | 'viewer';
export type IntegrationKind =
  | 'anthropic'
  | 'openai'
  | 'gemini'
  | 'yandex_metrika'
  | 'telegram'
  | 'email'
  | 'webhook'
  | 'storage'
  | 'dzen_channel'
  | 'csv';
export type AIProviderName = 'anthropic' | 'openai' | 'gemini' | 'local';

export interface ApiError {
  code: string;
  message: string;
  details?: unknown;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface MessageResponse {
  message: string;
}

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  last_login_at: string | null;
  created_at: string;
}

export interface WorkspaceShort {
  id: string;
  name: string;
}

export interface AuthResponse {
  user: User;
  workspaces: WorkspaceShort[];
  default_project_id: string | null;
  message: string;
}

export interface Project {
  id: string;
  workspace_id: string;
  name: string;
  description: string | null;
  niche: string | null;
  target_audience: string | null;
  tone_of_voice: string | null;
  region: string | null;
  timezone: string;
  dzen_channel_url: string | null;
  status: ProjectStatus;
  settings: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DashboardCounters {
  competitors: number;
  topics: number;
  articles: number;
  scheduled: number;
  published: number;
}

export interface SetupStep {
  code: string;
  title: string;
  description: string;
  done: boolean;
  progress: number;
  action_label: string;
  action_href: string;
}

export interface ActivityItem {
  kind: string;
  title: string;
  subtitle: string | null;
  href: string | null;
  level: 'info' | 'success' | 'warning' | 'error';
  happened_at: string | null;
  entity_id: string | null;
}

export interface Dashboard {
  project_id: string;
  project_name: string;
  greeting: string;
  user_name: string | null;
  counters: DashboardCounters;
  setup_progress: number;
  steps: SetupStep[];
  activity: ActivityItem[];
}

export interface Integration {
  id: string;
  project_id: string;
  kind: IntegrationKind;
  kind_label: string;
  title: string;
  key_mask: string;
  has_credentials: boolean;
  config: Record<string, unknown>;
  is_active: boolean;
  last_check_at: string | null;
  last_check_result: string | null;
  created_at: string;
}

export interface IntegrationTestResult {
  ok: boolean;
  message: string;
  checked_at: string;
}

export interface ModelInfo {
  id: string;
  title: string;
  recommended: boolean;
}

export interface ProviderInfo {
  provider: AIProviderName;
  title: string;
  available: boolean;
  description: string;
  models: ModelInfo[];
}

export interface AISettings {
  id: string | null;
  project_id: string;
  provider: AIProviderName;
  model: string;
  temperature: number;
  max_tokens: number;
  key_configured: boolean;
}

export interface AITestResponse {
  ok: boolean;
  provider: string;
  model: string;
  text: string;
  tokens_input: number;
  tokens_output: number;
}

export interface TimezoneOption {
  value: string;
  label: string;
  offset: string;
}
