import React from 'react'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'

import Sidebar from './components/Sidebar'
import Dashboard from './pages/Dashboard'
import SearchPage from './pages/SearchPage'
import JournalsPage from './pages/JournalsPage'
import HistoryPage from './pages/HistoryPage'
import SavedArticlesPage from './pages/SavedArticlesPage'
import SettingsPage from './pages/SettingsPage'
import ScopusDirectoryPage from './pages/ScopusDirectoryPage'

export default function App() {
  return (
    <BrowserRouter>
      <div className="app-layout" style={{ display: 'flex', minHeight: '100vh', width: '100vw', background: 'var(--bg-primary)' }}>
        {/* Fixed Left Sidebar */}
        <Sidebar />

        {/* Scrollable Main Application Area */}
        <main
          className="main-content"
          style={{
            flex: 1,
            marginLeft: 260,
            minHeight: '100vh',
            overflowY: 'auto',
            background: 'var(--bg-primary)',
          }}
        >
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/journals" element={<JournalsPage />} />
            <Route path="/scopus-sources" element={<ScopusDirectoryPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/saved" element={<SavedArticlesPage />} />
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>

        {/* Global Toast Notifications */}
        <Toaster
          position="bottom-right"
          toastOptions={{
            duration: 4000,
            style: {
              background: '#18181b',
              color: '#f4f4f5',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '12px',
              fontSize: '13px',
              boxShadow: '0 10px 30px -5px rgba(0, 0, 0, 0.5)',
            },
            success: {
              iconTheme: {
                primary: '#10b981',
                secondary: '#18181b',
              },
            },
            error: {
              iconTheme: {
                primary: '#ef4444',
                secondary: '#18181b',
              },
            },
          }}
        />
      </div>
    </BrowserRouter>
  )
}
