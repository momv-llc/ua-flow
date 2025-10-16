import React from 'react'

export default function DataTable({ columns, data, emptyText = 'Нет данных' }) {
  return (
    <div className="panel">
      <table className="table">
        <thead>
          <tr>
            {columns.map((column) => (
              <th key={column.key}>{column.title}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {data.length === 0 && (
            <tr>
              <td colSpan={columns.length} style={{ textAlign: 'center', padding: '40px 0', color: 'var(--text-muted)' }}>
                {emptyText}
              </td>
            </tr>
          )}
          {data.map((row) => (
            <tr key={row.id || row.key}>
              {columns.map((column) => (
                <td key={column.key}>{column.render ? column.render(row[column.key], row) : row[column.key]}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
