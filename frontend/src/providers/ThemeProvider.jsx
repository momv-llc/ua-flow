import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'

const ThemeContext = createContext()
const THEME_STORAGE_KEY = 'ua-flow-theme'

function resolveInitialTheme() {
  if (typeof window === 'undefined') return 'light'
  const stored = localStorage.getItem(THEME_STORAGE_KEY)
  if (stored) return stored
  if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark'
  }
  return 'light'
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(resolveInitialTheme)

  useEffect(() => {
    const root = document.documentElement
    root.setAttribute('data-theme', theme)
    localStorage.setItem(THEME_STORAGE_KEY, theme)
  }, [theme])

  useEffect(() => {
    const matcher = window.matchMedia('(prefers-color-scheme: dark)')
    const handler = (event) => {
      setTheme((current) => {
        const stored = localStorage.getItem(THEME_STORAGE_KEY)
        if (stored) return current
        return event.matches ? 'dark' : 'light'
      })
    }
    matcher.addEventListener('change', handler)
    return () => matcher.removeEventListener('change', handler)
  }, [])

  const value = useMemo(
    () => ({
      theme,
      setTheme,
      toggle: () => setTheme((prev) => (prev === 'dark' ? 'light' : 'dark')),
      themes: ['light', 'dark'],
    }),
    [theme],
  )

  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>
}

export function useTheme() {
  const context = useContext(ThemeContext)
  if (!context) throw new Error('useTheme must be used within ThemeProvider')
  return context
}
