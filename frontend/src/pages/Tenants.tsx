import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

type TFn = (en: string, vars?: Record<string, string | number>) => string

interface Tenant {
  id: string; name: string; short: string; color: string; type: string; plan: string
  mrr: number; msp: string | null; compliance: number; evidence_pending: number
  status: string; admin: string | null; created: string; last_login: string; archived: boolean
  activation_pending: boolean; audit_level: string
}
interface Resp { tenants: Tenant[]; counts: { all: number; msp: number; client: number } }

const complianceColor = (p: number) => (p >= 75 ? '#16A34A' : p >= 40 ? '#D97706' : '#DC2626')

interface PlanLite { id: string; name: string; tier: string; price_monthly: number; is_active: boolean }

function ConvertModal({ tenant, onClose }: { tenant: Tenant; onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const { data } = useQuery<{ plans: PlanLite[] }>({ queryKey: ['active-plans'], queryFn: async () => (await api.get('/plans/active')).data })
  const single = (data?.plans || []).filter(p => p.tier === 'single_client')
  const [planId, setPlanId] = useState('')
  const convert = useMutation({
    mutationFn: async () => (await api.post(`/tenants/${tenant.id}/convert-to-direct`, { plan_id: planId })).data,
    onSuccess: (r) => { toast.success(t('{name} converted to {plan}', { name: tenant.name, plan: r.plan })); qc.invalidateQueries({ queryKey: ['tenants'] }); onClose() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Conversion failed')),
  })
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 460 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Convert {name} to direct', { name: tenant.name })}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          <div className="page-sub" style={{ marginBottom: 12 }}>{t('Detaches {name} from {msp}, moves it to direct EVA billing on a single-client plan, and turns off MSP pre-review. All controls, evidence and users are kept.', { name: tenant.name, msp: tenant.msp || '' })}</div>
          <label className="form-label">{t('Choose a plan')}</label>
          {single.map(p => (
            <div key={p.id} onClick={() => setPlanId(p.id)} style={{
              padding: '10px 12px', borderRadius: 8, marginTop: 6, cursor: 'pointer',
              border: `1px solid ${planId === p.id ? 'var(--eva-blue2)' : 'var(--border-l)'}`, background: planId === p.id ? 'var(--soft)' : 'var(--card)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{planId === p.id ? '◉' : '○'} {p.name}</span>
                <span style={{ color: 'var(--green)', fontWeight: 600 }}>${p.price_monthly}{t('/mo')}</span>
              </div>
            </div>
          ))}
          {single.length === 0 && <div className="page-sub">{t('No active single-client plans - create one in Plans & Pricing first.')}</div>}
          <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} disabled={!planId || convert.isPending} onClick={() => convert.mutate()}>
            {convert.isPending ? t('Converting…') : t('Convert to direct client')}
          </button>
        </div>
      </div>
    </div>
  )
}

function EditPlanModal({ tenant, onClose }: { tenant: Tenant; onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const { data } = useQuery<{ plans: PlanLite[] }>({ queryKey: ['active-plans'], queryFn: async () => (await api.get('/plans/active')).data })
  const wantTier = tenant.type === 'msp' ? 'msp' : 'single_client'
  const options = (data?.plans || []).filter(p => p.tier === wantTier)
  const [planId, setPlanId] = useState('')
  const save = useMutation({
    mutationFn: async () => (await api.patch(`/tenants/${tenant.id}/plan`, { plan_id: planId })).data,
    onSuccess: (r) => { toast.success(t('{name} is now on {plan}', { name: tenant.name, plan: r.plan })); qc.invalidateQueries({ queryKey: ['tenants'] }); onClose() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not update plan')),
  })
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 460 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Edit plan - {name}', { name: tenant.name })}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          <div className="page-sub" style={{ marginBottom: 12 }}>{t('Current plan: {plan} (${mrr}/mo). Choose a new plan below.', { plan: tenant.plan, mrr: tenant.mrr })}</div>
          <label className="form-label">{t('Choose a plan')}</label>
          {options.map(p => (
            <div key={p.id} onClick={() => setPlanId(p.id)} style={{
              padding: '10px 12px', borderRadius: 8, marginTop: 6, cursor: 'pointer',
              border: `1px solid ${planId === p.id ? 'var(--eva-blue2)' : 'var(--border-l)'}`, background: planId === p.id ? 'var(--soft)' : 'var(--card)',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span style={{ fontWeight: 600, fontSize: 13 }}>{planId === p.id ? '◉' : '○'} {p.name}{p.name === tenant.plan ? ` ${t('(current)')}` : ''}</span>
                <span style={{ color: 'var(--green)', fontWeight: 600 }}>${p.price_monthly}{t('/mo')}</span>
              </div>
            </div>
          ))}
          {options.length === 0 && <div className="page-sub">{t('No active {tier} plans - create one in Plans & Pricing first.', { tier: wantTier })}</div>}
          <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 14 }} disabled={!planId || save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? t('Saving…') : t('Save plan')}
          </button>
        </div>
      </div>
    </div>
  )
}

interface Tier { min_clients: number; min_revenue?: number; discount_pct: number }
interface PartnerData {
  msp_name: string; enabled: boolean; max_clients: number; volume_tiers: Tier[]; discount_pct: number
  model: string; tier_basis: string; client_discount_pct: number; commission_pct: number; annual_revenue: number
  clients: { id: string; name: string; plan: string; active: boolean; retail: number; effective_wholesale: number; margin: number; floor: number }[]
  totals: { active_clients: number; client_mrr: number; eva_share: number; msp_payout: number; margin_pct: number }
}

function PartnerModal({ tenant, onClose }: { tenant: Tenant; onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const { data } = useQuery<PartnerData>({ queryKey: ['partner', tenant.id], queryFn: async () => (await api.get(`/partners/${tenant.id}`)).data })
  const [enabled, setEnabled] = useState(true)
  const [maxClients, setMaxClients] = useState(0)
  const [tiers, setTiers] = useState<Tier[]>([])
  const [model, setModel] = useState('wholesale')
  const [basis, setBasis] = useState('clients')
  const [clientDisc, setClientDisc] = useState(0)
  const [commission, setCommission] = useState(0)
  const [seeded, setSeeded] = useState(false)
  if (data && !seeded) {
    setEnabled(data.enabled); setMaxClients(data.max_clients); setTiers(data.volume_tiers)
    setModel(data.model || 'wholesale'); setBasis(data.tier_basis || 'clients')
    setClientDisc(data.client_discount_pct || 0); setCommission(data.commission_pct || 0); setSeeded(true)
  }

  const save = useMutation({
    mutationFn: async () => (await api.put(`/partners/${tenant.id}/terms`, {
      enabled, max_clients: maxClients, volume_tiers: tiers,
      model, tier_basis: basis, client_discount_pct: clientDisc, commission_pct: commission,
    })).data,
    onSuccess: () => { toast.success(t('Partner terms saved')); qc.invalidateQueries({ queryKey: ['partner', tenant.id] }); qc.invalidateQueries({ queryKey: ['tenants'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const setRetail = useMutation({
    mutationFn: async (v: { id: string; retail: number }) => (await api.patch(`/partners/client/${v.id}/retail`, { retail: v.retail })).data,
    onSuccess: () => { toast.success(t('Price updated')); qc.invalidateQueries({ queryKey: ['partner', tenant.id] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not update price')),
  })
  const genStatement = useMutation({
    mutationFn: async () => (await api.post(`/partners/${tenant.id}/statement`, {})).data,
    onSuccess: (r) => {
      toast.success(t('Statement {n} generated', { n: r?.invoice?.number || '' }))
      qc.invalidateQueries({ queryKey: ['msp-statements', tenant.id] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not generate statement')),
  })
  const tt = data?.totals

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 640 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Partner terms - {name}', { name: tenant.name })}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          {tt && (
            <div style={{ display: 'flex', gap: 10, marginBottom: 14, flexWrap: 'wrap' }}>
              <div className="kpi-card blue" style={{ flex: 1, minWidth: 120 }}><div className="kpi-lbl">{t('Active clients')}</div><div className="kpi-val blue">{tt.active_clients}</div></div>
              <div className="kpi-card purple" style={{ flex: 1, minWidth: 120 }}><div className="kpi-lbl">{t('Client MRR')}</div><div className="kpi-val purple">${tt.client_mrr}</div></div>
              <div className="kpi-card amber" style={{ flex: 1, minWidth: 120 }}><div className="kpi-lbl">{t('EVA net')}</div><div className="kpi-val amber">${tt.eva_share}</div></div>
              <div className="kpi-card green" style={{ flex: 1, minWidth: 120 }}><div className="kpi-lbl">{t('MSP payout')}</div><div className="kpi-val green">${tt.msp_payout}</div></div>
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 12 }}>
            <button className="tb-btn" disabled={genStatement.isPending} onClick={() => genStatement.mutate()}
              title={t('Issue this month’s payout statement and email the MSP admins')}>
              {genStatement.isPending ? t('Generating…') : t('📄 Generate monthly statement')}
            </button>
          </div>

          <label style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', gap: 6, alignItems: 'center', marginBottom: 10 }}>
            <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} /> {t('Partner program enabled')}
          </label>

          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 12 }}>
            <div className="form-row" style={{ width: 220 }}>
              <label className="form-label">{t('Partner model')}</label>
              <select className="form-input" value={model} onChange={e => setModel(e.target.value)}>
                <option value="wholesale">{t('Wholesale markup')}</option>
                <option value="commission">{t('Commission / referral')}</option>
              </select>
            </div>
            <div className="form-row" style={{ width: 200 }}>
              <label className="form-label">{t('Max client orgs (0 = ∞)')}</label>
              <input className="form-input" type="number" value={maxClients} onChange={e => setMaxClients(Number(e.target.value))} />
            </div>
          </div>

          {model === 'commission' && (
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 12 }}>
              <div className="form-row" style={{ width: 220 }}>
                <label className="form-label">{t('Fixed client discount (%)')}</label>
                <input className="form-input" type="number" value={clientDisc} onChange={e => setClientDisc(Number(e.target.value))} />
              </div>
              <div className="form-row" style={{ width: 220 }}>
                <label className="form-label">{t('Partner commission (%)')}</label>
                <input className="form-input" type="number" value={commission} onChange={e => setCommission(Number(e.target.value))} />
              </div>
            </div>
          )}

          {model === 'wholesale' && (
            <>
              <div className="form-row" style={{ width: 260, marginBottom: 8 }}>
                <label className="form-label">{t('Tier basis')}</label>
                <select className="form-input" value={basis} onChange={e => setBasis(e.target.value)}>
                  <option value="clients">{t('Active client count')}</option>
                  <option value="revenue">{t('Annual revenue ($)')}</option>
                </select>
              </div>
              <div className="form-label">{t('Volume tiers (discount on wholesale)')}</div>
              {tiers.map((tr, i) => (
                <div key={i} style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 6 }}>
                  {basis === 'revenue' ? (
                    <>
                      <input className="form-input" style={{ width: 130 }} type="number" value={tr.min_revenue || 0}
                        onChange={e => setTiers(s => s.map((x, j) => j === i ? { ...x, min_revenue: Number(e.target.value) } : x))} />
                      <span style={{ fontSize: 11, color: 'var(--text3)' }}>{t('$ /yr →')}</span>
                    </>
                  ) : (
                    <>
                      <input className="form-input" style={{ width: 110 }} type="number" value={tr.min_clients}
                        onChange={e => setTiers(s => s.map((x, j) => j === i ? { ...x, min_clients: Number(e.target.value) } : x))} />
                      <span style={{ fontSize: 11, color: 'var(--text3)' }}>{t('+ clients →')}</span>
                    </>
                  )}
                  <input className="form-input" style={{ width: 90 }} type="number" value={tr.discount_pct}
                    onChange={e => setTiers(s => s.map((x, j) => j === i ? { ...x, discount_pct: Number(e.target.value) } : x))} />
                  <span style={{ fontSize: 11, color: 'var(--text3)' }}>% {t('off')}</span>
                  <button className="ev-action-btn" onClick={() => setTiers(s => s.filter((_, j) => j !== i))}>✕</button>
                </div>
              ))}
              <button className="tb-btn" style={{ marginTop: 8 }} onClick={() => setTiers(s => [...s, { min_clients: 0, min_revenue: 0, discount_pct: 0 }])}>{t('+ Add tier')}</button>
            </>
          )}

          {data && data.clients.length > 0 && (
            <>
              <div className="form-label" style={{ marginTop: 16 }}>{t('Per-client retail price')}</div>
              <div className="ev-table-wrap" style={{ marginTop: 6 }}>
                <table className="ev-table">
                  <thead><tr><th>{t('Client')}</th><th>{t('Retail')}</th><th>{t('Floor')}</th><th>{t('Margin')}</th></tr></thead>
                  <tbody>
                    {data.clients.map(c => (
                      <tr key={c.id} style={{ opacity: c.active ? 1 : 0.55 }}>
                        <td style={{ fontWeight: 600 }}>{c.name}</td>
                        <td><input className="form-input" style={{ width: 80, fontSize: 12, padding: '2px 6px' }} type="number" defaultValue={c.retail}
                          onBlur={e => { const v = parseInt(e.target.value || '0', 10); if (v !== c.retail) setRetail.mutate({ id: c.id, retail: v }) }} /></td>
                        <td style={{ fontSize: 11, color: 'var(--text3)' }}>${c.floor}</td>
                        <td style={{ fontWeight: 700, color: 'var(--green)' }}>${c.margin}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}

          <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 16 }} disabled={save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? t('Saving…') : t('Save partner terms')}
          </button>
        </div>
      </div>
    </div>
  )
}

interface FwLite { framework_id: string; name: string; version: string; controls: number; provisioned?: number; billing_type?: string; amount?: number }
interface FwResp { tenant_id: string; tenant_name: string; monthly_price: number; assigned: FwLite[]; available: FwLite[]; synced?: number }

const billLabel = (tr: TFn, type?: string, a?: number) =>
  type === 'recurring' ? `$${a}${tr('/mo')}` : type === 'one_time' ? tr('{a} one-time', { a: `$${a}` }) : tr('Included (no charge)')

function FrameworksModal({ tenant, onClose }: { tenant: Tenant; onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const { data, isLoading } = useQuery<FwResp>({
    queryKey: ['tenant-frameworks', tenant.id],
    queryFn: async () => (await api.get(`/tenants/${tenant.id}/frameworks`)).data,
  })
  const [fwId, setFwId] = useState('')
  const [billing, setBilling] = useState('recurring')
  const [amount, setAmount] = useState('')

  const after = (d: FwResp) => {
    qc.setQueryData(['tenant-frameworks', tenant.id], d)
    qc.invalidateQueries({ queryKey: ['tenants'] })
    qc.invalidateQueries({ queryKey: ['controls'] })
  }
  const add = useMutation({
    mutationFn: async () => (await api.post(`/tenants/${tenant.id}/frameworks`, {
      framework_id: fwId, billing_type: billing, amount: billing === 'none' ? 0 : parseInt(amount || '0', 10),
    })).data,
    onSuccess: (d: FwResp) => { after(d); toast.success(t('Framework added')); setFwId(''); setAmount('') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not add framework')),
  })
  const remove = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/tenants/${tenant.id}/frameworks/${id}`)).data,
    onSuccess: (d: FwResp) => { after(d); toast.success(t('Framework removed')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not remove framework')),
  })
  const sync = useMutation({
    mutationFn: async () => (await api.post(`/tenants/${tenant.id}/frameworks/sync`, {})).data,
    onSuccess: (d: FwResp) => { after(d); toast.success(d.synced ? t('Added {n} missing controls', { n: d.synced }) : t('Already up to date - nothing to add')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not sync controls')),
  })

  const inp = { fontSize: 12, padding: '6px 8px', border: '1px solid var(--border-l)', borderRadius: 6, background: 'var(--card)' }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 560 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr">
          <span className="card-title">{t('Frameworks - {name}', { name: tenant.name })}</span>
          <button className="ev-action-btn" onClick={onClose}>✕</button>
        </div>
        <div className="modal-body">
          {isLoading || !data ? <div className="page-sub">{t('Loading…')}</div> : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 8, padding: '8px 12px' }}>
                <span style={{ fontSize: 12, color: 'var(--text2)' }}>{t('Current recurring price')}</span>
                <span style={{ fontSize: 15, fontWeight: 700, color: 'var(--green)' }}>${data.monthly_price}{t('/mo')}</span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <div className="form-label">{t('Assigned frameworks')}</div>
                {data.assigned.length > 0 && (
                  <button className="ev-action-btn" disabled={sync.isPending}
                    style={{ fontSize: 10, padding: '3px 8px' }}
                    title="Provision any missing controls for the assigned frameworks. Additive only - never deletes evidence."
                    onClick={() => sync.mutate()}>{t('↺ Sync controls')}</button>
                )}
              </div>
              {data.assigned.length === 0 && <div className="page-sub" style={{ marginBottom: 8 }}>{t('No frameworks assigned yet.')}</div>}
              {data.assigned.map(f => (
                <div key={f.framework_id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', border: '1px solid var(--border-l)', borderRadius: 7, marginBottom: 6 }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 12.5, fontWeight: 600 }}>{f.name} <span style={{ color: 'var(--text3)', fontWeight: 400 }}>v{f.version}</span></div>
                    <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>
                      {t('{n} controls', { n: f.controls })}
                      {f.provisioned !== undefined && f.provisioned < f.controls && (
                        <span style={{ color: 'var(--amber, #B45309)' }}> · {t('{n} not yet provisioned', { n: f.controls - f.provisioned })}</span>
                      )}
                      {' · '}{billLabel(t, f.billing_type, f.amount)}
                    </div>
                  </div>
                  <button className="ev-action-btn" disabled={remove.isPending}
                    style={{ fontSize: 10, padding: '3px 8px', background: '#FEE2E2', color: '#991B1B', borderColor: '#FECACA' }}
                    onClick={() => { if (confirm(`Remove ${f.name} from ${tenant.name}? This deletes its controls and evidence for this client.`)) remove.mutate(f.framework_id) }}>
                    {t('Remove')}
                  </button>
                </div>
              ))}

              <div className="form-label" style={{ marginTop: 14 }}>{t('Add a framework')}</div>
              {data.available.length === 0 ? (
                <div className="page-sub">{t('All frameworks are already assigned, or none are imported yet.')}</div>
              ) : (
                <div style={{ border: '1px solid var(--border-l)', borderRadius: 8, padding: 12 }}>
                  <select value={fwId} onChange={e => setFwId(e.target.value)} style={{ ...inp, width: '100%', marginBottom: 8 }}>
                    <option value="">{t('Choose a framework…')}</option>
                    {data.available.map(f => <option key={f.framework_id} value={f.framework_id}>{f.name} (v{f.version}, {t('{n} controls', { n: f.controls })})</option>)}
                  </select>
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    <select value={billing} onChange={e => setBilling(e.target.value)} style={inp}>
                      <option value="recurring">{t('Recurring add-on')}</option>
                      <option value="one_time">{t('One-time fee')}</option>
                      <option value="none">{t('No charge (included)')}</option>
                    </select>
                    {billing !== 'none' && (
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <span style={{ fontSize: 13, color: 'var(--text3)' }}>$</span>
                        <input type="number" min={0} value={amount} onChange={e => setAmount(e.target.value)} placeholder="0"
                          style={{ ...inp, width: 90 }} />
                        <span style={{ fontSize: 11, color: 'var(--text3)' }}>{billing === 'recurring' ? t('/mo') : t('one-time')}</span>
                      </div>
                    )}
                    <button className="submit-btn" style={{ marginLeft: 'auto', padding: '7px 16px' }}
                      disabled={!fwId || add.isPending} onClick={() => add.mutate()}>
                      {add.isPending ? t('Adding…') : t('+ Add')}
                    </button>
                  </div>
                  <div style={{ fontSize: 10.5, color: 'var(--text3)', marginTop: 8 }}>
                    {t("Recurring updates the client's monthly price. To replace a framework, remove one and add another.")}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

export default function TenantsPage() {
  const qc = useQueryClient()
  const t = useT()
  const [filter, setFilter] = useState<'all' | 'msp' | 'client'>('all')
  const [showArchived, setShowArchived] = useState(false)
  const [converting, setConverting] = useState<Tenant | null>(null)
  const [managingFw, setManagingFw] = useState<Tenant | null>(null)
  const [editingPlan, setEditingPlan] = useState<Tenant | null>(null)
  const [partnerOf, setPartnerOf] = useState<Tenant | null>(null)

  const { data, isLoading, isError, error } = useQuery<Resp>({
    queryKey: ['tenants'],
    queryFn: async () => (await api.get('/tenants/')).data,
  })

  const toggle = useMutation({
    mutationFn: async ({ id, suspend }: { id: string; suspend: boolean }) =>
      (await api.patch(`/tenants/${id}/status`, { suspend })).data,
    onSuccess: () => { toast.success(t('Tenant status updated')); qc.invalidateQueries({ queryKey: ['tenants'] }) },
    onError: () => toast.error(t('Update failed')),
  })
  const archive = useMutation({
    mutationFn: async ({ id, archived }: { id: string; archived: boolean }) =>
      (await api.patch(`/tenants/${id}/archive`, { archived })).data,
    onSuccess: (_d, v) => { toast.success(v.archived ? t('Tenant archived') : t('Tenant restored')); qc.invalidateQueries({ queryKey: ['tenants'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const authorize = useMutation({
    mutationFn: async (id: string) => (await api.post(`/tenants/${id}/authorize`)).data,
    onSuccess: () => { toast.success(t('Account authorized')); qc.invalidateQueries({ queryKey: ['tenants'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const exportTenant = async (id: string, name: string) => {
    try {
      const res = await api.get(`/tenants/${id}/export`, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url; a.download = `client_${name.replace(/[^A-Za-z0-9]+/g, '_')}.json`; a.click()
      URL.revokeObjectURL(url)
      toast.success(t('Export downloaded'))
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Export failed')) }
  }
  const setAuditLevel = useMutation({
    mutationFn: async (v: { id: string; level: string }) => (await api.patch(`/tenants/${v.id}/audit-level`, { audit_level: v.level })).data,
    onSuccess: () => { toast.success(t('Audit level updated')); qc.invalidateQueries({ queryKey: ['tenants'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })

  if (isLoading) return <div className="page-sub">{t('Loading tenants…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('Tenant management requires Super Admin access.') : t('Failed to load tenants.')}
    </div>
  }
  if (!data) return null

  const { counts } = data
  const archivedCount = data.tenants.filter(t => t.archived).length
  const filtered = data.tenants
    .filter(t => (showArchived ? t.archived : !t.archived))
    .filter(t => filter === 'all' ? true : t.type === filter)

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Tenant Management')}</div>
          <div className="page-sub">{t('{all} tenants · {msp} MSPs · {client} direct clients', { all: counts.all, msp: counts.msp, client: counts.client })}</div>
        </div>
      </div>

      <div className="aq-filters fi">
        {([['all', 'All Tenants'], ['msp', 'MSPs Only'], ['client', 'Clients Only']] as const).map(([v, l]) => (
          <button key={v} onClick={() => setFilter(v)}
            style={{
              padding: '5px 14px', borderRadius: 7,
              border: `1px solid ${filter === v ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
              background: filter === v ? 'var(--eva-blue2)' : 'var(--card)',
              color: filter === v ? '#fff' : 'var(--text2)', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)',
            }}>
            {t(l)} ({v === 'all' ? counts.all : v === 'msp' ? counts.msp : counts.client})
          </button>
        ))}
        <button onClick={() => setShowArchived(s => !s)}
          style={{ marginLeft: 'auto', padding: '5px 14px', borderRadius: 7,
            border: `1px solid ${showArchived ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
            background: showArchived ? 'var(--eva-blue2)' : 'var(--card)',
            color: showArchived ? '#fff' : 'var(--text2)', fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)' }}>
          {t('🗄 Archived')} ({archivedCount})
        </button>
        <span style={{ fontSize: 11, color: 'var(--text3)' }}>{t('{n} showing', { n: filtered.length })}</span>
      </div>

      <div className="detail-section fi">
        <table className="tenant-table">
          <thead>
            <tr><th>{t('Tenant')}</th><th>{t('Type')}</th><th>{t('Plan / MRR')}</th><th>{t('MSP Parent')}</th><th>{t('Compliance')}</th><th>{t('Evidence')}</th><th>{t('Status')}</th><th>{t('Last Login')}</th><th>{t('Actions')}</th></tr>
          </thead>
          <tbody>
            {filtered.map(tn => {
              const col = complianceColor(tn.compliance)
              const suspended = tn.status === 'suspended'
              return (
                <tr key={tn.id} style={{ opacity: tn.archived ? 0.6 : 1 }}>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <div className="t-avatar" style={{ background: tn.color }}>{tn.short}</div>
                      <div>
                        <div style={{ fontWeight: 600, fontSize: 12 }}>{tn.name}</div>
                        <div style={{ fontSize: 10, color: 'var(--text3)' }}>{tn.admin || t('No admin')} · {t('Since {date}', { date: tn.created })}</div>
                      </div>
                    </div>
                  </td>
                  <td><span className={`t-type ${tn.type === 'msp' ? 't-msp' : tn.type === 'eva' ? 't-eva' : tn.msp ? 't-client' : 't-client-direct'}`}>{tn.type === 'msp' ? 'MSP' : tn.type === 'eva' ? 'EVA' : tn.msp ? t('Client · MSP') : t('Client · Direct')}</span></td>
                  <td>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)' }}>{tn.plan}</div>
                    <div style={{ fontSize: 10, color: 'var(--green)', fontWeight: 600 }}>${tn.mrr}{t('/mo')}</div>
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text3)' }}>{tn.msp || t('Direct')}</td>
                  <td>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
                      <div style={{ flex: 1, height: 4, background: 'var(--surface-2)', borderRadius: 2, minWidth: 50 }}><div style={{ width: `${tn.compliance}%`, height: '100%', background: col, borderRadius: 2 }} /></div>
                      <span style={{ fontWeight: 700, color: col, fontSize: 11 }}>{tn.compliance}%</span>
                    </div>
                  </td>
                  <td>{tn.evidence_pending > 0
                    ? <span className="badge b-amber" style={{ fontSize: 9 }}>⏳ {tn.evidence_pending}</span>
                    : <span className="badge b-green" style={{ fontSize: 9 }}>{t('✓ Clear')}</span>}</td>
                  <td>
                    <span className={`badge ${tn.status === 'active' ? 'b-green' : tn.status === 'onboarding' ? 'b-amber' : 'b-red'}`}>{tn.status}</span>
                    {tn.activation_pending && <span className="badge b-amber" style={{ fontSize: 9, marginLeft: 4 }}>⏳ {t('Pending')}</span>}
                  </td>
                  <td style={{ fontSize: 11, color: 'var(--text3)' }}>{tn.last_login}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap', alignItems: 'center' }}>
                      {tn.activation_pending && (
                        <button className="ev-action-btn" disabled={authorize.isPending}
                          title={t('Approve this pending account so it can sign in and be used')}
                          style={{ fontSize: 10, padding: '3px 8px', background: '#DCFCE7', color: '#166534', borderColor: '#86EFAC' }}
                          onClick={() => authorize.mutate(tn.id)}>✓ {t('Authorize')}</button>
                      )}
                      {tn.type === 'client' && (
                        <select value={tn.audit_level} title={t('Audit level')}
                          onChange={e => setAuditLevel.mutate({ id: tn.id, level: e.target.value })}
                          className="ev-action-btn" style={{ fontSize: 10, padding: '3px 6px' }}>
                          <option value="self">{t('Self audit')}</option>
                          <option value="assisted">{t('Assisted')}</option>
                          <option value="audited">{t('Audited')}</option>
                        </select>
                      )}
                      {tn.type === 'client' && (
                        <button className="ev-action-btn" title={t('Assign or remove compliance frameworks for this client')}
                          style={{ fontSize: 10, padding: '3px 8px', background: '#F0FDFA', color: '#0F766E', borderColor: '#99F6E4' }}
                          onClick={() => setManagingFw(tn)}>{t('Frameworks')}</button>
                      )}
                      {tn.type === 'client' && tn.msp && (
                        <button className="ev-action-btn" title={t('Move this MSP-managed client to direct EVA billing (keeps all data)')}
                          style={{ fontSize: 10, padding: '3px 8px', background: 'var(--soft)', color: '#1E40AF', borderColor: '#BFDBFE' }}
                          onClick={() => setConverting(tn)}>→ {t('Direct')}</button>
                      )}
                      {tn.type === 'msp' && (
                        <button className="ev-action-btn" title={t('Edit this MSP’s partner terms (model, discount tiers, commission) and issue statements')}
                          style={{ fontSize: 10, padding: '3px 8px', background: '#FEF3C7', color: '#92400E', borderColor: '#FDE68A' }}
                          onClick={() => setPartnerOf(tn)}>{t('Partner')}</button>
                      )}
                      <button className="ev-action-btn" title={t('Change this organization’s plan and price')}
                        style={{ fontSize: 10, padding: '3px 8px', background: 'var(--surface)', color: 'var(--text2)', borderColor: 'var(--border-l)' }}
                        onClick={() => setEditingPlan(tn)}>{t('Plan')}</button>
                      {tn.type !== 'eva' && (
                        <button className="ev-action-btn" title={t('Download a full JSON export of this organization’s data')}
                          style={{ fontSize: 10, padding: '3px 8px', background: 'var(--surface)', color: 'var(--text2)', borderColor: 'var(--border-l)' }}
                          onClick={() => exportTenant(tn.id, tn.name)}>⬇ {t('Export')}</button>
                      )}
                      {tn.type !== 'eva' && !tn.archived && (
                        <button className="ev-action-btn" disabled={toggle.isPending}
                          title={suspended ? t('Re-enable sign-in and access for this organization') : t('Block sign-in for this organization (data kept)')}
                          style={{ fontSize: 10, padding: '3px 8px', background: suspended ? '#DCFCE7' : '#FEE2E2', color: suspended ? '#166534' : '#991B1B', borderColor: suspended ? '#86EFAC' : '#FECACA' }}
                          onClick={() => toggle.mutate({ id: tn.id, suspend: !suspended })}>
                          {suspended ? t('Reactivate') : t('Suspend')}
                        </button>
                      )}
                      {tn.type !== 'eva' && (tn.archived
                        ? <button className="ev-action-btn" disabled={archive.isPending}
                            title={t('Bring this archived organization back into lists and selectors')}
                            style={{ fontSize: 10, padding: '3px 8px', background: '#DCFCE7', color: '#166534', borderColor: '#86EFAC' }}
                            onClick={() => archive.mutate({ id: tn.id, archived: false })}>{t('Restore')}</button>
                        : <button className="ev-action-btn" disabled={archive.isPending}
                            title={t('Hide this organization from lists/selectors while keeping all its history')}
                            style={{ fontSize: 10, padding: '3px 8px', background: 'var(--surface)', color: 'var(--text3)', borderColor: 'var(--border-l)' }}
                            onClick={() => { if (window.confirm(t('Archive {name}? It keeps all history but disappears from selectors and lists.', { name: tn.name }))) archive.mutate({ id: tn.id, archived: true }) }}>{t('Archive')}</button>
                      )}
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {converting && <ConvertModal tenant={converting} onClose={() => setConverting(null)} />}
      {managingFw && <FrameworksModal tenant={managingFw} onClose={() => setManagingFw(null)} />}
      {editingPlan && <EditPlanModal tenant={editingPlan} onClose={() => setEditingPlan(null)} />}
      {partnerOf && <PartnerModal tenant={partnerOf} onClose={() => setPartnerOf(null)} />}
    </>
  )
}
