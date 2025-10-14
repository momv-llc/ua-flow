import React, { useEffect, useState } from 'react'
import { marked } from 'marked'
import { getDocs, createDoc } from '../api'

export default function Docs() {
  const [items, setItems] = useState([])
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')

  async function load() {
    const data = await getDocs()
    setItems(data)
  }

  useEffect(() => { load() }, [])

  async function add(e) {
    e.preventDefault()
    await createDoc(title, content)
    setTitle(''); setContent('')
    load()
  }

  return (
    <div style={{padding:20, fontFamily:'Inter, system-ui'}}>
      <h2>Документы / Wiki</h2>
      <form onSubmit={add} style={{display:'grid', gap:8, marginBottom:12}}>
        <input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Заголовок" />
        <textarea value={content} onChange={e=>setContent(e.target.value)} rows={6} placeholder="Markdown..." />
        <button>Сохранить</button>
      </form>

      {items.map(doc => (
        <div key={doc.id} style={{border:'1px solid #ddd', borderRadius:8, padding:12, marginBottom:10}}>
          <h3>{doc.title}</h3>
          <div dangerouslySetInnerHTML={{__html: marked.parse(doc.content_md || '')}} />
        </div>
      ))}
    </div>
  )
}
