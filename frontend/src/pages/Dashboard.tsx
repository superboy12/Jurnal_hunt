import React, { useEffect, useState } from 'react'
import { getStats, getHistory, type Stats, type SearchSummary } from '../api'
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts'
import { Search, TrendingUp, CheckCircle, BookOpen, Database, Clock, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { formatDistanceToNow } from 'date-fns'
import { id as idLocale } from 'date-fns/locale'

const COLORS = ['#6366f1', '#22d3ee', '#10b981', '#f59e0b', '#ef4444']

const STATUS_CONFIG: Record<string, { color: string; label: string }> = {
  completed: { color: '#10b981', label: 'Selesai' },
  running: { color: '#f59e0b', label: 'Berjalan' },
  pending: { color: '#6b7280', label: 'Menunggu' },
  failed: { color: '#ef4444', label: 'Gagal' },
  cancelled: { color: '#6b7280', label: 'Dibatalkan' },
}

export default function Dashboard() {
  const [stats, setStats] = useState<Stats | null>(null)
  const [history, setHistory] = useState<SearchSummary[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    getStats().then(r => setStats(r.data)).catch(console.error)
    getHistory(10).then(r => setHistory(r.data)).catch(console.error)
  }, [])

  const sourceData = [
    { name: 'Crossref', value: 45, color: '#f59e0b' },
    { name: 'OpenAlex', value: 30, color: '#6366f1' },
    { name: 'Sem. Scholar', value: 20, color: '#22d3ee' },
    { name: 'DOAJ', value: 15, color: '#10b981' },
  ]

  const yearData = [
    { year: '2020', count: 12 },
    { year: '2021', count: 18 },
    { year: '2022', count: 25 },
    { year: '2023', count: 34 },
    { year: '2024', count: 41 },
    { year: '2025', count: 29 },
    { year: '2026', count: 8 },
  ]

  return (
    <div className="fade-in">
      {/* Hero */}
      <div className="gradient-border" style={{ marginBottom: 28 }}>
        <div style={{
          background: 'linear-gradient(135deg, rgba(99,102,241,0.15) 0%, rgba(6,182,212,0.1) 100%)',
          borderRadius: 12,
          padding: '28px 32px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}>
          <div>
            <h1 style={{
              fontFamily: 'Space Grotesk, sans-serif',
              fontSize: 28,
              fontWeight: 800,
              margin: 0,
              background: 'linear-gradient(135deg, #a5b4fc, #22d3ee)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
            }}>
              AI Journal Hunter
            </h1>
            <p style={{ margin: '8px 0 0', color: 'var(--text-secondary)', fontSize: 14 }}>
              Sistem pencarian jurnal ilmiah otomatis berbasis perintah bahasa alami
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={() => navigate('/search')}
            style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 15, padding: '12px 28px' }}
          >
            <Search size={18} />
            Mulai Pencarian
          </button>
        </div>
      </div>

      {/* Stats */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 16, marginBottom: 28 }}>
        <StatCard
          icon={<Search size={22} />}
          label="Total Pencarian"
          value={stats?.total_searches ?? 0}
          color="indigo"
          trend="+12%"
        />
        <StatCard
          icon={<BookOpen size={22} />}
          label="Total Artikel"
          value={stats?.total_articles ?? 0}
          color="cyan"
          trend="+8%"
        />
        <StatCard
          icon={<TrendingUp size={22} />}
          label="Open Access"
          value={stats?.open_access_articles ?? 0}
          color="green"
          trend="+15%"
        />
        <StatCard
          icon={<Database size={22} />}
          label="Bookmark"
          value={stats?.total_bookmarks ?? 0}
          color="amber"
          trend="+5%"
        />
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 20, marginBottom: 28 }}>
        {/* Year distribution */}
        <div className="card">
          <h3 style={{ margin: '0 0 20px', fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
            📊 Distribusi Tahun Publikasi
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={yearData}>
              <XAxis dataKey="year" tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <YAxis tick={{ fill: '#9ca3af', fontSize: 12 }} />
              <Tooltip
                contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }}
                labelStyle={{ color: '#f9fafb' }}
              />
              <Bar dataKey="count" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Source distribution */}
        <div className="card">
          <h3 style={{ margin: '0 0 20px', fontSize: 15, fontWeight: 600, color: 'var(--text-primary)' }}>
            🗄️ Distribusi Sumber
          </h3>
          <ResponsiveContainer width="100%" height={200}>
            <PieChart>
              <Pie
                data={sourceData}
                cx="50%"
                cy="50%"
                innerRadius={50}
                outerRadius={80}
                dataKey="value"
                label={({ name, percent }: { name?: string; percent?: number }) =>
                  `${name || ''} ${percent != null ? (percent * 100).toFixed(0) : 0}%`
                }
                labelLine={false}
                fontSize={10}
              >
                {sourceData.map((entry, index) => (
                  <Cell key={index} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ background: '#1f2937', border: '1px solid #374151', borderRadius: 8 }} />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent searches */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h3 style={{ margin: 0, fontSize: 15, fontWeight: 600 }}>
            <Clock size={16} style={{ display: 'inline', marginRight: 6, verticalAlign: 'middle' }} />
            Pencarian Terbaru
          </h3>
          <button className="btn-ghost" onClick={() => navigate('/history')}>
            Lihat semua <ArrowRight size={14} style={{ display: 'inline', marginLeft: 4 }} />
          </button>
        </div>

        {history.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
            <Search size={36} style={{ marginBottom: 8, opacity: 0.3 }} />
            <p>Belum ada pencarian. Mulai dari menu AI Search.</p>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {history.map((s) => {
              const cfg = STATUS_CONFIG[s.status] || STATUS_CONFIG.pending
              return (
                <div
                  key={s.id}
                  onClick={() => navigate(`/search?id=${s.id}`)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 14px',
                    background: 'rgba(17,24,39,0.4)',
                    borderRadius: 8,
                    border: '1px solid var(--border)',
                    cursor: 'pointer',
                    transition: 'all 0.2s',
                  }}
                  onMouseEnter={e => (e.currentTarget.style.borderColor = 'rgba(99,102,241,0.4)')}
                  onMouseLeave={e => (e.currentTarget.style.borderColor = 'var(--border)')}
                >
                  <span style={{ color: cfg.color, fontSize: 11, fontWeight: 600, minWidth: 70 }}>
                    ● {cfg.label}
                  </span>
                  <span style={{ flex: 1, fontSize: 13, color: 'var(--text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {s.user_command}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)', minWidth: 80, textAlign: 'right' }}>
                    {s.total_after_dedup} hasil
                  </span>
                  <span style={{ fontSize: 11, color: 'var(--text-muted)', minWidth: 90, textAlign: 'right' }}>
                    {formatDistanceToNow(new Date(s.created_at), { addSuffix: true, locale: idLocale })}
                  </span>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}

function StatCard({ icon, label, value, color, trend }: {
  icon: React.ReactNode
  label: string
  value: number
  color: string
  trend: string
}) {
  const colorMap: Record<string, string> = {
    indigo: '#6366f1',
    cyan: '#22d3ee',
    green: '#10b981',
    amber: '#f59e0b',
  }
  const c = colorMap[color]

  return (
    <div className={`stat-card ${color}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{
          width: 44, height: 44, borderRadius: 10,
          background: `${c}20`,
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          color: c,
        }}>
          {icon}
        </div>
        <span style={{ fontSize: 11, color: '#10b981', fontWeight: 600 }}>{trend}</span>
      </div>
      <div style={{ marginTop: 16 }}>
        <div style={{ fontSize: 28, fontWeight: 800, color: 'var(--text-primary)' }}>
          {value.toLocaleString()}
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 2 }}>{label}</div>
      </div>
    </div>
  )
}
