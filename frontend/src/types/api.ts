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

// ---------- Конкуренты ----------

export type CompetitorStatus = 'new' | 'analyzing' | 'analyzed' | 'error';
export type DataSource = 'manual' | 'csv_import' | 'public_page' | 'official_api' | 'ai_estimate';

export interface Competitor {
  id: string;
  project_id: string;
  name: string;
  url: string | null;
  description: string | null;
  niche: string | null;
  group_name: string | null;
  notes: string | null;

  subscribers_count: number | null;
  publications_count: number | null;
  avg_publish_interval_days: number | null;
  avg_views: number | null;
  max_views: number | null;
  min_views: number | null;
  avg_engagement_rate: number | null;
  avg_article_length: number | null;

  formats_used: { format: string; count: number }[];
  frequent_topics: { topic: string; count: number }[];
  popular_title_words: { word: string; count: number }[];
  media_usage: Record<string, string>;

  data_source: DataSource;
  status: CompetitorStatus;
  last_analyzed_at: string | null;
  created_at: string;
  updated_at: string;

  stored_publications: number;
  has_analysis: boolean;
}

export interface CompetitorInput {
  name: string;
  url?: string | null;
  description?: string | null;
  niche?: string | null;
  group_name?: string | null;
  notes?: string | null;
}

export interface Publication {
  id: string;
  competitor_id: string;
  title: string;
  url: string | null;
  published_at: string | null;
  views: number | null;
  reactions: number | null;
  comments_count: number | null;
  topic_guess: string | null;
  format: string | null;
  title_length: number | null;
  body_length: number | null;
  title_emotionality: number | null;
  has_numbers: boolean | null;
  has_question: boolean | null;
  has_cta: boolean | null;
  audience_guess: string | null;
  data_source: DataSource;
  created_at: string;
}

export interface PublicationInput {
  title: string;
  url?: string | null;
  published_at?: string | null;
  views?: number | null;
  reactions?: number | null;
  comments_count?: number | null;
  topic_guess?: string | null;
  format?: string | null;
}

export interface CsvImportResult {
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
  message: string;
}

export interface CompetitorAnalysis {
  id: string;
  competitor_id: string;
  summary: string | null;
  why_it_works: string | null;
  publish_rhythm: string | null;
  working_topics: string[];
  working_titles: string[];
  failed_posts: string[];
  formats: string[];
  strengths: string[];
  weaknesses: string[];
  content_gaps: string[];
  differentiation: string[];
  adaptable_ideas: string[];
  ai_provider: string | null;
  ai_model: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  cost_usd: number | null;
  created_at: string;
}

export interface CompareRequest {
  competitor_ids: string[];
  period_days: number;
}

export interface CompareRow {
  competitor_id: string;
  name: string;
  publish_interval_days: number | null;
  publications_in_period: number;
  avg_views: number | null;
  max_views: number | null;
  avg_engagement_rate: number | null;
  avg_article_length: number | null;
  best_topics: string[];
  title_style: string;
  dynamics_percent: number | null;
  rating: number;
  rating_reason: string;
}

export interface ComparePoint {
  name: string;
  avg_views: number | null;
  publications: number;
  engagement: number | null;
}

export interface CompareResponse {
  period_days: number;
  rows: CompareRow[];
  chart: ComparePoint[];
  note: string;
}

// ---------- Темы ----------

export type TopicStatus =
  | 'suggested'
  | 'saved'
  | 'planned'
  | 'in_progress'
  | 'used'
  | 'hidden';
export type TopicOrigin = 'ai_search' | 'manual' | 'csv_import' | 'competitor_gap';
export type CompetitionLevel = 'low' | 'medium' | 'high';
export type TopicGoal = 'views' | 'subscribers' | 'leads' | 'income';

export interface ScoreBreakdown {
  interest: number;
  growth: number;
  competition: number;
  seasonality: number;
  competitor_success: number;
  series_potential: number;
  commercial: number;
  difficulty: number;
  decay_risk: number;
  audience_fit: number;
}

export interface TopicScore {
  total_score: number;
  verdict: string;
  explanation: string;
  breakdown: ScoreBreakdown;
  formula_version: string;
  created_at: string;
}

