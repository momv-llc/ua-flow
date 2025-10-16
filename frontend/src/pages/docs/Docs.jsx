import React, { useEffect, useState } from 'react'
import { createDoc, getDoc, listDocVersions, listDocs, signDoc, updateDoc } from '../../api'
import DocViewer from '../../components/common/DocViewer'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

const emptyDoc = {
  title: '',
  content_md: '# Новый документ\n\nОпишите требования и добавьте файлы через интеграции с Медок / Дія.',
}

export default function DocsPage() {
  const [docs, setDocs] = useState([])
  const [selected, setSelected] = useState(null)
  const [versions, setVersions] = useState([])
  const [form, setForm] = useState(emptyDoc)
  const [creating, setCreating] = useState(false)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  async function loadDocs() {
    setLoading(true)
    setError(null)
    try {
      const list = await listDocs()
      setDocs(list)
      if (list.length > 0) {
        selectDoc(list[0].id)
      } else {
        setSelected(null)
        setVersions([])
      }
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  async function selectDoc(docId) {
    try {
      const [doc, history] = await Promise.all([getDoc(docId), listDocVersions(docId)])
      setSelected(doc)
      setVersions(history)
      setForm({ title: doc.title, content_md: doc.content_md })
    } catch (err) {
      setError(err)
    }
  }

  async function handleCreate(event) {
    event.preventDefault()
    try {
      setCreating(true)
      await createDoc(form)
      await loadDocs()
      setForm(emptyDoc)
    } catch (err) {
      setError(err)
    } finally {
      setCreating(false)
    }
  }

  async function handleUpdate(event) {
    event.preventDefault()
    if (!selected) return
    try {
      await updateDoc(selected.id, form)
      await selectDoc(selected.id)
    } catch (err) {
      setError(err)
    }
  }

  async function handleSign() {
    if (!selected) return
    await signDoc(selected.id)
    await selectDoc(selected.id)
  }

  useEffect(() => {
    loadDocs()
  }, [])

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={loadDocs} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <h2>Документация и вики</h2>
        <div className="grid two" style={{ marginTop: 16 }}>
          <div className="panel" style={{ background: 'var(--bg-elevated)', maxHeight: 460, overflowY: 'auto' }}>
            <button className="primary" onClick={() => setSelected(null)}>
              + Новый документ
            </button>
            <ul className="timeline" style={{ marginTop: 20 }}>
              {docs.map((doc) => (
                <li key={doc.id} style={{ cursor: 'pointer' }} onClick={() => selectDoc(doc.id)}>
                  <strong>{doc.title}</strong>
                  <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Обновлено: {doc.updated_at}</div>
                </li>
              ))}
            </ul>
            {docs.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Документы не найдены</div>}
          </div>
          <div>
            {selected ? (
              <DocViewer content={selected.content_md} />
            ) : (
              <div className="panel" style={{ color: 'var(--text-muted)' }}>Выберите документ или создайте новый.</div>
            )}
          </div>
        </div>
      </section>

      <section className="panel">
        <h2>{selected ? 'Редактирование документа' : 'Создание документа'}</h2>
        <form className="grid" style={{ marginTop: 16 }} onSubmit={selected ? handleUpdate : handleCreate}>
          <label style={{ gridColumn: '1 / -1' }}>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Название</div>
            <input value={form.title} onChange={(event) => setForm((prev) => ({ ...prev, title: event.target.value }))} required />
          </label>
          <label style={{ gridColumn: '1 / -1' }}>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Содержание (Markdown)</div>
            <textarea
              value={form.content_md}
              rows={10}
              onChange={(event) => setForm((prev) => ({ ...prev, content_md: event.target.value }))}
            />
          </label>
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
            {selected && (
              <button type="button" className="secondary" onClick={handleSign}>
                Подписать КЕП
              </button>
            )}
            <button className="primary" type="submit" disabled={creating}>
              {creating ? 'Сохраняем...' : selected ? 'Сохранить изменения' : 'Создать'}
            </button>
          </div>
        </form>
      </section>

      {selected && (
        <section className="panel">
          <h2>История версий</h2>
          <table className="table" style={{ marginTop: 12 }}>
            <thead>
              <tr>
                <th>ID</th>
                <th>Автор</th>
                <th>Дата</th>
                <th>Подписано</th>
              </tr>
            </thead>
            <tbody>
              {versions.map((version) => (
                <tr key={version.id}>
                  <td>{version.id}</td>
                  <td>{version.author?.email}</td>
                  <td>{version.created_at}</td>
                  <td>{version.signed ? '✅' : '—'}</td>
                </tr>
              ))}
              {versions.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--text-muted)' }}>
                    История изменений появится после первого сохранения
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </section>
      )}
    </div>
  )
}
