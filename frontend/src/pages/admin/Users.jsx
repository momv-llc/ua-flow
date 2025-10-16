import React, { useEffect, useState } from 'react'
import { listAdminUsers, listAuditLogs, updateUserRole } from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

const roles = ['admin', 'moderator', 'user', 'integrator', 'guest']

export default function AdminUsersPage() {
  const [users, setUsers] = useState([])
  const [audit, setAudit] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function load() {
    setLoading(true)
    setError(null)
    try {
      const [userList, auditLog] = await Promise.all([listAdminUsers(), listAuditLogs(15)])
      setUsers(userList)
      setAudit(auditLog)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  async function changeRole(userId, role) {
    await updateUserRole(userId, role)
    await load()
  }

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={load} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <h2>Управление пользователями</h2>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>Email</th>
              <th>Роль</th>
              <th>2FA</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            {users.map((user) => (
              <tr key={user.id}>
                <td>{user.email}</td>
                <td>{user.role}</td>
                <td>{user.twofactor_enabled ? '✅' : '—'}</td>
                <td>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {roles.map((role) => (
                      <button
                        key={role}
                        className={user.role === role ? 'primary' : 'secondary'}
                        onClick={() => changeRole(user.id, role)}
                      >
                        {role}
                      </button>
                    ))}
                  </div>
                </td>
              </tr>
            ))}
            {users.length === 0 && (
              <tr>
                <td colSpan={4} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                  Пользователи не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>

      <section className="panel">
        <h2>Последние события безопасности</h2>
        <ul className="timeline" style={{ marginTop: 16 }}>
          {audit.map((record) => (
            <li key={record.id}>
              <strong>{record.action}</strong>
              <div style={{ color: 'var(--text-muted)', fontSize: '0.8rem' }}>{record.created_at}</div>
            </li>
          ))}
          {audit.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Нет событий</div>}
        </ul>
      </section>
    </div>
  )
}