export interface Topic {
  id: string;
  project_id: string;
  title: string;
  description: string | null;
  niche: string | null;
  audience: string | null;
  region: string | null;
  format: string | null;
  competition_level: CompetitionLevel | null;
  seasonality: string | null;
  recommended_length: number | null;

  title_variants: string[];
  reader_questions: string[];
  series_ideas: string[];
  monetization: string[];
  risks: string[];
  sources: string[];

  status: TopicStatus;
  origin: TopicOrigin;
  created_at: string;
  updated_at: string;

  score: TopicScore | null;
}

export interface TopicSearchRequest {
  niche: string;
  audience?: string | null;
  region?: string | null;
  format?: string | null;
  period_days: number;
  forbidden_topics: string[];
  competition_level?: CompetitionLevel | null;
  goal: TopicGoal;
  count: number;
}

export interface TopicSearchResponse {
  created: number;
  topics: Topic[];
  message: string;
  sources_note: string;
}

// ---------- Статьи ----------

export type ArticleStatus =
  | 'draft'
  | 'review'
  | 'ready'
  | 'scheduled'
  | 'published'
  | 'failed'
  | 'archived';

export type ImproveAction =
  | 'shorten'
  | 'expand'
  | 'simplify'
  | 'expertise'
  | 'change_tone'
  | 'rewrite_fragment'
  | 'add_examples'
  | 'remove_repeats'
  | 'check_structure'
  | 'check_title'
  | 'check_clickability'
  | 'check_readability'
  | 'find_unverified'
  | 'image_description'
  | 'image_prompts';

export interface ArticleCreateInput {
  title: string;
  topic_id?: string | null;
  goal?: string | null;
  audience?: string | null;
  tone?: string | null;
  target_length: number;
  keywords: string[];
  region?: string | null;
  required_facts: string[];
  source_links: string[];
  products: string[];
  forbidden_words: string[];
  cta?: string | null;
}

export interface OutlineSection {
  heading: string;
  points: string[];
}

export interface OutlineResponse {
  title_variants: string[];
  lead: string;
  sections: OutlineSection[];
  conclusion: string;
  cta: string;
  message: string;
}

export interface Article {
  id: string;
  project_id: string;
  topic_id: string | null;
  title: string;
  lead: string | null;
  body_markdown: string | null;
  outline: OutlineSection[];
  keywords: string[];
  cta: string | null;
  goal: string | null;
  audience: string | null;
  tone: string | null;
  target_length: number | null;
  status: ArticleStatus;
  status_label: string;
  checklist: Record<string, unknown>;
  generation_input: Record<string, unknown>;
  planned_publish_at: string | null;
  published_at: string | null;
  published_url: string | null;
  ai_provider: string | null;
  ai_model: string | null;
  tokens_input: number | null;
  tokens_output: number | null;
  cost_usd: number | null;
  word_count: number | null;
  reading_time_min: number | null;
  created_at: string;
  updated_at: string;
  versions_count: number;
}

export interface ArticleListItem {
  id: string;
  title: string;
  status: ArticleStatus;
  status_label: string;
  word_count: number | null;
  reading_time_min: number | null;
  planned_publish_at: string | null;
  published_at: string | null;
  updated_at: string;
  created_at: string;
}

export interface ArticleVersion {
  id: string;
  article_id: string;
  version_number: number;
  title: string | null;
  lead: string | null;
  change_note: string | null;
  created_at: string;
}

export interface ImproveResponse {
  action: string;
  action_label: string;
  changes_text: boolean;
  result: string;
  applied: boolean;
  message: string;
}

export interface ChecklistItem {
  code: string;
  label: string;
  done: boolean;
  hint: string;
}

export interface ChecklistResponse {
  items: ChecklistItem[];
  ready: boolean;
  message: string;
}

// ---------- Календарь ----------

export type CalendarView = 'day' | 'week' | 'month' | 'list';
export type RepeatRule = 'none' | 'daily' | 'weekly' | 'biweekly' | 'monthly';
export type ScheduleStatus =
  | 'planned'
  | 'ready'
  | 'publishing'
  | 'published'
  | 'failed'
  | 'cancelled';

