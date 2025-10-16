import React, { useEffect, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'
import {
  addPaymentMethod,
  cancelSubscription,
  createCheckout,
  createSubscription,
  deletePaymentMethod,
  listPaymentMethods,
  listPaymentPlans,
  listSubscriptions,
  listTransactions,
  setDefaultPaymentMethod,
} from '../../api'
import Loader from '../../components/common/Loader'
import ErrorState from '../../components/common/ErrorState'
import Card from '../../components/ui/Card'
import Button from '../../components/ui/Button'

const defaultMethod = {
  label: '',
  method_type: 'card',
  gateway: 'liqpay',
  cardNumber: '',
  expires: '',
  bankAccount: '',
  companyCode: '',
}

export default function BillingPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [plans, setPlans] = useState([])
  const [methods, setMethods] = useState([])
  const [subscriptions, setSubscriptions] = useState([])
  const [transactions, setTransactions] = useState([])
  const [form, setForm] = useState(defaultMethod)
  const [selectedPlan, setSelectedPlan] = useState(null)
  const [selectedMethod, setSelectedMethod] = useState(null)
  const [processing, setProcessing] = useState(false)
  const { t } = useTranslation()

  const defaultMethodId = useMemo(() => methods.find((item) => item.is_default)?.id || null, [methods])

  async function loadData() {
    setLoading(true)
    setError(null)
    try {
      const [planData, methodData, subsData, txData] = await Promise.all([
        listPaymentPlans(),
        listPaymentMethods(),
        listSubscriptions(),
        listTransactions(),
      ])
      setPlans(planData)
      setMethods(methodData)
      setSubscriptions(subsData)
      setTransactions(txData)
      if (!selectedPlan && planData.length > 0) {
        setSelectedPlan(planData[0].id)
      }
    } catch (err) {
      setError(err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadData()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  async function handleAddMethod(event) {
    event.preventDefault()
    setProcessing(true)
    try {
      const payload = {
        label: form.label,
        method_type: form.method_type,
        gateway: form.gateway,
        details: {},
      }
      if (form.method_type === 'card') {
        payload.details = {
          card_number: form.cardNumber,
          expires: form.expires,
        }
      } else if (form.method_type === 'bank_account') {
        payload.details = {
          iban: form.bankAccount,
          company_code: form.companyCode,
        }
      } else {
        payload.details = {
          account: form.bankAccount || form.cardNumber,
        }
      }
      await addPaymentMethod(payload)
      setForm(defaultMethod)
      setSelectedMethod(null)
      await loadData()
    } catch (err) {
      setError(err)
    } finally {
      setProcessing(false)
    }
  }

  async function handleSetDefault(id) {
    await setDefaultPaymentMethod(id)
    await loadData()
  }

  async function handleDeleteMethod(id) {
    if (!window.confirm(t('billing.methods.confirmDelete'))) return
    try {
      await deletePaymentMethod(id)
      setSelectedMethod((prev) => (prev === id ? null : prev))
      await loadData()
    } catch (err) {
      setError(err)
    }
  }

  async function handleSubscribe(planId) {
    setProcessing(true)
    try {
      await createSubscription({ plan_id: planId, payment_method_id: selectedMethod || defaultMethodId, auto_renew: true })
      await loadData()
    } catch (err) {
      setError(err)
    } finally {
      setProcessing(false)
    }
  }

  async function handleCheckout(planId) {
    setProcessing(true)
    try {
      await createCheckout({ plan_id: planId, payment_method_id: selectedMethod || defaultMethodId })
      await loadData()
    } catch (err) {
      setError(err)
    } finally {
      setProcessing(false)
    }
  }

  async function handleCancel(subscriptionId) {
    if (!window.confirm(t('billing.subscriptions.confirmCancel'))) return
    await cancelSubscription(subscriptionId)
    await loadData()
  }

  if (loading) return <Loader />
  if (error) return <ErrorState error={error} onRetry={loadData} />

  return (
    <div className="grid" style={{ gap: 24 }}>
      <Card
        title={t('billing.title')}
        subtitle={t('billing.subtitle')}
        headerAction={
          <div className="ui-select">
            <label htmlFor="method-select">{t('billing.paymentSelect')}</label>
            <select
              id="method-select"
              value={selectedMethod || defaultMethodId || ''}
              onChange={(event) => setSelectedMethod(event.target.value ? Number(event.target.value) : null)}
            >
              <option value="">{t('billing.defaultOption')}</option>
              {methods.map((method) => (
                <option key={method.id} value={method.id}>
                  {method.label} ({method.gateway})
                </option>
              ))}
            </select>
          </div>
        }
      >
        <div className="billing-grid">
          {plans.map((plan) => (
            <div key={plan.id} className={`plan-card${selectedPlan === plan.id ? ' active' : ''}`}>
              <div className="plan-card__header">
                <h3>{plan.name}</h3>
                <p>{plan.description}</p>
              </div>
              <div className="plan-card__price">
                <span>{plan.price} {plan.currency}</span>
                <small>
                  {t('billing.plans.perInterval', {
                    value:
                      plan.interval === 'monthly'
                        ? t('billing.plans.monthly')
                        : plan.interval === 'yearly'
                        ? t('billing.plans.yearly')
                        : t('billing.plans.period'),
                  })}
                </small>
              </div>
              <ul>
                {(plan.features || []).map((feature) => (
                  <li key={feature}>• {feature}</li>
                ))}
              </ul>
              <div className="plan-card__actions">
                <Button variant={selectedPlan === plan.id ? 'primary' : 'secondary'} onClick={() => setSelectedPlan(plan.id)}>
                  {t('billing.actions.choose')}
                </Button>
                <Button disabled={processing} onClick={() => handleSubscribe(plan.id)}>
                  {t('billing.actions.activate')}
                </Button>
                <Button variant="ghost" disabled={processing} onClick={() => handleCheckout(plan.id)}>
                  {t('billing.actions.invoice')}
                </Button>
              </div>
            </div>
          ))}
        </div>
      </Card>

      <div className="grid two">
        <Card title={t('billing.methods.title')} subtitle={t('billing.methods.subtitle')}>
          <form className="billing-method-form" onSubmit={handleAddMethod}>
            <label>
              {t('billing.methods.name')}
              <input value={form.label} onChange={(event) => setForm((prev) => ({ ...prev, label: event.target.value }))} required />
            </label>
            <label>
              {t('billing.methods.type')}
              <select value={form.method_type} onChange={(event) => setForm((prev) => ({ ...prev, method_type: event.target.value }))}>
                <option value="card">{t('billing.methods.card')}</option>
                <option value="bank_account">{t('billing.methods.bank')}</option>
                <option value="invoice">{t('billing.methods.invoice')}</option>
                <option value="ewallet">{t('billing.methods.ewallet')}</option>
              </select>
            </label>
            <label>
              {t('billing.methods.provider')}
              <select value={form.gateway} onChange={(event) => setForm((prev) => ({ ...prev, gateway: event.target.value }))}>
                <option value="liqpay">LiqPay</option>
                <option value="fondy">Fondy</option>
                <option value="wayforpay">WayForPay</option>
                <option value="stripe">Stripe</option>
                <option value="bank_transfer">Банковский перевод</option>
                <option value="invoice">Счёт на оплату</option>
              </select>
            </label>
            {form.method_type === 'card' && (
              <>
                <label>
                  {t('billing.methods.cardNumber')}
                  <input value={form.cardNumber} onChange={(event) => setForm((prev) => ({ ...prev, cardNumber: event.target.value }))} required />
                </label>
                <label>
                  {t('billing.methods.expires')}
                  <input
                    value={form.expires}
                    onChange={(event) => setForm((prev) => ({ ...prev, expires: event.target.value }))}
                    placeholder="MM/YY"
                  />
                </label>
              </>
            )}
            {form.method_type === 'bank_account' && (
              <>
                <label>
                  {t('billing.methods.iban')}
                  <input value={form.bankAccount} onChange={(event) => setForm((prev) => ({ ...prev, bankAccount: event.target.value }))} required />
                </label>
                <label>
                  {t('billing.methods.companyCode')}
                  <input value={form.companyCode} onChange={(event) => setForm((prev) => ({ ...prev, companyCode: event.target.value }))} />
                </label>
              </>
            )}
            <div className="form-actions">
              <Button type="submit" disabled={processing}>
                {processing ? t('billing.methods.saving') : t('billing.methods.add')}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setForm(defaultMethod)}>
                {t('billing.methods.clear')}
              </Button>
            </div>
          </form>

          <table className="table" style={{ marginTop: 24 }}>
            <thead>
              <tr>
                <th>{t('billing.methods.name')}</th>
                <th>{t('billing.methods.providerShort')}</th>
                <th>{t('billing.methods.details')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {methods.map((method) => (
                <tr key={method.id}>
                  <td>{method.label}</td>
                  <td>{method.gateway}</td>
                  <td>
                    <code style={{ fontSize: '0.8rem' }}>{JSON.stringify(method.details)}</code>
                  </td>
                <td style={{ display: 'flex', gap: 8 }}>
                    <Button variant="ghost" onClick={() => handleSetDefault(method.id)} disabled={method.is_default}>
                      {t('billing.methods.default')}
                    </Button>
                    <Button variant="danger" onClick={() => handleDeleteMethod(method.id)}>
                      {t('billing.methods.remove')}
                    </Button>
                  </td>
                </tr>
              ))}
              {methods.length === 0 && (
                <tr>
                  <td colSpan={4} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)' }}>
                    {t('billing.methods.empty')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>

        <Card title={t('billing.subscriptions.title')} subtitle={t('billing.subscriptions.subtitle')}>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('billing.subscriptions.plan')}</th>
                <th>{t('billing.subscriptions.status')}</th>
                <th>{t('billing.subscriptions.autoRenew')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {subscriptions.map((sub) => (
                <tr key={sub.id}>
                  <td>{sub.id}</td>
                  <td>{plans.find((plan) => plan.id === sub.plan_id)?.name || '—'}</td>
                  <td>{sub.status}</td>
                  <td>{sub.auto_renew ? t('billing.subscriptions.yes') : t('billing.subscriptions.no')}</td>
                  <td>
                    {sub.status !== 'canceled' && (
                      <Button variant="ghost" onClick={() => handleCancel(sub.id)}>
                        {t('billing.subscriptions.cancel')}
                      </Button>
                    )}
                  </td>
                </tr>
              ))}
              {subscriptions.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)' }}>
                    {t('billing.subscriptions.empty')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>

          <h3 style={{ marginTop: 32 }}>{t('billing.transactions.title')}</h3>
          <table className="table">
            <thead>
              <tr>
                <th>ID</th>
                <th>{t('billing.transactions.reference')}</th>
                <th>{t('billing.transactions.amount')}</th>
                <th>{t('billing.transactions.status')}</th>
                <th>{t('billing.transactions.date')}</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => (
                <tr key={tx.id}>
                  <td>{tx.id}</td>
                  <td>{tx.reference}</td>
                  <td>
                    {tx.amount} {tx.currency}
                  </td>
                  <td>{tx.status}</td>
                  <td>{new Date(tx.created_at).toLocaleString()}</td>
                </tr>
              ))}
              {transactions.length === 0 && (
                <tr>
                  <td colSpan={5} style={{ textAlign: 'center', padding: '24px 0', color: 'var(--color-text-muted)' }}>
                    {t('billing.transactions.empty')}
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </Card>
      </div>
    </div>
  )
}
