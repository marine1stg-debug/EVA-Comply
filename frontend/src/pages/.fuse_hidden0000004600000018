import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Inclusions {
  frameworks: string | string[]
  features: Record<string, boolean>
  max_users: number
  max_clients: number
  highlights?: string[]
}
interface Plan {
  id: string; name: string; tier: string; price_monthly: number; wholesale_monthly: number; is_active: boolean
  yearly_discount_pct?: number
  inclusions: Inclusions; tenants: number
}
interface Fw { id: string; name: string }

const FEATURE_LABEL: Record<string, string> = {
  reports: 'Report export', import: 'Custom framework import', msp_review: 'MSP pre-review',
  audit_logs: 'Audit logs', api: 'API access',
}

function PlanEditor({ plan, frameworks, featureKeys, onClose }: {
  plan: Plan | null; frameworks: Fw[]; featureKeys: string[]; onClose: () => void
}) {
  const qc = useQueryClient()
  const t = useT()
  const isNew = !plan
  const [name, setName] = useState(plan?.name || '')
  const [tier, setTier] = useState(plan?.tier || 'single_client')
  const [price, setPrice] = useState(plan?.price_monthly ?? 0)
  const [wholesale, setWholesale] = useState(plan?.wholesale_monthly ?? 0)
  // For NEW plans, auto-suggest wholesale at 80% of retail until the admin edits it.
  const [wsTouched, setWsTouched] = useState(!isNew)
  const onPriceChange = (v: number) => {
    setPrice(v)
    if (isNew && !wsTouched) setWholesale(Math.round(v * 0.8))
  }
  const [yearlyDisc, setYearlyDisc] = useState(plan?.yearly_discount_pct ?? 0)
  const [active, setActive] = useState(plan?.is_active ?? true)
  const [allFw, setAllFw] = useState(plan ? plan.inclusions.frameworks === 'all' : true)
  const [fwIds, setFwIds] = useState<string[]>(plan && Array.isArray(plan.inclusions.frameworks) ? plan.inclusions.frameworks : [])
  const [features, setFeatures] = useState<Record<string, boolean>>(() => {
    const base: Record<string, boolean> = {}; featureKeys.forEach(k => base[k] = plan?.inclusions.features?.[k] ?? false); return base
  })
  const [maxUsers, setMaxUsers] = useState(plan?.inclusions.max_users ?? 0)
  const [maxClients, setMaxClients] = useState(plan?.inclusions.max_clients ?? 0)
  const [highlights, setHighlights] = useState<string>((plan?.inclusions.highlights || []).join('\n'))

  const body = () => ({
    name, tier, price_monthly: price, wholesale_monthly: wholesale, is_active: active,
    yearly_discount_pct: yearlyDisc,
    inclusions: {
      frameworks: allFw ? 'all' : fwIds, features, max_users: maxUsers, max_clients: maxClients,
      highlights: highlights.split('\n').map(s => s.trim()).filter(Boolean),
    },
  })
  const save = useMutation({
    mutationFn: async () => isNew
      ? (await api.post('/plans/', body())).data
      : (await api.put(`/plans/${plan!.id}`, body())).data,
    onSuccess: () => { toast.success(isNew ? t('Plan created') : t('Plan updated')); qc.invalidateQueries({ queryKey: ['plans'] }); onClose() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 560 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{isNew ? t('New plan') : t('Edit — {name}', { name: plan!.name })}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          <div style={{ display: 'flex', gap: 10 }}>
            <div className="form-row" style={{ flex: 1 }}><label className="form-label">{t('Plan name')}</label><input className="form-input" value={name} onChange={e => setName(e.target.value)} /></div>
            <div className="form-row" style={{ width: 130 }}><label className="form-label">{t('Price $/mo')}</label><input className="form-input" type="number" value={price} onChange={e => onPriceChange(Number(e.target.value))} /></div>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <div className="form-row" style={{ width: 200 }}>
              <label className="form-label">{t('Wholesale $/mo (MSP cost)')}</label>
              <input className="form-input" type="number" value={wholesale} onChange={e => { setWholesale(Number(e.target.value)); setWsTouched(true) }} />
            </div>
            <div className="page-sub" style={{ fontSize: 11, alignSelf: 'flex-end', paddingBottom: 8 }}>
              {t('MSP margin before volume discount: ${m}/mo', { m: Math.max(0, price - wholesale) })}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <div className="form-row" style={{ width: 200 }}>
              <label className="form-label">{t('Yearly discount %')}</label>
              <input className="form-input" type="number" min={0} max={100} value={yearlyDisc} onChange={e => setYearlyDisc(Math.max(0, Math.min(100, Number(e.target.value))))} />
            </div>
            <div className="page-sub" style={{ fontSize: 11, alignSelf: 'flex-end', paddingBottom: 8 }}>
              {t('Yearly price: ${y} (vs ${m})', { y: Math.round(price * 12 * (1 - yearlyDisc / 100)), m: price * 12 })}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 10, marginTop: 8, alignItems: 'flex-end' }}>
            <div className="form-row" style={{ flex: 1 }}><label className="form-label">{t('Tier')}</label>
              <select className="form-select" value={tier} onChange={e => setTier(e.target.value)}>
                <option value="single_client">{t('Single Client')}</option>
                <option value="msp">MSP</option>
              </select>
            </div>
            <label style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', gap: 6, alignItems: 'center', paddingBottom: 8 }}>
              <input type="checkbox" checked={active} onChange={e => setActive(e.target.checked)} /> {t('Active')}
            </label>
          </div>

          <div className="form-label" style={{ marginTop: 14 }}>{t('Frameworks included')}</div>
          <label style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', gap: 6, alignItems: 'center', margin: '6px 0' }}>
            <input type="checkbox" checked={allFw} onChange={e => setAllFw(e.target.checked)} /> {t('All frameworks')}
          </label>
          {!allFw && frameworks.map(f => (
            <label key={f.id} style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', gap: 6, alignItems: 'center', padding: '3px 0' }}>
              <input type="checkbox" checked={fwIds.includes(f.id)} onChange={() => setFwIds(s => s.includes(f.id) ? s.filter(x => x !== f.id) : [...s, f.id])} /> {f.name}
            </label>
          ))}

          <div className="form-label" style={{ marginTop: 14 }}>{t('Feature modules')}</div>
          {featureKeys.map(k => (
            <label key={k} style={{ fontSize: 12, color: 'var(--text2)', display: 'flex', gap: 6, alignItems: 'center', padding: '3px 0' }}>
              <input type="checkbox" checked={!!features[k]} onChange={e => setFeatures(f => ({ ...f, [k]: e.target.checked }))} /> {t(FEATURE_LABEL[k] || k)}
            </label>
          ))}

          <div className="form-label" style={{ marginTop: 14 }}>{t('Landing-page highlights (one per line)')}</div>
          <textarea className="form-input" rows={4} style={{ width: '100%', boxSizing: 'border-box', fontSize: 12, lineHeight: 1.6 }}
            placeholder={t('e.g. Framework compliance tracking\nEvidence collection & review\nExpert EVA audit decisions')}
            value={highlights} onChange={e => setHighlights(e.target.value)} />
          <div className="page-sub" style={{ fontSize: 11, marginTop: 2 }}>{t('Shown as the ✓ bullets on the public landing page. Leave empty to use the default bullets.')}</div>

          <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
            <div className="form-row" style={{ flex: 1 }}><label className="form-label">{t('Max users (0 = ∞)')}</label><input className="form-input" type="number" value={maxUsers} onChange={e => setMaxUsers(Number(e.target.value))} /></div>
            {tier === 'msp' && <div className="form-row" style={{ flex: 1 }}><label className="form-label">{t('Max client orgs (0 = ∞)')}</label><input className="form-input" type="number" value={maxClients} onChange={e => setMaxClients(Number(e.target.value))} /></div>}
          </div>

          <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 16 }} disabled={!name.trim() || save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? t('Saving…') : isNew ? t('Create plan') : t('Save changes')}
          </button>
        </div>
      </div>
    </div>
  )
}

