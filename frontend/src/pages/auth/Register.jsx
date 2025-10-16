import React, { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../providers/AuthProvider'
import Button from '../../components/ui/Button'

export default function RegisterPage() {
  const { register } = useAuth()
  const navigate = useNavigate()
  const [form, setForm] = useState({ email: '', password: '' })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const [success, setSuccess] = useState(false)
  const { t } = useTranslation()

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
    <div
      style={{
        minHeight: '100vh',
        display: 'grid',
        placeItems: 'center',
        background: 'linear-gradient(160deg, #fde047 0%, #0d6efd 100%)',
        padding: 24,
      }}
    >
      <div className="panel" style={{ width: 'min(500px, 92vw)' }}>
        <div className="ui-chip">UA FLOW • {t('brand.tagline')}</div>
        <h1 style={{ marginTop: 12 }}>{t('auth.registerTitle')}</h1>
        <p style={{ color: 'var(--color-text-muted)' }}>{t('topbar.description')}</p>
        <form className="grid" style={{ marginTop: 24 }} onSubmit={handleSubmit}>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>{t('auth.email')}</div>
            <input
              required
              type="email"
              value={form.email}
              onChange={(event) => setForm((prev) => ({ ...prev, email: event.target.value }))}
            />
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>{t('auth.password')}</div>
            <input
              required
              type="password"
              value={form.password}
              onChange={(event) => setForm((prev) => ({ ...prev, password: event.target.value }))}
            />
          </label>
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button type="submit" disabled={loading}>
              {loading ? '…' : t('auth.goRegister')}
            </Button>
            <Link to="/auth/login" style={{ color: 'var(--color-accent)' }}>
              {t('auth.haveAccount')} {t('auth.goLogin')}
            </Link>
          </div>
        </form>
        {error && <div style={{ marginTop: 16, color: 'var(--danger)' }}>{error.message}</div>}
        {success && <div style={{ marginTop: 16, color: 'var(--success)' }}>{t('auth.registerSuccess')}</div>}
      </div>
    </div>
  )
}
