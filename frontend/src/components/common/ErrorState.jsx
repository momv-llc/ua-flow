import React from 'react'

export default function ErrorState({ error, onRetry }) {
  return (
    <div className="panel" style={{ textAlign: 'center', padding: '60px 0', border: '1px solid rgba(220,38,38,0.25)' }}>
      <div style={{ fontSize: '2rem' }}>⚠️</div>
      <div style={{ marginTop: 12, fontWeight: 600 }}>Произошла ошибка</div>
      <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>{error?.message || 'Не удалось получить данные'}</div>
      {onRetry && (
        <button className="primary" style={{ marginTop: 16 }} onClick={onRetry}>
          Повторить попытку
        </button>
      )}
    </div>
  )
}
