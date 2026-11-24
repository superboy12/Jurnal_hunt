import React, { useState, useEffect, useRef } from 'react'
import {
  interpretCommand, startSearch, getSearch, getSearchResults,
  cancelSearch, getExportUrl, getModels, generateLiteratureReview,
  searchByTitle,
  type InterpretedCommand, type SearchSummary, type SearchArticle,
  type PaginatedArticles, type AIModel, type TitleSearchResult
} from '../api'
import ArticleTable from '../components/ArticleTable'
import ArticleDetail from '../components/ArticleDetail'
import {
  Search, Send, ChevronDown, ChevronUp, X, Download, Sliders,
  CheckCircle, AlertCircle, Clock, Sparkles, Cpu, Copy, BookOpen, Key,
  FileText, Unlock, ExternalLink
} from 'lucide-react'
import toast from 'react-hot-toast'
import { useSearchParams } from 'react-router-dom'

const PRESETS = [
  { id: 'scopus_only', label: '🔶 Scopus Only' },
  { id: 'sinta_only', label: '🟢 SINTA Only' },
  { id: 'scopus_sinta', label: '🔷 Scopus + SINTA' },
  { id: 'cyber_security', label: '🛡️ Keamanan Siber / Cyber Security' },
  { id: 'it_computing', label: '💻 IT & Komputer' },
  { id: 'law_policy', label: '⚖️ Hukum & Kebijakan' },
  { id: 'open_access', label: '🔓 Open Access' },
  { id: 'community_service', label: '🤝 Jurnal Pengabdian' },
  { id: 'latest_research', label: '⚡ Latest Research' },
  { id: 'literature_review', label: '📚 Literature Review' },
]

const EXAMPLE_COMMANDS = [
  'Cari artikel SINTA atau Scopus kategori Keamanan Siber tentang pemblokiran judi online via DNS atau AI',
  'Cari artikel tentang pemblokiran judi online fokus teknologi IT/DNS (bukan aspek hukum)',
  'Cari artikel Scopus tentang cybersecurity dan machine learning yang terbit dalam 3 tahun terakhir',
  'Cari jurnal SINTA 2 sampai SINTA 4 yang membahas cloud computing dan network security',
  'Cari 20 artikel tentang Generative AI untuk otomatisasi administrasi pemerintahan, tahun 2022–2026',
]

type SortOption = { value: string; label: string }
const SORT_OPTIONS: SortOption[] = [
  { value: 'relevance', label: 'Relevansi' },
  { value: 'year', label: 'Tahun' },
  { value: 'citations', label: 'Sitasi' },
  { value: 'title', label: 'Judul' },
]

