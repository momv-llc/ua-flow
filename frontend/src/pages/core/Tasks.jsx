import React, { useEffect, useMemo, useState } from 'react'
import {
  createTask,
  getBurndown,
  getKanban,
  listProjects,
  listSprints,
  listTasks,
} from '../../api'
import KanbanBoard from '../../components/common/KanbanBoard'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

const DEFAULT_TASK = {
  title: '',
  description: '',
  project_id: '',
  sprint_id: '',
  status: 'todo',
  priority: 'medium',
  type: 'task',
}

export default function TasksPage() {
  const [projects, setProjects] = useState([])
  const [sprints, setSprints] = useState([])
  const [filters, setFilters] = useState({ project_id: '', sprint_id: '' })
  const [tasks, setTasks] = useState([])
  const [kanban, setKanban] = useState({})
  const [burndown, setBurndown] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [modalOpen, setModalOpen] = useState(false)
  const [form, setForm] = useState(DEFAULT_TASK)
  const [selectedTask, setSelectedTask] = useState(null)

  const projectId = filters.project_id || (projects[0]?.id ?? '')

  useEffect(() => {
    async function bootstrap() {
      try {
        setLoading(true)
        setError(null)
        const projectList = await listProjects()
        setProjects(projectList)
        const projectToLoad = filters.project_id || projectList[0]?.id
        if (projectToLoad) {
          const [taskList, board, sprintList, burndownData] = await Promise.all([
            listTasks({ project_id: projectToLoad }),
            getKanban(projectToLoad),
            listSprints(projectToLoad),
            getBurndown({ project_id: projectToLoad }),
          ])
          setTasks(taskList)
          setKanban(board)
          setSprints(sprintList)
          setBurndown(burndownData)
        } else {
          setTasks([])
          setKanban({})
          setSprints([])
        }
      } catch (err) {
        setError(err)
      } finally {
        setLoading(false)
      }
    }
    bootstrap()
  }, [])

  useEffect(() => {
    async function updateBoard() {
      if (!projectId) return
      try {
        const [taskList, board, sprintList, burndownData] = await Promise.all([
          listTasks({ project_id: projectId, sprint_id: filters.sprint_id }),
          getKanban(projectId),
          listSprints(projectId),
          getBurndown({ project_id: projectId, sprint_id: filters.sprint_id }),
        ])
        setTasks(taskList)
        setKanban(board)
        setSprints(sprintList)
        setBurndown(burndownData)
      } catch (err) {
        setError(err)
      }
    }
    updateBoard()
  }, [projectId, filters.sprint_id])

  async function handleCreateTask(event) {
    event.preventDefault()
    try {
      await createTask({ ...form, project_id: Number(form.project_id) || null, sprint_id: Number(form.sprint_id) || null })
      setModalOpen(false)
      setForm(DEFAULT_TASK)
      const [taskList, board] = await Promise.all([
        listTasks({ project_id: projectId, sprint_id: filters.sprint_id }),
        getKanban(projectId),
      ])
      setTasks(taskList)
      setKanban(board)
    } catch (err) {
      setError(err)
    }
  }

  const sprintOptions = useMemo(
    () => sprints.map((sprint) => ({ value: sprint.id, label: sprint.name })),
    [sprints],
  )

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={() => window.location.reload()} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Доска задач</h2>
          <button className="primary" onClick={() => setModalOpen(true)}>
            + Новая задача
          </button>
        </div>
        <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
          <select
            value={projectId}
            onChange={(event) => setFilters((prev) => ({ ...prev, project_id: Number(event.target.value) }))}
          >
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.name}
              </option>
            ))}
          </select>
          <select
            value={filters.sprint_id}
            onChange={(event) => setFilters((prev) => ({ ...prev, sprint_id: event.target.value }))}
          >
            <option value="">Все спринты</option>
            {sprintOptions.map((sprint) => (
              <option key={sprint.value} value={sprint.value}>
                {sprint.label}
              </option>
            ))}
          </select>
        </div>
        <div style={{ marginTop: 24 }}>
          <KanbanBoard lanes={kanban} onSelect={setSelectedTask} />
        </div>
      </section>

      <section className="panel">
        <h2>Burndown</h2>
        {burndown ? (
          <div className="grid two" style={{ marginTop: 16 }}>
            <div className="panel" style={{ background: 'var(--bg-elevated)' }}>
              <div className="chip">Осталось задач</div>
              <div style={{ fontSize: '2.4rem', fontWeight: 700 }}>{burndown.remaining}</div>
              <p style={{ color: 'var(--text-muted)' }}>Из {burndown.total} запланированных задач</p>
            </div>
            <div className="panel" style={{ background: 'var(--bg-elevated)' }}>
              <div className="chip">Дедлайн спринта</div>
              <div style={{ fontSize: '1.4rem', fontWeight: 600 }}>{burndown.sprint_end || '—'}</div>
              <p style={{ color: 'var(--text-muted)' }}>Идеальная линия: {burndown.ideal.map((value) => Math.round(value)).join(' → ')}</p>
            </div>
          </div>
        ) : (
          <div style={{ color: 'var(--text-muted)', marginTop: 16 }}>Нет данных для отчёта</div>
        )}
      </section>

      {modalOpen && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.55)',
            display: 'grid',
            placeItems: 'center',
            zIndex: 20,
          }}
        >
          <div className="panel" style={{ width: 'min(520px, 95vw)', maxHeight: '90vh', overflowY: 'auto' }}>
            <h2>Новая задача</h2>
            <form className="grid" style={{ marginTop: 16 }} onSubmit={handleCreateTask}>
              <label style={{ gridColumn: '1 / -1' }}>
                <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Заголовок</div>
                <input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} required />
              </label>
              <label style={{ gridColumn: '1 / -1' }}>
                <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Описание</div>
                <textarea value={form.description} onChange={(event) => setForm((prev) => ({ ...prev, description: event.target.value }))} />
              </label>
              <label>
                <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Проект</div>
                <select value={form.project_id} onChange={(event) => setForm((prev) => ({ ...prev, project_id: event.target.value }))} required>
                  <option value="">Выберите проект</option>
                  {projects.map((project) => (
                    <option key={project.id} value={project.id}>
                      {project.name}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Спринт</div>
                <select value={form.sprint_id} onChange={(event) => setForm((prev) => ({ ...prev, sprint_id: event.target.value }))}>
                  <option value="">Backlog</option>
                  {sprintOptions.map((sprint) => (
                    <option key={sprint.value} value={sprint.value}>
                      {sprint.label}
                    </option>
                  ))}
                </select>
              </label>
              <label>
                <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Статус</div>
                <select value={form.status} onChange={(event) => setForm((prev) => ({ ...prev, status: event.target.value }))}>
                  <option value="backlog">Backlog</option>
                  <option value="todo">To Do</option>
                  <option value="in_progress">В работе</option>
                  <option value="done">Готово</option>
                </select>
              </label>
              <label>
                <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Приоритет</div>
                <select value={form.priority} onChange={(event) => setForm((prev) => ({ ...prev, priority: event.target.value }))}>
                  <option value="low">Низкий</option>
                  <option value="medium">Средний</option>
                  <option value="high">Высокий</option>
                  <option value="critical">Критический</option>
                </select>
              </label>
              <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                <button type="button" className="secondary" onClick={() => setModalOpen(false)}>
                  Отмена
                </button>
                <button className="primary" type="submit">
                  Создать
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {selectedTask && (
        <div
          style={{
            position: 'fixed',
            inset: 0,
            background: 'rgba(15, 23, 42, 0.45)',
            display: 'grid',
            placeItems: 'center',
            zIndex: 15,
          }}
          onClick={() => setSelectedTask(null)}
        >
          <div className="panel" style={{ width: 'min(460px, 90vw)' }} onClick={(event) => event.stopPropagation()}>
            <h2>#{selectedTask.id} — {selectedTask.title}</h2>
            <p style={{ color: 'var(--text-muted)' }}>{selectedTask.description || 'Описание не заполнено'}</p>
            <div style={{ display: 'flex', gap: 12, marginTop: 16 }}>
              <span className="tag success">{selectedTask.status}</span>
              <span className="tag warning">Приоритет: {selectedTask.priority}</span>
            </div>
            <div style={{ marginTop: 12, fontSize: '0.85rem' }}>
              Исполнитель: <strong>{selectedTask.assignee?.email || 'не назначен'}</strong>
            </div>
            <button className="secondary" style={{ marginTop: 20 }} onClick={() => setSelectedTask(null)}>
              Закрыть
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
