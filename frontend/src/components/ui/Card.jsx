import React from 'react'

export default function Card({ title, subtitle, children, variant, className = '', headerAction }) {
  return (
    <section className={`ui-card${variant ? ` ui-card--${variant}` : ''} ${className}`.trim()}>
      {(title || subtitle || headerAction) && (
        <header
          style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'flex-start',
            gap: 16,
            marginBottom: 16,
          }}
        >
          <div>
            {title ? <h3>{title}</h3> : null}
            {subtitle ? (
              <p style={{ margin: '6px 0 0', fontSize: '0.9rem' }}>{subtitle}</p>
            ) : null}
          </div>
          {headerAction || null}
        </header>
      )}
      {children}
    </section>
  )
}

