import React from 'react'

const VARIANTS = {
  primary: 'ui-button ui-button--primary',
  secondary: 'ui-button ui-button--secondary',
  ghost: 'ui-button ui-button--ghost',
}

export default function Button({ variant = 'primary', className = '', icon, children, ...props }) {
  const classes = `${VARIANTS[variant] ?? VARIANTS.primary} ${className}`.trim()
  return (
    <button type="button" className={classes} {...props}>
      {icon ? <span aria-hidden="true">{icon}</span> : null}
      {children}
    </button>
  )
}