export default function SearchPage() {
  const [searchParams, setSearchParams] = useSearchParams()
  const [command, setCommand] = useState('')
  const [selectedPresets, setSelectedPresets] = useState<string[]>([])
  const [interpreted, setInterpreted] = useState<InterpretedCommand | null>(null)
  const [showFilters, setShowFilters] = useState(false)
  const [isInterpreting, setIsInterpreting] = useState(false)
  const [currentSearch, setCurrentSearch] = useState<SearchSummary | null>(null)
  const [results, setResults] = useState<PaginatedArticles | null>(null)
  const [page, setPage] = useState(1)
  const [sortBy, setSortBy] = useState('relevance')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [oaOnly, setOaOnly] = useState(false)
  const [minScore, setMinScore] = useState(0)
  const [sintaFilter, setSintaFilter] = useState<'all' | 'both' | '1' | '2' | '3' | '4' | '5' | '6' | 'scopus'>('all')
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])
  const [selectedArticle, setSelectedArticle] = useState<SearchArticle | null>(null)
  const [isSearching, setIsSearching] = useState(false)
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null)

  // 15 AI Models State
  const [models, setModels] = useState<AIModel[]>([])
  const [selectedModel, setSelectedModel] = useState('gemini-3-flash-preview')
  const [activeKeysCount, setActiveKeysCount] = useState(3)

  // Literature Review Synthesis State
  const [synthesisReview, setSynthesisReview] = useState<string | null>(null)
  const [isSynthesizing, setIsSynthesizing] = useState(false)
  const [showSynthesisModal, setShowSynthesisModal] = useState(false)

  // Search Mode: 'topic' (AI command) or 'title' (direct title search)
  const [searchMode, setSearchMode] = useState<'topic' | 'title'>('topic')
  const [titleQuery, setTitleQuery] = useState('')
  const [titleResults, setTitleResults] = useState<TitleSearchResult[]>([])
  const [titleSearching, setTitleSearching] = useState(false)
  const [titleTotal, setTitleTotal] = useState(0)

  // Load models on mount
  useEffect(() => {
    getModels()
      .then(res => {
        setModels(res.data.models)
        if (res.data.default_model) {
          setSelectedModel(res.data.default_model)
        }
        if (res.data.active_gemini_keys) {
          setActiveKeysCount(res.data.active_gemini_keys)
        }
      })
      .catch(console.error)
  }, [])

  // Load existing search from URL
  useEffect(() => {
    const id = searchParams.get('id')
    if (id) {
      loadSearch(id)
    }
  }, [])

  const loadSearch = async (id: string) => {
    try {
      const res = await getSearch(id)
      setCurrentSearch(res.data)
      if (res.data.status === 'completed' || res.data.status === 'failed') {
        fetchResults(id)
      } else if (res.data.status === 'running' || res.data.status === 'pending') {
        startPolling(id)
      }
    } catch (e) {
      console.error(e)
    }
  }

  const startPolling = (searchId: string) => {
    setIsSearching(true)
    if (pollingRef.current) clearInterval(pollingRef.current)
    pollingRef.current = setInterval(async () => {
      try {
        const res = await getSearch(searchId)
        setCurrentSearch(res.data)
        if (res.data.status === 'completed' || res.data.status === 'failed' || res.data.status === 'cancelled') {
          clearInterval(pollingRef.current!)
          pollingRef.current = null
          setIsSearching(false)
          if (res.data.status === 'completed') {
            fetchResults(searchId)
            toast.success(`Pencarian selesai! Ditemukan ${res.data.total_after_dedup} artikel.`)
          } else if (res.data.status === 'failed') {
            toast.error(`Pencarian gagal: ${res.data.error_message}`)
          }
        }
      } catch (e) {
        console.error(e)
      }
    }, 2000)
  }

  useEffect(() => () => { if (pollingRef.current) clearInterval(pollingRef.current) }, [])

  const fetchResults = async (searchId: string) => {
    try {
      const sinta_rank = ['1', '2', '3', '4', '5', '6'].includes(sintaFilter) ? parseInt(sintaFilter) : undefined
      const scopus_only = sintaFilter === 'scopus' ? true : undefined
      const indexing_target = sintaFilter === 'both' ? 'both' : undefined
      const categories = selectedCategories.length > 0 ? selectedCategories.join(',') : undefined
      const res = await getSearchResults(searchId, {
        page, page_size: 20, sort_by: sortBy, order: sortOrder,
        open_access_only: oaOnly, min_score: minScore,
        sinta_rank, scopus_only, indexing_target, categories,
      })
      setResults(res.data)
    } catch (e) {
      console.error(e)
    }
  }

  useEffect(() => {
    if (currentSearch?.status === 'completed') {
      fetchResults(currentSearch.id)
    }
  }, [page, sortBy, sortOrder, oaOnly, minScore, sintaFilter, selectedCategories])

  const handleInterpret = async () => {
    if (!command.trim()) return
    setIsInterpreting(true)
    try {
      const res = await interpretCommand(command, selectedPresets.length > 0 ? selectedPresets : undefined)
      setInterpreted(res.data)
      setShowFilters(true)
      toast.success('Perintah berhasil diinterpretasi!')
    } catch (e) {
      console.error(e)
      toast.error('Gagal menginterpretasi perintah')
    } finally {
      setIsInterpreting(false)
    }
  }

  const handleSearch = async () => {
    if (!command.trim()) return
    let params = interpreted
    if (!params) {
      setIsInterpreting(true)
      try {
        const res = await interpretCommand(command, selectedPresets.length > 0 ? selectedPresets : undefined)
        params = res.data
        setInterpreted(res.data)
      } catch {
        toast.error('Gagal menginterpretasi perintah')
        setIsInterpreting(false)
        return
      } finally {
        setIsInterpreting(false)
      }
    }

    try {
      setIsSearching(true)
      const res = await startSearch(command, params)
      setCurrentSearch(res.data)
      setResults(null)
      setSelectedArticle(null)
      setSearchParams({ id: res.data.id })
      startPolling(res.data.id)
    } catch (e) {
      console.error(e)
      toast.error('Gagal memulai pencarian')
      setIsSearching(false)
    }
  }

  const handleCancel = async () => {
    if (!currentSearch) return
    try {
      await cancelSearch(currentSearch.id)
      if (pollingRef.current) clearInterval(pollingRef.current)
      setIsSearching(false)
      toast.success('Pencarian dibatalkan')
    } catch (e) {
      console.error(e)
    }
  }

  const handlePresetToggle = (presetId: string) => {
    setSelectedPresets(prev => {
      let next = prev.includes(presetId)
        ? prev.filter(p => p !== presetId)
        : [...prev, presetId]

      // Smart mutual exclusion for indexing targets
      if (presetId === 'scopus_sinta' && next.includes('scopus_sinta')) {
        next = next.filter(p => p !== 'scopus_only' && p !== 'sinta_only')
      } else if ((presetId === 'scopus_only' || presetId === 'sinta_only') && next.includes(presetId)) {
        if (next.includes('scopus_only') && next.includes('sinta_only')) {
          next = next.filter(p => p !== 'scopus_only' && p !== 'sinta_only').concat('scopus_sinta')
        } else {
          next = next.filter(p => p !== 'scopus_sinta')
        }
      }
      return next
    })
    setInterpreted(null)
  }

  const handleExport = (format: string) => {
    if (!currentSearch) return
    window.open(getExportUrl(currentSearch.id, format), '_blank')
  }

  const handleSynthesize = async () => {
    if (!currentSearch) return
    setIsSynthesizing(true)
    setShowSynthesisModal(true)
    try {
      const res = await generateLiteratureReview(currentSearch.id, selectedModel)
      setSynthesisReview(res.data.literature_review)
      toast.success('Sintesis tinjauan pustaka berhasil dibuat!')
    } catch (e) {
      console.error(e)
      toast.error('Gagal membuat sintesis tinjauan pustaka')
    } finally {
      setIsSynthesizing(false)
    }
  }

  const copySynthesis = () => {
    if (synthesisReview) {
      navigator.clipboard.writeText(synthesisReview)
      toast.success('Tinjauan pustaka disalin ke clipboard!')
    }
  }

  const statusProgress = () => {
    if (!currentSearch) return 0
    const logs = currentSearch.source_logs || []
    if (!logs.length) return 10
    const done = logs.filter(l => l.status === 'completed' || l.status === 'failed' || l.status === 'skipped').length
    return Math.round((done / logs.length) * 90) + 10
  }

  const handleTitleSearch = async () => {
    if (!titleQuery.trim()) return
    setTitleSearching(true)
    try {
      const res = await searchByTitle(titleQuery.trim(), 15)
      setTitleResults(res.data.results || [])
      setTitleTotal(res.data.total || 0)
      if (!res.data.results || res.data.results.length === 0) {
        toast('Tidak ada artikel yang cocok dengan judul tersebut', { icon: 'ℹ️' })
      } else {
        toast.success(`Ditemukan ${res.data.results.length} artikel berdasarkan judul!`)
      }
    } catch (err: any) {
      console.error(err)
      toast.error('Gagal mencari artikel berdasarkan judul')
    } finally {
      setTitleSearching(false)
    }
  }

  return (
    <div className="page-container" style={{ padding: '28px 36px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Page Title & AI Model Selector Header */}
      <div style={{ marginBottom: 20 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 14 }}>
          <div>
            <h1 style={{ fontSize: 24, fontWeight: 700, color: 'var(--text-primary)', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
              Intelligent Academic Journal Discovery
            </h1>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Pencarian jurnal ilmiah otomatis berbasis bahasa alami dengan verifikasi Scopus & SINTA
            </p>
          </div>

          {/* AI Model & Key Rotation Selector */}
          <div className="glass-panel" style={{
            padding: '8px 14px', borderRadius: 12, display: 'flex', alignItems: 'center', gap: 10,
            background: 'rgba(99, 102, 241, 0.08)', border: '1px solid rgba(99, 102, 241, 0.3)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
              <Cpu size={16} color="var(--primary-light)" />
              <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-primary)' }}>AI Model:</span>
            </div>

            <select
              value={selectedModel}
              onChange={e => setSelectedModel(e.target.value)}
              style={{
                fontSize: 12,
                padding: '4px 8px',
                borderRadius: 8,
                background: 'var(--bg-card)',
                color: 'var(--text-primary)',
                border: '1px solid var(--border)',
                fontWeight: 600,
                cursor: 'pointer',
              }}
            >
              {models.map(m => (
                <option key={m.id} value={m.id}>
                  {m.name} ({m.badge})
                </option>
              ))}
            </select>

            <span style={{
              fontSize: 11,
              padding: '2px 8px',
              borderRadius: 10,
              background: 'rgba(16, 185, 129, 0.15)',
              color: '#10b981',
              border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              fontWeight: 600,
            }}>
              <Key size={11} /> {activeKeysCount} Gemini Keys Active
            </span>
          </div>
        </div>
      </div>

      {/* Search Mode Toggle Tabs */}
      <div style={{ display: 'flex', gap: 12, marginBottom: 18 }}>
        <button
          onClick={() => setSearchMode('topic')}
          style={{
            padding: '9px 20px',
            borderRadius: 10,
            fontSize: 13,
            fontWeight: 700,
            border: `1px solid ${searchMode === 'topic' ? 'rgba(99, 102, 241, 0.6)' : 'var(--border)'}`,
            background: searchMode === 'topic' ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-card)',
            color: searchMode === 'topic' ? 'var(--primary-light)' : 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            transition: 'all 0.2s',
          }}
        >
          <Sparkles size={16} color={searchMode === 'topic' ? 'var(--primary-light)' : 'var(--text-muted)'} />
          <span>🔍 Cari Berdasarkan Topik (AI)</span>
        </button>

        <button
          onClick={() => setSearchMode('title')}
          style={{
            padding: '9px 20px',
            borderRadius: 10,
            fontSize: 13,
            fontWeight: 700,
            border: `1px solid ${searchMode === 'title' ? 'rgba(99, 102, 241, 0.6)' : 'var(--border)'}`,
            background: searchMode === 'title' ? 'rgba(99, 102, 241, 0.15)' : 'var(--bg-card)',
            color: searchMode === 'title' ? 'var(--primary-light)' : 'var(--text-secondary)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            transition: 'all 0.2s',
          }}
        >
          <FileText size={16} color={searchMode === 'title' ? 'var(--primary-light)' : 'var(--text-muted)'} />
          <span>📄 Cari Berdasarkan Judul Spesifik</span>
        </button>
      </div>

      {searchMode === 'title' && (
        <div>
          {/* Title Search Input Card */}
          <div className="glass-panel" style={{ padding: 22, borderRadius: 16, marginBottom: 20 }}>
            <div style={{ marginBottom: 14 }}>
              <label style={{ display: 'block', fontSize: 13, fontWeight: 700, color: 'var(--text-primary)', marginBottom: 8 }}>
                Ketik Judul Artikel atau Naskah Ilmiah:
              </label>
              <div style={{ display: 'flex', gap: 10 }}>
                <input
                  type="text"
                  value={titleQuery}
                  onChange={e => setTitleQuery(e.target.value)}
                  onKeyDown={e => { if (e.key === 'Enter') handleTitleSearch() }}
                  placeholder="Contoh: Attention Is All You Need, Deep Residual Learning for Image Recognition, atau judul naskah lainnya..."
                  className="input-field"
                  style={{ flex: 1, padding: '12px 16px', fontSize: 14 }}
                />
                <button
                  onClick={handleTitleSearch}
                  disabled={!titleQuery.trim() || titleSearching}
                  className="btn-primary"
                  style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '0 24px', whiteSpace: 'nowrap' }}
                >
                  {titleSearching ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Search size={16} />}
                  <span>Cari Judul</span>
                </button>
              </div>
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <span>💡</span>
              <span>Sistem mencari naskah secara spesifik di Crossref & OpenAlex, mendeteksi status Open Access legal, serta menyediakan direct resolver Sci-Hub jika naskah berbayar.</span>
            </div>
          </div>

          {/* Title Search Results List */}
          {titleResults.length > 0 && (
            <div className="fade-in">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
                  Hasil Pencarian Judul ({titleResults.length} artikel ditemukan)
                </h2>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
                {titleResults.map((item, idx) => (
                  <div
                    key={idx}
                    className="glass-panel"
                    style={{
                      padding: '18px 22px',
                      borderRadius: 14,
                      border: '1px solid var(--border)',
                      background: 'var(--bg-card)',
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: 16, marginBottom: 8 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8, flexWrap: 'wrap' }}>
                          <span style={{
                            fontSize: 11,
                            fontWeight: 700,
                            padding: '2px 8px',
                            borderRadius: 6,
                            background: item.source === 'Crossref' ? 'rgba(59, 130, 246, 0.15)' : 'rgba(16, 185, 129, 0.15)',
                            color: item.source === 'Crossref' ? '#60a5fa' : '#34d399',
                            border: `1px solid ${item.source === 'Crossref' ? 'rgba(59, 130, 246, 0.3)' : 'rgba(16, 185, 129, 0.3)'}`,
                          }}>
                            {item.source}
                          </span>

                          {item.year && (
                            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
                              Tahun {item.year}
                            </span>
                          )}

                          {item.is_open_access ? (
                            <span style={{
                              fontSize: 11,
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 6,
                              background: 'rgba(16, 185, 129, 0.15)',
                              color: '#34d399',
                              border: '1px solid rgba(16, 185, 129, 0.3)',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4,
                            }}>
                              <CheckCircle size={11} /> Open Access
                            </span>
                          ) : (
                            <span style={{
                              fontSize: 11,
                              fontWeight: 700,
                              padding: '2px 8px',
                              borderRadius: 6,
                              background: 'rgba(239, 68, 68, 0.12)',
                              color: '#f87171',
                              border: '1px solid rgba(239, 68, 68, 0.3)',
                              display: 'flex',
                              alignItems: 'center',
                              gap: 4,
                            }}>
                              <Unlock size={11} /> Berbayar / Terkunci
                            </span>
                          )}

                          {item.citation_count !== undefined && item.citation_count !== null && (
                            <span style={{ fontSize: 11, color: 'var(--text-secondary)' }}>
                              • {item.citation_count} Sitasi
                            </span>
                          )}
                        </div>

                        <h3 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 6px', lineHeight: 1.4 }}>
                          {item.title}
                        </h3>

                        {item.journal_name && (
                          <div style={{ fontSize: 13, color: 'var(--primary-light)', fontWeight: 600, marginBottom: 4 }}>
                            {item.journal_name}
                          </div>
                        )}

                        {item.authors && item.authors.length > 0 && (
                          <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                            {item.authors.join(', ')}
                          </div>
                        )}

                        {item.abstract && (
                          <p style={{ fontSize: 12, color: 'var(--text-muted)', margin: '6px 0 0', lineHeight: 1.5 }}>
                            {item.abstract}...
                          </p>
                        )}
                      </div>
                    </div>

                    {/* Action buttons */}
                    <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 12, paddingTop: 12, borderTop: '1px solid rgba(255,255,255,0.06)' }}>
                      {item.doi && (
                        <a
                          href={`https://doi.org/${item.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-outline"
                          style={{ fontSize: 12, padding: '6px 12px', display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
                        >
                          <ExternalLink size={12} />
                          DOI: {item.doi}
                        </a>
                      )}

                      {item.open_access_url && (
                        <a
                          href={item.open_access_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-primary"
                          style={{
                            fontSize: 12,
                            padding: '6px 14px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            textDecoration: 'none',
                            background: 'linear-gradient(135deg, #059669, #10b981)',
                            borderColor: '#059669',
                          }}
                        >
                          <FileText size={12} />
                          Buka PDF (Open Access)
                        </a>
                      )}

                      {item.sci_hub_url && (
                        <a
                          href={item.sci_hub_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="btn-secondary"
                          style={{
                            fontSize: 12,
                            padding: '6px 14px',
                            display: 'flex',
                            alignItems: 'center',
                            gap: 6,
                            textDecoration: 'none',
                            background: !item.is_open_access ? 'linear-gradient(135deg, rgba(225, 29, 72, 0.2), rgba(190, 18, 60, 0.35))' : undefined,
                            borderColor: !item.is_open_access ? 'rgba(225, 29, 72, 0.45)' : undefined,
                            color: !item.is_open_access ? '#fda4af' : undefined,
                            fontWeight: 600,
                          }}
                        >
                          <Unlock size={12} />
                          {!item.is_open_access ? 'Auto Buka via Sci-Hub (Bypass Paywall)' : 'Buka via Sci-Hub'}
                        </a>
                      )}

                      {item.doi && (
                        <button
                          onClick={() => {
                            navigator.clipboard.writeText(item.doi)
                            toast.success(`DOI ${item.doi} berhasil disalin!`)
                          }}
                          className="btn-outline"
                          style={{ fontSize: 12, padding: '6px 10px', display: 'flex', alignItems: 'center', gap: 6 }}
                        >
                          <Copy size={12} /> Salin DOI
                        </button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {titleResults.length === 0 && !titleSearching && (
            <div style={{ textAlign: 'center', padding: '60px 20px', color: 'var(--text-muted)' }}>
              <FileText size={44} style={{ opacity: 0.3, marginBottom: 12 }} />
              <div style={{ fontSize: 15, fontWeight: 600, color: 'var(--text-secondary)' }}>
                Belum ada pencarian judul
              </div>
              <div style={{ fontSize: 13, marginTop: 4 }}>
                Ketikkan judul artikel ilmiah yang ingin Anda cari pada kolom di atas
              </div>
            </div>
          )}
        </div>
      )}

      {searchMode === 'topic' && (
        <>
          {/* Natural Language Command Card */}
          <div className="glass-panel" style={{ padding: 22, borderRadius: 16, marginBottom: 20 }}>
        <div style={{ position: 'relative', marginBottom: 14 }}>
          <textarea
            value={command}
            onChange={e => { setCommand(e.target.value); setInterpreted(null) }}
            onKeyDown={e => {
              if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) handleInterpret()
            }}
            className="input-field"
            placeholder="Ketik perintah pencarian dalam bahasa Indonesia atau Inggris...&#10;Contoh: Cari 20 artikel tentang Generative AI untuk otomatisasi administrasi pemerintahan, tahun 2022–2026"
            style={{ width: '100%', minHeight: 90, padding: '14px 16px', resize: 'vertical', fontSize: 15 }}
          />
          <div style={{ position: 'absolute', right: 12, bottom: 12, fontSize: 11, color: 'var(--text-muted)' }}>
            Ctrl+Enter untuk interpretasi
          </div>
        </div>

        {/* Presets (Multi-Select) */}
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, color: 'var(--text-muted)', marginBottom: 6, display: 'flex', alignItems: 'center', gap: 5 }}>
            <Sparkles size={12} color="var(--primary-light)" />
            <span>Pilihan Target & Kategori (Bisa pilih lebih dari satu / multi-select):</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {PRESETS.map(p => {
              const isSelected = selectedPresets.includes(p.id)
              return (
                <button
                  key={p.id}
                  onClick={() => handlePresetToggle(p.id)}
                  style={{
                    padding: '6px 14px',
                    borderRadius: 999,
                    fontSize: 12,
                    fontWeight: isSelected ? 700 : 500,
                    border: `1px solid ${isSelected ? 'var(--primary-light)' : 'var(--border)'}`,
                    background: isSelected ? 'rgba(99,102,241,0.22)' : 'transparent',
                    color: isSelected ? '#a5b4fc' : 'var(--text-secondary)',
                    boxShadow: isSelected ? '0 0 10px rgba(99,102,241,0.25)' : 'none',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                    fontFamily: 'inherit',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: 6,
                  }}
                >
                  {isSelected && <span style={{ fontWeight: 800, color: '#10b981' }}>✓</span>}
                  <span>{p.label}</span>
                </button>
              )
            })}
          </div>
        </div>

        {/* Example commands */}
        {!command && (
          <div style={{ marginBottom: 14 }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8 }}>💡 Contoh perintah:</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
              {EXAMPLE_COMMANDS.map((ex, i) => (
                <button
                  key={i}
                  onClick={() => setCommand(ex)}
                  style={{
                    textAlign: 'left', background: 'transparent', border: 'none',
                    color: 'var(--text-muted)', fontSize: 12, cursor: 'pointer',
                    padding: '3px 0', fontFamily: 'inherit',
                  }}
                >
                  <span style={{ color: 'var(--primary-light)', marginRight: 6 }}>→</span>
                  {ex}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: 10, alignItems: 'center' }}>
          <button
            onClick={handleInterpret}
            disabled={!command.trim() || isInterpreting}
            className="btn-secondary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            {isInterpreting ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Sliders size={14} />}
            Interpretasi
          </button>
          <button
            onClick={handleSearch}
            disabled={!command.trim() || isSearching}
            className="btn-primary"
            style={{ display: 'flex', alignItems: 'center', gap: 6 }}
          >
            {isSearching ? <div className="spinner" style={{ width: 14, height: 14 }} /> : <Send size={14} />}
            Mulai Pencarian
          </button>
          {isSearching && (
            <button onClick={handleCancel} className="btn-ghost" style={{ color: '#ef4444' }}>
              Batalkan
            </button>
          )}
        </div>
      </div>

      {/* Interpreted Parameters Card */}
      {interpreted && (
        <div className="glass-panel" style={{ padding: 20, borderRadius: 16, marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span style={{ color: 'var(--primary-light)', fontWeight: 600, fontSize: 14 }}>
                ⚡ Hasil Interpretasi Perintah
              </span>
              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                (Model: {selectedModel})
              </span>
            </div>
            <button
              onClick={() => setShowFilters(!showFilters)}
              className="btn-ghost"
              style={{ fontSize: 12, padding: '4px 8px' }}
            >
              {showFilters ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
              {showFilters ? 'Sembunyikan Pengaturan' : 'Ubah Pengaturan'}
            </button>
          </div>

          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>
            <span className="badge badge-info">Topik: {interpreted.topic}</span>
            {interpreted.year_from && (
              <span className="badge badge-warning">
                Tahun: {interpreted.year_from}–{interpreted.year_to || 'sekarang'}
              </span>
            )}
            {interpreted.indexing_target && (
              <span className="badge badge-primary">
                Target: {interpreted.indexing_target.toUpperCase()}
              </span>
            )}
            {interpreted.sinta_rank_min && (
              <span className="badge badge-success">
                SINTA {interpreted.sinta_rank_min}–{interpreted.sinta_rank_max}
              </span>
            )}
            <span className="badge badge-neutral">Max: {interpreted.max_results}</span>
            {interpreted.open_access_only && <span className="badge badge-success">Open Access Only</span>}
          </div>

          {showFilters && (
            <div style={{ marginTop: 14, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: 14 }}>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Topik</label>
                  <input
                    type="text"
                    value={interpreted.topic}
                    onChange={e => setInterpreted({ ...interpreted, topic: e.target.value })}
                    className="input-field"
                    style={{ width: '100%', marginTop: 4 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Tahun Mulai</label>
                  <input
                    type="number"
                    value={interpreted.year_from || ''}
                    onChange={e => setInterpreted({ ...interpreted, year_from: parseInt(e.target.value) || undefined })}
                    className="input-field"
                    style={{ width: '100%', marginTop: 4 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Tahun Sampai</label>
                  <input
                    type="number"
                    value={interpreted.year_to || ''}
                    onChange={e => setInterpreted({ ...interpreted, year_to: parseInt(e.target.value) || undefined })}
                    className="input-field"
                    style={{ width: '100%', marginTop: 4 }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Target Indeksasi</label>
                  <select
                    value={interpreted.indexing_target || 'any'}
                    onChange={e => setInterpreted({ ...interpreted, indexing_target: e.target.value })}
                    className="input-field"
                    style={{ width: '100%', marginTop: 4 }}
                  >
                    <option value="any">Semua</option>
                    <option value="scopus">Scopus</option>
                    <option value="sinta">SINTA</option>
                    <option value="both">Scopus + SINTA</option>
                  </select>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Search Progress */}
      {currentSearch && (currentSearch.status === 'running' || currentSearch.status === 'pending') && (
        <div className="glass-panel" style={{ padding: 20, borderRadius: 16, marginBottom: 20 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
            <div className="spinner" />
            <h3 style={{ margin: 0, fontSize: 14, fontWeight: 600 }}>Pencarian Berlangsung...</h3>
          </div>
          <div className="progress-bar" style={{ marginBottom: 12 }}>
            <div className="progress-fill" style={{ width: `${statusProgress()}%` }} />
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8 }}>
            {currentSearch.source_logs.map(log => (
              <div key={log.source_name} style={{
                display: 'flex', alignItems: 'center', gap: 8,
                padding: '8px 12px', background: 'rgba(17,24,39,0.5)',
                borderRadius: 8, fontSize: 12,
              }}>
                <span className={`status-dot ${log.status}`} />
                <div>
                  <div style={{ fontWeight: 600, textTransform: 'capitalize' }}>
                    {log.source_name.replace('_', ' ')}
                  </div>
                  <div style={{ color: 'var(--text-muted)' }}>
                    {log.articles_found > 0 && `${log.articles_found} artikel`}
                    {log.status === 'failed' && '⚠ Gagal'}
                    {log.status === 'completed' && log.articles_found === 0 && '0 ditemukan'}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Summary Banner */}
      {currentSearch && currentSearch.status === 'completed' && (
        <div className="glass-panel" style={{ padding: '16px 22px', borderRadius: 16, marginBottom: 20 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 14 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 12, fontSize: 13, flexWrap: 'wrap' }}>
              <span style={{ fontWeight: 700, color: '#10b981', display: 'flex', alignItems: 'center', gap: 4 }}>
                <CheckCircle size={15} /> Selesai
              </span>
              <span style={{ color: 'var(--text-secondary)' }}>
                <b>{currentSearch.total_after_dedup}</b> artikel unik ({currentSearch.total_found} ditemukan, duplikat dihapus)
              </span>
              <span style={{ color: '#06b6d4' }}>
                <b>{currentSearch.total_verified}</b> terverifikasi Scopus/SINTA
              </span>
              <span style={{ color: '#a855f7' }}>
                <b>{currentSearch.total_open_access}</b> open access
              </span>
            </div>

            {/* AI Synthesis & Export Actions */}
            <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
              <button
                onClick={handleSynthesize}
                disabled={isSynthesizing}
                className="btn-primary"
                style={{
                  fontSize: 12,
                  padding: '6px 14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: 6,
                  background: 'linear-gradient(135deg, #6366f1, #a855f7)',
                }}
              >
                {isSynthesizing ? <div className="spinner" style={{ width: 12, height: 12 }} /> : <Sparkles size={13} />}
                <span>Sintesis Literature Review (Gemini)</span>
              </button>

              <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Export:</span>
              {['csv', 'xlsx', 'bibtex', 'ris', 'apa7'].map(fmt => (
                <button
                  key={fmt}
                  onClick={() => handleExport(fmt)}
                  className="btn-ghost"
                  style={{ fontSize: 11, padding: '4px 8px' }}
                >
                  <Download size={11} style={{ display: 'inline', marginRight: 3 }} />
                  {fmt.toUpperCase()}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* SINTA & Scopus Quick Filter Pills */}
      {results && (
        <div style={{
          display: 'flex',
          gap: 8,
          marginBottom: 12,
          flexWrap: 'wrap',
          alignItems: 'center',
          background: 'rgba(255, 255, 255, 0.03)',
          padding: '8px 12px',
          borderRadius: 12,
          border: '1px solid rgba(255, 255, 255, 0.07)'
        }}>
          <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text-muted)', marginRight: 4 }}>
            Filter Akreditasi:
          </span>
          {[
            { id: 'all', label: 'Semua Indeks' },
            { id: 'both', label: '🔷 Scopus + SINTA' },
            { id: 'scopus', label: '🌐 Terindeks Scopus' },
            { id: '1', label: '⭐ SINTA 1' },
            { id: '2', label: '🥇 SINTA 2' },
            { id: '3', label: '🥈 SINTA 3' },
            { id: '4', label: '🥉 SINTA 4' },
            { id: '5', label: '📗 SINTA 5' },
            { id: '6', label: '📘 SINTA 6' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => { setSintaFilter(tab.id as any); setPage(1) }}
              className={sintaFilter === tab.id ? 'btn-primary' : 'btn-ghost'}
              style={{
                fontSize: 12,
                padding: '4px 12px',
                borderRadius: 20,
                cursor: 'pointer',
                fontWeight: sintaFilter === tab.id ? 700 : 500,
                ...(sintaFilter === tab.id && tab.id === 'both' ? { background: '#6366f1', borderColor: '#6366f1', color: '#fff' } : {}),
                ...(sintaFilter === tab.id && tab.id === 'scopus' ? { background: '#ec4899', borderColor: '#ec4899', color: '#fff' } : {}),
                ...(sintaFilter === tab.id && tab.id === '1' ? { background: '#f59e0b', borderColor: '#f59e0b', color: '#000' } : {}),
                ...(sintaFilter === tab.id && tab.id === '2' ? { background: '#10b981', borderColor: '#10b981', color: '#fff' } : {}),
                ...(sintaFilter === tab.id && tab.id === '3' ? { background: '#3b82f6', borderColor: '#3b82f6', color: '#fff' } : {}),
                ...(sintaFilter === tab.id && tab.id === '4' ? { background: '#8b5cf6', borderColor: '#8b5cf6', color: '#fff' } : {}),
                ...(sintaFilter === tab.id && tab.id === '5' ? { background: '#06b6d4', borderColor: '#06b6d4', color: '#fff' } : {}),
                ...(sintaFilter === tab.id && tab.id === '6' ? { background: '#64748b', borderColor: '#64748b', color: '#fff' } : {}),
              }}
            >
              {tab.label}
            </button>
          ))}
        </div>
      )}

      {/* Subject Category Quick Filter Pills (Multi-Select) */}
      {results && (
        <div style={{
          display: 'flex',
          gap: 8,
          marginBottom: 14,
          flexWrap: 'wrap',
          alignItems: 'center',
          background: 'rgba(99, 102, 241, 0.05)',
          padding: '10px 14px',
          borderRadius: 12,
          border: '1px solid rgba(99, 102, 241, 0.2)'
        }}>
          <span style={{ fontSize: 12, fontWeight: 700, color: 'var(--primary-light)', display: 'flex', alignItems: 'center', gap: 5, marginRight: 4 }}>
            <span>🎯</span> Filter Kategori (Bisa pilih &gt; 1):
          </span>
          <button
            onClick={() => { setSelectedCategories([]); setPage(1) }}
            className={selectedCategories.length === 0 ? 'btn-primary' : 'btn-ghost'}
            style={{
              fontSize: 12,
              padding: '4px 12px',
              borderRadius: 20,
              cursor: 'pointer',
              fontWeight: selectedCategories.length === 0 ? 700 : 500,
            }}
          >
            Semua Bidang {results.total ? `(${results.total})` : ''}
          </button>
          {[
            { id: 'Keamanan Siber', label: '🛡️ Keamanan Siber / Cyber Security', color: '#ef4444' },
            { id: 'Teknologi Informasi & Komputer', label: '💻 IT & Komputer', color: '#3b82f6' },
            { id: 'Hukum & Kebijakan', label: '⚖️ Hukum & Kebijakan', color: '#a855f7' },
            { id: 'Kesehatan & Kedokteran', label: '🩺 Kesehatan', color: '#10b981' },
            { id: 'Ekonomi & Bisnis', label: '📈 Ekonomi & Bisnis', color: '#f59e0b' },
            { id: 'Pendidikan', label: '🎓 Pendidikan', color: '#0ea5e9' },
          ].map(cat => {
            const count = results.category_counts?.[cat.id]
            const isActive = selectedCategories.includes(cat.id)
            return (
              <button
                key={cat.id}
                onClick={() => {
                  setSelectedCategories(prev =>
                    prev.includes(cat.id) ? prev.filter(c => c !== cat.id) : [...prev, cat.id]
                  )
                  setPage(1)
                }}
                className={isActive ? 'btn-primary' : 'btn-ghost'}
                style={{
                  fontSize: 12,
                  padding: '4px 12px',
                  borderRadius: 20,
                  cursor: 'pointer',
                  fontWeight: isActive ? 700 : 500,
                  border: `1px solid ${isActive ? cat.color : 'rgba(255, 255, 255, 0.12)'}`,
                  background: isActive ? `${cat.color}25` : undefined,
                  color: isActive ? '#fff' : 'var(--text-secondary)',
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: 6,
                }}
              >
                {isActive && <span style={{ fontWeight: 800 }}>✓</span>}
                <span>{cat.label}</span>
                {count !== undefined && (
                  <span style={{
                    fontSize: 10,
                    padding: '1px 6px',
                    borderRadius: 10,
                    background: isActive ? cat.color : 'rgba(255, 255, 255, 0.15)',
                    color: '#fff',
                    fontWeight: 700,
                  }}>
                    {count}
                  </span>
                )}
              </button>
            )
          })}
        </div>
      )}

      {/* Filters for results */}
      {results && (
        <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap', alignItems: 'center' }}>
          <select
            value={sortBy}
            onChange={e => { setSortBy(e.target.value); setPage(1) }}
            className="input-field"
            style={{ fontSize: 13, height: 36 }}
          >
            {SORT_OPTIONS.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
          <button
            onClick={() => setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc')}
            className="btn-ghost"
            style={{ fontSize: 12, padding: '6px 12px' }}
          >
            {sortOrder === 'desc' ? '↓ Descending' : '↑ Ascending'}
          </button>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer', color: 'var(--text-primary)', fontSize: 13 }}>
            <input type="checkbox" checked={oaOnly} onChange={e => { setOaOnly(e.target.checked); setPage(1) }} />
            Open Access Only
          </label>
          <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13, color: 'var(--text-secondary)' }}>
            Min Score:
            <input
              type="number" min={0} max={100}
              value={minScore}
              onChange={e => { setMinScore(parseInt(e.target.value) || 0); setPage(1) }}
              className="input-field"
              style={{ width: 60, height: 32, fontSize: 13 }}
            />
          </label>
          <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 'auto' }}>
            {results.total} artikel, halaman {results.page}/{results.pages || 1}
          </span>
        </div>
      )}

      {/* Results Table */}
      {results && results.items.length > 0 && (
        <div className="fade-in">
          <ArticleTable
            articles={results.items}
            onViewDetail={sa => setSelectedArticle(sa)}
          />

          {/* Pagination */}
          <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 16 }}>
            <button className="btn-ghost" disabled={page <= 1} onClick={() => setPage(p => p - 1)}>
              ← Prev
            </button>
            {Array.from({ length: Math.min(results.pages || 1, 7) }, (_, i) => {
              const p = i + 1
              return (
                <button
                  key={p}
                  onClick={() => setPage(p)}
                  className="btn-ghost"
                  style={p === page ? { background: 'rgba(99,102,241,0.2)', borderColor: 'rgba(99,102,241,0.5)', color: 'var(--primary-light)' } : {}}
                >
                  {p}
                </button>
              )
            })}
            <button className="btn-ghost" disabled={page >= (results.pages || 1)} onClick={() => setPage(p => p + 1)}>
              Next →
            </button>
          </div>
        </div>
      )}
        </>
      )}

      {/* Article Detail Drawer Modal */}
      {selectedArticle && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.65)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20
        }}>
          <div style={{ width: '100%', maxWidth: 840, maxHeight: '90vh', overflowY: 'auto' }}>
            <ArticleDetail
              searchArticle={selectedArticle}
              onClose={() => setSelectedArticle(null)}
            />
          </div>
        </div>
      )}

      {/* Literature Review Synthesis Modal */}
      {showSynthesisModal && (
        <div style={{
          position: 'fixed', inset: 0, background: 'rgba(0,0,0,0.7)', backdropFilter: 'blur(4px)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20
        }}>
          <div className="glass-panel" style={{
            width: '100%', maxWidth: 860, maxHeight: '88vh', display: 'flex', flexDirection: 'column',
            borderRadius: 16, padding: 24, boxShadow: '0 20px 50px rgba(0,0,0,0.6)'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <Sparkles size={20} color="var(--primary-light)" />
                <h3 style={{ margin: 0, fontSize: 17, fontWeight: 700, color: 'var(--text-primary)' }}>
                  Sintesis Tinjauan Pustaka (Literature Review)
                </h3>
              </div>
              <button
                onClick={() => setShowSynthesisModal(false)}
                className="btn-ghost"
                style={{ padding: 4 }}
              >
                <X size={18} />
              </button>
            </div>

            <div style={{ flex: 1, overflowY: 'auto', marginBottom: 16 }}>
              {isSynthesizing ? (
                <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
                  <div className="spinner" style={{ margin: '0 auto 16px' }} />
                  <div>Menyintesis literatur ilmiah dengan Google Gemini ({selectedModel})...</div>
                </div>
              ) : synthesisReview ? (
                <div style={{
                  background: 'var(--bg-surface)', padding: 18, borderRadius: 12,
                  border: '1px solid var(--border)', fontSize: 14, lineHeight: 1.7,
                  color: 'var(--text-secondary)', whiteSpace: 'pre-wrap'
                }}>
                  {synthesisReview}
                </div>
              ) : (
                <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
                  Tidak ada teks sintesis yang dihasilkan.
                </div>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10 }}>
              {synthesisReview && (
                <button onClick={copySynthesis} className="btn-secondary" style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                  <Copy size={14} /> Salin Teks
                </button>
              )}
              <button onClick={() => setShowSynthesisModal(false)} className="btn-primary">
                Tutup
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
