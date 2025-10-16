import React, { useEffect, useState } from 'react'
import { installMarketplaceApp, listMarketplaceApps } from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

export default function MarketplacePage() {
  const [apps, setApps] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [installing, setInstalling] = useState(null)

  async function loadApps() {
    setLoading(true)
    setError(null)
    try {
      const data = await listMarketplaceApps()
      setApps(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadApps()
  }, [])

  async function handleInstall(id) {
    setInstalling(id)
    try {
      await installMarketplaceApp(id)
      await loadApps()
    } catch (err) {
      setError(err)
    } finally {
      setInstalling(null)
    }
  }

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={loadApps} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <h2>UA Marketplace</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Расширяйте платформу интеграциями: Prozorro, Дія, Медок, 1С и кастомные решения партнёров.
        </p>
        <div className="grid three" style={{ marginTop: 16 }}>
          {apps.map((app) => (
            <div key={app.id} className="panel" style={{ background: 'var(--bg-elevated)' }}>
              <div className="badge-dot">{app.name}</div>
              <div style={{ marginTop: 8, color: 'var(--text-muted)' }}>{app.description}</div>
              <div style={{ marginTop: 12, fontSize: '0.8rem', color: 'var(--text-muted)' }}>Категория: {app.category}</div>
              <button
                className="primary"
                style={{ marginTop: 16 }}
                onClick={() => handleInstall(app.id)}
                disabled={installing === app.id}
              >
                {app.installed ? 'Установлено' : installing === app.id ? 'Устанавливаем...' : 'Установить'}
              </button>
            </div>
          ))}
          {apps.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Пока нет доступных приложений</div>}
        </div>
      </section>
    </div>
  )
}
