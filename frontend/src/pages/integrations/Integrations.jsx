import React, { useEffect, useMemo, useState } from 'react'
import {
  listIntegrations,
  listIntegrationLogs,
  syncIntegration,
  testIntegration,
  triggerWebhookPreview,
} from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'

function formatDate(value) {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString('uk-UA')
  } catch (error) {
    return value
  }
}

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncPayload, setSyncPayload] = useState('{}')
  const [actionResult, setActionResult] = useState(null)
  const [webhookPayload, setWebhookPayload] = useState('')
  const [webhookResponse, setWebhookResponse] = useState('')
  const [logs, setLogs] = useState([])
  const [selectedIntegration, setSelectedIntegration] = useState(null)
  const [working, setWorking] = useState(false)

  const selectedDetails = useMemo(
    () => integrations.find((item) => item.id === selectedIntegration) || null,
    [integrations, selectedIntegration],
  )

  async function fetchIntegrations() {
    setLoading(true)
    setError(null)
    try {
      const data = await listIntegrations()
      setIntegrations(data)
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  async function fetchLogs(id) {
    try {
      const data = await listIntegrationLogs(id)
      setLogs(data)
      setSelectedIntegration(id)
    } catch (err) {
      setError(err)
    }
  }

  async function handleAction(id, action) {
    setWorking(true)
    setError(null)
    try {
      if (action === 'test') {
        const result = await testIntegration(id)
        setActionResult({ type: 'test', response: result.details })
      } else {
        let parsed = {}
        if (syncPayload.trim()) {
          try {
            parsed = JSON.parse(syncPayload)
          } catch (err) {
            throw new Error('Sync payload должен быть корректным JSON')
          }
        }
        const result = await syncIntegration(id, parsed)
        setActionResult({ type: 'sync', response: result.details })
      }
      await fetchIntegrations()
      await fetchLogs(id)
    } catch (err) {
      setError(err)
    } finally {
      setWorking(false)
    }
  }

  async function handleWebhookPreview(event) {
    event.preventDefault()
    try {
      const parsed = webhookPayload ? JSON.parse(webhookPayload) : {}
      const response = await triggerWebhookPreview(parsed)
      setWebhookResponse(JSON.stringify(response, null, 2))
    } catch (err) {
      setWebhookResponse(err.message)
    }
  }

  useEffect(() => {
    fetchIntegrations()
  }, [])

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={fetchIntegrations} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <section className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Активные интеграции</h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {integrations.length} подключено
          </span>
        </div>
        <div className="grid two" style={{ marginTop: 16, gap: 16 }}>
          {integrations.map((integration) => (
            <div key={integration.id} className="panel" style={{ background: 'var(--bg-elevated)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div className="badge-dot">{integration.name}</div>
                  <div style={{ marginTop: 4, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {integration.integration_type}
                  </div>
                </div>
                <div
                  style={{
                    background: integration.is_active ? 'var(--primary)' : 'var(--border)',
                    color: integration.is_active ? '#fff' : 'var(--text-muted)',
                    padding: '4px 10px',
                    borderRadius: 999,
                    fontSize: '0.75rem',
                  }}
                >
                  {integration.status}
                </div>
              </div>
              <p style={{ marginTop: 12, color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: 1.4 }}>
                {integration.description || 'Описание отсутствует'}
              </p>
              <dl style={{ marginTop: 12, fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <dt>Последний обмен</dt>
                  <dd>{formatDate(integration.last_synced_at)}</dd>
                </div>
              </dl>
              <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <button className="secondary" disabled={working} onClick={() => handleAction(integration.id, 'test')}>
                  Проверить соединение
                </button>
                <button className="primary" disabled={working} onClick={() => handleAction(integration.id, 'sync')}>
                  Форсировать синк
                </button>
                <button className="ghost" onClick={() => fetchLogs(integration.id)}>
                  Логи
                </button>
              </div>
            </div>
          ))}
          {integrations.length === 0 && <div style={{ color: 'var(--text-muted)' }}>Интеграции не настроены</div>}
        </div>
      </section>

      <section className="panel">
        <h2>Настройки синхронизации</h2>
        <div className="grid" style={{ gap: 16 }}>
          <label style={{ display: 'block' }}>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Payload (JSON)</div>
            <textarea
              value={syncPayload}
              onChange={(event) => setSyncPayload(event.target.value)}
              placeholder='{ "operation": "catalogs" }'
              rows={6}
            />
          </label>
          {actionResult && (
            <div className="panel" style={{ background: 'var(--bg-elevated)' }}>
              <div style={{ fontWeight: 600 }}>Результат {actionResult.type === 'test' ? 'теста' : 'синхронизации'}</div>
              <pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', fontSize: '0.75rem' }}>
                {JSON.stringify(actionResult.response, null, 2)}
              </pre>
            </div>
          )}
        </div>
      </section>

      <section className="panel">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <h2>Логи интеграции</h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            {selectedDetails ? selectedDetails.name : 'Не выбрана'}
          </span>
        </div>
        {logs.length === 0 ? (
          <div style={{ marginTop: 16, color: 'var(--text-muted)' }}>Логи появятся после синхронизации</div>
        ) : (
          <div className="table" style={{ marginTop: 16 }}>
            <div className="thead">
              <div>Дата</div>
              <div>Статус</div>
              <div>Код</div>
              <div>Payload</div>
            </div>
            {logs.map((log) => (
              <div key={log.id} className="tr">
                <div>{formatDate(log.created_at)}</div>
                <div>{log.status}</div>
                <div>{log.response_code}</div>
                <div>
                  <pre style={{ whiteSpace: 'pre-wrap', fontSize: '0.7rem' }}>{log.payload}</pre>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      <section className="panel">
        <h2>Webhook sandbox</h2>
        <form className="grid" style={{ marginTop: 16 }} onSubmit={handleWebhookPreview}>
          <label style={{ gridColumn: '1 / -1' }}>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Payload (JSON)</div>
            <textarea
              value={webhookPayload}
              onChange={(event) => setWebhookPayload(event.target.value)}
              placeholder='{"event": "task.created", "payload": {"id": 1}}'
              rows={5}
            />
          </label>
          <div style={{ gridColumn: '1 / -1', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="primary" type="submit">
              Смоделировать
            </button>
          </div>
        </form>
        {webhookResponse && (
          <pre
            style={{
              marginTop: 16,
              whiteSpace: 'pre-wrap',
              background: 'var(--bg-elevated)',
              padding: 16,
              borderRadius: 12,
              fontSize: '0.8rem',
            }}
          >
            {webhookResponse}
          </pre>
        )}
      </section>
    </div>
  )
}
