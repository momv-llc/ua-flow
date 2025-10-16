import React from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { AuthProvider } from './providers/AuthProvider'
import { ThemeProvider } from './providers/ThemeProvider'
import Layout from './components/layout/Layout'
import ProtectedRoute from './components/common/ProtectedRoute'
import Dashboard from './pages/core/Dashboard'
import TasksPage from './pages/core/Tasks'
import DocsPage from './pages/docs/Docs'
import SupportPage from './pages/support/Support'
import IntegrationsPage from './pages/integrations/Integrations'
import AnalyticsPage from './pages/analytics/Analytics'
import SettingsPage from './pages/settings/Settings'
import MarketplacePage from './pages/marketplace/Marketplace'
import AdminUsersPage from './pages/admin/Users'
import LoginPage from './pages/auth/Login'
import RegisterPage from './pages/auth/Register'
import './styles.css'

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <BrowserRouter>
          <Routes>
            <Route path="/auth/login" element={<LoginPage />} />
            <Route path="/auth/register" element={<RegisterPage />} />

            <Route element={<ProtectedRoute />}>
              <Route element={<Layout />}>
                <Route index element={<Dashboard />} />
                <Route path="core/tasks" element={<TasksPage />} />
                <Route path="docs" element={<DocsPage />} />
                <Route path="support" element={<SupportPage />} />
                <Route path="integrations" element={<IntegrationsPage />} />
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="marketplace" element={<MarketplacePage />} />

                <Route element={<ProtectedRoute roles={['admin', 'moderator']} />}>
                  <Route path="admin/users" element={<AdminUsersPage />} />
                </Route>
              </Route>
            </Route>

            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </BrowserRouter>
      </AuthProvider>
    </ThemeProvider>
  )
}

createRoot(document.getElementById('root')).render(<App />)
