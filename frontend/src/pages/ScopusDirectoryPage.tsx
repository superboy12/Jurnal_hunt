import React, { useEffect, useState } from 'react'
import {
  Compass, ExternalLink, Search, CheckCircle, ShieldCheck,
  BookOpen, Sparkles, Award, ArrowRight, Layers, FileText, Database, RefreshCw
} from 'lucide-react'
import { getScopusDirectory, type ScopusDirectoryData } from '../api'
import toast from 'react-hot-toast'

export default function ScopusDirectoryPage() {
  const [data, setData] = useState<ScopusDirectoryData | null>(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState<'engines' | 'scopus' | 'publishers' | 'roadmap'>('engines')
  const [verifyQuery, setVerifyQuery] = useState('')

  useEffect(() => {
    loadDirectory()
  }, [])

  const loadDirectory = async () => {
    setLoading(true)
    try {
      const res = await getScopusDirectory()
      setData(res.data)
    } catch (e) {
      console.error(e)
      toast.error('Gagal memuat direktori akademik')
    } finally {
      setLoading(false)
    }
  }

  // Real-time verification links generator based on user input
  const getDirectLinks = (q: string) => {
    const clean = q.trim()
    const encoded = encodeURIComponent(clean)
    return [
      {
        name: 'Scopus Sources (Official)',
        url: clean ? `https://www.scopus.com/sources.uri?query=${encoded}` : 'https://www.scopus.com/sources',
        color: '#ff6600',
        badge: 'Indeks & CiteScore',
        desc: 'Verifikasi status indeksasi resmi Scopus dan riwayat cakupan aktif/discontinued.',
      },
      {
        name: 'SCImago Journal & Country Rank (SJR)',
        url: clean ? `https://www.scimagojr.com/journalsearch.php?q=${encoded}&tip=iss` : 'https://www.scimagojr.com/',
        color: '#0284c7',
        badge: 'Kuartil Q1–Q4 & SJR',
        desc: 'Cek pemeringkatan kuartil internasional tahunan (Q1, Q2, Q3, Q4) berbasis Scopus.',
      },
      {
        name: 'SINTA Kemdikbud',
        url: clean ? `https://sinta.kemdikbud.go.id/journals?q=${encoded}` : 'https://sinta.kemdikbud.go.id/journals',
        color: '#10b981',
        badge: 'Akreditasi Nasional S1–S6',
        desc: 'Verifikasi peringkat akreditasi jurnal nasional Indonesia Kemdikbudristek.',
      },
      {
        name: 'DOAJ Open Access',
        url: clean ? `https://doaj.org/search/journals?source=%7B%22query%22%3A%7B%22query_string%22%3A%7B%22query%22%3A%22${encoded}%22%7D%7D%7D` : 'https://doaj.org/',
        color: '#f59e0b',
        badge: 'Peer-Reviewed OA',
        desc: 'Periksa transparansi biaya APC, lisensi Creative Commons, dan hak cipta.',
      },
      {
        name: 'Unpaywall Legal PDF',
        url: clean ? `https://unpaywall.org/search?q=${encoded}` : 'https://unpaywall.org/',
        color: '#8b5cf6',
        badge: 'Open Access Bebas Bayar',
        desc: 'Temukan lokasi file PDF resmi legal dari 50M+ makalah akademik.',
      },
      {
        name: 'CORE Academic Repositories',
        url: clean ? `https://core.ac.uk/search?q=${encoded}` : 'https://core.ac.uk/',
        color: '#ec4899',
        badge: 'Repositori Riset Global',
        desc: 'Penelusuran ke ribuan repositori institusi dan perpustakaan universitas.',
      },
      {
        name: 'Sci-Hub Academic Unlocker',
        url: clean ? `https://sci-hub.box/${clean}` : 'https://sci-hub.box/',
        color: '#e11d48',
        badge: 'Bypass Paywall via DOI',
        desc: 'Unduh naskah lengkap artikel berbayar/terkunci secara bebas menggunakan nomor DOI.',
      },
    ]
  }

  return (
    <div className="page-container" style={{ padding: '28px 36px', maxWidth: 1440, margin: '0 auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 24 }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span style={{
              display: 'inline-flex', alignItems: 'center', gap: 6,
              background: 'rgba(255, 102, 0, 0.15)', color: '#ff7700',
              padding: '4px 12px', borderRadius: 20, fontSize: 12, fontWeight: 700,
              border: '1px solid rgba(255, 102, 0, 0.3)'
            }}>
              <Compass size={14} /> Scopus & Academic Research Directory
            </span>
            <span style={{
              background: 'rgba(16, 185, 129, 0.15)', color: '#10b981',
              padding: '4px 10px', borderRadius: 20, fontSize: 12, fontWeight: 600,
              border: '1px solid rgba(16, 185, 129, 0.3)'
            }}>
              10 Mesin Pencari · 3 Otoritas Scopus · 10 Penerbit OA
            </span>
          </div>
          <h1 style={{ fontSize: 26, fontWeight: 700, color: 'var(--text-primary)', margin: 0, fontFamily: 'Space Grotesk, sans-serif' }}>
            Pusat Verifikasi Jurnal Scopus & Sumber Ilmiah Terpercaya
          </h1>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '4px 0 0', maxWidth: 900 }}>
            Kompilasi direktori terkurasi untuk mesin pencarian ilmiah, portal verifikasi resmi Scopus & SCImago SJR,
            penerbit Open Access dunia, serta rekomendasi alur otomatisasi panen artikel akademik.
          </p>
        </div>

        <button
          onClick={loadDirectory}
          disabled={loading}
          className="btn-secondary"
          style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 13 }}
        >
          <RefreshCw size={14} className={loading ? 'spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Quick Verifier Widget */}
      <div className="glass-panel" style={{
        padding: 24, borderRadius: 16, marginBottom: 28,
        background: 'linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))',
        border: '1px solid rgba(99, 102, 241, 0.25)',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
          <ShieldCheck size={22} color="#ff7700" />
          <h2 style={{ fontSize: 17, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
            Verifikator Instan: Cek Indeksasi Scopus, Kuartil SJR, dan SINTA
          </h2>
        </div>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: '0 0 16px' }}>
          Masukkan nama jurnal atau ISSN untuk membuat tautan pencarian verifikasi langsung ke portal resmi Scopus Sources, SCImago SJR, SINTA, DOAJ, dan Unpaywall.
        </p>

        <div style={{ display: 'flex', gap: 10, marginBottom: 18 }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search size={18} style={{ position: 'absolute', left: 14, top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)' }} />
            <input
              type="text"
              className="input-field"
              value={verifyQuery}
              onChange={(e) => setVerifyQuery(e.target.value)}
              placeholder="Ketik Nama Jurnal atau ISSN (misal: TELKOMNIKA, 1693-6930, Nature Communications, IEEE Access)..."
              style={{ width: '100%', paddingLeft: 42, fontSize: 14 }}
            />
          </div>
          {verifyQuery && (
            <button
              onClick={() => setVerifyQuery('')}
              className="btn-secondary"
              style={{ fontSize: 13 }}
            >
              Reset
            </button>
          )}
        </div>

        {/* Generated Direct Links Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: 12,
        }}>
          {getDirectLinks(verifyQuery).map((item, idx) => (
            <a
              key={idx}
              href={item.url}
              target="_blank"
              rel="noopener noreferrer"
              style={{
                textDecoration: 'none',
                display: 'block',
                padding: '14px 16px',
                borderRadius: 12,
                background: 'rgba(255, 255, 255, 0.03)',
                border: '1px solid var(--border)',
                transition: 'all 0.2s ease',
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.borderColor = item.color
                e.currentTarget.style.transform = 'translateY(-2px)'
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.06)'
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.borderColor = 'var(--border)'
                e.currentTarget.style.transform = 'translateY(0)'
                e.currentTarget.style.background = 'rgba(255, 255, 255, 0.03)'
              }}
            >
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                <span style={{ fontSize: 11, fontWeight: 700, color: item.color, textTransform: 'uppercase' }}>
                  {item.badge}
                </span>
                <ExternalLink size={13} color="var(--text-muted)" />
              </div>
              <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text-primary)', marginBottom: 4 }}>
                {item.name}
              </div>
              <div style={{ fontSize: 12, color: 'var(--text-secondary)', lineHeight: 1.4 }}>
                {item.desc}
              </div>
              {verifyQuery && (
                <div style={{ marginTop: 8, fontSize: 11, color: item.color, fontWeight: 600 }}>
                  Periksa "{verifyQuery}" →
                </div>
              )}
            </a>
          ))}
        </div>
      </div>

      {/* Tabs */}
      <div style={{
        display: 'flex', gap: 8, borderBottom: '1px solid var(--border)',
        marginBottom: 24, overflowX: 'auto', paddingBottom: 2
      }}>
        <button
          onClick={() => setActiveTab('engines')}
          style={{
            padding: '10px 18px', borderRadius: '10px 10px 0 0', border: 'none',
            background: activeTab === 'engines' ? 'rgba(99, 102, 241, 0.15)' : 'transparent',
            color: activeTab === 'engines' ? 'var(--primary-light)' : 'var(--text-secondary)',
            fontWeight: 600, fontSize: 14, cursor: 'pointer',
            borderBottom: activeTab === 'engines' ? '2px solid var(--primary-light)' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          <Database size={16} /> A. 10 Mesin Pencari Ilmiah
        </button>

        <button
          onClick={() => setActiveTab('scopus')}
          style={{
            padding: '10px 18px', borderRadius: '10px 10px 0 0', border: 'none',
            background: activeTab === 'scopus' ? 'rgba(255, 102, 0, 0.15)' : 'transparent',
            color: activeTab === 'scopus' ? '#ff7700' : 'var(--text-secondary)',
            fontWeight: 600, fontSize: 14, cursor: 'pointer',
            borderBottom: activeTab === 'scopus' ? '2px solid #ff7700' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          <Award size={16} /> B. Otoritas Verifikasi Scopus & SJR
        </button>

        <button
          onClick={() => setActiveTab('publishers')}
          style={{
            padding: '10px 18px', borderRadius: '10px 10px 0 0', border: 'none',
            background: activeTab === 'publishers' ? 'rgba(16, 185, 129, 0.15)' : 'transparent',
            color: activeTab === 'publishers' ? '#10b981' : 'var(--text-secondary)',
            fontWeight: 600, fontSize: 14, cursor: 'pointer',
            borderBottom: activeTab === 'publishers' ? '2px solid #10b981' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          <BookOpen size={16} /> C. 10 Penerbit Open Access
        </button>

        <button
          onClick={() => setActiveTab('roadmap')}
          style={{
            padding: '10px 18px', borderRadius: '10px 10px 0 0', border: 'none',
            background: activeTab === 'roadmap' ? 'rgba(168, 85, 247, 0.15)' : 'transparent',
            color: activeTab === 'roadmap' ? '#a855f7' : 'var(--text-secondary)',
            fontWeight: 600, fontSize: 14, cursor: 'pointer',
            borderBottom: activeTab === 'roadmap' ? '2px solid #a855f7' : '2px solid transparent',
            display: 'flex', alignItems: 'center', gap: 8,
          }}
        >
          <Layers size={16} /> D. Rekomendasi Alur Otomasi
        </button>
      </div>

      {/* Tab 1: 10 Search Engines */}
      {activeTab === 'engines' && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px' }}>
              Mesin Pencari Ilmiah & Repositori Terbuka Terintegrasi
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
              Sistem AI Journal Hunter menghubungkan berbagai sumber data global ini secara paralel untuk memastikan pencarian komprehensif tanpa duplikasi.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
            gap: 16,
          }}>
            {(data?.search_engines || []).map((engine) => (
              <div
                key={engine.id}
                className="glass-panel"
                style={{ padding: '20px 22px', borderRadius: 14, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
                    <span style={{
                      fontSize: 11, fontWeight: 700, padding: '3px 8px', borderRadius: 8,
                      background: 'rgba(99, 102, 241, 0.15)', color: 'var(--primary-light)',
                      border: '1px solid rgba(99, 102, 241, 0.3)'
                    }}>
                      {engine.badge}
                    </span>
                    <span style={{
                      fontSize: 11, fontWeight: 600, color: '#10b981', display: 'flex', alignItems: 'center', gap: 4
                    }}>
                      <CheckCircle size={13} /> Terhubung API
                    </span>
                  </div>

                  <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px' }}>
                    {engine.name}
                  </h4>
                  <div style={{ fontSize: 12, fontWeight: 600, color: '#38bdf8', marginBottom: 8 }}>
                    {engine.role}
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 14px' }}>
                    {engine.description}
                  </p>

                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 16 }}>
                    {engine.features.map((f, i) => (
                      <span
                        key={i}
                        style={{
                          fontSize: 11, padding: '2px 8px', borderRadius: 6,
                          background: 'rgba(255, 255, 255, 0.05)', color: 'var(--text-muted)',
                        }}
                      >
                        • {f}
                      </span>
                    ))}
                  </div>
                </div>

                <div style={{ display: 'flex', gap: 8, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                  <a
                    href={engine.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn-secondary"
                    style={{
                      flex: 1, textDecoration: 'none', display: 'flex', alignItems: 'center',
                      justifyContent: 'center', gap: 6, fontSize: 12, padding: '8px 12px'
                    }}
                  >
                    Buka {engine.name} <ExternalLink size={12} />
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 2: Scopus Verification Portals */}
      {activeTab === 'scopus' && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px' }}>
              Portal Verifikasi Resmi Jurnal Scopus & Pemeringkatan SJR
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
              Gunakan situs rujukan otoritatif ini untuk memvalidasi apakah jurnal benar-benar terindeks Scopus dan melihat kuartil resmi (Q1, Q2, Q3, Q4).
            </p>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 18 }}>
            {(data?.scopus_verification || []).map((portal) => (
              <div
                key={portal.id}
                className="glass-panel"
                style={{
                  padding: 24, borderRadius: 16,
                  border: '1px solid rgba(255, 102, 0, 0.25)',
                  display: 'flex', flexDirection: 'column', justifyContent: 'space-between'
                }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                    <span style={{
                      fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 8,
                      background: 'rgba(255, 102, 0, 0.15)', color: '#ff7700',
                      border: '1px solid rgba(255, 102, 0, 0.3)'
                    }}>
                      {portal.badge}
                    </span>
                    <Award size={18} color="#ff7700" />
                  </div>

                  <h4 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 6px' }}>
                    {portal.name}
                  </h4>
                  <div style={{ fontSize: 13, fontWeight: 600, color: '#ff9933', marginBottom: 10 }}>
                    {portal.role}
                  </div>
                  <p style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5, margin: '0 0 16px' }}>
                    {portal.description}
                  </p>

                  <div style={{
                    padding: 12, borderRadius: 10, background: 'rgba(255, 255, 255, 0.04)',
                    marginBottom: 16, fontSize: 12, color: 'var(--text-muted)'
                  }}>
                    <strong style={{ color: 'var(--text-primary)' }}>Metode Verifikasi:</strong> {portal.verification_method}
                  </div>
                </div>

                <a
                  href={portal.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-primary"
                  style={{
                    textDecoration: 'none', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', gap: 6, fontSize: 13, background: 'linear-gradient(135deg, #ea580c, #c2410c)'
                  }}
                >
                  Buka Portal Resmi {portal.name} <ExternalLink size={14} />
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 3: Open Access Publishers */}
      {activeTab === 'publishers' && (
        <div>
          <div style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 18, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px' }}>
              Direktori 10 Penerbit Internasional Terkemuka (Open Access & Scopus)
            </h3>
            <p style={{ fontSize: 13, color: 'var(--text-secondary)', margin: 0 }}>
              Penerbit terakreditasi internasional yang menyediakan artikel ilmiah Open Access dengan peninjauan sejawat (peer-reviewed) ketat.
            </p>
          </div>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: 14,
          }}>
            {(data?.open_access_publishers || []).map((pub, idx) => (
              <div
                key={idx}
                className="glass-panel"
                style={{ padding: '18px 20px', borderRadius: 12, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
              >
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                    <span style={{
                      fontSize: 11, fontWeight: 700, padding: '2px 8px', borderRadius: 6,
                      background: 'rgba(16, 185, 129, 0.15)', color: '#10b981',
                      border: '1px solid rgba(16, 185, 129, 0.3)'
                    }}>
                      {pub.type}
                    </span>
                    <BookOpen size={16} color="var(--text-muted)" />
                  </div>

                  <h4 style={{ fontSize: 16, fontWeight: 700, color: 'var(--text-primary)', margin: '0 0 4px' }}>
                    {pub.name}
                  </h4>
                  <p style={{ fontSize: 12, color: 'var(--text-secondary)', margin: '0 0 12px', lineHeight: 1.4 }}>
                    {pub.scope}
                  </p>
                </div>

                <a
                  href={pub.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="btn-secondary"
                  style={{
                    textDecoration: 'none', display: 'flex', alignItems: 'center',
                    justifyContent: 'center', gap: 6, fontSize: 12, padding: '7px 10px'
                  }}
                >
                  Kunjungi {pub.name} <ExternalLink size={12} />
                </a>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Tab 4: Recommendation Roadmap */}
      {activeTab === 'roadmap' && (
        <div className="glass-panel" style={{ padding: 28, borderRadius: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
            <Layers size={22} color="var(--primary-light)" />
            <h3 style={{ fontSize: 20, fontWeight: 700, color: 'var(--text-primary)', margin: 0 }}>
              {data?.recommendations.title || 'Alur Rekomendasi Otomasi Pencarian Jurnal Ilmiah'}
            </h3>
          </div>
          <p style={{ fontSize: 14, color: 'var(--text-secondary)', margin: '0 0 24px' }}>
            Arsitektur bertingkat yang diimplementasikan pada AI Journal Hunter untuk memastikan akurasi data, kelengkapan metadata, dan ketersediaan naskah PDF legal.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            {(data?.recommendations.steps || []).map((step) => (
              <div
                key={step.step}
                style={{
                  display: 'flex', alignItems: 'flex-start', gap: 16,
                  padding: '16px 20px', borderRadius: 12,
                  background: 'rgba(255, 255, 255, 0.03)',
                  border: '1px solid var(--border)',
                }}
              >
                <div style={{
                  width: 36, height: 36, borderRadius: '50%',
                  background: 'rgba(99, 102, 241, 0.2)', color: 'var(--primary-light)',
                  display: 'flex', alignItems: 'center', justifyContent: 'center',
                  fontWeight: 700, fontSize: 15, flexShrink: 0
                }}>
                  {step.step}
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--text-primary)' }}>
                      {step.source}
                    </span>
                    <span style={{
                      fontSize: 10, padding: '1px 6px', borderRadius: 6,
                      background: 'rgba(16, 185, 129, 0.15)', color: '#10b981', fontWeight: 600
                    }}>
                      Tahap {step.step}
                    </span>
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                    {step.action}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
