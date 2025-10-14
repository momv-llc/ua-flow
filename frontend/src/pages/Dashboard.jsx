import React, { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { getMe } from '../api'

export default function Dashboard() {
  const [me, setMe] = useState(null)
  const nav = useNavigate()

  useEffect(() => {
    getMe().then(setMe)
  }, [])

  function logout() {
    localStorage.removeItem('token')
    nav('/login')
  }

  return (
    <div style={{padding:20, fontFamily:'Inter, system-ui'}}>
      <h2>Dashboard</h2>
      <p>Здравствуйте, {me?.email}</p>
      <nav style={{display:'flex', gap:12}}>
        <Link to="/tasks">Задачи</Link>
        <Link to="/docs">Документы</Link>
        <button onClick={logout}>Выйти</button>
      </nav>
    </div>
  )
}
