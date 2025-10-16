import React, { useEffect, useState } from 'react'
import { listAnalyticsSummary, listAnalyticsSupport, listAnalyticsVelocity } from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

export default function AnalyticsPage() {
  const [summary, setSummary] = useState(null)
  const [velocity, setVelocity] = useState([])
  const [support, setSupport] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [overview, velocityData, supportData] = await Promise.all([
        listAnalyticsSummary(),
        listAnalyticsVelocity({ weeks: 6 }),
        listAnalyticsSupport({ weeks: 6 }),
      ])
      setSummary(overview)
      setVelocity(velocityData)
      setSupport(supportData)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={load} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <h2>Сводка по платформе</h2>
        <div className="grid three" style={{ marginTop: 16 }}>
          <div className="panel" style={{ background: 'var(--bg-elevated)' }}>
            <div className="chip">Команды</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{summary?.core?.teams ?? '—'}</div>
            <div style={{ color: 'var(--text-muted)' }}>Подключено команд</div>
          </div>
          <div className="panel" style={{ background: 'var(--bg-elevated)' }}>
            <div className="chip">Активные интеграции</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{summary?.integration?.active ?? '—'}</div>
            <div style={{ color: 'var(--text-muted)' }}>Включено коннекторов</div>
          </div>
          <div className="panel" style={{ background: 'var(--bg-elevated)' }}>
            <div className="chip">Поддержка</div>
            <div style={{ fontSize: '2rem', fontWeight: 700 }}>{summary?.support?.open_tickets ?? '0'}</div>
            <div style={{ color: 'var(--text-muted)' }}>Открытых тикетов</div>
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>Velocity по спринтам</h2>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Неделя</th>
              <th>Скорость</th>
              <th>Завершено задач</th>
              <th>План</th>
            </tr>
          </thead>
          <tbody>
            {velocity.map((row) => (
              <tr key={row.week}>
                <td>{row.week}</td>
                <td>{row.velocity}</td>
                <td>{row.completed}</td>
                <td>{row.planned}</td>
              </tr>
            ))}
            {velocity.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                  Недостаточно данных для расчёта velocity
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Служба поддержки</h2>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Неделя</th>
              <th>Входящих тикетов</th>
              <th>Решено</th>
              <th>SLA, ч</th>
            </tr>
          </thead>
          <tbody>
            {support.map((row) => (
              <tr key={row.week}>
                <td>{row.week}</td>
                <td>{row.incoming}</td>
                <td>{row.resolved}</td>
                <td>{row.avg_sla}</td>
              </tr>
            ))}
            {support.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                  Данные службы поддержки появятся после первых обращений
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
