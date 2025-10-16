import React from 'react'

const columns = [
  { key: 'backlog', label: 'Backlog' },
  { key: 'todo', label: 'To Do' },
  { key: 'in_progress', label: 'В работе' },
  { key: 'done', label: 'Готово' },
]

export default function KanbanBoard({ lanes = {}, onSelect }) {
  return (
    <div className="grid four" style={{ gap: 16, alignItems: 'flex-start' }}>
      {columns.map((column) => {
        const tasks = lanes[column.key] || []
        return (
          <div key={column.key} className="panel" style={{ minHeight: 280 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <strong>{column.label}</strong>
              <span className="chip" style={{ background: 'rgba(255,255,255,0.1)', color: 'var(--accent-strong)' }}>
                {tasks.length}
              </span>
            </div>
            <div style={{ marginTop: 16, display: 'grid', gap: 12 }}>
              {tasks.map((task) => (
                <button
                  key={task.id}
                  onClick={() => onSelect?.(task)}
                  className="panel"
                  style={{
                    padding: 16,
                    background: 'var(--bg-elevated)',
                    border: '1px solid rgba(15, 23, 42, 0.08)',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>#{task.key || task.id}</div>
                  <div style={{ fontWeight: 600 }}>{task.title}</div>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)', marginTop: 8 }}>{task.assignee?.email || 'Не назначено'}</div>
                </button>
              ))}
              {tasks.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Нет задач</div>}
            </div>
          </div>
        )
      })}
    </div>
  )
}
