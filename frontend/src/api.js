const resolveDefaultApiUrl = () => {
  if (typeof window !== 'undefined') {
    const host = window.location.hostname
    if (host === 'localhost' || host === '127.0.0.1') {
      return 'http://localhost:8000/api/v1'
    }
    return '/api/v1'
  }
  return 'http://localhost:8000/api/v1'
}

const API_URL = (import.meta.env.VITE_API_URL || resolveDefaultApiUrl()).replace(/\/$/, '')

async function request(path, { method = 'GET', data, params, headers, auth = true } = {}) {
  const url = new URL(`${API_URL}${path}`)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.append(key, value)
      }
    })
  }

async function request(path, { method = 'GET', data, params, headers, auth = true } = {}) {
  const url = new URL(`${API_URL}${path}`)
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') {
        url.searchParams.append(key, value)
      }
    })
  }

  const finalHeaders = new Headers(headers || {})
  if (auth) {
    const token = localStorage.getItem('token')
    if (token) {
      finalHeaders.set('Authorization', `Bearer ${token}`)
    }
  }

  let body
  if (data !== undefined) {
    if (data instanceof FormData) {
      body = data
    } else {
      finalHeaders.set('Content-Type', 'application/json')
      body = JSON.stringify(data)
    }
  }

  const res = await fetch(url.toString(), {
    method,
    headers: finalHeaders,
    body,
  })

  if (res.status === 204) {
    return null
  }

  const text = await res.text()
  const contentType = res.headers.get('content-type') || ''
  let payload = null
  if (text && contentType.includes('application/json')) {
    try {
      payload = JSON.parse(text)
    } catch (error) {
      const snippet = text.length > 120 ? `${text.slice(0, 117)}...` : text
      throw new Error(`Unexpected response from server: ${snippet}`)
    }
  }
  if (!res.ok) {
    const detail = payload?.detail || (text && !contentType.includes('application/json') ? text : res.statusText)
    throw new Error(Array.isArray(detail) ? detail.join(', ') : detail)
  }
  if (payload !== null) {
    return payload
  }
  if (!text) {
    return null
  }
  if (!contentType.includes('application/json')) {
    throw new Error('Server returned an unexpected response format. Please try again later.')
  }
  const payload = text ? JSON.parse(text) : null
  if (!res.ok) {
    const detail = payload?.detail || res.statusText
    throw new Error(Array.isArray(detail) ? detail.join(', ') : detail)
  }
  return payload
}

export async function login(email, password, twofaCode) {
  return request('/auth/login', {
    method: 'POST',
    data: { email, password, twofa_code: twofaCode },
    auth: false,
  })
}

export async function register(email, password) {
  return request('/auth/register', {
    method: 'POST',
    data: { email, password },
    auth: false,
  })
}

export async function refreshToken(refresh_token) {
  return request('/auth/refresh', {
    method: 'POST',
    data: { refresh_token },
    auth: false,
  })
}

export async function getCurrentUser() {
  return request('/auth/me')
}

export async function setup2FA() {
  return request('/auth/2fa/setup', { method: 'POST' })
}

export async function enable2FA(code) {
  return request('/auth/2fa/enable', { method: 'POST', data: { code } })
}

export async function disable2FA() {
  return request('/auth/2fa/disable', { method: 'POST' })
}

export async function listProjects() {
  return request('/projects/projects')
}

export async function createProject(payload) {
  return request('/projects/projects', { method: 'POST', data: payload })
}

export async function listTeams() {
  return request('/projects/teams')
}

export async function listSprints(projectId) {
  return request(`/projects/projects/${projectId}/sprints`)
}

export async function listEpics(projectId) {
  return request(`/projects/projects/${projectId}/epics`)
}

export async function listTasks(filters = {}) {
  return request('/tasks/', { params: filters })
}

export async function createTask(payload) {
  return request('/tasks/', { method: 'POST', data: payload })
}

export async function updateTask(taskId, payload) {
  return request(`/tasks/${taskId}`, { method: 'PUT', data: payload })
}

export async function changeTaskStatus(taskId, status) {
  return request(`/tasks/${taskId}/status`, { method: 'PATCH', params: { status } })
}

export async function getKanban(projectId) {
  return request('/tasks/board/view', { params: { project_id: projectId } })
}

export async function getBurndown(filters) {
  return request('/tasks/reports/burndown', { method: 'POST', data: filters })
}

export async function listDocs() {
  return request('/docs/')
}

export async function getDoc(docId) {
  return request(`/docs/${docId}`)
}

export async function createDoc(payload) {
  return request('/docs/', { method: 'POST', data: payload })
}

export async function updateDoc(docId, payload) {
  return request(`/docs/${docId}`, { method: 'PUT', data: payload })
}

export async function signDoc(docId) {
  return request(`/docs/${docId}/sign`, { method: 'POST' })
}

export async function listDocVersions(docId) {
  return request(`/docs/${docId}/versions`)
}

export async function listTickets(filters = {}) {
  return request('/support/', { params: filters })
}

export async function createTicket(payload) {
  return request('/support/', { method: 'POST', data: payload })
}

export async function listIntegrations() {
  return request('/integrations/connections')
}

export async function listIntegrationLogs(id) {
  return request(`/integrations/connections/${id}/logs`)
}

export async function testIntegration(id) {
  return request(`/integrations/connections/${id}/test`, { method: 'POST' })
}

export async function syncIntegration(id, payload) {
  return request(`/integrations/connections/${id}/sync`, { method: 'POST', data: payload })
}

export async function listAdminUsers() {
  return request('/admin/users')
}

export async function listAuditLogs(limit = 10) {
  return request('/admin/audit', { params: { limit } })
}

export async function updateUserRole(userId, role) {
  return request(`/admin/users/${userId}/role`, { method: 'POST', data: { role } })
}

export async function listAnalyticsSummary() {
  return request('/analytics/overview')
}

export async function listAnalyticsVelocity(params) {
  return request('/analytics/velocity', { params })
}

export async function listAnalyticsSupport(params) {
  return request('/analytics/support', { params })
}

export async function listSettings() {
  return request('/admin/settings')
}

export async function updateSetting(key, value) {
  return request(`/admin/settings/${key}`, { method: 'PUT', data: { value } })
}

export async function listMarketplaceApps() {
  return request('/integrations/marketplace')
}

export async function installMarketplaceApp(appId) {
  return request(`/integrations/marketplace/${appId}/install`, { method: 'POST' })
}

export async function triggerWebhookPreview(payload) {
  return request('/integrations/webhooks/preview', { method: 'POST', data: payload })
}

export async function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('refreshToken')
}

export function storeTokens({ access_token, refresh_token }) {
  if (access_token) localStorage.setItem('token', access_token)
  if (refresh_token) localStorage.setItem('refreshToken', refresh_token)
}
