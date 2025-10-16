import React from 'react'

export default function StatCard({ title, value, trend, trendLabel, icon }) {
  const positive = trend >= 0
  return (
    <div className="panel stat-card" style={{ position: 'relative', overflow: 'hidden' }}>
      <div style={{ fontSize: '1.4rem', position: 'absolute', top: 16, right: 24, opacity: 0.15 }}>{icon}</div>
      <h3>{title}</h3>
      <strong>{value}</strong>
      {trend !== undefined && (
        <div style={{ marginTop: 12, fontSize: '0.8rem', color: positive ? 'var(--success)' : 'var(--danger)' }}>
          {positive ? '▲' : '▼'} {Math.abs(trend)}% {trendLabel}
        </div>
      )}
    </div>
  )
}
