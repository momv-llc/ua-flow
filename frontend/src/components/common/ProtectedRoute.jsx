import React from 'react'
import { Navigate, Outlet } from 'react-router-dom'
import Loader from './Loader'
import { useAuth } from '../../providers/AuthProvider'

export default function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth()

  if (loading) {
    return <Loader text="Проверяем авторизацию..." />
  }

  if (!user) {
    return <Navigate to="/auth/login" replace />
  }

  if (roles && roles.length > 0 && !roles.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
