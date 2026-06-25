import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Invoice {
  id: string; number: string; kind: string; amount: number; currency: string
  status: string; issued_at: string | null; period_end: string | null
}
interface Billing {
  tenant: string; tenant_type?: string; plan: string; status: string; price: number
  yearly_price: number; yearly_discount_pct: number
  seats: number; frameworks: number; invoices: Invoice[]
  stripe_connected: boolean; stripe_enabled: boolean
  interval: string; auto_renew: boolean; cancel_at_period_end: boolean; renews_at: string | null
}

export default function BillingPage() {
  const qc = useQueryClient()
  const t = useT()
  const [interval, setInterval] = useState<'month' | 'year'>('month')

  const { data, isLoading, isError, error } = useQuery<Billing>({
    queryKey: ['billing'],
    queryFn: async () => (await api.get('/billing/')).data,
  })

  useEffect(() => {
    const p = new URLSearchParams(window.location.search).get('checkout')
    if (p === 'success') { toast.success(t('Payment complete — subscription active')); qc.invalidateQueries({ queryKey: ['billing'] }) }
    if (p === 'cancel') toast(t('Checkout cancelled'))
    if (p) window.history.replaceState({}, '', '/billing')
  }, [qc])

  const checkout = useMutation({
    mutationFn: async () => (await api.post('/billing/checkout', {
      plan: data?.plan || 'Professional',
      interval,
      success_url: `${window.location.origin}/billing`,
      cancel_url: `${window.location.origin}/billing`,
    })).data,
    onSuccess: (r) => {
      if (r.url) { window.location.href = r.url }
      else { toast.success(r.message || t('Subscription activated')); qc.invalidateQueries({ queryKey: ['billing'] }) }
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Checkout failed')),
  })

  const setRenew = useMutation({
    mutationFn: async (on: boolean) => (await api.post(`/billing/${on ? 'resume' : 'cancel'}`)).data,
    onSuccess: (_d, on) => {
      toast.success(on ? t('Auto-renewal re-enabled') : t('Auto-renewal turned off — plan stays active until the period ends'))
      qc.invalidateQueries({ queryKey: ['billing'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not update auto-renewal')),
  })

  // Fetch the invoice HTML with the auth header and open it in a new tab.
  const openInvoice = async (inv: Invoice) => {
    try {
      const res = await api.get(`/billing/invoices/${inv.id}/download`, { responseType: 'text' })
      const blob = new Blob([res.data], { type: 'text/html' })
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
      setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch {
      toast.error(t('Could not open invoice'))
    }
  }

  if (isLoading) return <div className="page-sub">{t('Loading billing…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('Billing requires admin access.') : t('Failed to load billing.')}
    </div>
  }
  if (!data) return null

  const statusBadge = data.status === 'active' ? 'b-green' : data.status === 'suspended' ? 'b-red' : 'b-amber'
  const kindLabel = (k: string) => k === 'msp_consolidated' ? t('Statement') : k === 'manual' ? t('Manual') : t('Subscription')
  const priceForInterval = interval === 'year' ? data.yearly_price : data.price

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Billing')}</div>
          <div className="page-sub">{data.tenant} · {t('subscription & invoices')}</div>
        </div>
        <div className="page-actions" style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <div className="seg" style={{ display: 'inline-flex', border: '1px solid var(--border)', borderRadius: 8, overflow: 'hidden' }}>
            <button className="tb-btn" style={{ borderRadius: 0, border: 'none', background: interval === 'month' ? 'var(--blue)' : 'transparent', color: interval === 'month' ? '#fff' : 'var(--text2)' }} onClick={() => setInterval('month')}>{t('Monthly')}</button>
            <button className="tb-btn" style={{ borderRadius: 0, border: 'none', background: interval === 'year' ? 'var(--blue)' : 'transparent', color: interval === 'year' ? '#fff' : 'var(--text2)' }} onClick={() => setInterval('year')}>
              {t('Yearly')}{data.yearly_discount_pct ? ` (−${data.yearly_discount_pct}%)` : ''}
            </button>
          </div>
          <button className="tb-btn pri" disabled={checkout.isPending} onClick={() => checkout.mutate()}>
            {checkout.isPending ? t('Starting…') : data.stripe_enabled ? t('💳 Subscribe with Stripe') : t('Activate plan')}
          </button>
        </div>
      </div>

      {data.tenant_type === 'eva_internal' && (
        <div style={{ margin: '4px 0 14px', padding: '10px 14px', borderRadius: 10,
          border: '1px solid var(--border)', borderLeft: '4px solid var(--blue)',
          background: 'var(--card2, rgba(46,95,163,.08))', fontSize: 13, color: 'var(--text2)' }}>
          ℹ️ {t('This is the EVA internal organization — billing does not apply here. To manage a client’s subscription, use Tenants or Clients.')}
        </div>
      )}

      <div className="stat-grid fi2">
        <div className="stat-card blue"><div className="stat-icon blue">📦</div><div className="stat-lbl">{t('Plan')}</div><div className="stat-val blue" style={{ fontSize: 20 }}>{data.plan}</div><div className="stat-sub">${data.price}{t('/mo')}</div></div>
        <div className="stat-card green"><div className="stat-icon green">👥</div><div className="stat-lbl">{t('Seats')}</div><div className="stat-val green">{data.seats}</div><div className="stat-sub">{t('active users')}</div></div>
        <div className="stat-card amber"><div className="stat-icon amber">🛡</div><div className="stat-lbl">{t('Frameworks')}</div><div className="stat-val amber">{data.frameworks}</div><div className="stat-sub">{t('in use')}</div></div>
        <div className="stat-card red"><div className="stat-icon red">📅</div><div className="stat-lbl">{interval === 'year' ? t('Yearly total') : t('Monthly total')}</div><div className="stat-val red" style={{ fontSize: 20 }}>${priceForInterval}</div><div className="stat-sub">{interval === 'year' ? t('billed annually') : t('billed monthly')}</div></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 14 }} className="fi3">
        <div className="detail-section">
          <div className="card-hdr"><span className="card-title">{t('Invoice History')}</span></div>
          <table className="tenant-table">
            <thead><tr><th>{t('Invoice')}</th><th>{t('Type')}</th><th>{t('Date')}</th><th>{t('Amount')}</th><th>{t('Status')}</th><th></th></tr></thead>
            <tbody>
              {data.invoices.length === 0 && (
                <tr><td colSpan={6} className="page-sub" style={{ padding: 16 }}>{t('No invoices yet.')}</td></tr>
              )}
              {data.invoices.map(inv => (
                <tr key={inv.id}>
                  <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{inv.number}</td>
                  <td>{kindLabel(inv.kind)}</td>
                  <td>{inv.issued_at ? inv.issued_at.slice(0, 10) : '—'}</td>
                  <td>${inv.amount.toFixed(2)}</td>
                  <td><span className={`badge ${inv.status === 'paid' ? 'b-green' : inv.status === 'void' ? 'b-red' : 'b-amber'}`}>{inv.status}</span></td>
                  <td><button className="ev-action-btn download" style={{ fontSize: 10 }} onClick={() => openInvoice(inv)}>⬇ {t('View')}</button></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div className="detail-section">
          <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Subscription')}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Plan')}</span><span className="meta-val">{data.plan}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Status')}</span><span className={`badge ${statusBadge}`}>{data.status}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Monthly')}</span><span className="meta-val">${data.price}{t('/mo')}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Yearly')}</span><span className="meta-val">${data.yearly_price}{data.yearly_discount_pct ? ` (−${data.yearly_discount_pct}%)` : ''}</span></div>
          <div className="meta-row"><span className="meta-key">Stripe</span><span className="meta-val">{data.stripe_connected ? t('Subscription linked') : data.stripe_enabled ? t('Test mode ready') : t('Simulated (no key)')}</span></div>
          <div className="meta-row"><span className="meta-key">{t('Auto-renewal')}</span>
            <span className={`badge ${data.auto_renew ? 'b-green' : 'b-amber'}`}>{data.auto_renew ? t('On') : t('Off')}</span></div>
          {data.renews_at && (
            <div className="meta-row"><span className="meta-key">{data.cancel_at_period_end ? t('Ends on') : t('Renews on')}</span>
              <span className="meta-val">{data.renews_at}</span></div>
          )}
          <button className="tb-btn" style={{ width: '100%', marginTop: 12, justifyContent: 'center' }} disabled={checkout.isPending} onClick={() => checkout.mutate()}>
            {data.stripe_enabled ? t('Subscribe / update via Stripe') : t('Activate plan')}
          </button>
          {data.status === 'active' && (
            data.auto_renew ? (
              <button className="tb-btn" style={{ width: '100%', marginTop: 8, justifyContent: 'center', color: 'var(--red)' }}
                disabled={setRenew.isPending} onClick={() => { if (window.confirm(t('Turn off auto-renewal? Your plan stays active until the period ends.'))) setRenew.mutate(false) }}>
                {t('Turn off auto-renewal')}
              </button>
            ) : (
              <button className="tb-btn" style={{ width: '100%', marginTop: 8, justifyContent: 'center' }}
                disabled={setRenew.isPending} onClick={() => setRenew.mutate(true)}>
                {t('Re-enable auto-renewal')}
              </button>
            )
          )}
        </div>
      </div>
    </>
  )
}
