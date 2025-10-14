import React, { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../../providers/AuthProvider'
import '../../styles.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [params] = useSearchParams()
  const [form, setForm] = useState({
    email: params.get('email') || 'admin@example.com',
    password: 'admin123',
    code: '',
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  async function handleSubmit(e) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      await login(form)
      navigate('/')
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ minHeight: '100vh', display: 'grid', placeItems: 'center', background: 'linear-gradient(140deg, #0d6efd 0%, #fde047 100%)' }}>
      <div className="panel" style={{ width: 'min(480px, 90vw)' }}>
        <div className="chip">UA FLOW • Единая авторизация</div>
        <h1 style={{ marginTop: 12 }}>Вход в систему</h1>
        <p style={{ color: 'var(--text-muted)' }}>
          Используйте корпоративную почту или учетную запись Telegram Login / eID для входа. 2FA поддерживается.
        </p>
        <form className="grid" style={{ marginTop: 24 }} onSubmit={handleSubmit}>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Email</div>
            <input
              type="email"
              required
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            />
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Пароль</div>
            <input
              type="password"
              required
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            />
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>2FA код (если включен)</div>
            <input
              placeholder="000000"
              value={form.code}
              onChange={(event) => setForm((prev) => ({ ...prev, code: event.target.value }))}
            />
          </label>
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <button className="primary" type="submit" disabled={loading}>
              {loading ? 'Входим...' : 'Войти'}
            </button>
            <Link to="/auth/register" style={{ color: 'var(--accent)' }}>
              Регистрация нового аккаунта
            </Link>
          </div>
        </form>
        {error && <div style={{ marginTop: 16, color: 'var(--danger)' }}>{error.message}</div>}
      </div>
    </div>
  )
}
