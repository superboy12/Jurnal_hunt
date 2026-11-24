import React, { useState } from 'react'
import type { SearchArticle, AISummary } from '../api'
import { VerificationBadge, RelevanceScore, SourceBadges, CategoryBadge } from './Badges'
import {
  ExternalLink, FileText, Bookmark, Copy, ChevronDown,
  ChevronUp, X, CheckCircle, BookOpen, User, Sparkles,
  Layers, CheckSquare, Lightbulb, Compass, Award, Unlock
} from 'lucide-react'
import { saveArticle, getCitation, getArticleAISummary, autoResolveAccess } from '../api'
import toast from 'react-hot-toast'

interface ArticleDetailProps {
  searchArticle: SearchArticle
  onClose?: () => void
}

export default function ArticleDetail({ searchArticle, onClose }: ArticleDetailProps) {
  const {
    article,
    relevance_score,
    relevance_reason,
    sinta_rank,
    is_scopus,
    scimago_quartile,
    sjr_score,
    scimago_url,
  } = searchArticle

  const [citationOpen, setCitationOpen] = useState(false)
  const [citation, setCitation] = useState('')
  const [citFormat, setCitFormat] = useState('apa7')
  const [saving, setSaving] = useState(false)
  const [saved, setSaved] = useState(false)
  const [copiedDoi, setCopiedDoi] = useState(false)
  const [autoResolving, setAutoResolving] = useState(false)

  // Clean DOI for Sci-Hub integration (https://sci-hub.box/<doi>)
  const cleanDoi = article.doi ? article.doi.trim().replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '') : ''
  const sciHubUrl = cleanDoi ? `https://sci-hub.box/${cleanDoi}` : 'https://sci-hub.box/'

  const handleCopyDoi = () => {
    if (cleanDoi) {
      navigator.clipboard.writeText(cleanDoi)
      setCopiedDoi(true)
      toast.success(`DOI ${cleanDoi} berhasil disalin! Silakan tempel di Sci-Hub.`)
      setTimeout(() => setCopiedDoi(false), 2500)
    }
  }

  // AI Summary State
  const [aiSummary, setAiSummary] = useState<AISummary | null>(null)
  const [isSummarizing, setIsSummarizing] = useState(false)

  const authorsStr = article.authors?.map(a => a.name).join(', ') || 'Unknown authors'

  const handleSave = async () => {
    setSaving(true)
    try {
      await saveArticle(article.id, { status: 'want_to_read' })
      setSaved(true)
      toast.success('Artikel tersimpan di bookmark!')
    } catch {
      toast.error('Gagal menyimpan artikel')
    } finally {
      setSaving(false)
    }
  }

  const handleCitation = async (format: string) => {
    setCitFormat(format)
    try {
      const res = await getCitation(article.id, format)
      setCitation(res.data.citation)
      setCitationOpen(true)
    } catch {
      toast.error('Gagal memuat sitasi')
    }
  }

  const handleAISummarize = async () => {
    setIsSummarizing(true)
    try {
      const res = await getArticleAISummary(article.id)
      setAiSummary(res.data)
      toast.success('Analisis AI selesai!')
    } catch (err: any) {
      toast.error('Gagal menghasilkan analisis AI')
    } finally {
      setIsSummarizing(false)
    }
  }

  const handleAutoResolve = async () => {
    setAutoResolving(true)
    try {
      const res = await autoResolveAccess(article.id)
      const data = res.data
      if (data.status === 'open_access') {
        toast.success(data.message)
        if (data.url) window.open(data.url, '_blank')
      } else if (data.status === 'sci_hub') {
        toast(data.message, { icon: '🔓' })
        if (data.url) window.open(data.url, '_blank')
      } else {
        toast.error(data.message)
      }
    } catch {
      toast.error('Gagal me-resolve akses artikel')
    } finally {
      setAutoResolving(false)
    }
  }

  const handleCopy = (text: string) => {
    navigator.clipboard.writeText(text)
    toast.success('Disalin ke clipboard!')
  }

  const doiUrl = article.doi ? `https://doi.org/${article.doi}` : null

  return (
    <div style={{
      background: 'var(--bg-card)',
      border: '1px solid var(--border)',
      borderRadius: 16,
      padding: 24,
      boxShadow: 'var(--shadow-card)',
      position: 'relative',
    }}>
      {/* Header with Close */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <VerificationBadge
            status={article.verification_status}
            sintaRank={sinta_rank}
            isScopus={is_scopus}
            scimagoQuartile={scimago_quartile}
            sjrScore={sjr_score}
            isOA={article.is_open_access}
          />
          {(article.subject_category || searchArticle.subject_category) && (
            <CategoryBadge category={article.subject_category || searchArticle.subject_category} />
          )}
          <SourceBadges sources={article.sources || []} />
          {article.publication_type && (
            <span style={{
              fontSize: 11,
              padding: '2px 8px',
              borderRadius: 4,
              background: 'var(--bg-surface)',
              color: 'var(--text-muted)',
              border: '1px solid var(--border)',
            }}>
              {article.publication_type}
            </span>
          )}
        </div>
        {onClose && (
          <button onClick={onClose} style={{
            background: 'none', border: 'none', color: 'var(--text-muted)',
            cursor: 'pointer', padding: 4, borderRadius: 6,
          }}>
            <X size={18} />
          </button>
        )}
      </div>

      {/* Title */}
      <h2 style={{
        fontSize: 18,
        fontWeight: 700,
        color: 'var(--text-primary)',
        lineHeight: 1.4,
        marginBottom: 12,
        fontFamily: 'Space Grotesk, sans-serif',
      }}>
        {article.title}
      </h2>

      {/* Authors & Meta */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 16, fontSize: 13, color: 'var(--text-secondary)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <User size={14} color="var(--text-muted)" />
          <span>{authorsStr}</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
          <BookOpen size={14} color="var(--text-muted)" />
          <span>{article.journal_name || 'Jurnal Ilmiah'}</span>
          {article.year && <span>• <b>{article.year}</b></span>}
          {article.volume && <span>• Vol. {article.volume}</span>}
          {article.issue && <span>• No. {article.issue}</span>}
          {article.pages && <span>• Hal. {article.pages}</span>}
          {article.publisher && <span>• {article.publisher}</span>}
        </div>
      </div>

      {/* Relevance Card */}
      {relevance_score !== undefined && (
        <div style={{
          background: 'var(--bg-surface)',
          border: '1px solid var(--border)',
          borderRadius: 10,
          padding: '12px 14px',
          marginBottom: 16,
          display: 'flex',
          gap: 12,
          alignItems: 'center',
        }}>
          <RelevanceScore score={relevance_score} />
          <div style={{ flex: 1, fontSize: 12 }}>
            <div style={{ fontWeight: 600, color: 'var(--text-primary)', marginBottom: 2 }}>
              Skor Relevansi Terhadap Perintah
            </div>
            {relevance_reason && (
              <div style={{ color: 'var(--text-secondary)' }}>{relevance_reason}</div>
            )}
          </div>
        </div>
      )}

      {/* Access Status Banner */}
      {article.is_open_access === true ? (
        <div style={{
          padding: '12px 16px', borderRadius: 10, marginBottom: 16,
          background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.35)',
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <CheckCircle size={18} color="#34d399" />
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#34d399' }}>Jurnal Open Access (Akses Terbuka & Bebas Biaya)</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Makalah ini diterbitkan dengan akses terbuka penuh dari penerbit resmi dan bebas dibaca atau diunduh secara legal.</div>
            </div>
          </div>
          <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 4, background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', fontWeight: 700 }}>
            100% Bebas Unduh
          </span>
        </div>
      ) : article.is_open_access === false ? (
        <div style={{
          padding: '12px 16px', borderRadius: 10, marginBottom: 16,
          background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.35)',
          display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap', justifyContent: 'space-between'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <Unlock size={18} color="#f87171" />
            <div>
              <div style={{ fontWeight: 700, fontSize: 13, color: '#f87171' }}>Artikel Berbayar / Terkunci (Non-Open Access)</div>
              <div style={{ fontSize: 11, color: 'var(--text-secondary)' }}>Naskah ini terkunci langganan di penerbit resmi. Gunakan Sci-Hub di bawah untuk mengunduh naskah lengkap.</div>
            </div>
          </div>
          <span style={{ fontSize: 11, padding: '3px 10px', borderRadius: 4, background: 'rgba(239, 68, 68, 0.2)', color: '#f87171', fontWeight: 700 }}>
            Terkunci Paywall
          </span>
        </div>
      ) : null}

      {/* Action Buttons */}
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 20 }}>
        {doiUrl && (
          <a
            href={doiUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-outline"
            style={{ fontSize: 12, padding: '7px 12px', display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none' }}
          >
            <ExternalLink size={13} />
            DOI: {cleanDoi || article.doi}
          </a>
        )}
        {cleanDoi && (
          <button
            onClick={handleCopyDoi}
            className="btn-outline"
            style={{
              fontSize: 12,
              padding: '7px 12px',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              color: copiedDoi ? '#34d399' : 'var(--text-secondary)',
              borderColor: copiedDoi ? 'rgba(16, 185, 129, 0.5)' : 'var(--border)'
            }}
            title="Salin nomor DOI artikel ini untuk ditempel di Sci-Hub (https://sci-hub.box/)"
          >
            {copiedDoi ? <CheckCircle size={13} color="#34d399" /> : <Copy size={13} />}
            <span>{copiedDoi ? 'DOI Tersalin!' : 'Salin DOI'}</span>
          </button>
        )}
        {article.pdf_url && (
          <a
            href={article.pdf_url}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary"
            style={{
              fontSize: 12, padding: '7px 14px', display: 'flex', alignItems: 'center', gap: 6, textDecoration: 'none',
              background: 'linear-gradient(135deg, #059669, #10b981)', borderColor: '#059669'
            }}
          >
            <FileText size={13} />
            Unduh Full-Text PDF {article.is_open_access ? '(Gratis)' : ''}
          </a>
        )}
        {cleanDoi && (
          <a
            href={sciHubUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-secondary"
            style={{
              fontSize: 12,
              padding: '7px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              textDecoration: 'none',
              background: article.is_open_access === false
                ? 'linear-gradient(135deg, rgba(225, 29, 72, 0.25), rgba(190, 18, 60, 0.4))'
                : 'rgba(255, 255, 255, 0.05)',
              borderColor: article.is_open_access === false ? 'rgba(225, 29, 72, 0.5)' : 'var(--border)',
              color: article.is_open_access === false ? '#fda4af' : 'var(--text-secondary)',
              fontWeight: 600,
            }}
            title="Buka atau unduh naskah lengkap melalui Sci-Hub (https://sci-hub.box/)"
          >
            <Unlock size={13} color={article.is_open_access === false ? '#fb7185' : 'var(--text-muted)'} />
            <span>{article.is_open_access === false ? 'Unduh via Sci-Hub (Bypass Paywall)' : 'Buka via Sci-Hub (Mirror)'}</span>
          </a>
        )}
        {/* Auto Open Access Button for paywalled articles */}
        {(article.is_open_access === false || article.is_open_access === null) && (
          <button
            onClick={handleAutoResolve}
            disabled={autoResolving}
            className="btn-secondary"
            style={{
              fontSize: 12,
              padding: '7px 14px',
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(5, 150, 105, 0.3))',
              borderColor: 'rgba(16, 185, 129, 0.4)',
              color: '#34d399',
              fontWeight: 600,
            }}
            title="Cari akses terbuka secara otomatis via Unpaywall atau Sci-Hub"
          >
            {autoResolving ? (
              <div className="spinner" style={{ width: 13, height: 13 }} />
            ) : (
              <Unlock size={13} color="#34d399" />
            )}
            <span>{autoResolving ? 'Mencari akses...' : '🔓 Buka Otomatis'}</span>
          </button>
        )}
        <button
          onClick={handleAISummarize}
          disabled={isSummarizing}
          className="btn-secondary"
          style={{
            fontSize: 12,
            padding: '7px 14px',
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(168,85,247,0.2))',
            borderColor: 'rgba(99,102,241,0.4)',
            color: 'var(--primary-light)',
          }}
        >
          {isSummarizing ? (
            <div className="spinner" style={{ width: 13, height: 13 }} />
          ) : (
            <Sparkles size={13} color="#a855f7" />
          )}
          <span>{aiSummary ? 'Perbarui Ringkasan AI' : 'Bedah dengan AI (Gemini)'}</span>
        </button>
        <button
          onClick={handleSave}
          disabled={saving || saved}
          className="btn-secondary"
          style={{ fontSize: 12, padding: '7px 12px', display: 'flex', alignItems: 'center', gap: 6 }}
        >
          <Bookmark size={13} fill={saved ? 'currentColor' : 'none'} />
          {saved ? 'Tersimpan' : 'Simpan'}
        </button>
      </div>

      {/* Sci-Hub Paywall Bypass & Mirror Panel (https://sci-hub.box/) */}
      {cleanDoi && (
        <div style={{
          padding: '14px 18px',
          borderRadius: 12,
          marginBottom: 18,
          background: article.is_open_access === false
            ? 'linear-gradient(135deg, rgba(225, 29, 72, 0.08), rgba(159, 18, 57, 0.12))'
            : article.is_open_access === true
            ? 'rgba(16, 185, 129, 0.04)'
            : 'rgba(255, 255, 255, 0.02)',
          border: article.is_open_access === false
            ? '1px solid rgba(225, 29, 72, 0.35)'
            : article.is_open_access === true
            ? '1px solid rgba(16, 185, 129, 0.2)'
            : '1px solid rgba(255, 255, 255, 0.08)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 8, flexWrap: 'wrap', gap: 8 }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <Unlock size={16} color={article.is_open_access === false ? '#fb7185' : '#34d399'} />
              <h4 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: article.is_open_access === false ? '#fb7185' : 'var(--text-primary)' }}>
                {article.is_open_access === false
                  ? 'Akses Naskah Bebas via Sci-Hub (Bypass Paywall)'
                  : 'Akses Mirror Cadangan via Sci-Hub'}
              </h4>
              <span style={{
                fontSize: 10, fontWeight: 700, padding: '2px 8px', borderRadius: 4,
                ...(article.is_open_access === false
                  ? { background: 'rgba(225, 29, 72, 0.25)', color: '#fda4af', border: '1px solid rgba(225, 29, 72, 0.4)' }
                  : { background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)' }
                )
              }}>
                {article.is_open_access === false ? 'Solusi Jurnal Berbayar / Terkunci' : 'Jurnal Open Access Resmi'}
              </span>
            </div>
            <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
              Situs resmi: <a href="https://sci-hub.box/" target="_blank" rel="noopener noreferrer" style={{ color: article.is_open_access === false ? '#fb7185' : '#34d399', textDecoration: 'underline' }}>sci-hub.box</a>
            </span>
          </div>

          <p style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 10px 0' }}>
            {article.is_open_access === false
              ? 'Artikel ini terkunci (berbayar) di penerbit resmi. Anda dapat mengunduh naskah lengkapnya secara bebas di Sci-Hub menggunakan tautan instan di bawah atau menyalin nomor DOI.'
              : 'Artikel ini berstatus Open Access resmi dan bebas diakses dari penerbit. Anda dapat mengunduh naskah resmi di atas, atau menggunakan Sci-Hub sebagai mirror cadangan jika tautan penerbit mengalami kendala.'}
          </p>

          <div style={{
            display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            flexWrap: 'wrap', gap: 10, padding: '10px 14px', borderRadius: 8,
            background: 'rgba(0, 0, 0, 0.25)', border: '1px solid rgba(255, 255, 255, 0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text-primary)', flexWrap: 'wrap' }}>
              <span style={{ color: 'var(--text-muted)' }}>Nomor DOI:</span>
              <code style={{ background: 'rgba(255, 255, 255, 0.08)', padding: '2px 8px', borderRadius: 4, fontFamily: 'monospace', color: article.is_open_access === false ? '#fb7185' : '#34d399', fontWeight: 600 }}>
                {cleanDoi}
              </code>
            </div>

            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              <button
                onClick={handleCopyDoi}
                className="btn-secondary"
                style={{
                  fontSize: 11, padding: '5px 12px', display: 'flex', alignItems: 'center', gap: 5,
                  color: copiedDoi ? '#34d399' : 'var(--text-secondary)',
                  borderColor: copiedDoi ? 'rgba(16, 185, 129, 0.5)' : 'var(--border)'
                }}
                title="Salin nomor DOI artikel ini untuk ditempel di Sci-Hub"
              >
                {copiedDoi ? <CheckCircle size={12} color="#34d399" /> : <Copy size={12} />}
                <span>{copiedDoi ? 'DOI Tersalin!' : 'Salin DOI'}</span>
              </button>

              <a
                href={sciHubUrl}
                target="_blank"
                rel="noopener noreferrer"
                style={{
                  textDecoration: 'none', fontSize: 11, padding: '6px 14px', borderRadius: 6,
                  background: article.is_open_access === false
                    ? 'linear-gradient(135deg, #e11d48, #be123c)'
                    : 'linear-gradient(135deg, #0284c7, #0369a1)',
                  color: '#fff',
                  display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600,
                  boxShadow: article.is_open_access === false ? '0 2px 8px rgba(225, 29, 72, 0.3)' : 'none'
                }}
              >
                <Unlock size={12} /> {article.is_open_access === false ? 'Buka Langsung di Sci-Hub' : 'Buka Mirror Sci-Hub'} <ExternalLink size={11} />
              </a>
            </div>
          </div>
        </div>
      )}

      {/* SCImago Journal Rank (SJR) & Scopus Verification Box */}
      <div style={{
        padding: '16px 18px', borderRadius: 12, marginBottom: 18,
        background: is_scopus ? 'rgba(2, 132, 199, 0.08)' : 'rgba(255, 255, 255, 0.03)',
        border: is_scopus ? '1px solid rgba(2, 132, 199, 0.35)' : '1px solid rgba(255, 255, 255, 0.1)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <Award size={16} color={is_scopus ? '#38bdf8' : '#9ca3af'} />
            <h4 style={{ margin: 0, fontSize: 13, fontWeight: 700, color: is_scopus ? '#38bdf8' : 'var(--text-primary)' }}>
              Analisis SCImago Journal Rank (Scopus Authority)
            </h4>
          </div>
          <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>
            Sumber data: <a href="https://www.scimagojr.com/" target="_blank" rel="noopener noreferrer" style={{ color: '#38bdf8', textDecoration: 'underline' }}>scimagojr.com</a>
          </span>
        </div>

        {/* SCImago Result Details */}
        <div style={{
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          flexWrap: 'wrap', gap: 12, padding: '10px 14px', borderRadius: 8,
          background: 'rgba(0, 0, 0, 0.25)', marginBottom: 12
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{
              fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 6,
              background: is_scopus ? 'rgba(16, 185, 129, 0.2)' : 'rgba(239, 68, 68, 0.15)',
              color: is_scopus ? '#34d399' : '#f87171',
              border: is_scopus ? '1px solid rgba(16, 185, 129, 0.4)' : '1px solid rgba(239, 68, 68, 0.3)'
            }}>
              {is_scopus ? '✓ Terverifikasi Scopus' : '✗ Bukan Jurnal Scopus (Tidak Terdaftar di SCImago)'}
            </span>

            {scimago_quartile && (
              <span style={{
                fontSize: 12, fontWeight: 800, padding: '3px 10px', borderRadius: 6,
                ...(scimago_quartile === 'Q1'
                  ? { background: 'rgba(245, 158, 11, 0.25)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.6)' }
                  : scimago_quartile === 'Q2'
                  ? { background: 'rgba(16, 185, 129, 0.25)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.6)' }
                  : scimago_quartile === 'Q3'
                  ? { background: 'rgba(59, 130, 246, 0.25)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.6)' }
                  : { background: 'rgba(168, 85, 247, 0.25)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.6)' }
                )
              }}>
                Kuartil {scimago_quartile}
              </span>
            )}

            {sjr_score !== undefined && sjr_score !== null && (
              <span style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                Nilai SJR: <b style={{ color: '#38bdf8' }}>{sjr_score}</b>
              </span>
            )}
          </div>

          <a
            href={scimago_url || `https://www.scimagojr.com/journalsearch.php?q=${encodeURIComponent(article.journal_name || '')}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: 'none', fontSize: 12, padding: '6px 12px', borderRadius: 6,
              background: 'linear-gradient(135deg, #0284c7, #0369a1)', color: '#fff',
              display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600
            }}
          >
            Buka Profil SCImago JR <ExternalLink size={12} />
          </a>
        </div>

        {/* 1-Click Verification Links */}
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', alignItems: 'center' }}>
          <span style={{ fontSize: 11, color: 'var(--text-muted)', marginRight: 2 }}>Verifikasi Otoritas Lain:</span>
          <a
            href={`https://www.scopus.com/sources.uri?query=${encodeURIComponent(article.journal_name || '')}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: 'none', fontSize: 11, padding: '4px 8px', borderRadius: 6,
              background: 'rgba(255, 102, 0, 0.15)', color: '#ff7700', border: '1px solid rgba(255, 102, 0, 0.3)',
              display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600
            }}
          >
            Scopus Sources <ExternalLink size={10} />
          </a>
          <a
            href={`https://sinta.kemdikbud.go.id/journals?q=${encodeURIComponent(article.journal_name || '')}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: 'none', fontSize: 11, padding: '4px 8px', borderRadius: 6,
              background: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.3)',
              display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600
            }}
          >
            SINTA Kemdikbud <ExternalLink size={10} />
          </a>
          {article.doi && (
            <a
              href={`https://api.unpaywall.org/v2/${article.doi}?email=user@journalhunter.app`}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                textDecoration: 'none', fontSize: 11, padding: '4px 8px', borderRadius: 6,
                background: 'rgba(139, 92, 246, 0.15)', color: '#c084fc', border: '1px solid rgba(139, 92, 246, 0.3)',
                display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600
              }}
            >
              Unpaywall OA <ExternalLink size={10} />
            </a>
          )}
          <a
            href={`https://europepmc.org/search?query=${encodeURIComponent(article.doi || article.title || '')}`}
            target="_blank"
            rel="noopener noreferrer"
            style={{
              textDecoration: 'none', fontSize: 11, padding: '4px 8px', borderRadius: 6,
              background: 'rgba(236, 72, 153, 0.15)', color: '#f472b6', border: '1px solid rgba(236, 72, 153, 0.3)',
              display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600
            }}
          >
            Europe PMC <ExternalLink size={10} />
          </a>
          {cleanDoi && (
            <a
              href={sciHubUrl}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                textDecoration: 'none', fontSize: 11, padding: '4px 8px', borderRadius: 6,
                background: 'rgba(225, 29, 72, 0.15)', color: '#fb7185', border: '1px solid rgba(225, 29, 72, 0.3)',
                display: 'flex', alignItems: 'center', gap: 4, fontWeight: 600
              }}
            >
              Sci-Hub Unlock <ExternalLink size={10} />
            </a>
          )}
        </div>
      </div>

      {/* AI Deep Summary Box */}
      {aiSummary && (
        <div className="glass-panel" style={{
          padding: '16px 18px',
          borderRadius: 14,
          marginBottom: 20,
          background: 'rgba(99, 102, 241, 0.05)',
          border: '1px solid rgba(99, 102, 241, 0.3)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 12 }}>
            <Sparkles size={16} color="var(--primary-light)" />
            <h4 style={{ margin: 0, fontSize: 14, fontWeight: 700, color: 'var(--primary-light)' }}>
              Hasil Analisis & Ekstraksi AI (Google Gemini)
            </h4>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
            <div>
              <b style={{ color: 'var(--text-primary)' }}>🎯 Tujuan Penelitian:</b>
              <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)' }}>{aiSummary.objective}</p>
            </div>
            <div>
              <b style={{ color: 'var(--text-primary)' }}>🔬 Metodologi:</b>
              <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)' }}>{aiSummary.methodology}</p>
            </div>
            <div>
              <b style={{ color: 'var(--text-primary)' }}>📊 Temuan Utama:</b>
              <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)' }}>{aiSummary.findings}</p>
            </div>
            <div>
              <b style={{ color: 'var(--text-primary)' }}>💡 Implikasi Praktis:</b>
              <p style={{ margin: '3px 0 0', color: 'var(--text-secondary)' }}>{aiSummary.implications}</p>
            </div>
            {aiSummary.key_takeaways?.length > 0 && (
              <div>
                <b style={{ color: 'var(--text-primary)' }}>🔑 Poin Kunci (Key Takeaways):</b>
                <ul style={{ margin: '4px 0 0', paddingLeft: 18, color: 'var(--text-secondary)' }}>
                  {aiSummary.key_takeaways.map((takeaway, idx) => (
                    <li key={idx} style={{ marginBottom: 3 }}>{takeaway}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Abstract */}
      <div style={{ marginBottom: 20 }}>
        <h3 style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 8 }}>
          Abstrak
        </h3>
        <p style={{
          fontSize: 13,
          lineHeight: 1.7,
          color: 'var(--text-secondary)',
          background: 'var(--bg-surface)',
          padding: '12px 14px',
          borderRadius: 8,
          border: '1px solid var(--border)',
        }}>
          {article.abstract || 'Abstrak tidak tersedia dari penerbit.'}
        </p>
      </div>

      {/* Citation Generator */}
      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 10 }}>
          <span style={{ fontSize: 13, fontWeight: 600, color: 'var(--text-primary)' }}>Sitasi Akademik</span>
          <div style={{ display: 'flex', gap: 6 }}>
            {['apa7', 'bibtex', 'ris'].map(fmt => (
              <button
                key={fmt}
                onClick={() => handleCitation(fmt)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 6,
                  fontSize: 11,
                  fontWeight: 600,
                  border: '1px solid var(--border)',
                  background: citFormat === fmt && citationOpen ? 'var(--primary)' : 'var(--bg-surface)',
                  color: citFormat === fmt && citationOpen ? '#fff' : 'var(--text-secondary)',
                  cursor: 'pointer',
                  textTransform: 'uppercase',
                }}
              >
                {fmt}
              </button>
            ))}
          </div>
        </div>

        {citationOpen && citation && (
          <div style={{
            background: 'var(--bg-surface)',
            border: '1px solid var(--border)',
            borderRadius: 8,
            padding: '10px 14px',
            position: 'relative',
          }}>
            <pre style={{
              fontSize: 12,
              fontFamily: 'monospace',
              color: 'var(--text-secondary)',
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-all',
              margin: 0,
            }}>
              {citation}
            </pre>
            <button
              onClick={() => handleCopy(citation)}
              style={{
                position: 'absolute',
                top: 8,
                right: 8,
                background: 'var(--bg-card)',
                border: '1px solid var(--border)',
                borderRadius: 4,
                padding: '3px 8px',
                color: 'var(--text-muted)',
                fontSize: 11,
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: 4,
              }}
            >
              <Copy size={11} /> Salin
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