export interface ScheduleItem {
  id: string;
  project_id: string;
  article_id: string;
  article_title: string;
  article_status: string;
  channel_id: string | null;
  scheduled_at: string;
  local_datetime: string;
  local_date: string;
  local_time: string;
  timezone: string;
  timezone_label: string;
  repeat_rule: string | null;
  note: string | null;
  confirmed_by_user: boolean;
  status: ScheduleStatus;
  status_label: string;
  attempts: number;
  created_at: string;
}

export interface CalendarResponse {
  view: CalendarView;
  period_start: string;
  period_end: string;
  timezone: string;
  timezone_label: string;
  items: ScheduleItem[];
  note: string;
}

export interface CalendarOptions {
  default: string;
  popular: TimezoneOption[];
  all: string[];
  repeat_rules: { value: RepeatRule; label: string }[];
}

export interface ScheduleCreateInput {
  article_id: string;
  local_datetime: string;
  timezone: string;
  channel_id?: string | null;
  repeat_rule: RepeatRule;
  repeat_count: number;
  note?: string | null;
}

// ---------- Публикации ----------

export type PublicationMethod =
  | 'official_api'
  | 'partner_service'
  | 'manual_export'
  | 'copy_formatted'
  | 'file_export'
  | 'reminder';

export type PublicationResult = 'success' | 'error' | 'skipped';

export interface PreflightCheck {
  code: string;
  label: string;
  passed: boolean;
  detail: string;
}

export interface PreflightResponse {
  checks: PreflightCheck[];
  ready: boolean;
  available_methods: { value: PublicationMethod; label: string }[];
  message: string;
}

export interface PublishResponse {
  log_id: string;
  method: PublicationMethod;
  method_label: string;
  result: PublicationResult;
  published_url: string | null;
  error_message: string | null;
  can_retry: boolean;
  payload: Record<string, string>;
  message: string;
  next_step: string;
}

export interface PublicationLogItem {
  id: string;
  article_id: string;
  article_title: string;
  scheduled_publication_id: string | null;
  method: PublicationMethod;
  method_label: string;
  result: PublicationResult;
  result_label: string;
  published_url: string | null;
  error_message: string | null;
  attempt_number: number;
  response_payload: Record<string, unknown>;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ExportResponse {
  format: string;
  filename: string;
  content: string;
  message: string;
}

// ---------- Аналитика ----------

export type AnalyticsPeriod = '7d' | '30d' | '90d' | 'custom';

export interface MetricValue {
  value: number | null;
  change_percent: number | null;
  available: boolean;
  note: string | null;
}

export interface AnalyticsOverview {
  period_start: string;
  period_end: string;
  published_articles: MetricValue;
  total_views: MetricValue;
  avg_views: MetricValue;
  subscribers: MetricValue;
  avg_engagement: MetricValue;
  publish_frequency: MetricValue;
  data_source_note: string;
}

export interface TimeseriesPoint {
  day: string;
  views: number | null;
  subscribers: number | null;
  published: number;
}

export interface TimeseriesResponse {
  points: TimeseriesPoint[];
  has_data: boolean;
  note: string;
}

export interface WeekdayStat {
  weekday: number;
  label: string;
  published: number;
  avg_views: number | null;
}

export interface HourStat {
  hour: number;
  label: string;
  published: number;
  avg_views: number | null;
}

export interface TopArticle {
  article_id: string;
  title: string;
  views: number | null;
  published_at: string | null;
  reading_time_min: number | null;
}

export interface TopTopic {
  title: string;
  articles: number;
  avg_views: number | null;
}

export interface TopTitleWord {
  word: string;
  count: number;
  avg_views: number | null;
}

export interface AnalyticsTop {
  articles: TopArticle[];
  topics: TopTopic[];
  title_words: TopTitleWord[];
  note: string;
}

export interface CompetitorComparisonRow {
  name: string;
  avg_views: number | null;
  publications: number;
  is_you: boolean;
}

export interface AnalyticsComparison {
  rows: CompetitorComparisonRow[];
  note: string;
}

export interface CsvImportSummary {
  created: number;
  updated: number;
  skipped: number;
  errors: string[];
  message: string;
}
