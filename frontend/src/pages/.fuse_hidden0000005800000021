import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface ClientRow {
  id: string; name: string; plan: string; status: string; active: boolean
  retail: number; wholesale: number; effective_wholesale: number; margin: number; floor: number
}
interface Tier { min_clients: number; discount_pct: number }
interface Partner {
  msp_id: string; msp_name: string; enabled: boolean; max_clients: number
  model: string; tier_basis: string; client_discount_pct: number; commission_pct: number; annual_revenue: number
  volume_tiers: Tier[]; discount_pct: number; current_tier: Tier
  next_tier: { min_clients: number; discount_pct: number; clients_needed: number } | null
  clients: ClientRow[]
  totals: { clients: number; active_clients: number; client_mrr: number; eva_share: number; msp_payout: number; margin_pct: number }
  can_edit_terms: boolean; can_edit_retail: boolean
}

function RetailCell({ row, canEdit }: { row: ClientRow; canEdit: boolean }) {
  const t = useT(); const qc = useQueryClient()
  const [editing, setEditing] = useState(false)
  const [val, setVal] = useState(String(row.retail))
  const save = useMutation({
    mutationFn: async () => (await api.patch(`/partners/client/${row.id}/retail`, { retail: parseInt(val || '0', 10) })).data,
    onSuccess: () => { toast.success(t('Price updated')); setEditing(false); qc.invalidateQueries({ queryKey: ['partner-me'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not update price')),
  })
  if (!canEdit) return <span style={{ fontWeight: 600 }}>${row.retail}</span>
  if (!editing) return (
    <span style={{ fontWeight: 600, cursor: 'pointer' }} onClick={() => { setVal(String(row.retail)); setEditing(true) }} title={t('Edit retail price')}>
      ${row.retail} <span style={{ color: 'var(--text3)', fontSize: 10 }}>✎</span>
    </span>
  )
  return (
    <span style={{ display: 'inline-flex', gap: 4, alignItems: 'center' }}>
      <input className="form-input" style={{ width: 78, fontSize: 12, padding: '2px 6px' }} type="number" value={val}
        autoFocus onChange={e => setVal(e.target.value)} onKeyDown={e => { if (e.key === 'Enter') save.mutate(); if (e.key === 'Escape') setEditing(false) }} />
      <button className="ev-action-btn" disabled={save.isPending} onClick={() => save.mutate()}>✓</button>
      <button className="ev-action-btn" onClick={() => setEditing(false)}>✕</button>
    </span>
  )
}

interface Statement {
  id: string; number: string; amount: number; status: string; issued_at: string | null; period_end: string | null
}

function StatementsSection({ mspId }: { mspId: string }) {
  const t = useT()
  const { data } = useQuery<{ statements: Statement[] }>({
    queryKey: ['msp-statements', mspId],
    queryFn: async () => (await api.get(`/partners/${mspId}/statements`)).data,
  })
  const open = async (s: Statement) => {
    try {
      const res = await api.get(`/billing/invoices/${s.id}/download`, { responseType: 'text' })
      const url = URL.createObjectURL(new Blob([res.data], { type: 'text/html' }))
      window.open(url, '_blank'); setTimeout(() => URL.revokeObjectURL(url), 60000)
    } catch { toast.error(t('Could not open statement')) }
  }
  const rows = data?.statements || []
  return (
    <div className="detail-section fi" style={{ marginTop: 16 }}>
      <div className="card-hdr"><span className="card-title">{t('Monthly statements')}</span>
        <span className="page-sub" style={{ fontSize: 10.5 }}>{t('Your payout statements issued by EVA')}</span></div>
      {rows.length === 0 ? <div className="page-sub" style={{ marginTop: 8 }}>{t('No statements yet.')}</div> : (
        <table className="tenant-table" style={{ marginTop: 8 }}>
          <thead><tr><th>{t('Statement')}</th><th>{t('Date')}</th><th>{t('Payout')}</th><th>{t('Status')}</th><th></th></tr></thead>
          <tbody>
            {rows.map(s => (
              <tr key={s.id}>
                <td style={{ fontFamily: 'var(--mono)', fontSize: 11 }}>{s.number}</td>
                <td>{s.issued_at ? s.issued_at.slice(0, 10) : '—'}</td>
                <td style={{ fontWeight: 700, color: 'var(--green)' }}>${s.amount.toFixed(2)}</td>
                <td><span className={`badge ${s.status === 'paid' ? 'b-green' : 'b-amber'}`}>{s.status}</span></td>
                <td><button className="ev-action-btn download" style={{ fontSize: 10 }} onClick={() => open(s)}>⬇ {t('View')}</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  )
}

export default function PartnerPage() {
  const t = useT()
  const { data, isLoading, isError } = useQuery<Partner>({
    queryKey: ['partner-me'],
    queryFn: async () => (await api.get('/partners/me')).data,
    retry: false,
  })

  if (isLoading) return <div className="page-sub">{t('Loading…')}</div>
  // This page is the MSP self-view. Super admins (and any non-MSP account) get a
  // 403 from /partners/me — show guidance instead of a blank screen.
  if (isError || !data) return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Margin & Revenue')}</div>
          <div className="page-sub">{t('Your clients are billed by EVA. We pay you the difference between the retail price you set and your wholesale cost.')}</div>
        </div>
      </div>
      <div className="detail-section fi">
        <div className="page-sub">{t('This page shows an MSP partner’s own margin and payouts. Your account is not an MSP partner, so there is nothing to display here. Super admins can review and edit each MSP’s partner terms from Tenant Management.')}</div>
      </div>
    </>
  )

  const tt = data.totals
  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Margin & Revenue')}</div>
          <div className="page-sub">{t('Your clients are billed by EVA. We pay you the difference between the retail price you set and your wholesale cost.')}</div>
        </div>
      </div>

      {!data.enabled && (
        <div className="detail-section fi" style={{ marginBottom: 16 }}>
          <div className="page-sub">{t('The partner program is not enabled for your account yet. Contact EVA to get set up.')}</div>
        </div>
      )}

      <div className="msp-kpi-grid fi" style={{ marginBottom: 16 }}>
        <div className="kpi-card blue"><div className="kpi-lbl">{t('Active clients')}</div><div className="kpi-val blue">{tt.active_clients}</div><div className="kpi-sub">{t('{n} total', { n: tt.clients })}</div></div>
        <div className="kpi-card purple"><div className="kpi-lbl">{t('Client MRR (billed by EVA)')}</div><div className="kpi-val purple">${tt.client_mrr}</div><div className="kpi-sub">{t('per month')}</div></div>
        <div className="kpi-card green"><div className="kpi-lbl">{data.model === 'commission' ? t('Your monthly commission') : t('Your monthly payout')}</div><div className="kpi-val green">${tt.msp_payout}</div><div className="kpi-sub">{t('{p}% margin', { p: tt.margin_pct })}</div></div>
        {data.model === 'commission' ? (
          <div className="kpi-card amber"><div className="kpi-lbl">{t('Commission rate')}</div><div className="kpi-val amber">{data.commission_pct}%</div>
            <div className="kpi-sub">{t('clients get −{d}%', { d: data.client_discount_pct })}</div>
          </div>
        ) : (
          <div className="kpi-card amber"><div className="kpi-lbl">{t('Volume discount')}</div><div className="kpi-val amber">{data.discount_pct}%</div>
            <div className="kpi-sub">{data.next_tier
              ? (data.tier_basis === 'revenue'
                  ? t('+{d}% at ${n}/yr', { d: data.next_tier.discount_pct, n: (data.next_tier as any).min_revenue })
                  : t('+{d}% at {n} clients ({k} to go)', { d: data.next_tier.discount_pct, n: data.next_tier.min_clients, k: data.next_tier.clients_needed }))
              : t('top tier reached')}</div>
          </div>
        )}
      </div>

      {data.model === 'commission' ? (
        <div className="detail-section fi" style={{ marginBottom: 16 }}>
          <div className="card-hdr"><span className="card-title">{t('Commission / referral terms')}</span>
            <span className="page-sub" style={{ fontSize: 10.5 }}>{t('Set by EVA')}</span></div>
          <div className="page-sub" style={{ marginTop: 8 }}>
            {t('Your referred clients receive a fixed {d}% discount. EVA bills them and pays you {c}% of what it collects as cumulative commission.', { d: data.client_discount_pct, c: data.commission_pct })}
          </div>
        </div>
      ) : (
        <div className="detail-section fi" style={{ marginBottom: 16 }}>
          <div className="card-hdr"><span className="card-title">{t('Volume tiers')}</span>
            <span className="page-sub" style={{ fontSize: 10.5 }}>{data.tier_basis === 'revenue' ? t('More annual revenue lowers your wholesale cost — set by EVA') : t('More active clients lowers your wholesale cost — set by EVA')}</span></div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 8 }}>
            {data.volume_tiers.map((tr, i) => {
              const isCurrent = data.current_tier && tr.min_clients === data.current_tier.min_clients && (data.current_tier as any).min_revenue === (tr as any).min_revenue
              const label = data.tier_basis === 'revenue' ? t('${n}+/yr', { n: (tr as any).min_revenue || 0 }) : t('{n}+ clients', { n: tr.min_clients })
              return (
                <div key={i} style={{ padding: '8px 12px', borderRadius: 8, border: `1px solid ${isCurrent ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
                  background: isCurrent ? 'var(--soft)' : 'var(--card)', minWidth: 120 }}>
                  <div style={{ fontSize: 11, color: 'var(--text3)' }}>{label}</div>
                  <div style={{ fontSize: 15, fontWeight: 700, color: isCurrent ? 'var(--eva-blue2)' : 'var(--text)' }}>{tr.discount_pct}% {t('off wholesale')}</div>
                  {isCurrent && <div style={{ fontSize: 9.5, color: 'var(--eva-blue2)', fontWeight: 600 }}>{t('● current')}</div>}
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div className="detail-section fi">
        <div className="card-hdr"><span className="card-title">{t('Per-client margin')}</span></div>
        {data.clients.length === 0 ? <div className="page-sub">{t('No clients yet.')}</div> : (
          <div className="ev-table-wrap">
            <table className="ev-table">
              <thead><tr>
                <th>{t('Client')}</th><th>{t('Plan')}</th><th>{t('Status')}</th>
                <th>{t('Retail (client pays)')}</th><th>{t('Your cost')}</th><th>{t('Your margin')}</th>
              </tr></thead>
              <tbody>
                {data.clients.map(c => (
                  <tr key={c.id} style={{ opacity: c.active ? 1 : 0.55 }}>
                    <td style={{ fontWeight: 600 }}>{c.name}</td>
                    <td style={{ fontSize: 11, color: 'var(--text3)' }}>{c.plan}</td>
                    <td><span className={`badge ${c.active ? 'b-green' : 'b-gray'}`} style={{ fontSize: 9 }}>{c.status}</span></td>
                    <td><RetailCell row={c} canEdit={data.can_edit_retail} /></td>
                    <td style={{ color: 'var(--text2)' }}>${c.effective_wholesale}{c.wholesale !== c.effective_wholesale && <span style={{ fontSize: 9, color: 'var(--text3)' }}> ({t('was')} ${c.wholesale})</span>}</td>
                    <td style={{ fontWeight: 700, color: 'var(--green)' }}>${c.margin}</td>
                  </tr>
                ))}
              </tbody>
              <tfoot><tr style={{ borderTop: '2px solid var(--border-l)', fontWeight: 700 }}>
                <td colSpan={3}>{t('Totals (active)')}</td>
                <td>${tt.client_mrr}</td><td>${tt.eva_share}</td><td style={{ color: 'var(--green)' }}>${tt.msp_payout}</td>
              </tr></tfoot>
            </table>
          </div>
        )}
      </div>

      <StatementsSection mspId={data.msp_id} />
    </>
  )
}
