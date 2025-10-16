import React from 'react'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../providers/AuthProvider'
import ThemeToggle from '../ui/ThemeToggle'
import Button from '../ui/Button'
import LanguageSwitch from '../ui/LanguageSwitch'

export default function Topbar() {
  const { user, logout } = useAuth()
  const { t } = useTranslation()
  const displayName = user?.email?.split('@')[0] || 'guest'

  return (
    <header className="main-header" style={{ marginBottom: 32 }}>
      <div>
        <div className="ui-chip">UA FLOW • {t('brand.tagline')}</div>
        <h1>{t('topbar.welcome', { name: displayName })}</h1>
        <p style={{ color: 'var(--color-text-muted)', marginTop: 8 }}>{t('topbar.description')}</p>
      </div>
      <div className="ui-toolbar">
        <LanguageSwitch />
        <ThemeToggle />
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 12,
            background: 'var(--color-elevated)',
            borderRadius: '999px',
            padding: '10px 16px',
            border: '1px solid var(--color-border)',
            boxShadow: 'var(--shadow-sm)',
          }}
        >
          <div
            style={{
              width: 34,
              height: 34,
              borderRadius: '50%',
              background: 'var(--color-accent)',
              color: '#fff',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontWeight: 600,
            }}
          >
            {user?.email ? user.email[0].toUpperCase() : '?'}
          </div>
          <div style={{ minWidth: 120 }}>
            <strong style={{ fontSize: '0.95rem' }}>{user?.email || '—'}</strong>
            <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{user?.role || 'guest'}</div>
          </div>
          <Button variant="ghost" onClick={logout}>
            {t('topbar.logout')}
          </Button>
        </div>
      </div>
    </header>
  )
}
