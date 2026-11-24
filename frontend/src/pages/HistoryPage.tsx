import React, { useEffect, useState } from 'react'
import { getHistory, getSearchResults, type SearchSummary, type SearchArticle } from '../api'
import { formatDistanceToNow } from 'date-fns'
import { id as idLocale } from 'date-fns/locale'
import { Clock, Search, CheckCircle, AlertCircle, XCircle, ChevronRight, RefreshCw } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import ArticleDetail from '../components/ArticleDetail'

const STATUS_CONFIG: Record<string, { icon: React.ReactNode; color: string; label: string }> = {
  completed: { icon: <CheckCircle size={14} />, color: '#10b981', label: 'Selesai' },
  running: { icon: <div className="spinner" style={{ width: 14, height: 14 }} />, color: '#f59e0b', label: 'Berjalan' },
  pending: { icon: <Clock size={14} />, color: '#6b7280', label: 'Menunggu' },
  failed: { icon: <AlertCircle size={14} />, color: '#ef4444', label: 'Gagal' },
  cancelled: { icon: <XCircle size={14} />, color: '#6b7280', label: 'Dibatalkan' },
}

export default function HistoryPage() {
  const [history, setHistory] = useState<SearchSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [expanded, setExpanded] = useState<string | null>(null)
  const [articlePreviews, setArticlePreviews] = useState<Record<string, SearchArticle[]>>({})
  const navigate = useNavigate()

  useEffect(() => {
    getHistory(50)
      .then(r => setHistory(r.data))
      .catch(console.error)
      .finally(() => setLoading(false))
  }, [])

  const toggleExpand = async (id: string) => {
    if (expanded === id) { setExpanded(null); return }
    setExpanded(id)
    if (!articlePreviews[id]) {
      try {
        const res = await getSearchResults(id, { page: 1, page_size: 5, sort_by: 'relevance', order: 'desc' })
        setArticlePreviews(prev => ({ ...prev, [id]: res.data.items }))
      } catch (e) { console.error(e) }
    }
  }

  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: 200 }}>
        <div className="spinner" />
      </div>
    )
  }

  return (
    <div className="fade-in">
      <h1 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 22, fontWeight: 700, margin: '0 0 20px' }}>
        📋 Search History
      </h1>

      {history.length === 0 ? (
        <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
          <Clock size={48} style={{ marginBottom: 12, opacity: 0.2 }} />
          <p>Belum ada riwayat pencarian.</p>
          <button className="btn-primary" onClick={() => navigate('/search')} style={{ marginTop: 12 }}>
            Mulai Pencarian
          </button>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {history.map(s => {
            const cfg = STATUS_CONFIG[s.status] || STATUS_CONFIG.pending
            const isExp = expanded === s.id
            const previews = articlePreviews[s.id] || []

            return (
              <div key={s.id} className="card" style={{ padding: 0, overflow: 'hidden' }}>
                <div
                  onClick={() => toggleExpand(s.id)}
                  style={{
                    display: 'flex', alignItems: 'center', gap: 12,
                    padding: '14px 18px', cursor: 'pointer',
                  }}
                >
                  <span style={{ color: cfg.color, display: 'flex', alignItems: 'center', gap: 4, minWidth: 90, fontSize: 13 }}>
                    {cfg.icon} {cfg.label}
                  </span>
                  <div style={{ flex: 1, overflow: 'hidden' }}>
                    <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {s.user_command}
                    </div>
                    <div style={{ display: 'flex', gap: 12, marginTop: 3, fontSize: 12, color: 'var(--text-muted)' }}>
                      <span>{formatDistanceToNow(new Date(s.created_at), { addSuffix: true, locale: idLocale })}</span>
                      {s.status === 'completed' && (
                        <>
                          <span>🔍 {s.total_found} ditemukan</span>
                          <span>✅ {s.total_after_dedup} unik</span>
                          <span>🔓 {s.total_open_access} OA</span>
                        </>
                      )}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button
                      className="btn-ghost"
                      onClick={e => { e.stopPropagation(); navigate(`/search?id=${s.id}`) }}
                      style={{ fontSize: 12, padding: '4px 10px' }}
                    >
                      <ChevronRight size={13} style={{ display: 'inline', marginRight: 3 }} />
                      Buka
                    </button>
                    <button
                      className="btn-ghost"
                      onClick={e => { e.stopPropagation(); navigate(`/search?cmd=${encodeURIComponent(s.user_command)}`) }}
                      style={{ fontSize: 12, padding: '4px 10px' }}
                      title="Ulangi pencarian"
                    >
                      <RefreshCw size={12} />
                    </button>
                  </div>
                </div>

                {/* Source logs */}
                {s.source_logs?.length > 0 && (
                  <div style={{
                    display: 'flex', gap: 8, flexWrap: 'wrap',
                    padding: '0 18px 10px',
                    borderTop: '1px solid var(--border)',
                    paddingTop: 10,
                  }}>
                    {s.source_logs.map(log => (
                      <span key={log.source_name} style={{
                        fontSize: 11, padding: '2px 8px', borderRadius: 4,
                        background: 'rgba(17,24,39,0.5)',
                        border: '1px solid var(--border)',
                        display: 'flex', alignItems: 'center', gap: 4,
                        color: 'var(--text-secondary)',
                      }}>
                        <span className={`status-dot ${log.status}`} style={{ width: 6, height: 6 }} />
                        {log.source_name.replace('_', ' ')}: {log.articles_found}
                      </span>
                    ))}
                  </div>
                )}

                {/* Article previews */}
                {isExp && (
                  <div style={{ borderTop: '1px solid var(--border)', padding: '12px 18px' }}>
                    {previews.length === 0 ? (
                      <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>
                        Tidak ada artikel tersimpan untuk pencarian ini.
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>
                          5 artikel teratas:
                        </div>
                        {previews.map(sa => (
                          <div key={sa.article.id} style={{
                            fontSize: 13, padding: '8px 10px',
                            background: 'rgba(17,24,39,0.3)', borderRadius: 6,
                            border: '1px solid var(--border)',
                          }}>
                            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
                              {sa.article.title}
                            </div>
                            <div style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                              {sa.article.authors?.[0]?.name} · {sa.article.year} · Skor: {sa.relevance_score.toFixed(1)}
                            </div>
                          </div>
                        ))}
                        <button
                          className="btn-secondary"
                          onClick={() => navigate(`/search?id=${s.id}`)}
                          style={{ alignSelf: 'flex-start', marginTop: 6, fontSize: 13 }}
                        >
                          Lihat semua hasil →
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
