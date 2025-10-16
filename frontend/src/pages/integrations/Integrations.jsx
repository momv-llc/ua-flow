import React, { useEffect, useMemo, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  getIntegrationTask,
  listIntegrationLogs,
  listIntegrationSandboxes,
  listIntegrations,
  runIntegrationSandbox,
  syncIntegration,
  testIntegration,
  triggerWebhookPreview,
} from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'
import Button from '../../components/ui/Button'
import Card from '../../components/ui/Card'

function formatDate(value) {
  if (!value) return '—'
  try {
    return new Date(value).toLocaleString('uk-UA')
  } catch (error) {
    return value
  }
}

export default function IntegrationsPage() {
  const { t } = useTranslation()
  const [integrations, setIntegrations] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [syncPayload, setSyncPayload] = useState('{\n  "operation": "catalogs"\n}')
  const [syncMode, setSyncMode] = useState('async')
  const [actionResult, setActionResult] = useState(null)
  const [logs, setLogs] = useState([])
  const [selectedIntegration, setSelectedIntegration] = useState(null)
  const [activeTaskId, setActiveTaskId] = useState(null)
  const [taskStatus, setTaskStatus] = useState(null)
  const pollRef = useRef(null)

  const [sandboxes, setSandboxes] = useState([])
  const [selectedSandbox, setSelectedSandbox] = useState(null)
  const [sandboxPayload, setSandboxPayload] = useState('{}')
  const [sandboxResult, setSandboxResult] = useState(null)
  const [webhookPayload, setWebhookPayload] = useState('')
  const [webhookResponse, setWebhookResponse] = useState('')

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
      if (!selectedIntegration && data.length) {
        setSelectedIntegration(data[0].id)
        fetchLogs(data[0].id)
      }
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

  async function fetchSandboxes() {
    try {
      const data = await listIntegrationSandboxes()
      setSandboxes(data)
      if (data.length) {
        setSelectedSandbox(data[0].slug)
        setSandboxPayload(JSON.stringify(data[0].request_example, null, 2))
      }
    } catch (err) {
      if (String(err.message || '').toLowerCase().includes('forbidden')) {
        return
      }
      setError(err)
    }
  }

  async function handleAction(id, action) {
    setError(null)
    setActionResult(null)
    if (action === 'test') {
      try {
        const result = await testIntegration(id)
        setActionResult({ type: 'test', response: result.details })
        await fetchIntegrations()
        await fetchLogs(id)
      } catch (err) {
        setError(err)
      }
      return
    }

    let parsed = {}
    if (syncPayload.trim()) {
      try {
        parsed = JSON.parse(syncPayload)
      } catch (err) {
        setError(new Error('Payload must be valid JSON'))
        return
      }
    }

    try {
      const result = await syncIntegration(id, parsed, syncMode)
      if (result.status === 'queued') {
        setActiveTaskId(result.details.task_id)
        setTaskStatus({ state: 'PENDING', task_id: result.details.task_id })
      } else {
        setActionResult({ type: 'sync', response: result.details })
        await fetchIntegrations()
        await fetchLogs(id)
      }
    } catch (err) {
      setError(err)
    }
  }

  useEffect(() => {
    if (!activeTaskId) return

    async function poll() {
      try {
        const status = await getIntegrationTask(activeTaskId)
        setTaskStatus(status)
        if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(status.state.toUpperCase())) {
          setActiveTaskId(null)
          clearInterval(pollRef.current)
          if (selectedIntegration) {
            await fetchIntegrations()
            await fetchLogs(selectedIntegration)
          }
          if (status.details) {
            setActionResult({ type: 'sync', response: status.details })
          }
        }
      } catch (err) {
        setTaskStatus({ state: 'ERROR', error: err.message, task_id: activeTaskId })
        setActiveTaskId(null)
        clearInterval(pollRef.current)
      }
    }

    poll()
    pollRef.current = setInterval(poll, 2500)
    return () => clearInterval(pollRef.current)
  }, [activeTaskId, selectedIntegration])

  useEffect(() => {
    fetchIntegrations()
    fetchSandboxes()
    return () => {
      if (pollRef.current) clearInterval(pollRef.current)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

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

  async function handleSandboxRun(event) {
    event.preventDefault()
    if (!selectedSandbox) return
    try {
      const parsed = sandboxPayload ? JSON.parse(sandboxPayload) : {}
      const response = await runIntegrationSandbox(selectedSandbox, parsed)
      setSandboxResult(JSON.stringify(response, null, 2))
    } catch (err) {
      setSandboxResult(err.message)
    }
  }

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={fetchIntegrations} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <Card
        title={t('integrations.title')}
        subtitle={t('integrations.count', { count: integrations.length })}
      >
        <div className="grid two">
          {integrations.map((integration) => (
            <div key={integration.id} className="panel" style={{ background: 'var(--color-elevated)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div className="badge-dot">{integration.name}</div>
                  <div style={{ marginTop: 4, fontSize: '0.8rem', color: 'var(--color-text-muted)' }}>
                    {integration.integration_type}
                  </div>
                </div>
                <div
                  style={{
                    background: integration.is_active ? 'var(--color-accent)' : 'var(--color-border)',
                    color: integration.is_active ? '#fff' : 'var(--color-text-muted)',
                    padding: '4px 10px',
                    borderRadius: 999,
                    fontSize: '0.75rem',
                  }}
                >
                  {integration.status}
                </div>
              </div>
              <p style={{ marginTop: 12, color: 'var(--color-text-muted)', fontSize: '0.9rem' }}>
                {integration.description || t('integrations.noIntegrations')}
              </p>
              <div style={{ marginTop: 16, display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Button variant="secondary" onClick={() => handleAction(integration.id, 'test')}>
                  {t('integrations.test')}
                </Button>
                <Button onClick={() => handleAction(integration.id, 'sync')}>
                  {t('integrations.sync')}
                </Button>
                <Button variant="ghost" onClick={() => fetchLogs(integration.id)}>
                  {t('integrations.logs')}
                </Button>
              </div>
            </div>
          ))}
          {integrations.length === 0 && (
            <div style={{ color: 'var(--color-text-muted)' }}>{t('integrations.noIntegrations')}</div>
          )}
        </div>
      </Card>

      <Card
        title={t('integrations.payloadLabel')}
        subtitle={t('integrations.queueStatus')}
        headerAction={
          <div className="ui-segmented" role="group" aria-label="Sync mode">
            <button
              type="button"
              className={syncMode === 'async' ? 'active' : ''}
              onClick={() => setSyncMode('async')}
            >
              Async
            </button>
            <button
              type="button"
              className={syncMode === 'sync' ? 'active' : ''}
              onClick={() => setSyncMode('sync')}
            >
              Sync
            </button>
          </div>
        }
      >
        <textarea
          value={syncPayload}
          onChange={(event) => setSyncPayload(event.target.value)}
          rows={8}
        />
        {taskStatus && (
          <div style={{ marginTop: 16, fontSize: '0.85rem', color: 'var(--color-text-muted)' }}>
            <strong>{t('integrations.queueStatus')}:</strong>{' '}
            {taskStatus.state} {taskStatus.error ? `— ${taskStatus.error}` : ''}
            {taskStatus.state === 'SUCCESS' && !activeTaskId ? ` — ${t('integrations.eager')}` : ''}
          </div>
        )}
        {actionResult && (
          <div className="panel" style={{ marginTop: 16, background: 'var(--color-elevated)' }}>
            <div style={{ fontWeight: 600 }}>{t('integrations.resultTitle')}</div>
            <pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', fontSize: '0.8rem' }}>
              {JSON.stringify(actionResult.response, null, 2)}
            </pre>
          </div>
        )}
      </Card>

      <Card
        title={t('integrations.logs')}
        subtitle={selectedDetails ? selectedDetails.name : '—'}
      >
        {logs.length === 0 ? (
          <div style={{ color: 'var(--color-text-muted)' }}>{t('integrations.noLogs')}</div>
        ) : (
          <div className="table" style={{ marginTop: 12 }}>
            <div className="thead">
              <div>#{t('dashboard.focus.columns.id')}</div>
              <div>{t('dashboard.focus.columns.status')}</div>
              <div>Payload</div>
              <div>{t('integrations.lastSync')}</div>
            </div>
            <div className="tbody">
              {logs.map((log) => (
                <div key={log.id}>
                  <div style={{ fontWeight: 600 }}>{log.id}</div>
                  <div style={{ color: log.status === 'success' ? 'var(--color-success)' : 'var(--color-danger)' }}>
                    {log.status}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{log.payload}</div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--color-text-muted)' }}>{formatDate(log.created_at)}</div>
                </div>
              ))}
            </div>
          </div>
        )}
      </Card>

      <Card
        title={t('integrations.sandboxTitle')}
        subtitle={t('integrations.sandboxNote')}
      >
        <form className="grid" style={{ gap: 16 }} onSubmit={handleSandboxRun}>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Sandbox</div>
            <select
              value={selectedSandbox || ''}
              onChange={(event) => {
                const slug = event.target.value
                setSelectedSandbox(slug)
                const next = sandboxes.find((item) => item.slug === slug)
                if (next) {
                  setSandboxPayload(JSON.stringify(next.request_example, null, 2))
                }
              }}
            >
              {sandboxes.map((sandbox) => (
                <option key={sandbox.slug} value={sandbox.slug}>
                  {sandbox.title}
                </option>
              ))}
            </select>
          </label>
          <label>
            <div style={{ fontSize: '0.8rem', marginBottom: 6 }}>Payload</div>
            <textarea
              rows={6}
              value={sandboxPayload}
              onChange={(event) => setSandboxPayload(event.target.value)}
            />
          </label>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Button type="submit">{t('integrations.sandboxRun')}</Button>
          </div>
        </form>
        {sandboxResult && (
          <pre style={{ marginTop: 16, background: 'var(--color-elevated)', padding: 16, borderRadius: 12 }}>
            {sandboxResult}
          </pre>
        )}
      </Card>

      <Card title="Webhook Preview" subtitle="HMAC signing helper">
        <form className="grid" style={{ gap: 12 }} onSubmit={handleWebhookPreview}>
          <textarea
            rows={6}
            value={webhookPayload}
            onChange={(event) => setWebhookPayload(event.target.value)}
            placeholder={'{\n  "event": "handshake"\n}'}
          />
          <Button type="submit" variant="secondary">
            Preview signature
          </Button>
        </form>
        {webhookResponse && (
          <pre style={{ marginTop: 16, background: 'var(--color-elevated)', padding: 16, borderRadius: 12 }}>
            {webhookResponse}
          </pre>
        )}
      </Card>
    </div>
  )
}
