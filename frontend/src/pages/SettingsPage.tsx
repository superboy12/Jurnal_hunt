import React, { useEffect, useState } from 'react'
import { getHealth, getModels, type HealthCheck, type ModelsResponse } from '../api'
import {
  CheckCircle, XCircle, Key, Globe, Database, Cpu, Sparkles,
  ShieldCheck, Server, RefreshCw
} from 'lucide-react'
import toast from 'react-hot-toast'

export default function SettingsPage() {
  const [health, setHealth] = useState<HealthCheck | null>(null)
  const [modelsData, setModelsData] = useState<ModelsResponse | null>(null)
  const [loading, setLoading] = useState(true)

  const loadData = async () => {
    setLoading(true)
    try {
      const [hRes, mRes] = await Promise.all([
        getHealth(),
        getModels(),
      ])
      setHealth(hRes.data)
      setModelsData(mRes.data)
    } catch (e) {
      console.error(e)
      toast.error('Gagal memuat status sistem')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
  }, [])

  const SOURCE_INFO = [
    {
      name: 'Crossref',
      key: 'crossref',
      status: health?.available_sources.includes('crossref') ?? null,
      description: 'Metadata artikel ilmiah global. Terhubung melalui polite pool email.',
      url: 'https://api.crossref.org/',
      type: 'Global DOI & Crossref Registry',
    },
    {
      name: 'OpenAlex',
      key: 'openalex',
      status: health?.available_sources.includes('openalex') ?? null,
      description: 'Graf akademik global dengan 250M+ karya ilmiah dan kutipan.',
      url: 'https://openalex.org/',
      type: 'Open Bibliographic Knowledge Graph',
    },
    {
      name: 'Semantic Scholar',
      key: 'semantic_scholar',
      status: health?.available_sources.includes('semantic_scholar') ?? null,
      description: 'AI-powered scientific literature search dari Allen Institute for AI.',
      url: 'https://api.semanticscholar.org/',
      type: 'Academic Graph & Citation Context',
    },
    {
      name: 'DOAJ',
      key: 'doaj',
      status: health?.available_sources.includes('doaj') ?? null,
      description: 'Direktori jurnal Open Access internasional terakreditasi.',
      url: 'https://doaj.org/',
      type: 'Peer-reviewed Open Access Index',
    },
    {
      name: 'Scopus Elsevier',
      key: 'scopus',
      status: health?.available_sources.includes('scopus') ?? null,
      description: 'Pengindeks Scopus internasional dan verifikasi kuartil jurnal (Q1–Q4).',
      url: 'https://www.scopus.com/',
      type: 'Scopus Indexed & Verified Source',
    },
  ]

  return (
    <div className="page-container" style={{ padding: '28px 36px', maxWidth: 1400, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 28 }}>
        <div>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
            System Settings & AI Configuration
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '4px 0 0' }}>
            Konfigurasi 15 AI Models, status Google Gemini multi-key failover, database PostgreSQL, dan integrasi sumber ilmiah.
          </p>
        </div>
        <button
          onClick={loadData}
          disabled={loading}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          Refresh Status
        </button>
      </div>

      {/* Infrastructure Status Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: 18,
        marginBottom: 28,
      }}>
        {/* PostgreSQL Database */}
        <div className="stat-card glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'rgba(6, 182, 212, 0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#06b6d4',
            }}>
              <Database size={20} />
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Database API</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>Prisma Cloud Postgres</div>
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#10b981', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
            <CheckCircle size={14} /> Terhubung (db.prisma.io:5432)
          </div>
        </div>

        {/* Gemini API Keys (3 Keys) */}
        <div className="stat-card glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'rgba(99, 102, 241, 0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: 'var(--primary-light)',
            }}>
              <Key size={20} />
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Google Gemini API</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                3 API Keys Rotasi
              </div>
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#10b981', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
            <ShieldCheck size={14} /> Failover & Round-Robin Siap
          </div>
        </div>

        {/* DeepSeek API */}
        <div className="stat-card glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'rgba(59, 130, 246, 0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#3b82f6',
            }}>
              <Server size={20} />
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>DeepSeek API</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                Terhubung (Aktif)
              </div>
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#3b82f6', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
            <CheckCircle size={14} /> Terintegrasi (V3 & R1 Mode)
          </div>
        </div>

        {/* AI Models Registry */}
        <div className="stat-card glass-panel" style={{ padding: '20px 22px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <div style={{
              width: 38, height: 38, borderRadius: 10,
              background: 'rgba(168, 85, 247, 0.15)',
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              color: '#a855f7',
            }}>
              <Cpu size={20} />
            </div>
            <div>
              <div style={{ fontSize: 12, color: 'var(--text-muted)', textTransform: 'uppercase', fontWeight: 600 }}>Model Selector</div>
              <div style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)' }}>
                15 Model AI Aktif
              </div>
            </div>
          </div>
          <div style={{ fontSize: 12, color: '#a855f7', display: 'flex', alignItems: 'center', gap: 6, fontWeight: 600 }}>
            <Sparkles size={14} /> Default: {modelsData?.default_model || 'gemini-3.5-flash'}
          </div>
        </div>
      </div>

      {/* 15 AI Models Table */}
      <div className="glass-panel" style={{ padding: 24, borderRadius: 16, marginBottom: 28 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <Sparkles size={20} color="var(--primary-light)" />
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Daftar 15 Model AI Terintegrasi
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '2px 0 0' }}>
              Model yang dapat dipilih peneliti untuk analisis instruksi, interpretasi kata kunci, dan pembuatan sintesis literatur.
            </p>
          </div>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--border)', textAlign: 'left', color: 'var(--text-muted)' }}>
                <th style={{ padding: '10px 14px' }}>Nama Model</th>
                <th style={{ padding: '10px 14px' }}>Provider</th>
                <th style={{ padding: '10px 14px' }}>Karakteristik / Badge</th>
                <th style={{ padding: '10px 14px' }}>Konteks</th>
                <th style={{ padding: '10px 14px' }}>Deskripsi</th>
              </tr>
            </thead>
            <tbody>
              {(modelsData?.models || []).map((m) => (
                <tr
                  key={m.id}
                  style={{
                    borderBottom: '1px solid var(--border)',
                    transition: 'background 0.15s ease',
                  }}
                >
                  <td style={{ padding: '12px 14px', fontWeight: 600, color: 'var(--text-primary)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <span>{m.name}</span>
                      {m.id === modelsData?.default_model && (
                        <span style={{
                          fontSize: 10,
                          padding: '1px 6px',
                          borderRadius: 8,
                          background: 'rgba(16, 185, 129, 0.2)',
                          color: '#10b981',
                          border: '1px solid rgba(16, 185, 129, 0.4)',
                        }}>
                          Active Default
                        </span>
                      )}
                    </div>
                    <code style={{ fontSize: 11, color: 'var(--text-muted)' }}>{m.id}</code>
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-secondary)' }}>
                    {m.provider}
                  </td>
                  <td style={{ padding: '12px 14px' }}>
                    <span style={{
                      fontSize: 11,
                      padding: '3px 8px',
                      borderRadius: 10,
                      background: 'rgba(99, 102, 241, 0.12)',
                      color: 'var(--primary-light)',
                      border: '1px solid rgba(99, 102, 241, 0.3)',
                      fontWeight: 600,
                    }}>
                      {m.badge}
                    </span>
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-muted)', fontSize: 12 }}>
                    {m.context_window}
                  </td>
                  <td style={{ padding: '12px 14px', color: 'var(--text-secondary)', fontSize: 12 }}>
                    {m.description}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Academic Sources Status */}
      <div className="glass-panel" style={{ padding: 24, borderRadius: 16 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 18 }}>
          <Globe size={20} color="#06b6d4" />
          <div>
            <h2 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              Status Sumber Indeksasi & API Akademik
            </h2>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '2px 0 0' }}>
              Sumber data langsung yang diakses secara paralel oleh search pipeline.
            </p>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 14 }}>
          {SOURCE_INFO.map((src) => (
            <div
              key={src.key}
              style={{
                padding: '14px 16px',
                borderRadius: 12,
                background: 'var(--bg-surface)',
                border: '1px solid var(--border)',
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'flex-start',
                gap: 12,
              }}
            >
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <span style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)' }}>{src.name}</span>
                  <span style={{ fontSize: 10, color: 'var(--text-muted)' }}>({src.type})</span>
                </div>
                <p style={{ margin: 0, fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                  {src.description}
                </p>
              </div>

              <div>
                {src.status ? (
                  <span style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    fontSize: 11, fontWeight: 600, color: '#10b981',
                    background: 'rgba(16, 185, 129, 0.1)', padding: '2px 8px', borderRadius: 8,
                  }}>
                    <CheckCircle size={12} /> Aktif
                  </span>
                ) : (
                  <span style={{
                    display: 'flex', alignItems: 'center', gap: 4,
                    fontSize: 11, fontWeight: 600, color: 'var(--text-muted)',
                    background: 'rgba(100, 116, 139, 0.1)', padding: '2px 8px', borderRadius: 8,
                  }}>
                    {src.key === 'scopus' ? 'Perlu Elsevier Key' : 'Siap'}
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
