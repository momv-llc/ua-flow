import React, { useEffect, useState } from 'react'
import { listAnalyticsSummary, listProjects, listTasks } from '../../api'
import StatCard from '../../components/common/StatCard'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [projects, setProjects] = useState([])
  const [tasks, setTasks] = useState([])

  async function fetchData() {
    setLoading(true)
    setError(null)
    try {
      const [summary, projectList, taskList] = await Promise.all([
        listAnalyticsSummary(),
        listProjects(),
        listTasks({ status: 'in_progress' }),
      ])
      setStats(summary)
      setProjects(projectList.slice(0, 5))
      setTasks(taskList.slice(0, 5))
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={fetchData} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <div className="grid three">
        <StatCard
          title="Активных задач"
          value={stats?.core?.active_tasks ?? tasks.length}
          trend={stats?.core?.task_growth || 0}
          trendLabel="за неделю"
          icon="🗂️"
        />
        <StatCard
          title="Средний SLA (часы)"
          value={stats?.support?.avg_sla_hours ?? '—'}
          trend={-1 * (stats?.support?.sla_delta || 0)}
          trendLabel="быстрее, чем раньше"
          icon="🛟"
        />
        <StatCard
          title="Документов подписано"
          value={stats?.docs?.signed_count ?? 0}
          trend={stats?.docs?.weekly_growth || 0}
          trendLabel="подписей"
          icon="✍️"
        />
      </div>

      <section className="panel">
        <h2>Проекты и спринты</h2>
        <div className="grid two" style={{ marginTop: 16 }}>
          {projects.map((project) => (
            <div key={project.id} className="panel" style={{ background: 'var(--bg-elevated)' }}>
              <div className="badge-dot">{project.name}</div>
              <div style={{ marginTop: 8, color: 'var(--text-muted)', fontSize: '0.9rem' }}>{project.description}</div>
              <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
                <span className="tag success">{project.methodology}</span>
                <span className="tag warning">Key: {project.key}</span>
              </div>
            </div>
          ))}
          {projects.length === 0 && <div style={{ color: 'var(--text-muted)' }}>У вас пока нет проектов.</div>}
        </div>
      </section>

      <section className="panel">
        <h2>Фокусные задачи</h2>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>ID</th>
              <th>Название</th>
              <th>Статус</th>
              <th>Исполнитель</th>
              <th>Срок</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((task) => (
              <tr key={task.id}>
                <td>{task.id}</td>
                <td>{task.title}</td>
                <td>
                  <span className={`tag ${task.status === 'done' ? 'success' : 'warning'}`}>{task.status}</span>
                </td>
                <td>{task.assignee?.email || '—'}</td>
                <td>{task.due_date || '—'}</td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr>
                <td colSpan={5} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                  Назначенные задачи не найдены
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </section>
    </div>
  )
}
