import React from 'react'
import type { SearchArticle } from '../api'

interface VerificationBadgeProps {
  status?: string
  sintaRank?: number
  isScopus?: boolean
  scimagoQuartile?: string
  sjrScore?: number
  isOA?: boolean
  small?: boolean
}

const VERIFICATION_CONFIG: Record<string, { label: string; className: string }> = {
  verified_scopus: { label: 'Scopus ✓', className: 'badge-scopus' },
  verified_sinta: { label: 'SINTA ✓', className: 'badge-sinta' },
  verified_both: { label: 'Scopus+SINTA ✓', className: 'badge-both' },
  not_verified: { label: 'Not Verified', className: 'badge-pending' },
  unavailable: { label: 'Verification N/A', className: 'badge-pending' },
  conflicting: { label: '⚠ Conflicting', className: 'badge-pending' },
  pending: { label: 'Pending', className: 'badge-pending' },
}

export function VerificationBadge({
  status,
  sintaRank,
  isScopus,
  scimagoQuartile,
  sjrScore,
  isOA,
  small,
}: VerificationBadgeProps) {
  const cfg = VERIFICATION_CONFIG[status || 'pending'] || VERIFICATION_CONFIG.pending
  const size = small ? { fontSize: 10, padding: '1px 6px' } : {}

  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4, alignItems: 'center' }}>
      <span className={cfg.className} style={size}>{cfg.label}</span>
      {sintaRank && (
        <span className="badge-sinta" style={{ ...size }}>S{sintaRank}</span>
      )}
      {scimagoQuartile && (
        <span
          title={`SCImago Journal Rank: ${scimagoQuartile}${sjrScore !== undefined && sjrScore !== null ? ` (SJR: ${sjrScore})` : ''}`}
          style={{
            ...size,
            fontWeight: 700,
            borderRadius: 4,
            display: 'inline-flex',
            alignItems: 'center',
            cursor: 'help',
            ...(scimagoQuartile === 'Q1'
              ? { background: 'rgba(245, 158, 11, 0.2)', color: '#fbbf24', border: '1px solid rgba(245, 158, 11, 0.5)' }
              : scimagoQuartile === 'Q2'
              ? { background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', border: '1px solid rgba(16, 185, 129, 0.5)' }
              : scimagoQuartile === 'Q3'
              ? { background: 'rgba(59, 130, 246, 0.2)', color: '#60a5fa', border: '1px solid rgba(59, 130, 246, 0.5)' }
              : { background: 'rgba(168, 85, 247, 0.2)', color: '#c084fc', border: '1px solid rgba(168, 85, 247, 0.5)' }
            ),
          }}
        >
          {scimagoQuartile}
        </span>
      )}
      {isScopus && !scimagoQuartile && status !== 'verified_scopus' && status !== 'verified_both' && (
        <span className="badge-scopus" style={size}>Scopus</span>
      )}
      {isOA && (
        <span className="badge-oa" style={size}>OA</span>
      )}
    </div>
  )
}

interface RelevanceScoreProps {
  score: number
  small?: boolean
}

export function RelevanceScore({ score, small }: RelevanceScoreProps) {
  const color = score >= 70 ? 'var(--success)' : score >= 40 ? 'var(--warning)' : 'var(--danger)'
  const size = small ? 13 : 15

  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <div style={{
        width: small ? 32 : 40, height: small ? 32 : 40,
        borderRadius: '50%',
        border: `2px solid ${color}`,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        fontSize: size - 1, fontWeight: 700, color,
        background: `${color}15`,
      }}>
        {score.toFixed(0)}
      </div>
      {!small && (
        <div style={{ flex: 1, maxWidth: 80 }}>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${score}%`, background: color }} />
          </div>
        </div>
      )}
    </div>
  )
}

interface SourceBadgeProps {
  sources: string[]
}

const SOURCE_COLORS: Record<string, string> = {
  crossref: '#f59e0b',
  openalex: '#6366f1',
  semantic_scholar: '#22d3ee',
  doaj: '#10b981',
  scopus: '#f97316',
}

export function SourceBadges({ sources }: SourceBadgeProps) {
  return (
    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
      {sources.map((s) => (
        <span key={s} style={{
          padding: '1px 6px',
          borderRadius: 4,
          fontSize: 10,
          fontWeight: 600,
          background: `${SOURCE_COLORS[s] || '#6b7280'}20`,
          color: SOURCE_COLORS[s] || '#9ca3af',
          border: `1px solid ${SOURCE_COLORS[s] || '#6b7280'}40`,
          textTransform: 'capitalize',
        }}>
          {s.replace('_', ' ')}
        </span>
      ))}
    </div>
  )
}

const CATEGORY_COLORS: Record<string, { bg: string; color: string; border: string; icon: string }> = {
  'Keamanan Siber': { bg: 'rgba(239, 68, 68, 0.15)', color: '#f87171', border: 'rgba(239, 68, 68, 0.4)', icon: '🛡️' },
  'Teknologi Informasi & Komputer': { bg: 'rgba(59, 130, 246, 0.15)', color: '#60a5fa', border: 'rgba(59, 130, 246, 0.4)', icon: '💻' },
  'Hukum & Kebijakan': { bg: 'rgba(168, 85, 247, 0.15)', color: '#c084fc', border: 'rgba(168, 85, 247, 0.4)', icon: '⚖️' },
  'Kesehatan & Kedokteran': { bg: 'rgba(16, 185, 129, 0.15)', color: '#34d399', border: 'rgba(16, 185, 129, 0.4)', icon: '🩺' },
  'Ekonomi & Bisnis': { bg: 'rgba(245, 158, 11, 0.15)', color: '#fbbf24', border: 'rgba(245, 158, 11, 0.4)', icon: '📈' },
  'Pendidikan': { bg: 'rgba(14, 165, 233, 0.15)', color: '#38bdf8', border: 'rgba(14, 165, 233, 0.4)', icon: '🎓' },
  'Sosial & Humaniora': { bg: 'rgba(236, 72, 153, 0.15)', color: '#f472b6', border: 'rgba(236, 72, 153, 0.4)', icon: '👥' },
  'Teknik & Rekayasa': { bg: 'rgba(249, 115, 22, 0.15)', color: '#fb923c', border: 'rgba(249, 115, 22, 0.4)', icon: '⚙️' },
  'Sains & Matematika': { bg: 'rgba(99, 102, 241, 0.15)', color: '#818cf8', border: 'rgba(99, 102, 241, 0.4)', icon: '🔬' },
  'Lainnya': { bg: 'rgba(107, 114, 128, 0.15)', color: '#9ca3af', border: 'rgba(107, 114, 128, 0.4)', icon: '📑' },
}

export function CategoryBadge({ category, small, onClick }: { category?: string; small?: boolean; onClick?: () => void }) {
  if (!category) return null
  const style = CATEGORY_COLORS[category] || CATEGORY_COLORS['Lainnya']
  return (
    <span
      onClick={onClick}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 4,
        padding: small ? '2px 7px' : '3px 10px',
        borderRadius: 6,
        fontSize: small ? 11 : 12,
        fontWeight: 600,
        background: style.bg,
        color: style.color,
        border: `1px solid ${style.border}`,
        cursor: onClick ? 'pointer' : 'default',
        whiteSpace: 'nowrap',
      }}
      title={`Kategori Bidang Ilmu: ${category}`}
    >
      <span>{style.icon}</span>
      <span>{category}</span>
    </span>
  )
}