interface PlatformSettings { billing_mode: string; trial_days: number; modes: { key: string; name: string; desc: string }[] }

function BillingModePanel() {
  const qc = useQueryClient()
  const t = useT()
  const { data } = useQuery<PlatformSettings>({ queryKey: ['platform-settings'], queryFn: async () => (await api.get('/platform/settings')).data })
  const [mode, setMode] = useState<string | null>(null)
  const [days, setDays] = useState<number | null>(null)
  const m = mode ?? data?.billing_mode ?? 'no_card_trial'
  const d = days ?? data?.trial_days ?? 14
  const save = useMutation({
    mutationFn: async () => (await api.put('/platform/settings', { billing_mode: m, trial_days: d })).data,
    onSuccess: () => { toast.success(t('Billing mode saved')); qc.invalidateQueries({ queryKey: ['platform-settings'] }); qc.invalidateQueries({ queryKey: ['entitlements'] }) },
    onError: () => toast.error(t('Save failed')),
  })
  if (!data) return null
  return (
    <div className="detail-section fi" style={{ marginBottom: 16 }}>
      <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Billing & Trials')}</span></div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 10 }}>
        {data.modes.map(opt => (
          <div key={opt.key} onClick={() => setMode(opt.key)} style={{
            padding: '12px 14px', borderRadius: 10, cursor: 'pointer',
            border: `1px solid ${m === opt.key ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
            background: m === opt.key ? 'var(--soft)' : 'var(--card)',
          }}>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>{m === opt.key ? '◉' : '○'} {opt.name}</div>
            <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4, lineHeight: 1.5 }}>{opt.desc}</div>
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 12, marginTop: 12 }}>
        <div className="form-row" style={{ width: 160 }}>
          <label className="form-label">{t('Trial length (days)')}</label>
          <input className="form-input" type="number" value={d} disabled={m === 'charge_immediately'} onChange={e => setDays(Number(e.target.value))} />
        </div>
        <button className="submit-btn" disabled={save.isPending} onClick={() => save.mutate()}>{save.isPending ? t('Saving…') : t('Save billing mode')}</button>
      </div>
      <div className="page-sub" style={{ marginTop: 8 }}>{t('Applies to new sign-ups. Card-required modes need Stripe keys configured.')}</div>
    </div>
  )
}

interface Promo {
  id: string; code: string; billing_mode: string; hint?: string; label?: string | null
  is_active: boolean; expires_at: string | null; max_uses: number | null; uses: number; usable: boolean
}
const MODE_NAME: Record<string, string> = {
  no_card_trial: 'No-card trial', card_trial: 'Card trial → auto-charge', charge_immediately: 'Charge immediately',
}

function EmailPanel() {
  const t = useT()
  const { data } = useQuery<{ backend: string; smtp_host: string; senders: { invoicing: string; cases: string; noreply: string } }>({
    queryKey: ['email-config'], queryFn: async () => (await api.get('/platform/email-config')).data,
  })
  const [to, setTo] = useState(''); const [sender, setSender] = useState('noreply')
  const test = useMutation({
    mutationFn: async () => (await api.post('/platform/email-test', { to, sender })).data,
    onSuccess: (r: any) => toast.success(t('Test sent (backend: {b})', { b: r.backend })),
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Send failed')),
  })
  if (!data) return null
  return (
    <div className="detail-section fi" style={{ marginBottom: 16 }}>
      <div className="card-hdr" style={{ marginBottom: 6 }}><span className="card-title">{t('Email senders')}</span>
        <span className="badge b-gray" style={{ fontSize: 9 }}>{t('Backend')}: {data.backend}{data.backend === 'smtp' && data.smtp_host ? ` · ${data.smtp_host}` : ''}</span></div>
      <div className="page-sub" style={{ marginBottom: 10 }}>{t('Set SMTP and the three sender addresses via environment variables (SMTP_*, EMAIL_FROM_*).')}</div>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 4, fontSize: 12, marginBottom: 12 }}>
        <div>📑 {t('Invoicing')}: <b>{data.senders.invoicing}</b></div>
        <div>🎧 {t('Cases')}: <b>{data.senders.cases}</b></div>
        <div>🔕 {t('No-reply')}: <b>{data.senders.noreply}</b></div>
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap', paddingTop: 10, borderTop: '1px solid var(--border-l)' }}>
        <div><div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 3 }}>{t('Send a test to')}</div>
          <input className="form-input" style={{ width: 220, fontSize: 12 }} value={to} onChange={e => setTo(e.target.value)} placeholder="you@company.com" /></div>
        <div><div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 3 }}>{t('From')}</div>
          <select className="form-select" style={{ fontSize: 12 }} value={sender} onChange={e => setSender(e.target.value)}>
            <option value="noreply">{t('No-reply')}</option><option value="cases">{t('Cases')}</option><option value="invoicing">{t('Invoicing')}</option>
          </select></div>
        <button className="tb-btn" disabled={!to.trim() || test.isPending} onClick={() => test.mutate()}>{test.isPending ? t('Sending…') : t('Send test')}</button>
      </div>
    </div>
  )
}

function PromoCodesPanel() {
  const qc = useQueryClient()
  const t = useT()
  const { data } = useQuery<{ promos: Promo[]; modes: string[] }>({ queryKey: ['promos'], queryFn: async () => (await api.get('/promos/')).data })
  const [code, setCode] = useState(''); const [mode, setMode] = useState('no_card_trial')
  const [labelTxt, setLabelTxt] = useState(''); const [maxUses, setMaxUses] = useState('')
  const after = () => qc.invalidateQueries({ queryKey: ['promos'] })
  const create = useMutation({
    mutationFn: async () => (await api.post('/promos/', {
      code, billing_mode: mode, label: labelTxt || undefined, max_uses: maxUses ? parseInt(maxUses, 10) : undefined,
    })).data,
    onSuccess: () => { toast.success(t('Promo code created')); after(); setCode(''); setLabelTxt(''); setMaxUses('') },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not create code')),
  })
  const patch = useMutation({ mutationFn: async (v: { id: string; body: any }) => (await api.patch(`/promos/${v.id}`, v.body)).data, onSuccess: after })
  const del = useMutation({ mutationFn: async (id: string) => (await api.delete(`/promos/${id}`)).data, onSuccess: () => { toast.success(t('Code deleted')); after() } })
  if (!data) return null
  const inp = { fontSize: 12, padding: '6px 8px', border: '1px solid var(--border-l)', borderRadius: 6, background: 'var(--card)' }
  return (
    <div className="detail-section fi" style={{ marginBottom: 16 }}>
      <div className="card-hdr" style={{ marginBottom: 4 }}><span className="card-title">{t('Signup promo codes')}</span></div>
      <div className="page-sub" style={{ marginBottom: 10 }}>{t('A code overrides the default billing mode for clients who sign up with it. No code → the default above.')}</div>

      {data.promos.map(p => (
        <div key={p.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 10px', border: '1px solid var(--border-l)', borderRadius: 7, marginBottom: 6, opacity: p.is_active ? 1 : .55 }}>
          <span style={{ fontFamily: 'var(--mono)', fontWeight: 700, fontSize: 12.5, background: 'var(--soft)', color: '#1E40AF', padding: '2px 8px', borderRadius: 5 }}>{p.code}</span>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 12, fontWeight: 600 }}>{t(MODE_NAME[p.billing_mode] || p.billing_mode)}</div>
            <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>
              {p.label ? p.label + ' · ' : ''}{t('{n} used', { n: p.uses })}{p.max_uses ? ` / ${p.max_uses}` : t(' · unlimited')}
            </div>
          </div>
          <span className={`badge ${p.usable ? 'b-green' : 'b-gray'}`} style={{ fontSize: 9 }}>{p.usable ? t('active') : t('inactive')}</span>
          <button className="ev-action-btn" style={{ fontSize: 10, padding: '3px 8px' }}
            onClick={() => patch.mutate({ id: p.id, body: { is_active: !p.is_active } })}>{p.is_active ? t('Disable') : t('Enable')}</button>
          <button className="ev-action-btn" style={{ fontSize: 10, padding: '3px 8px', background: '#FEE2E2', color: '#991B1B', borderColor: '#FECACA' }}
            onClick={() => { if (confirm(`Delete code ${p.code}?`)) del.mutate(p.id) }}>✕</button>
        </div>
      ))}
      {data.promos.length === 0 && <div className="page-sub" style={{ marginBottom: 8 }}>{t('No promo codes yet.')}</div>}

      <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap', marginTop: 10, paddingTop: 12, borderTop: '1px solid var(--border-l)' }}>
        <div><div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 3 }}>{t('Code')}</div>
          <input value={code} onChange={e => setCode(e.target.value.toUpperCase())} placeholder="EVA-TRIAL" style={{ ...inp, width: 130, textTransform: 'uppercase' }} /></div>
        <div><div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 3 }}>{t('Grants')}</div>
          <select value={mode} onChange={e => setMode(e.target.value)} style={inp}>
            {data.modes.map(md => <option key={md} value={md}>{t(MODE_NAME[md] || md)}</option>)}
          </select></div>
        <div><div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 3 }}>{t('Label (optional)')}</div>
          <input value={labelTxt} onChange={e => setLabelTxt(e.target.value)} placeholder="e.g. Partner referral" style={{ ...inp, width: 150 }} /></div>
        <div><div style={{ fontSize: 10, color: 'var(--text3)', marginBottom: 3 }}>{t('Max uses')}</div>
          <input type="number" min={1} value={maxUses} onChange={e => setMaxUses(e.target.value)} placeholder="∞" style={{ ...inp, width: 70 }} /></div>
        <button className="submit-btn" disabled={!code.trim() || create.isPending} onClick={() => create.mutate()} style={{ padding: '7px 16px' }}>{t('+ Create')}</button>
      </div>
    </div>
  )
}

export default function PlansPage() {
  const qc = useQueryClient()
  const t = useT()
  const [editing, setEditing] = useState<Plan | null | undefined>(undefined) // undefined = closed, null = new
  const [frameworks, setFrameworks] = useState<Fw[]>([])

  const { data, isLoading, isError, error } = useQuery<{ plans: Plan[]; feature_keys: string[] }>({
    queryKey: ['plans'],
    queryFn: async () => (await api.get('/plans/')).data,
  })
  useEffect(() => { api.get('/auth/signup-options').then(r => setFrameworks(r.data.frameworks)).catch(() => {}) }, [])

  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/plans/${id}`)).data,
    onSuccess: () => { toast.success(t('Plan deleted')); qc.invalidateQueries({ queryKey: ['plans'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Delete failed')),
  })

  if (isLoading) return <div className="page-sub">{t('Loading plans…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('Plans & Pricing requires Super Admin access.') : t('Failed to load plans.')}
    </div>
  }
  if (!data) return null

  const fwName = (id: string) => frameworks.find(f => f.id === id)?.name || '—'

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Plans & Pricing')}</div>
          <div className="page-sub">{t('Configure package pricing and what each plan includes.')}</div>
        </div>
        <div className="page-actions"><button className="tb-btn pri" onClick={() => setEditing(null)}>{t('+ New Plan')}</button></div>
      </div>

      <BillingModePanel />
      <EmailPanel />
      <PromoCodesPanel />

      <div className="detail-section fi">
        <table className="tenant-table">
          <thead><tr><th>{t('Plan')}</th><th>{t('Tier')}</th><th>{t('Price')}</th><th>{t('Frameworks')}</th><th>{t('Features')}</th><th>{t('Limits')}</th><th>{t('In use')}</th><th></th></tr></thead>
          <tbody>
            {data.plans.map(p => {
              const feats = Object.entries(p.inclusions.features || {}).filter(([, v]) => v).map(([k]) => t(FEATURE_LABEL[k] || k))
              const fw = p.inclusions.frameworks === 'all' ? t('All') : (p.inclusions.frameworks as string[]).map(fwName).join(', ') || t('None')
              return (
                <tr key={p.id}>
                  <td style={{ fontWeight: 600 }}>{p.name} {!p.is_active && <span className="badge b-gray" style={{ fontSize: 9 }}>{t('inactive')}</span>}</td>
                  <td><span className={`t-type ${p.tier === 'msp' ? 't-msp' : 't-client'}`}>{p.tier === 'msp' ? 'MSP' : t('Client')}</span></td>
                  <td>${p.price_monthly}{t('/mo')}<div style={{ fontSize: 10, color: 'var(--text3)' }}>{t('wholesale')} ${p.wholesale_monthly}</div></td>
                  <td style={{ fontSize: 11, maxWidth: 160 }}>{fw}</td>
                  <td style={{ fontSize: 11, maxWidth: 180 }}>{feats.length ? feats.join(', ') : '—'}</td>
                  <td style={{ fontSize: 11 }}>{p.inclusions.max_users || '∞'} {t('users')}{p.tier === 'msp' ? ` · ${p.inclusions.max_clients || '∞'} clients` : ''}</td>
                  <td>{p.tenants}</td>
                  <td>
                    <div style={{ display: 'flex', gap: 5 }}>
                      <button className="ev-action-btn" onClick={() => setEditing(p)}>{t('Edit')}</button>
                      <button className="ev-action-btn delete" disabled={p.tenants > 0 || del.isPending} onClick={() => del.mutate(p.id)}>{t('Delete')}</button>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {editing !== undefined && <PlanEditor plan={editing} frameworks={frameworks} featureKeys={data.feature_keys} onClose={() => setEditing(undefined)} />}
    </>
  )
}
