import React from 'react'
import { useAuth } from '../../providers/AuthProvider'
import { useTheme } from '../../providers/ThemeProvider'

export default function Topbar() {
  const { user, logout } = useAuth()
  const { theme, toggle } = useTheme()

  return (
    <header className="main-header" style={{ marginBottom: 32 }}>
      <div>
        <div className="chip">UA FLOW • Всё под контролем</div>
        <h1>Добро пожаловать, {user?.email?.split('@')[0] || 'гость'}!</h1>
        <p style={{ color: 'var(--text-muted)', marginTop: 8 }}>
          Центральная панель управления задачами, документами, сервисом поддержки и интеграциями.
        </p>
      </div>
      <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
        <button className="secondary" onClick={toggle}>
          {theme === 'dark' ? 'Светлая тема' : 'Тёмная тема'}
        </button>
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'var(--bg-panel)',
            borderRadius: '999px',
            padding: '8px 14px',
            border: '1px solid var(--border)',
          }}
        >
          <div style={{ width: 32, height: 32, borderRadius: '50%', background: 'var(--accent)', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
            {user?.email ? user.email[0].toUpperCase() : '?'}
          </div>
          <div>
            <strong style={{ fontSize: '0.95rem' }}>{user?.email || 'Неавторизован'}</strong>
            <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{user?.role || 'guest'}</div>
          </div>
          <button className="link" onClick={logout} style={{ marginLeft: 4 }}>
            Выйти
          </button>
        </div>
      </div>
    </header>
  )
}
