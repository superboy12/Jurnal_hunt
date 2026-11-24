import React from 'react'
import { NavLink } from 'react-router-dom'
import {
  LayoutDashboard, Search, BookOpen, Clock, Bookmark,
  Settings, Zap, Database, Compass
} from 'lucide-react'

export default function Sidebar() {
  const navItems = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/search', icon: Search, label: 'AI Search' },
    { to: '/journals', icon: BookOpen, label: 'Journal Explorer' },
    { to: '/scopus-sources', icon: Compass, label: 'Scopus & Sumber Ilmiah' },
    { to: '/history', icon: Clock, label: 'Search History' },
    { to: '/saved', icon: Bookmark, label: 'Saved Articles' },
    { to: '/settings', icon: Settings, label: 'Settings' },
  ]

  return (
    <aside className="sidebar" style={{ display: 'flex', flexDirection: 'column', height: '100vh', position: 'fixed', left: 0, top: 0, width: 260, borderRight: '1px solid var(--border)', background: 'var(--bg-secondary)', zIndex: 100 }}>
      {/* Logo */}
      <div style={{ padding: '20px 20px 14px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div className="gradient-primary" style={{
            width: 36, height: 36, borderRadius: 10,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            boxShadow: '0 0 20px rgba(99,102,241,0.4)'
          }}>
            <Zap size={20} color="white" />
          </div>
          <div>
            <div style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 700, fontSize: 15, color: 'var(--text-primary)', lineHeight: 1.2 }}>
              AI Journal
            </div>
            <div style={{ fontFamily: 'Space Grotesk, sans-serif', fontWeight: 700, fontSize: 15, color: 'var(--primary-light)', lineHeight: 1.2 }}>
              Hunter
            </div>
          </div>
        </div>
        <div style={{ marginTop: 8, fontSize: 11, color: 'var(--text-muted)' }}>
          Academic Discovery & Verification
        </div>
      </div>

      {/* Navigation */}
      <nav style={{ flex: 1, padding: '12px 0', overflowY: 'auto' }}>
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              `sidebar-nav-item ${isActive ? 'active' : ''}`
            }
            style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <Icon size={18} />
              <span>{label}</span>
            </div>
          </NavLink>
        ))}
      </nav>

      {/* Footer */}
      <div style={{
        padding: '10px 16px',
        borderTop: '1px solid var(--border)',
        fontSize: 11,
        color: 'var(--text-muted)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
          <Database size={11} />
          <span>v1.0.0</span>
        </div>
        <span>AI Journal Hunter</span>
      </div>
    </aside>
  )
}
