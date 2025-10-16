import React, { useEffect, useState } from 'react'
import { disable2FA, listSettings, updateSetting } from '../../api'
import { useAuth } from '../../providers/AuthProvider'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

export default function SettingsPage() {
  const { user, initialize2FA: init2fa, verify2FA, twoFactor, bootstrap } = useAuth()
  const [settings, setSettings] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [code, setCode] = useState('')
  const [savingKey, setSavingKey] = useState(null)

  async function loadSettings() {
    setLoading(true)
    setError(null)
    try {
      const data = await listSettings()
      setSettings(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadSettings()
  }, [])

  async function toggle2FA() {
    if (user?.twofactor_enabled) {
      await disable2FA()
      await Promise.all([loadSettings(), bootstrap()])
    } else {
      await init2fa()
    }
  }

  async function confirm2FA(event) {
    event.preventDefault()
    await verify2FA(code)
    await Promise.all([loadSettings(), bootstrap()])
    setCode('')
  }

  async function saveSetting(key, value) {
    setSavingKey(key)
    await updateSetting(key, value)
    await loadSettings()
    setSavingKey(null)
  }

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={loadSettings} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <h2>Безопасность</h2>
        <p style={{ color: 'var(--text-muted)' }}>Включите двухфакторную аутентификацию для защиты доступа.</p>
        <button className="primary" onClick={toggle2FA}>
          {user?.twofactor_enabled ? 'Отключить 2FA' : 'Настроить 2FA'}
        </button>
        {twoFactor && (
          <div style={{ marginTop: 20 }}>
            <div>Секрет: <code>{twoFactor.secret}</code></div>
            <div style={{ marginTop: 8 }}>Отсканируйте QR через приложение Google Authenticator / Дія.</div>
            <div style={{ marginTop: 16 }}>
              <form onSubmit={confirm2FA}>
                <input value={code} onChange={(event) => setCode(event.target.value)} placeholder="Введите код" />
                <button className="primary" type="submit" style={{ marginLeft: 12 }}>
                  Подтвердить
                </button>
              </form>
            </div>
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Параметры организации</h2>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Ключ</th>
              <th>Значение</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {settings.map((setting) => (
              <tr key={setting.key}>
                <td>{setting.key}</td>
                <td>
                  <input
                    value={setting.value}
                    onChange={(event) =>
                      setSettings((prev) =>
                        prev.map((item) =>
                          item.key === setting.key ? { ...item, value: event.target.value } : item,
                        ),
                      )
                    }
                  />
                </td>
                <td>
                  <button
                    className="primary"
                    disabled={savingKey === setting.key}
                    onClick={() => saveSetting(setting.key, setting.value)}
                  >
                    Сохранить
                  </button>
                </td>
              </tr>
            ))}
            {settings.length === 0 && (
              <tr>
                <td colSpan={3} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                  Системные настройки не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
