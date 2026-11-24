import React, { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { getJournals, type Journal } from '../api'
import {
  BookOpen, Search, CheckCircle, ExternalLink, Globe,
  ShieldCheck, Filter, ArrowUpRight, Award, Zap
} from 'lucide-react'

const SINTA_COLORS: Record<number, { bg: string; text: string; border: string }> = {
  1: { bg: 'rgba(16, 185, 129, 0.15)', text: '#10b981', border: 'rgba(16, 185, 129, 0.4)' },
  2: { bg: 'rgba(6, 182, 212, 0.15)', text: '#06b6d4', border: 'rgba(6, 182, 212, 0.4)' },
  3: { bg: 'rgba(59, 130, 246, 0.15)', text: '#3b82f6', border: 'rgba(59, 130, 246, 0.4)' },
  4: { bg: 'rgba(168, 85, 247, 0.15)', text: '#a855f7', border: 'rgba(168, 85, 247, 0.4)' },
  5: { bg: 'rgba(245, 158, 11, 0.15)', text: '#f59e0b', border: 'rgba(245, 158, 11, 0.4)' },
  6: { bg: 'rgba(100, 116, 139, 0.15)', text: '#94a3b8', border: 'rgba(100, 116, 139, 0.4)' },
}

export default function JournalsPage() {
  const navigate = useNavigate()
  const [journals, setJournals] = useState<Journal[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState('')
  const [selectedSinta, setSelectedSinta] = useState<number | null>(null)
  const [scopusOnly, setScopusOnly] = useState(false)

  const fetchJournals = async () => {
    setLoading(true)
    try {
      const res = await getJournals({
        search: searchTerm.trim() || undefined,
        sinta_rank: selectedSinta || undefined,
        scopus_only: scopusOnly,
        limit: 100,
      })
      setJournals(res.data)
    } catch (err) {
      console.error('Failed to load journals', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    const timer = setTimeout(() => {
      fetchJournals()
    }, 250)
    return () => clearTimeout(timer)
  }, [searchTerm, selectedSinta, scopusOnly])

  const scopusCount = journals.filter((j) => j.is_scopus_indexed).length
  const sintaCount = journals.filter((j) => j.sinta_rank !== null && j.sinta_rank !== undefined).length
  const oaCount = journals.filter((j) => j.is_open_access).length

  return (
    <div className="page-container" style={{ padding: '28px 36px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 8 }}>
          <div className="gradient-primary" style={{
            width: 42, height: 42, borderRadius: 12,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 24px rgba(99,102,241,0.35)'
          }}>
            <BookOpen size={22} color="white" />
          </div>
          <div>
            <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
              Journal Explorer & Verification Database
            </h1>
            <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
              Database jurnal ilmiah terverifikasi SINTA (S1–S6) dan Scopus dengan cakupan pengindeksan nasional & internasional.
            </p>
          </div>
        </div>

        {/* Stats metrics */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: 16,
          marginTop: 20
        }}>
          <div className="stat-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
              Total Terverifikasi
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: 'var(--text-primary)', marginTop: 4 }}>
              {journals.length}
            </div>
          </div>
          <div className="stat-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: 12, color: '#10b981', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Award size={14} /> Terindeks SINTA
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#10b981', marginTop: 4 }}>
              {sintaCount}
            </div>
          </div>
          <div className="stat-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: 12, color: '#06b6d4', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
              <ShieldCheck size={14} /> Terindeks Scopus
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#06b6d4', marginTop: 4 }}>
              {scopusCount}
            </div>
          </div>
          <div className="stat-card" style={{ padding: '16px 20px' }}>
            <div style={{ fontSize: 12, color: '#a855f7', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600, display: 'flex', alignItems: 'center', gap: 6 }}>
              <Globe size={14} /> Open Access
            </div>
            <div style={{ fontSize: 28, fontWeight: 700, color: '#a855f7', marginTop: 4 }}>
              {oaCount}
            </div>
          </div>
        </div>
      </div>

      {/* Search & Filter Bar */}
      <div className="glass-panel" style={{ padding: '18px 22px', marginBottom: 24, borderRadius: 16 }}>
        <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'center' }}>
          {/* Search Input */}
          <div style={{ flex: 1, minWidth: 260, position: 'relative' }}>
            <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              placeholder="Cari nama jurnal, penerbit, atau ISSN..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="input-field"
              style={{ paddingLeft: 42, width: '100%', height: 42 }}
            />
          </div>

          {/* SINTA Filter Pills */}
          <div style={{ display: 'flex', gap: 6, alignItems: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => setSelectedSinta(null)}
              className={`pill-btn ${selectedSinta === null ? 'active' : ''}`}
              style={{
                padding: '6px 12px',
                borderRadius: 20,
                fontSize: 12,
                cursor: 'pointer',
                fontWeight: 600,
                background: selectedSinta === null ? 'var(--primary)' : 'var(--bg-card)',
                color: selectedSinta === null ? '#fff' : 'var(--text-secondary)',
                border: '1px solid var(--border)',
              }}
            >
              Semua SINTA
            </button>
            {[1, 2, 3, 4, 5, 6].map((rank) => {
              const active = selectedSinta === rank
              const c = SINTA_COLORS[rank]
              return (
                <button
                  key={rank}
                  onClick={() => setSelectedSinta(active ? null : rank)}
                  style={{
                    padding: '6px 12px',
                    borderRadius: 20,
                    fontSize: 12,
                    cursor: 'pointer',
                    fontWeight: 600,
                    background: active ? c.bg : 'var(--bg-card)',
                    color: active ? c.text : 'var(--text-secondary)',
                    border: `1px solid ${active ? c.border : 'var(--border)'}`,
                    transition: 'all 0.15s ease',
                  }}
                >
                  S{rank}
                </button>
              )
            })}
          </div>

          {/* Scopus Toggle */}
          <button
            onClick={() => setScopusOnly(!scopusOnly)}
            style={{
              padding: '8px 16px',
              borderRadius: 20,
              fontSize: 12,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: scopusOnly ? 'rgba(6, 182, 212, 0.2)' : 'var(--bg-card)',
              color: scopusOnly ? '#06b6d4' : 'var(--text-secondary)',
              border: `1px solid ${scopusOnly ? 'rgba(6, 182, 212, 0.5)' : 'var(--border)'}`,
            }}
          >
            <ShieldCheck size={14} />
            <span>Scopus Only</span>
          </button>
        </div>
      </div>

      {/* Journal Cards List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '60px 0', color: 'var(--text-muted)' }}>
          <div className="spinner" style={{ margin: '0 auto 16px' }} />
          <div>Memuat data jurnal terverifikasi...</div>
        </div>
      ) : journals.length === 0 ? (
        <div className="glass-panel" style={{ textAlign: 'center', padding: '60px 20px', borderRadius: 16 }}>
          <BookOpen size={48} style={{ margin: '0 auto 16px', color: 'var(--text-muted)', opacity: 0.5 }} />
          <h3 style={{ fontSize: 18, color: 'var(--text-primary)', marginBottom: 8 }}>Tidak ada jurnal yang sesuai</h3>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14 }}>
            Coba ganti kata kunci pencarian atau sesuaikan filter SINTA / Scopus.
          </p>
        </div>
      ) : (
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fill, minmax(380px, 1fr))',
          gap: 18
        }}>
          {journals.map((journal) => {
            const sintaCol = journal.sinta_rank ? SINTA_COLORS[journal.sinta_rank] : null

            return (
              <div
                key={journal.id}
                className="journal-card glass-panel"
                style={{
                  padding: '20px 22px',
                  borderRadius: 16,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: 16,
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease',
                  border: '1px solid var(--border)',
                }}
              >
                <div>
                  {/* Badges Header */}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap', marginBottom: 12 }}>
                    {journal.sinta_rank && sintaCol && (
                      <span style={{
                        padding: '3px 10px',
                        borderRadius: 12,
                        fontSize: 11,
                        fontWeight: 700,
                        letterSpacing: '0.04em',
                        background: sintaCol.bg,
                        color: sintaCol.text,
                        border: `1px solid ${sintaCol.border}`,
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4
                      }}>
                        <Award size={12} />
                        SINTA {journal.sinta_rank}
                      </span>
                    )}

                    {journal.is_scopus_indexed && (
                      <span style={{
                        padding: '3px 10px',
                        borderRadius: 12,
                        fontSize: 11,
                        fontWeight: 700,
                        letterSpacing: '0.04em',
                        background: 'rgba(6, 182, 212, 0.15)',
                        color: '#06b6d4',
                        border: '1px solid rgba(6, 182, 212, 0.4)',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 4
                      }}>
                        <ShieldCheck size={12} />
                        Scopus Indexed
                      </span>
                    )}

                    {journal.is_open_access && (
                      <span style={{
                        padding: '3px 8px',
                        borderRadius: 12,
                        fontSize: 11,
                        fontWeight: 600,
                        background: 'rgba(16, 185, 129, 0.12)',
                        color: '#10b981',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                      }}>
                        Open Access
                      </span>
                    )}
                  </div>

                  {/* Journal Title */}
                  <h3 style={{
                    fontSize: 16,
                    fontWeight: 700,
                    color: 'var(--text-primary)',
                    lineHeight: 1.4,
                    marginBottom: 8
                  }}>
                    {journal.name}
                  </h3>

                  {/* Publisher & Metadata */}
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 6 }}>
                    {journal.publisher || 'Penerbit terakreditasi'}
                  </div>

                  <div style={{ display: 'flex', gap: 14, fontSize: 12, color: 'var(--text-muted)' }}>
                    {journal.issn && <span>ISSN: {journal.issn}</span>}
                    {journal.eissn && <span>E-ISSN: {journal.eissn}</span>}
                  </div>
                </div>

                {/* Footer Action Buttons */}
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  paddingTop: 14,
                  borderTop: '1px solid var(--border)',
                  gap: 8,
                  flexWrap: 'wrap'
                }}>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {journal.sinta_profile_url && (
                      <a
                        href={journal.sinta_profile_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-outline"
                        style={{
                          fontSize: 11,
                          padding: '5px 10px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          textDecoration: 'none',
                          color: '#10b981',
                          borderColor: 'rgba(16, 185, 129, 0.3)'
                        }}
                      >
                        <span>SINTA Profile</span>
                        <ExternalLink size={11} />
                      </a>
                    )}

                    {journal.scopus_source_url && (
                      <a
                        href={journal.scopus_source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-outline"
                        style={{
                          fontSize: 11,
                          padding: '5px 10px',
                          display: 'flex',
                          alignItems: 'center',
                          gap: 4,
                          textDecoration: 'none',
                          color: '#06b6d4',
                          borderColor: 'rgba(6, 182, 212, 0.3)'
                        }}
                      >
                        <span>Scopus Source</span>
                        <ExternalLink size={11} />
                      </a>
                    )}
                  </div>

                  <button
                    onClick={() => {
                      navigate(`/search?q=${encodeURIComponent(journal.name)}`)
                    }}
                    className="btn-ghost"
                    style={{
                      fontSize: 12,
                      padding: '5px 10px',
                      display: 'flex',
                      alignItems: 'center',
                      gap: 4,
                      color: 'var(--primary-light)',
                      cursor: 'pointer',
                      border: 'none',
                      background: 'transparent'
                    }}
                  >
                    <span>Cari Artikel</span>
                    <ArrowUpRight size={14} />
                  </button>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}
