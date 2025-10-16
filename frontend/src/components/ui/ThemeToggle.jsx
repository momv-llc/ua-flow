import React from 'react'
import { useTranslation } from 'react-i18next'
import { useTheme } from '../../providers/ThemeProvider'
import Button from './Button'

export default function ThemeToggle() {
  const { theme, toggle } = useTheme()
  const { t } = useTranslation()
  const label = theme === 'dark' ? t('theme.light') : t('theme.dark')

  return (
    <Button variant="secondary" onClick={toggle} aria-label={t('theme.toggle')}>
      {theme === 'dark' ? '🌞' : '🌙'} {label}
    </Button>
  )
}

