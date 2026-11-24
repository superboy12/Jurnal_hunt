import React, { useEffect, useState } from 'react'
import {
  getSavedArticles, getProjects, createProject, updateBookmark, deleteBookmark,
  type Bookmark, type Project
} from '../api'
import { Bookmark as BookmarkIcon, Plus, Trash2, Edit, FolderOpen, Tag } from 'lucide-react'
import { VerificationBadge, RelevanceScore, SourceBadges } from '../components/Badges'
import toast from 'react-hot-toast'

const STATUS_OPTIONS = [
  { value: 'want_to_read', label: '📖 Ingin Dibaca', color: '#6366f1' },
  { value: 'read', label: '✅ Sudah Dibaca', color: '#10b981' },
  { value: 'candidate', label: '⭐ Kandidat Referensi', color: '#f59e0b' },
  { value: 'not_relevant', label: '❌ Tidak Relevan', color: '#6b7280' },
]

export default function SavedArticlesPage() {
  const [bookmarks, setBookmarks] = useState<Bookmark[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [selectedProject, setSelectedProject] = useState<string | null>(null)
  const [filterStatus, setFilterStatus] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [newProjectName, setNewProjectName] = useState('')
  const [showNewProject, setShowNewProject] = useState(false)
  const [editingNote, setEditingNote] = useState<string | null>(null)
  const [noteText, setNoteText] = useState('')

  useEffect(() => {
    fetchAll()
  }, [selectedProject])

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [bmRes, projRes] = await Promise.all([
        getSavedArticles(selectedProject || undefined),
        getProjects(),
      ])
      setBookmarks(bmRes.data)
      setProjects(projRes.data)
    } catch { }
    finally { setLoading(false) }
  }

  const handleCreateProject = async () => {
    if (!newProjectName.trim()) return
    try {
      await createProject({ name: newProjectName })
      setNewProjectName('')
      setShowNewProject(false)
      fetchAll()
      toast.success('Proyek dibuat!')
    } catch { toast.error('Gagal membuat proyek') }
  }

  const handleUpdateStatus = async (id: string, status: string) => {
    try {
      await updateBookmark(id, { status })
      setBookmarks(prev => prev.map(b => b.id === id ? { ...b, status } : b))
      toast.success('Status diperbarui')
    } catch { toast.error('Gagal memperbarui') }
  }

  const handleSaveNote = async (id: string) => {
    try {
      await updateBookmark(id, { notes: noteText })
      setBookmarks(prev => prev.map(b => b.id === id ? { ...b, notes: noteText } : b))
      setEditingNote(null)
      toast.success('Catatan tersimpan')
    } catch { toast.error('Gagal menyimpan catatan') }
  }

  const handleDelete = async (id: string) => {
    if (!confirm('Hapus bookmark ini?')) return
    try {
      await deleteBookmark(id)
      setBookmarks(prev => prev.filter(b => b.id !== id))
      toast.success('Bookmark dihapus')
    } catch { toast.error('Gagal menghapus') }
  }

  const filtered = bookmarks.filter(b => !filterStatus || b.status === filterStatus)

  return (
    <div className="fade-in">
      <h1 style={{ fontFamily: 'Space Grotesk, sans-serif', fontSize: 22, fontWeight: 700, margin: '0 0 20px' }}>
        🔖 Saved Articles
      </h1>

      <div style={{ display: 'grid', gridTemplateColumns: '220px 1fr', gap: 20 }}>
        {/* Sidebar: Projects */}
        <div>
          <div className="card" style={{ padding: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h3 style={{ margin: 0, fontSize: 13, fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Proyek
              </h3>
              <button className="btn-ghost" onClick={() => setShowNewProject(!showNewProject)} style={{ padding: '2px 8px', fontSize: 11 }}>
                <Plus size={12} />
              </button>
            </div>

            {showNewProject && (
              <div style={{ marginBottom: 10 }}>
                <input
                  value={newProjectName}
                  onChange={e => setNewProjectName(e.target.value)}
                  placeholder="Nama proyek..."
                  style={{ width: '100%', fontSize: 13, marginBottom: 6 }}
                  onKeyDown={e => e.key === 'Enter' && handleCreateProject()}
                />
                <button className="btn-primary" onClick={handleCreateProject} style={{ fontSize: 12, padding: '5px 12px', width: '100%' }}>
                  Buat
                </button>
              </div>
            )}

            <div
              onClick={() => setSelectedProject(null)}
              style={{
                padding: '8px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
                background: !selectedProject ? 'rgba(99,102,241,0.15)' : 'transparent',
                color: !selectedProject ? 'var(--primary-light)' : 'var(--text-secondary)',
                marginBottom: 2,
                display: 'flex', alignItems: 'center', gap: 8,
              }}
            >
              <BookmarkIcon size={13} />
              Semua Bookmark
            </div>
            {projects.map(p => (
              <div
                key={p.id}
                onClick={() => setSelectedProject(p.id)}
                style={{
                  padding: '8px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 13,
                  background: selectedProject === p.id ? 'rgba(99,102,241,0.15)' : 'transparent',
                  color: selectedProject === p.id ? 'var(--primary-light)' : 'var(--text-secondary)',
                  marginBottom: 2,
                  display: 'flex', alignItems: 'center', gap: 8,
                }}
              >
                <FolderOpen size={13} />
                {p.name}
              </div>
            ))}

            <hr style={{ margin: '12px 0' }} />
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 8, fontWeight: 600 }}>Filter Status</div>
            {[{ value: null, label: 'Semua' }, ...STATUS_OPTIONS].map(o => (
              <div
                key={o.value || 'all'}
                onClick={() => setFilterStatus(o.value)}
                style={{
                  padding: '6px 10px', borderRadius: 6, cursor: 'pointer', fontSize: 12,
                  background: filterStatus === o.value ? 'rgba(99,102,241,0.1)' : 'transparent',
                  color: filterStatus === o.value ? 'var(--text-primary)' : 'var(--text-secondary)',
                  marginBottom: 1,
                }}
              >
                {o.label}
              </div>
            ))}
          </div>
        </div>

        {/* Articles list */}
        <div>
          {loading ? (
            <div style={{ display: 'flex', justifyContent: 'center', paddingTop: 40 }}>
              <div className="spinner" />
            </div>
          ) : filtered.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '80px 0', color: 'var(--text-muted)' }}>
              <BookmarkIcon size={48} style={{ marginBottom: 12, opacity: 0.2 }} />
              <p>Tidak ada artikel tersimpan.</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              {filtered.map(bookmark => {
                const art = bookmark.article
                if (!art) return null
                const statusCfg = STATUS_OPTIONS.find(s => s.value === bookmark.status)

                return (
                  <div key={bookmark.id} className="card" style={{ padding: 16 }}>
                    <div style={{ display: 'flex', gap: 12 }}>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 8, flexWrap: 'wrap' }}>
                          <select
                            value={bookmark.status}
                            onChange={e => handleUpdateStatus(bookmark.id, e.target.value)}
                            style={{
                              fontSize: 11, padding: '2px 8px', borderRadius: 999,
                              background: `${statusCfg?.color}15`,
                              color: statusCfg?.color,
                              border: `1px solid ${statusCfg?.color}40`,
                              fontWeight: 600,
                            }}
                          >
                            {STATUS_OPTIONS.map(o => (
                              <option key={o.value} value={o.value}>{o.label}</option>
                            ))}
                          </select>
                          <VerificationBadge
                            status={art.verification_status}
                            isOA={art.is_open_access ?? undefined}
                            small
                          />
                        </div>

                        <div style={{ fontWeight: 700, fontSize: 14, color: 'var(--text-primary)', marginBottom: 4 }}>
                          {art.title}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-secondary)', marginBottom: 6 }}>
                          {art.authors?.map(a => a.name).join(', ')} · {art.year} · <em>{art.journal_name}</em>
                        </div>

                        {bookmark.notes && editingNote !== bookmark.id && (
                          <div style={{
                            background: 'rgba(99,102,241,0.06)',
                            border: '1px solid rgba(99,102,241,0.15)',
                            borderRadius: 6, padding: '8px 12px',
                            fontSize: 13, color: 'var(--text-secondary)',
                            marginBottom: 6,
                          }}>
                            📝 {bookmark.notes}
                          </div>
                        )}

                        {editingNote === bookmark.id && (
                          <div style={{ marginBottom: 8 }}>
                            <textarea
                              value={noteText}
                              onChange={e => setNoteText(e.target.value)}
                              style={{ width: '100%', fontSize: 13, minHeight: 70 }}
                              placeholder="Tambahkan catatan..."
                            />
                            <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                              <button className="btn-primary" onClick={() => handleSaveNote(bookmark.id)} style={{ fontSize: 12, padding: '4px 12px' }}>Simpan</button>
                              <button className="btn-ghost" onClick={() => setEditingNote(null)} style={{ fontSize: 12 }}>Batal</button>
                            </div>
                          </div>
                        )}

                        <SourceBadges sources={art.sources || []} />
                      </div>

                      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, alignItems: 'flex-end' }}>
                        <button
                          className="btn-ghost"
                          onClick={() => { setEditingNote(bookmark.id); setNoteText(bookmark.notes || '') }}
                          style={{ padding: '4px 8px', fontSize: 11 }}
                        >
                          <Edit size={11} /> Catatan
                        </button>
                        {art.doi && (
                          <a
                            href={`https://doi.org/${art.doi}`}
                            target="_blank" rel="noopener noreferrer"
                            className="btn-ghost"
                            style={{ padding: '4px 8px', fontSize: 11, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 3 }}
                          >
                            DOI →
                          </a>
                        )}
                        {art.pdf_url && (
                          <a
                            href={art.pdf_url}
                            target="_blank" rel="noopener noreferrer"
                            className="btn-ghost"
                            style={{ padding: '4px 8px', fontSize: 11, textDecoration: 'none', display: 'flex', alignItems: 'center', gap: 3, color: '#10b981', borderColor: '#10b98140' }}
                          >
                            PDF →
                          </a>
                        )}
                        <button
                          className="btn-ghost"
                          onClick={() => handleDelete(bookmark.id)}
                          style={{ padding: '4px 8px', fontSize: 11, color: '#ef4444', borderColor: '#ef444430' }}
                        >
                          <Trash2 size={11} />
                        </button>
                      </div>
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
