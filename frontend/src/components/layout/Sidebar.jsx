import React, { useMemo } from 'react'
import { NavLink } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../providers/AuthProvider'

export default function Sidebar() {
  const { t } = useTranslation()
  const { user } = useAuth()
  const role = user?.role || 'user'

  const sections = useMemo(
    () => [
      {
        title: t('nav.platform'),
        links: [
          { to: '/', label: t('nav.dashboard'), icon: '📊' },
          { to: '/core/tasks', label: t('nav.tasks'), icon: '🗂️' },
          { to: '/docs', label: t('nav.docs'), icon: '📚' },
          { to: '/support', label: t('nav.support'), icon: '🛟' },
          { to: '/integrations', label: t('nav.integrations'), icon: '🔌' },
        ],
      },
      {
        title: t('nav.management'),
        links: [
          { to: '/analytics', label: t('nav.analytics'), icon: '📈' },
          { to: '/settings', label: t('nav.settings'), icon: '⚙️' },
          { to: '/billing', label: t('nav.billing'), icon: '💳' },
          { to: '/marketplace', label: t('nav.marketplace'), icon: '🧩' },
        ],
      },
    ],
    [t],
  )

  const adminSection = useMemo(
    () => ({
      title: t('nav.admin'),
      links: [
        { to: '/admin/users', label: t('nav.users'), icon: '🛡️' },
        { to: '/admin/audit', label: t('nav.audit'), icon: '🗒️' },
      ],
    }),
    [t],
  )

  return (
    <aside className="sidebar">
      <div className="logo">
        <span style={{ fontSize: '1.8rem' }}>🇺🇦</span>
        <div>
          <div style={{ fontWeight: 700 }}>UA FLOW</div>
          <small style={{ opacity: 0.75 }}>{t('brand.tagline')}</small>
        </div>
      </div>

      {[...sections, ...(role === 'admin' || role === 'moderator' ? [adminSection] : [])].map((section) => (
        <div className="nav-section" key={section.title}>
          <div className="nav-title">{section.title}</div>
          {section.links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) => `nav-link${isActive ? ' active' : ''}`}
            >
              <span className="nav-icon">{link.icon}</span>
              <span>{link.label}</span>
            </NavLink>
          ))}
        </div>
      ))}

      <div style={{ marginTop: 'auto', fontSize: '0.8rem', opacity: 0.65 }}>
        <div>v0.4 — Heroic Tryzub</div>
        <div>© {new Date().getFullYear()} UA FLOW</div>
      </div>
    </aside>
  )
}
