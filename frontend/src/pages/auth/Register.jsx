import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../providers/AuthProvider'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setLoading(true)
    setError(null)
    setSuccess(false)
    try {
      await register(form)
      setSuccess(true)
      setTimeout(() => navigate(`/auth/login?email=${encodeURIComponent(form.email)}`), 1200)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'linear-gradient(160deg, #fde047 0%, #0d6efd 100%)' }}>
      <div className="panel" style={{ width: 'min(520px, 90vw)' }}>
        <div className="chip">UA FLOW • Регистрация</div>
        <h1 style={{ marginTop: 12 }}>Создайте рабочий аккаунт</h1>
        <p style={{ color: 'var(--text-muted)' }}>
          Доступ к проектам, документации и службе поддержки будет предоставлен в соответствии с ролью.
        </p>
        <form className="grid" style={{ marginTop: 24 }} onSubmit={handleSubmit}>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Рабочий email</div>
            <input
              required
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            />
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Пароль</div>
            <input
              required
              type="password"
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            />
          </label>
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="primary" type="submit" disabled={loading}>
              {loading ? 'Создаём...' : 'Создать аккаунт'}
            </button>
            <Link to="/auth/login" style={{ color: 'var(--accent)' }}>
              Уже зарегистрированы? Войдите
            </Link>
          </div>
        </form>
        {error && <div style={{ marginTop: 16, color: 'var(--danger)' }}>{error.message}</div>}
        {success && <div style={{ marginTop: 16, color: 'var(--success)' }}>Аккаунт создан! Перенаправляем на вход...</div>}
      </div>
    </div>
  )
}
