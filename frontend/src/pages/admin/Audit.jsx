import React, { useEffect, useState } from 'react'
import { listAuditLogs } from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'
import Button from '../../components/ui/Button'

export default function AuditPage() {
  const [logs, setLogs] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function fetchLogs() {
    setLoading(true)
    setError(null)
    try {
      const data = await listAuditLogs(50)
      setLogs(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchLogs()
  }, [])

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={fetchLogs} />

  return (
    <section className="panel">
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 16 }}>
        <div>
          <h2>Журнал действий</h2>
          <p style={{ color: 'var(--color-text-muted)', marginTop: 4 }}>
            Последние операции безопасности и администрирования. Логи хранятся 90 дней.
          </p>
        </div>
        <Button variant="ghost" onClick={fetchLogs}>
          Обновить
        </Button>
      </div>

      <table className="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>Пользователь</th>
            <th>Действие</th>
            <th>Детали</th>
            <th>Время</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id}>
              <td>{log.id}</td>
              <td>{log.actor_id ?? '—'}</td>
              <td>{log.action}</td>
              <td>
                <code style={{ fontSize: '0.8rem' }}>{JSON.stringify(log.metadata)}</code>
              </td>
              <td>{new Date(log.created_at).toLocaleString()}</td>
            </tr>
          ))}
          {logs.length === 0 && (
            <tr>
              <td colSpan={5} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)' }}>
                Записей аудита пока нет
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </section>
  )
}
