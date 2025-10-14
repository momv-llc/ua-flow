const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export async function login(email, password) {
  const res = await fetch(`${API_URL}/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) throw new Error('Login failed')
  return res.json()
}

export async function register(email, password) {
  const res = await fetch(`${API_URL}/auth/register`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
  })
  if (!res.ok) throw new Error('Register failed')
  return res.json()
}

function authHeaders() {
  const token = localStorage.getItem('token')
  return { Authorization: `Bearer ${token}` }
}

export async function getMe() {
  const token = localStorage.getItem('token')
  const res = await fetch(`${API_URL}/auth/me?token=${token}`)
  return res.json()
}

export async function getTasks() {
  const res = await fetch(`${API_URL}/tasks/`, { headers: authHeaders() })
  return res.json()
}

export async function createTask(title, description) {
  const res = await fetch(`${API_URL}/tasks/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ title, description })
  })
  return res.json()
}

export async function setTaskStatus(id, status) {
  const res = await fetch(`${API_URL}/tasks/${id}/status?status=${encodeURIComponent(status)}`, {
    method: 'PATCH',
    headers: authHeaders()
  })
  return res.json()
}

export async function getDocs() {
  const res = await fetch(`${API_URL}/docs/`, { headers: authHeaders() })
  return res.json()
}

export async function createDoc(title, content_md) {
  const res = await fetch(`${API_URL}/docs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: JSON.stringify({ title, content_md })
  })
  return res.json()
}
