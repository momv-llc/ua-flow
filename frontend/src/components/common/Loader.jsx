import React from 'react'

export default function Loader({ text = 'Загрузка данных...' }) {
  return (
    <div className="panel" style={{ textAlign: 'center', padding: '60px 0' }}>
      <div style={{ fontSize: '2rem' }}>🔄</div>
      <div style={{ marginTop: 12, fontWeight: 600 }}>{text}</div>
      <div style={{ marginTop: 6, color: 'var(--text-muted)' }}>Пожалуйста, подождите...</div>
    </div>
  )
}
