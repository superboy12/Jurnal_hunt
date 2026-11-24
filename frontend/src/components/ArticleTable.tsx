import React, { useState } from 'react'
import type { SearchArticle } from '../api'
import { VerificationBadge, RelevanceScore, SourceBadges, CategoryBadge } from './Badges'
import { ExternalLink, FileText, Bookmark, Eye, ChevronDown, ChevronUp, Unlock, Copy } from 'lucide-react'
import { saveArticle } from '../api'
import toast from 'react-hot-toast'

interface ArticleTableProps {
  articles: SearchArticle[]
  onViewDetail: (article: SearchArticle) => void
}

export default function ArticleTable({ articles, onViewDetail }: ArticleTableProps) {
  const [sortCol, setSortCol] = useState<string>('rank')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const handleSort = (col: string) => {
    if (sortCol === col) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc')
    } else {
      setSortCol(col)
      setSortDir('asc')
    }
  }

  const SortIcon = ({ col }: { col: string }) => {
    if (sortCol !== col) return <ChevronDown size={12} style={{ opacity: 0.3 }} />
    return sortDir === 'asc' ? <ChevronUp size={12} /> : <ChevronDown size={12} />
  }

  const handleSave = async (articleId: string, e: React.MouseEvent) => {
    e.stopPropagation()
    try {
      await saveArticle(articleId, { status: 'want_to_read' })
      toast.success('Saved!')
    } catch {
      toast.error('Failed to save')
    }
  }

  const toggleSelect = (id: string, e: React.MouseEvent) => {
    e.stopPropagation()
    const next = new Set(selected)
    if (next.has(id)) next.delete(id)
    else next.add(id)
    setSelected(next)
  }

  const toggleAll = () => {
    if (selected.size === articles.length) {
      setSelected(new Set())
    } else {
      setSelected(new Set(articles.map(a => a.article.id)))
    }
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th style={{ width: 36 }}>
              <input
                type="checkbox"
                checked={selected.size === articles.length && articles.length > 0}
                onChange={toggleAll}
                style={{ width: 14, height: 14 }}
              />
            </th>
            <th onClick={() => handleSort('rank')} style={{ cursor: 'pointer' }}>
              # <SortIcon col="rank" />
            </th>
            <th style={{ minWidth: 300 }}>Title</th>
            <th style={{ minWidth: 120 }}>Authors</th>
            <th onClick={() => handleSort('year')} style={{ cursor: 'pointer', width: 70 }}>
              Year <SortIcon col="year" />
            </th>
            <th style={{ minWidth: 180 }}>Journal</th>
            <th style={{ width: 120 }}>Indexing</th>
            <th onClick={() => handleSort('score')} style={{ cursor: 'pointer', width: 80 }}>
              Score <SortIcon col="score" />
            </th>
            <th style={{ width: 60 }}>OA</th>
            <th style={{ width: 120 }}>Sources</th>
            <th style={{ width: 120 }}>Actions</th>
          </tr>
        </thead>
        <tbody>
          {articles.map((sa) => {
            const art = sa.article
            const firstAuthor = art.authors?.[0]?.name
            const moreAuthors = (art.authors?.length || 0) - 1
            const cleanDoi = art.doi ? art.doi.trim().replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, '') : ''
            const doiUrl = cleanDoi ? `https://doi.org/${cleanDoi}` : null

            return (
              <tr
                key={art.id}
                onClick={() => onViewDetail(sa)}
                style={{ cursor: 'pointer' }}
              >
                <td onClick={e => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selected.has(art.id)}
                    onChange={() => {}}
                    onClick={(e) => toggleSelect(art.id, e)}
                    style={{ width: 14, height: 14 }}
                  />
                </td>
                <td style={{ color: 'var(--text-muted)', fontSize: 12 }}>
                  {sa.rank || '—'}
                </td>
                <td>
                  {(art.subject_category || sa.subject_category) && (
                    <div style={{ marginBottom: 5 }}>
                      <CategoryBadge category={art.subject_category || sa.subject_category} small />
                    </div>
                  )}
                  <div style={{ fontWeight: 600, fontSize: 13, lineHeight: 1.4, marginBottom: 4, color: 'var(--text-primary)' }}>
                    {art.title}
                  </div>
                  {art.doi && (
                    <div style={{ fontSize: 11, color: 'var(--text-muted)', display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                      <span>DOI: {cleanDoi}</span>
                      <button
                        onClick={(e) => {
                          e.stopPropagation()
                          navigator.clipboard.writeText(cleanDoi)
                          toast.success(`DOI ${cleanDoi} disalin!`)
                        }}
                        className="btn-ghost"
                        style={{ padding: '0 5px', height: 18, fontSize: 10, display: 'inline-flex', alignItems: 'center', gap: 3, color: '#fb7185' }}
                        title="Salin nomor DOI ini untuk ditempel di Sci-Hub (https://sci-hub.box/)"
                      >
                        <Copy size={10} /> Salin
                      </button>
                    </div>
                  )}
                </td>
                <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  {firstAuthor}
                  {moreAuthors > 0 && (
                    <span style={{ color: 'var(--text-muted)' }}> +{moreAuthors}</span>
                  )}
                </td>
                <td style={{ fontSize: 13, fontWeight: 600 }}>{art.year || '—'}</td>
                <td style={{ fontSize: 12, color: 'var(--text-secondary)' }}>
                  <div style={{ maxWidth: 200, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {art.journal_name || '—'}
                  </div>
                </td>
                <td>
                  <VerificationBadge
                    status={art.verification_status}
                    sintaRank={sa.sinta_rank ?? undefined}
                    isScopus={sa.is_scopus ?? undefined}
                    scimagoQuartile={sa.scimago_quartile ?? undefined}
                    sjrScore={sa.sjr_score ?? undefined}
                    small
                  />
                </td>
                <td>
                  <RelevanceScore score={sa.relevance_score} small />
                </td>
                <td>
                  {art.is_open_access === true ? (
                    <span className="badge-oa" style={{ fontSize: 10 }} title="Open Access (Gratis / Bebas Biaya)">OA</span>
                  ) : art.is_open_access === false ? (
                    <span
                      style={{
                        fontSize: 9,
                        fontWeight: 700,
                        padding: '1px 5px',
                        borderRadius: 4,
                        background: 'rgba(239, 68, 68, 0.15)',
                        color: '#f87171',
                        border: '1px solid rgba(239, 68, 68, 0.3)',
                        display: 'inline-block'
                      }}
                      title="Artikel Berbayar / Terkunci (Gunakan Sci-Hub)"
                    >
                      Paywall
                    </span>
                  ) : (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>—</span>
                  )}
                </td>
                <td>
                  <SourceBadges sources={art.sources || []} />
                </td>
                <td onClick={e => e.stopPropagation()}>
                  <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
                    <button
                      className="btn-ghost"
                      onClick={() => onViewDetail(sa)}
                      title="Detail"
                      style={{ padding: '4px 8px' }}
                    >
                      <Eye size={13} />
                    </button>
                    {(art.article_url || doiUrl) && (
                      <a
                        href={art.article_url || doiUrl!}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-ghost"
                        title={art.is_open_access === true ? "Buka laman naskah (Open Access)" : "Open article"}
                        style={{ padding: '4px 8px', display: 'flex', alignItems: 'center' }}
                      >
                        <ExternalLink size={13} />
                      </a>
                    )}
                    {art.pdf_url && (
                      <a
                        href={art.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-ghost"
                        title="Unduh PDF Resmi (Open Access Gratis)"
                        style={{ padding: '4px 8px', display: 'flex', alignItems: 'center', color: '#10b981' }}
                      >
                        <FileText size={13} />
                      </a>
                    )}
                    {cleanDoi && (
                      <a
                        href={`https://sci-hub.box/${cleanDoi}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="btn-ghost"
                        title={art.is_open_access === false ? "Unduh via Sci-Hub (Bypass Paywall)" : "Buka via Sci-Hub (Mirror Cadangan)"}
                        style={{
                          padding: '4px 8px',
                          display: 'flex',
                          alignItems: 'center',
                          color: (art.is_open_access === false) ? '#f43f5e' : '#fda4af',
                        }}
                      >
                        <Unlock size={13} />
                      </a>
                    )}
                    <button
                      className="btn-ghost"
                      onClick={(e) => handleSave(art.id, e)}
                      title="Save article"
                      style={{ padding: '4px 8px' }}
                    >
                      <Bookmark size={13} />
                    </button>
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
