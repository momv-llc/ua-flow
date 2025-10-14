import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { login, register } from '../api'

export default function Login() {
  const [email, setEmail] = useState('admin@example.com')
  const [password, setPassword] = useState('admin123')
  const [mode, setMode] = useState('login')
  const nav = useNavigate()

  async function submit(e) {
    e.preventDefault()
    try {
      if (mode === 'login') {
        const data = await login(email, password)
        localStorage.setItem('token', data.access_token)
        nav('/')
      } else {
        await register(email, password)
        alert('Registered. Now login.')
        setMode('login')
      }
    } catch (e) {
      alert(e.message)
    }
  }

  return (
    <div style={{maxWidth: 420, margin: '80px auto', fontFamily: 'Inter, system-ui'}}>
      <h1>UA FLOW</h1>
      <p>Вход / Регистрация</p>
      <form onSubmit={submit}>
        <input placeholder="Email" value={email} onChange={e => setEmail(e.target.value)} style={{width:'100%',padding:10,margin:'8px 0'}}/>
        <input type="password" placeholder="Пароль" value={password} onChange={e => setPassword(e.target.value)} style={{width:'100%',padding:10,margin:'8px 0'}}/>
        <button style={{padding:10,width:'100%'}}>{mode === 'login' ? 'Войти' : 'Зарегистрироваться'}</button>
      </form>
      <div style={{marginTop:10}}>
        <button onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
          {mode === 'login' ? 'Нет аккаунта? Регистрация' : 'Уже есть аккаунт? Войти'}
        </button>
      </div>
    </div>
  )
}
