import React, { useEffect, useState } from 'react'
import { useTranslation } from 'react-i18next'
import { listAnalyticsSummary, listProjects, listTasks } from '../../api'
import StatCard from '../../components/common/StatCard'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'
import ModuleShowcase from '../../components/dashboard/ModuleShowcase'
import Card from '../../components/ui/Card'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [stats, setStats] = useState(null)
  const [projects, setProjects] = useState([])
  const [tasks, setTasks] = useState([])
  const { t } = useTranslation()

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
      <ModuleShowcase />

      <div className="grid three">
        <StatCard
          title={t('dashboard.stats.activeTasks')}
          value={stats?.core?.active_tasks ?? tasks.length}
          trend={stats?.core?.task_growth || 0}
          trendLabel={t('dashboard.stats.activeTrend')}
          icon="🗂️"
        />
        <StatCard
          title={t('dashboard.stats.sla')}
          value={stats?.support?.avg_sla_hours ?? '—'}
          trend={-1 * (stats?.support?.sla_delta || 0)}
          trendLabel={t('dashboard.stats.slaTrend')}
          icon="🛟"
        />
        <StatCard
          title={t('dashboard.stats.docsSigned')}
          value={stats?.docs?.signed_count ?? 0}
          trend={stats?.docs?.weekly_growth || 0}
          trendLabel={t('dashboard.stats.docsTrend')}
          icon="✍️"
        />
      </div>

      <Card title={t('dashboard.projects.title')}>
        {projects.length === 0 ? (
          <p style={{ color: 'var(--color-text-muted)', margin: 0 }}>{t('dashboard.projects.empty')}</p>
        ) : (
          <div className="grid two">
            {projects.map((project) => (
              <div key={project.id} className="panel" style={{ background: 'var(--color-elevated)' }}>
                <div className="badge-dot">{project.name}</div>
                <div style={{ marginTop: 8, color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                  {project.description}
                </div>
                <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <span className="tag success">{t('dashboard.projects.methodology')}: {project.methodology}</span>
                  <span className="tag warning">{t('dashboard.projects.key')}: {project.key}</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </Card>

      <Card title={t('dashboard.focus.title')}>
        <table className="table" style={{ marginTop: 12 }}>
          <thead>
            <tr>
              <th>{t('dashboard.focus.columns.id')}</th>
              <th>{t('dashboard.focus.columns.title')}</th>
              <th>{t('dashboard.focus.columns.status')}</th>
              <th>{t('dashboard.focus.columns.assignee')}</th>
              <th>{t('dashboard.focus.columns.due')}</th>
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
                <td colSpan={5} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)' }}>
                  {t('dashboard.focus.empty')}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </Card>
    </div>
  )
}
