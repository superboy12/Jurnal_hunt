// API client using axios with proxy to backend or remote API
import axios from 'axios'

const baseURL = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL.replace(/\/+$/, '')}/api`
  : '/api'

const api = axios.create({
  baseURL,
  timeout: 120000,
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    console.error('API Error:', err.response?.data || err.message)
    return Promise.reject(err)
  }
)

export default api

// ── Types ────────────────────────────────────────────────────────────

export interface InterpretedCommand {
  topic: string
  keywords: string[]
  synonyms: string[]
  language?: string
  year_from?: number
  year_to?: number
  max_results: number
  indexing_target?: string
  sinta_rank_min?: number
  sinta_rank_max?: number
  publication_type?: string
  open_access_only: boolean
  require_doi: boolean
  require_pdf: boolean
  sources: string[]
  interpretation_notes: string
}

export interface SearchSourceLog {
  source_name: string
  status: string
  articles_found: number
  error_message?: string
  started_at?: string
  completed_at?: string
  request_count: number
}

export interface SearchSummary {
  id: string
  user_command: string
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled'
  total_found: number
  total_after_dedup: number
  total_verified: number
  total_open_access: number
  error_message?: string
  created_at: string
  started_at?: string
  completed_at?: string
  source_logs: SearchSourceLog[]
}

export interface Author {
  name: string
  affiliation?: string
  orcid?: string
  order: number
}

export interface Article {
  id: string
  doi?: string
  title: string
  abstract?: string
  year?: number
  publication_date?: string
  journal_name?: string
  publisher?: string
  volume?: string
  issue?: string
  pages?: string
  language?: string
  keywords: string[]
  publication_type?: string
  is_open_access?: boolean
  open_access_url?: string
  pdf_url?: string
  article_url?: string
  sci_hub_url?: string
  citation_count?: number
  subject_category?: string
  sources: string[]
  verification_status?: string
  authors: Author[]
}

export interface SearchArticle {
  article: Article
  relevance_score: number
  relevance_reason?: string
  rank?: number
  source_found_in: string[]
  sinta_rank?: number
  is_scopus?: boolean
  scimago_quartile?: string
  sjr_score?: number
  scimago_url?: string
  sci_hub_url?: string
  subject_category?: string
}

export interface PaginatedArticles {
  total: number
  page: number
  page_size: number
  pages: number
  items: SearchArticle[]
  available_categories?: string[]
  category_counts?: Record<string, number>
}

export interface Bookmark {
  id: string
  article_id: string
  project_id?: string
  status: string
  notes?: string
  created_at: string
  article?: Article
}

export interface Project {
  id: string
  name: string
  description?: string
  created_at: string
}

export interface HealthCheck {
  status: string
  version: string
  database: string
  ai_provider: string
  available_sources: string[]
}

export interface Stats {
  total_searches: number
  total_articles: number
  total_journals: number
  total_bookmarks: number
  open_access_articles: number
}

// ── API Functions ─────────────────────────────────────────────────────

export const interpretCommand = (command: string, preset?: string | string[]) => {
  const payload: any = { command }
  if (Array.isArray(preset)) {
    payload.presets = preset
  } else if (preset) {
    payload.preset = preset
  }
  return api.post<InterpretedCommand>('/interpret-command', payload)
}

export const startSearch = (command: string, parameters: InterpretedCommand) =>
  api.post<SearchSummary>('/search', { command, parameters })

export const getSearch = (id: string) =>
  api.get<SearchSummary>(`/search/${id}`)

export const getSearchResults = (
  id: string,
  params: {
    page?: number
    page_size?: number
    sort_by?: string
    order?: string
    open_access_only?: boolean
    min_score?: number
    sinta_rank?: number
    scopus_only?: boolean
    indexing_target?: string
    category?: string
    categories?: string
  }
) => api.get<PaginatedArticles>(`/search/${id}/results`, { params })

export const cancelSearch = (id: string) =>
  api.post(`/search/${id}/cancel`)

export const getHistory = (limit?: number) =>
  api.get<SearchSummary[]>('/history', { params: { limit } })

export const getArticle = (id: string) =>
  api.get<Article>(`/articles/${id}`)

export const saveArticle = (articleId: string, data: { project_id?: string; status?: string; notes?: string }) =>
  api.post<Bookmark>(`/articles/${articleId}/save`, data)

export const getSavedArticles = (projectId?: string) =>
  api.get<Bookmark[]>('/saved-articles', { params: { project_id: projectId } })

export const updateBookmark = (id: string, data: { status?: string; notes?: string; project_id?: string }) =>
  api.patch<Bookmark>(`/saved-articles/${id}`, data)

export const deleteBookmark = (id: string) =>
  api.delete(`/saved-articles/${id}`)

export const getProjects = () =>
  api.get<Project[]>('/projects')

export const createProject = (data: { name: string; description?: string }) =>
  api.post<Project>('/projects', data)

export const getHealth = () =>
  api.get<HealthCheck>('/health')

export const getStats = () =>
  api.get<Stats>('/stats')

export const getCitation = (articleId: string, format: string) =>
  api.get<{ citation: string; format: string }>(`/articles/${articleId}/citation`, { params: { format } })

export interface Journal {
  id: string
  name: string
  issn?: string
  eissn?: string
  publisher?: string
  is_scopus_indexed?: boolean
  scopus_coverage_start?: number
  scopus_coverage_end?: number
  sinta_rank?: number
  sinta_id?: string
  sinta_profile_url?: string
  scopus_source_url?: string
  scimago_quartile?: string
  sjr_score?: number
  scimago_url?: string
  h_index?: number
  doaj_url?: string
  is_open_access?: boolean
  apc_amount?: number
  apc_currency?: string
  verification_source?: string
  verified_at?: string
}

export interface AIModel {
  id: string
  name: string
  provider: string
  badge: string
  context_window: string
  description: string
}

export const DEFAULT_AI_MODELS: AIModel[] = [
  { id: "gemini-3.5-flash", name: "Gemini 3.5 Flash", provider: "Google Gemini", badge: "Gemini 3.5 · Default SOTA Fast", context_window: "1M tokens", description: "Default production-grade frontier Gemini 3.5 model for natural language queries and synthesis." },
  { id: "gemini-3.5-flash-lite", name: "Gemini 3.5 Flash-Lite", provider: "Google Gemini", badge: "Gemini 3.5 · High Efficiency", context_window: "1M tokens", description: "Lightweight Gemini 3.5 model for rapid academic keyword extraction and filter parsing." },
  { id: "gemini-3-flash-preview", name: "Gemini 3 Flash Preview", provider: "Google Gemini", badge: "Gemini 3.0 · Next-Gen Multimodal", context_window: "1M tokens", description: "Next-gen multimodal Gemini 3 model optimized for academic search interpretation and extraction." },
  { id: "gemini-3.1-pro-preview", name: "Gemini 3.1 Pro Preview", provider: "Google Gemini", badge: "Gemini 3.1 · Frontier Reasoning", context_window: "2M tokens", description: "Gemini 3.1 frontier reasoning engine for complex scientific synthesis and comparative analysis." },
  { id: "gemini-3.1-flash-lite", name: "Gemini 3.1 Flash-Lite", provider: "Google Gemini", badge: "Gemini 3.1 · High Throughput", context_window: "1M tokens", description: "Optimized Gemini 3.1 high-speed model for instant citation scoring and batch processing." },
  { id: "gemini-3.6-flash", name: "Gemini 3.6 Flash", provider: "Google Gemini", badge: "Gemini 3.6 · SINTA & Citation", context_window: "1M tokens", description: "Enhanced Gemini 3.6 generation model optimized for Indonesian SINTA and bibliographic integrity." },
  { id: "gemini-3.7-flash", name: "Gemini 3.7 Flash", provider: "Google Gemini", badge: "Gemini 3.7 · Logical Deduction", context_window: "1M tokens", description: "Gemini 3.7 reasoning model for research gap discovery and methodology validation." },
  { id: "gemini-3.8-flash", name: "Gemini 3.8 Flash", provider: "Google Gemini", badge: "Gemini 3.8 · Literature Synthesizer", context_window: "1M tokens", description: "Advanced Gemini 3.8 generation authoring engine for publication-grade literature review synthesis." },
  { id: "gemini-4-argon", name: "Gemini 4 Argon", provider: "Google Gemini", badge: "Gemini 4.0 · Ultimate Frontier", context_window: "2M tokens", description: "Google DeepMind's flagship Gemini 4.0 next-generation frontier architecture for comprehensive scientific research." },
  { id: "gemini-2.5-pro", name: "Gemini 2.5 Pro", provider: "Google Gemini", badge: "Gemini 2.5 · Deep Reasoning", context_window: "2M tokens", description: "Advanced Gemini 2.5 reasoning architecture for rigorous scientific deduction." },
  { id: "gemini-2.5-flash", name: "Gemini 2.5 Flash", provider: "Google Gemini", badge: "Gemini 2.5 · High Throughput", context_window: "1M tokens", description: "Gemini 2.5 generation high-speed model for academic abstract extraction." },
  { id: "gemini-2.5-flash-lite", name: "Gemini 2.5 Flash-Lite", provider: "Google Gemini", badge: "Gemini 2.5 · Efficient", context_window: "1M tokens", description: "Low-latency Gemini 2.5 processing for real-time natural language query parsing." },
  { id: "gemini-flash-latest", name: "Gemini 1.5 Flash (Latest)", provider: "Google Gemini", badge: "Gemini 1.5 · Production Stable", context_window: "1M tokens", description: "Google Gemini 1.5 production endpoint for reliable metadata classification and search parsing." },
  { id: "gemini-pro-latest", name: "Gemini 1.5 Pro (Latest)", provider: "Google Gemini", badge: "Gemini 1.5 · Deep Analysis", context_window: "2M tokens", description: "Long-context Gemini 1.5 model for comprehensive multi-paper analysis." },
  { id: "gemini-flash-lite-latest", name: "Gemini 1.5 Flash-Lite", provider: "Google Gemini", badge: "Gemini 1.5 · Low Latency", context_window: "1M tokens", description: "Gemini 1.5 ultra-fast lightweight model for instant keyword expansion." },
]

export interface ModelsResponse {
  default_model: string
  models: AIModel[]
  active_gemini_keys: number
  ai_provider: string
}

export interface AISummary {
  objective: string
  methodology: string
  findings: string
  implications: string
  key_takeaways: string[]
  recommended_keywords: string[]
}

export interface LiteratureReviewResponse {
  topic: string
  model: string
  literature_review: string
}

export const getModels = () =>
  api.get<ModelsResponse>('/models')

export const getArticleAISummary = (articleId: string, model?: string) =>
  api.post<AISummary>(`/articles/${articleId}/ai-summary`, null, { params: { model } })

export const generateLiteratureReview = (searchId: string, model?: string) =>
  api.post<LiteratureReviewResponse>(`/search/${searchId}/ai-synthesis`, null, { params: { model } })

export const getExportUrl = (searchId: string, format: string) =>
  `/api/search/${searchId}/export/${format}`

export const getJournals = (params?: {
  search?: string
  sinta_rank?: number
  scopus_only?: boolean
  limit?: number
}) => api.get<Journal[]>('/journals', { params })

export const getJournal = (id: string) =>
  api.get<Journal>(`/journals/${id}`)

export interface ScopusSearchEngine {
  id: string
  name: string
  url: string
  api_status: string
  role: string
  description: string
  features: string[]
  badge: string
}

export interface ScopusVerificationSource {
  id: string
  name: string
  url: string
  role: string
  description: string
  verification_method: string
  badge: string
}

export interface OAPublisher {
  name: string
  url: string
  type: string
  scope: string
}

export interface ScopusDirectoryData {
  search_engines: ScopusSearchEngine[]
  scopus_verification: ScopusVerificationSource[]
  open_access_publishers: OAPublisher[]
  recommendations: {
    title: string
    steps: { step: number; source: string; action: string }[]
  }
}

export const getScopusDirectory = () =>
  api.get<ScopusDirectoryData>('/scopus/directory')

export const getArticleVerificationLinks = (articleId: string) =>
  api.get<{
    article_id: string
    title: string
    journal_name?: string
    doi?: string
    verification_links: Record<string, string>
  }>(`/articles/${articleId}/verification-links`)

// ── Title Search ──────────────────────────────────────────────────────

export interface TitleSearchResult {
  source: string
  doi: string
  title: string
  year?: number
  authors: string[]
  journal_name: string
  citation_count?: number
  is_open_access?: boolean
  open_access_url?: string
  sci_hub_url?: string
  abstract?: string
}

export interface TitleSearchResponse {
  query: string
  total: number
  results: TitleSearchResult[]
}

export const searchByTitle = (title: string, limit?: number) =>
  api.get<TitleSearchResponse>('/articles/search-by-title', { params: { title, limit } })

// ── Auto Access Resolve ───────────────────────────────────────────────

export const autoResolveAccess = (articleId: string) =>
  api.get<{ status: string; method: string; url?: string; doi?: string; message: string }>(`/articles/${articleId}/auto-resolve-access`)
