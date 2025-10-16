import React, { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../providers/AuthProvider'
import Button from '../../components/ui/Button'
import '../../styles.css'

export default function LoginPage() {
  const navigate = useNavigate()
  const { login } = useAuth()
  const [params] = useSearchParams()
  const { t } = useTranslation()
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
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: 'linear-gradient(140deg, #0d6efd 0%, #fde047 100%)',
        padding: 24,
      }}
    >
      <div className="panel" style={{ width: 'min(460px, 92vw)' }}>
        <div className="ui-chip">UA FLOW • {t('brand.tagline')}</div>
        <h1 style={{ marginTop: 12 }}>{t('auth.loginTitle')}</h1>
        <p style={{ color: 'var(--color-text-muted)' }}>
          {t('topbar.description')}
        </p>
        <form className="grid" style={{ marginTop: 24 }} onSubmit={handleSubmit}>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>{t('auth.email')}</div>
            <input
              type="email"
              required
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            />
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>{t('auth.password')}</div>
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
            <Button type="submit" disabled={loading}>
              {loading ? '…' : t('auth.submit')}
            </Button>
            <Link to="/auth/register" style={{ color: 'var(--color-accent)' }}>
              {t('auth.noAccount')} {t('auth.goRegister')}
            </Link>
          </div>
        </form>
        {error && <div style={{ marginTop: 16, color: 'var(--danger)' }}>{error.message}</div>}
      </div>
    </div>
  )
}
