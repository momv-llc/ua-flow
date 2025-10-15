import React, { useMemo } from 'react'
import { marked } from 'marked'

marked.setOptions({
  breaks: true,
  gfm: true,
})

export default function DocViewer({ content = '' }) {
  const html = useMemo(() => marked.parse(content || 'Документ пока пуст'), [content])

  return (
    <div className="panel markdown" dangerouslySetInnerHTML={{ __html: html }} />
  )
}
