import React, { createContext, useContext, useEffect, useMemo, useState } from 'react'
import {
  enable2FA,
  getCurrentUser,
  login,
  logout as apiLogout,
  refreshToken,
  register,
  setup2FA,
  storeTokens,
} from '../api'

const AuthContext = createContext()

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [twoFactor, setTwoFactor] = useState(null)

  async function bootstrap() {
    setLoading(true)
    try {
      const profile = await getCurrentUser()
      setUser(profile)
    } catch (error) {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    bootstrap()
  }, [])

  async function handleLogin({ email, password, code }) {
    const tokens = await login(email, password, code)
    storeTokens(tokens)
    await bootstrap()
    return tokens
  }

  async function handleRegister({ email, password }) {
    return register(email, password)
  }

  async function handleRefresh() {
    const refresh_token = localStorage.getItem('refreshToken')
    if (!refresh_token) return null
    const tokens = await refreshToken(refresh_token)
    storeTokens(tokens)
    return tokens
  }

  async function handleLogout() {
    apiLogout()
    setUser(null)
  }

  async function initialize2FA() {
    const setup = await setup2FA()
    setTwoFactor(setup)
    return setup
  }

  async function verify2FA(code) {
    const response = await enable2FA(code)
    setTwoFactor(null)
    await bootstrap()
    return response
  }

  const value = useMemo(
    () => ({
      user,
      loading,
      login: handleLogin,
      register: handleRegister,
      refresh: handleRefresh,
      logout: handleLogout,
      bootstrap,
      initialize2FA,
      verify2FA,
      twoFactor,
    }),
    [user, loading, twoFactor],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth must be used within AuthProvider')
  return context
}
