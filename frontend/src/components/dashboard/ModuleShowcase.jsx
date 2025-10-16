import React, { useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import Card from '../ui/Card'

const MODULES = [
  {
    key: 'kanban',
    icon: '🗂️',
    lanes: [
      { title: 'Backlog', count: 5 },
      { title: 'In Progress', count: 3 },
      { title: 'Review', count: 2 },
      { title: 'Done', count: 12 },
    ],
  },
  {
    key: 'scrum',
    icon: '🏃‍♀️',
    metrics: [
      { name: 'Velocity', value: '32 SP', trend: '+8%' },
      { name: 'Focus factor', value: '78%', trend: '+4%' },
      { name: 'Burndown', value: 'on track', trend: '✓' },
    ],
  },
  {
    key: 'docs',
    icon: '📚',
    docs: [
      { title: 'Процес узгодження договорів', version: 'v4', signed: true },
      { title: 'Інструкція з безпеки даних', version: 'v2', signed: false },
    ],
  },
  {
    key: 'support',
    icon: '🛟',
    tickets: [
      { id: 'SUP-218', status: 'SLA 2h', channel: 'Telegram' },
      { id: 'SUP-219', status: 'Escalated', channel: 'Email' },
    ],
  },
]

export default function ModuleShowcase() {
  const { t } = useTranslation()
  const [active, setActive] = useState('kanban')

  const description = useMemo(() => t(`dashboard.cards.${active}.description`), [active, t])

  const activeModule = useMemo(() => MODULES.find((item) => item.key === active), [active])

  return (
    <Card
      title={t('dashboard.modulesHeading')}
      subtitle={t('dashboard.modulesDescription')}
      headerAction={
        <div className="ui-segmented" role="tablist" aria-label="Module showcase">
          {MODULES.map((module) => (
            <button
              key={module.key}
              type="button"
              className={module.key === active ? 'active' : ''}
              onClick={() => setActive(module.key)}
              role="tab"
              aria-selected={module.key === active}
            >
              {module.icon} {t(`dashboard.cards.${module.key}.title`)}
            </button>
          ))}
        </div>
      }
    >
      <p style={{ marginBottom: 20 }}>{description}</p>

      {activeModule?.lanes && (
        <div className="grid four">
          {activeModule.lanes.map((lane) => (
            <div key={lane.title} className="panel" style={{ textAlign: 'center' }}>
              <div className="chip" style={{ marginBottom: 12 }}>
                {lane.title}
              </div>
              <strong style={{ fontSize: '2rem' }}>{lane.count}</strong>
              <div style={{ color: 'var(--color-text-muted)', marginTop: 6 }}>
                {t('dashboard.cards.kanban.cardsLabel')}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeModule?.metrics && (
        <div className="grid three">
          {activeModule.metrics.map((metric) => (
            <div key={metric.name} className="panel">
              <div className="badge-dot">{metric.name}</div>
              <div style={{ fontSize: '2rem', fontWeight: 700, marginTop: 12 }}>{metric.value}</div>
              <div style={{ color: 'var(--color-success)', marginTop: 6 }}>{metric.trend}</div>
            </div>
          ))}
        </div>
      )}

      {activeModule?.docs && (
        <div className="grid two">
          {activeModule.docs.map((doc) => (
            <div key={doc.title} className="panel">
              <div className="badge-dot">{doc.title}</div>
              <div style={{ marginTop: 8, color: 'var(--color-text-muted)' }}>{t('dashboard.cards.docs.title')}</div>
              <div style={{ marginTop: 12, fontWeight: 600 }}>
                {t('dashboard.cards.docs.version', { value: doc.version })}
              </div>
              <div style={{ marginTop: 6, color: doc.signed ? 'var(--color-success)' : 'var(--color-warning)' }}>
                {doc.signed ? t('dashboard.cards.docs.signed') : t('dashboard.cards.docs.pending')}
              </div>
            </div>
          ))}
        </div>
      )}

      {activeModule?.tickets && (
        <div className="grid two">
          {activeModule.tickets.map((ticket) => (
            <div key={ticket.id} className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div className="badge-dot">{ticket.id}</div>
              <div style={{ fontSize: '0.9rem', color: 'var(--color-text-muted)' }}>{ticket.channel}</div>
              <div style={{ fontWeight: 600 }}>{ticket.status}</div>
            </div>
          ))}
        </div>
      )}
    </Card>
  )
}

