import React from 'react'
import { NavLink } from 'react-router-dom'
import { useAuth } from '../../providers/AuthProvider'

const sections = [
  {
    title: 'Платформа',
    links: [
      { to: '/', label: 'Дашборд', icon: '📊' },
      { to: '/core/tasks', label: 'Задачи', icon: '🗂️' },
      { to: '/docs', label: 'Документы', icon: '📚' },
      { to: '/support', label: 'Служба поддержки', icon: '🛟' },
      { to: '/integrations', label: 'Integration Hub', icon: '🔌' },
    ],
  },
  {
    title: 'Управление',
    links: [
      { to: '/analytics', label: 'Аналитика', icon: '📈' },
      { to: '/settings', label: 'Настройки', icon: '⚙️' },
      { to: '/marketplace', label: 'Маркетплейс', icon: '🧩' },
    ],
  },
]

const adminSection = {
  title: 'Администрирование',
  links: [
    { to: '/admin/users', label: 'Пользователи и роли', icon: '🛡️' },
    { to: '/admin/audit', label: 'Аудит и безопасность', icon: '🗒️' },
  ],
}

export default function Sidebar() {
  const { user } = useAuth()
  const role = user?.role || 'user'

  return (
    <aside className="sidebar">
      <div className="logo">
        <span style={{ fontSize: '1.8rem' }}>🇺🇦</span>
        <div>
          <div>UA FLOW</div>
          <small style={{ opacity: 0.75 }}>Национальная платформа</small>
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
