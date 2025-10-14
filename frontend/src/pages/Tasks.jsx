import React, { useEffect, useState } from 'react'
import { getTasks, createTask, setTaskStatus } from '../api'

export default function Tasks() {
  const [items, setItems] = useState([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')

  async function load() {
    const data = await getTasks()
    setItems(data)
  }

  useEffect(() => { load() }, [])

  async function addTask(e) {
    e.preventDefault()
    await createTask(title, description)
    setTitle(''); setDescription('')
    load()
  }

  async function move(id, status) {
    await setTaskStatus(id, status)
    load()
  }

  return (
    <div style={{padding:20, fontFamily:'Inter, system-ui'}}>
      <h2>Задачи</h2>
      <form onSubmit={addTask} style={{display:'flex', gap:8, marginBottom:12}}>
        <input value={title} onChange={e=>setTitle(e.target.value)} placeholder="Заголовок" />
        <input value={description} onChange={e=>setDescription(e.target.value)} placeholder="Описание" />
        <button>Добавить</button>
      </form>

      <div style={{display:'grid', gridTemplateColumns:'1fr 1fr 1fr', gap:12}}>
        {['ToDo','In Progress','Done'].map(col => (
          <div key={col} style={{border:'1px solid #ddd', borderRadius:8, padding:8}}>
            <h3>{col}</h3>
            {items.filter(x=>x.status===col).map(t => (
              <div key={t.id} style={{border:'1px solid #ccc', padding:8, borderRadius:6, marginBottom:8}}>
                <b>{t.title}</b>
                <div style={{fontSize:12, opacity:.8}}>{t.description}</div>
                <div style={{display:'flex', gap:6, marginTop:6}}>
                  {col !== 'ToDo' && <button onClick={()=>move(t.id,'ToDo')}>ToDo</button>}
                  {col !== 'In Progress' && <button onClick={()=>move(t.id,'In Progress')}>In Progress</button>}
                  {col !== 'Done' && <button onClick={()=>move(t.id,'Done')}>Done</button>}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  )
}
