import React, { useEffect, useState } from 'react'
import { createTicket, listTickets } from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

const initialTicket = {
  subject: '',
  body: '',
  priority: 'normal',
  channel: 'web',
}

export default function SupportPage() {
  const [tickets, setTickets] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [form, setForm] = useState(initialTicket)
  const [submitting, setSubmitting] = useState(false)

  async function fetchTickets() {
    setLoading(true)
    setError(null)
    try {
      const data = await listTickets()
      setTickets(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTickets()
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    setSubmitting(true)
    try {
      await createTicket(form)
      setForm(initialTicket)
      await fetchTickets()
    } catch (err) {
      setError(err)
    } finally {
      setSubmitting(false)
    }
  }

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={fetchTickets} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <h2>Создать обращение</h2>
        <p style={{ color: 'var(--text-muted)' }}>
          Поддерживаются каналы: веб-портал, Telegram-бот, email. SLA рассчитывается автоматически по приоритету.
        </p>
        <form className="grid" style={{ marginTop: 16 }} onSubmit={handleSubmit}>
          <label style={{ gridColumn: '1 / -1' }}>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Тема</div>
            <input value={form.subject} onChange={(event) => setForm((prev) => ({ ...prev, subject: event.target.value }))} required />
          </label>
          <label style={{ gridColumn: '1 / -1' }}>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Описание проблемы</div>
            <textarea value={form.body} onChange={(event) => setForm((prev) => ({ ...prev, body: event.target.value }))} required />
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Приоритет</div>
            <select value={form.priority} onChange={(event) => setForm((prev) => ({ ...prev, priority: event.target.value }))}>
              <option value="low">Низкий</option>
              <option value="normal">Нормальный</option>
              <option value="high">Высокий</option>
              <option value="urgent">Критичный</option>
            </select>
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Канал</div>
            <select value={form.channel} onChange={(event) => setForm((prev) => ({ ...prev, channel: event.target.value }))}>
              <option value="web">Веб-портал</option>
              <option value="telegram">Telegram</option>
              <option value="email">Email</option>
            </select>
          </label>
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            <button className="primary" type="submit" disabled={submitting}>
              {submitting ? 'Отправляем...' : 'Отправить заявку'}
            </button>
          </div>
        </form>
      </section>

      <section className="panel">
        <h2>Последние тикеты</h2>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Тема</th>
              <th>Статус</th>
              <th>Приоритет</th>
              <th>SLA до</th>
            </tr>
          </thead>
          <tbody>
            {tickets.map((ticket) => (
              <tr key={ticket.id}>
                <td>{ticket.id}</td>
                <td>{ticket.subject}</td>
                <td>
                  <span className={`tag ${ticket.status === 'resolved' ? 'success' : ticket.status === 'urgent' ? 'danger' : 'warning'}`}>
                    {ticket.status}
                  </span>
                </td>
                <td>{ticket.priority}</td>
                <td>{ticket.sla_due}</td>
              </tr>
            ))}
            {tickets.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                  Обращения не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
