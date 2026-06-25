import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useT } from '../lib/i18n'

interface Client {
  id: string; name: string; short: string; color: string; compliance: number
  controls_done: number; controls_total: number; evidence_pending: number; status: string
  frameworks: string[]; plan: string; msp_review: boolean; users: number; admin: string | null
  last_activity: string; monthly_fee: number; eva_cost: number; margin: number
  recent_evidence?: { title: string; status: string; ref: string }[]
}

const progColor = (p: number) => (p >= 75 ? '#16A34A' : p >= 40 ? '#D97706' : '#DC2626')

interface Fw { id: string; name: string; version: string; controls: number }

function AddClientModal({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const [org, setOrg] = useState(''); const [adminName, setAdminName] = useState('')
  const [adminEmail, setAdminEmail] = useState('')
  const [price, setPrice] = useState(499); const [review, setReview] = useState(true)
  const [fwIds, setFwIds] = useState<string[]>([])
  const [frameworks, setFrameworks] = useState<Fw[]>([])
  const [inviteLink, setInviteLink] = useState<string | null>(null)

  useEffect(() => { api.get('/auth/signup-options').then(r => setFrameworks(r.data.frameworks)).catch(() => {}) }, [])
  // Pre-fill the MSP pre-review checkbox from the MSP-wide default.
  useEffect(() => { api.get('/msp/review-default').then(r => setReview(!!r.data.default)).catch(() => {}) }, [])
  const toggle = (id: string) => setFwIds(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])

  const create = useMutation({
    mutationFn: async () => (await api.post('/msp/clients', {
      org_name: org, admin_name: adminName, admin_email: adminEmail,
      plan: 'Professional', monthly_price: price, msp_review_enabled: review, framework_ids: fwIds,
    })).data,
    onSuccess: (r) => {
      toast.success(t('Client created — send them the invite'))
      qc.invalidateQueries({ queryKey: ['msp-clients'] }); qc.invalidateQueries({ queryKey: ['msp-portfolio'] })
      setInviteLink(r.invite_link || 'sent')
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not add client')),
  })

  const ok = org.trim() && adminName.trim() && adminEmail.trim()

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Add Client')}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          {inviteLink ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ fontSize: 34 }}>✉️</div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 6 }}>{t('Client created')}</div>
              <div className="page-sub" style={{ marginTop: 4 }}>{t('Send {name} this invite link to set their password and sign in:', { name: adminName })}</div>
              {inviteLink !== 'sent'
                ? <div style={{ marginTop: 12, padding: '10px 12px', background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 8, fontSize: 11, fontFamily: 'var(--mono)', wordBreak: 'break-all', textAlign: 'left' }}>{inviteLink}</div>
                : <div className="page-sub" style={{ marginTop: 8 }}>{t('An invitation email has been sent.')}</div>}
              <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
                {inviteLink !== 'sent' && <button className="tb-btn" style={{ flex: 1, justifyContent: 'center' }} onClick={() => { navigator.clipboard?.writeText(inviteLink); toast.success(t('Copied')) }}>{t('Copy link')}</button>}
                <button className="submit-btn" style={{ flex: 1, justifyContent: 'center' }} onClick={onClose}>{t('Done')}</button>
              </div>
            </div>
          ) : (
            <>
              <div className="form-row"><label className="form-label">{t('Organization name')}</label><input className="form-input" value={org} onChange={e => setOrg(e.target.value)} /></div>
              <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
                <div className="form-row" style={{ flex: 1 }}><label className="form-label">{t('Admin name')}</label><input className="form-input" value={adminName} onChange={e => setAdminName(e.target.value)} /></div>
                <div className="form-row" style={{ flex: 1 }}><label className="form-label">{t('Admin email')}</label><input className="form-input" type="email" value={adminEmail} onChange={e => setAdminEmail(e.target.value)} /></div>
              </div>
              <div className="form-row" style={{ width: 140, marginTop: 8 }}><label className="form-label">{t('Price $/mo')}</label><input className="form-input" type="number" value={price} onChange={e => setPrice(Number(e.target.value))} /></div>
              <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text2)', margin: '10px 0' }}>
                <input type="checkbox" checked={review} onChange={e => setReview(e.target.checked)} /> {t('Enable MSP pre-review before evidence reaches EVA')}
              </label>
              <label className="form-label">{t('Assign frameworks')}</label>
              <div style={{ marginTop: 6 }}>
                {frameworks.map(f => (
                  <label key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '6px 0', fontSize: 12, cursor: 'pointer' }}>
                    <input type="checkbox" checked={fwIds.includes(f.id)} onChange={() => toggle(f.id)} />
                    {f.name} <span style={{ color: 'var(--text3)' }}>v{f.version} · {t('{n} controls', { n: f.controls })}</span>
                  </label>
                ))}
              </div>
              <div className="page-sub" style={{ marginTop: 8 }}>{t('The client admin gets an invite link to set their own password — you don’t set it.')}</div>
              <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 12 }} disabled={!ok || create.isPending} onClick={() => create.mutate()}>
                {create.isPending ? t('Creating…') : t('Create client & generate invite')}
              </button>
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function ClientList({ onOpen }: { onOpen: (id: string) => void }) {
  const t = useT()
  const qc = useQueryClient()
  const [adding, setAdding] = useState(false)
  const role = useAuthStore(s => s.user?.role || '')
  const canAdd = ['super_admin', 'msp_admin'].includes(role)
  const isMspAdmin = role === 'msp_admin'
  const { data, isLoading, isError, error } = useQuery<{ clients: Client[]; total: number }>({
    queryKey: ['msp-clients'],
    queryFn: async () => (await api.get('/msp/clients')).data,
  })
  const { data: rd } = useQuery<{ default: boolean }>({
    queryKey: ['msp-review-default'], enabled: isMspAdmin,
    queryFn: async () => (await api.get('/msp/review-default')).data,
  })
  const setDefault = useMutation({
    mutationFn: async (enabled: boolean) => (await api.put('/msp/review-default', { enabled })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['msp-review-default'] }); toast.success(t('Saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  if (isLoading) return <div className="page-sub">{t('Loading clients…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('Client management requires MSP access.') : t('Failed to load clients.')}
    </div>
  }
  if (!data) return null

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Client Management')}</div>
          <div className="page-sub">{t('{n} clients · click a client to view details', { n: data.total })}</div>
        </div>
        <div className="page-actions" style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {isMspAdmin && rd && (
            <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 11.5, color: 'var(--text2)' }}
              title={t('Pre-fills the MSP pre-review setting for clients you add')}>
              <input type="checkbox" checked={!!rd.default} disabled={setDefault.isPending} onChange={e => setDefault.mutate(e.target.checked)} />
              {t('MSP pre-review on by default for new clients')}
            </label>
          )}
          {canAdd && <button className="tb-btn pri" onClick={() => setAdding(true)}>{t('+ Add Client')}</button>}
        </div>
      </div>
      {adding && <AddClientModal onClose={() => setAdding(false)} />}
      <div className="client-list fi">
        {data.clients.length === 0 && <div className="page-sub">{t('No client organizations yet.')}</div>}
        {data.clients.map(c => {
          const col = progColor(c.compliance)
          return (
            <div key={c.id} className="client-card" onClick={() => onOpen(c.id)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                <div className="client-avatar" style={{ background: c.color }}>{c.short}</div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span className="client-name">{c.name}</span>
                    <span className="badge b-blue" style={{ fontSize: 9 }}>{c.plan}</span>
                    {c.msp_review && <span className="badge b-purple" style={{ fontSize: 9 }}>{t('MSP Review ON')}</span>}
                    <span className={`badge ${c.status === 'active' ? 'b-green' : 'b-amber'}`} style={{ fontSize: 9 }}>{c.status}</span>
                  </div>
                  <div className="client-sub">{c.admin || t('No admin assigned')} · {t('{n} users', { n: c.users })} · {t('Last active: {date}', { date: c.last_activity })}</div>
                </div>
                <div style={{ textAlign: 'right', flexShrink: 0, minWidth: 140 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: col }}>{c.compliance}%</div>
                  <div className="client-prog-wrap"><div className="client-prog-bar"><div className="client-prog-fill" style={{ width: `${c.compliance}%`, background: col }} /></div></div>
                  <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 2 }}>{t('{a}/{b} controls', { a: c.controls_done, b: c.controls_total })}</div>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 5, flexShrink: 0, minWidth: 80 }}>
                  {c.evidence_pending > 0
                    ? <span className="badge b-amber">{t('⏳ {n} pending', { n: c.evidence_pending })}</span>
                    : <span className="badge b-green">{t('✓ Up to date')}</span>}
                  <span style={{ fontSize: 10, color: 'var(--text3)' }}>${c.monthly_fee}{t('/mo')}</span>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </>
  )
}

function ClientDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const t = useT()
  const qc = useQueryClient()
  const role = useAuthStore(s => s.user?.role || '')
  const canToggle = ['super_admin', 'msp_admin'].includes(role)
  const { data: c, isLoading, isError } = useQuery<Client>({
    queryKey: ['msp-client', id],
    queryFn: async () => (await api.get(`/msp/clients/${id}`)).data,
  })
  const toggleReview = useMutation({
    mutationFn: async (enabled: boolean) => (await api.patch(`/msp/clients/${id}/review`, { enabled })).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['msp-client', id] }); qc.invalidateQueries({ queryKey: ['msp-clients'] })
      toast.success(t('Saved'))
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  if (isLoading) return <div className="page-sub">{t('Loading client…')}</div>
  if (isError || !c) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load client.')}</div>
  const col = progColor(c.compliance)

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, flexWrap: 'wrap' }} className="fi">
        <button className="tb-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={onBack}>← {t('Clients')}</button>
        <div className="client-avatar" style={{ background: c.color, width: 32, height: 32 }}>{c.short}</div>
        <span style={{ fontSize: 16, fontWeight: 600 }}>{c.name}</span>
        <span className="badge b-blue">{c.plan}</span>
        <span className={`badge ${c.status === 'active' ? 'b-green' : 'b-amber'}`}>{c.status}</span>
      </div>

      <div className="msp-kpi-grid fi" style={{ gridTemplateColumns: 'repeat(4,1fr)' }}>
        <div className="kpi-card green"><div className="kpi-icon green">🛡</div><div className="kpi-lbl">{t('Compliance')}</div><div className="kpi-val green">{c.compliance}%</div><div className="kpi-sub">{t('{a}/{b} controls', { a: c.controls_done, b: c.controls_total })}</div></div>
        <div className="kpi-card amber"><div className="kpi-icon amber">⏳</div><div className="kpi-lbl">{t('Pending Review')}</div><div className="kpi-val amber">{c.evidence_pending}</div><div className="kpi-sub">{t('evidence items')}</div></div>
        <div className="kpi-card blue"><div className="kpi-icon blue">👥</div><div className="kpi-lbl">{t('Users')}</div><div className="kpi-val blue">{c.users}</div><div className="kpi-sub">{c.admin || t('No admin')}</div></div>
        <div className="kpi-card purple"><div className="kpi-icon purple">💰</div><div className="kpi-lbl">{t('Margin')}</div><div className="kpi-val purple">${c.margin}</div><div className="kpi-sub">{t('{fee} fee · {cost} cost', { fee: `$${c.monthly_fee}`, cost: `$${c.eva_cost}` })}</div></div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 14 }} className="fi">
        <div className="detail-section">
          <div className="card-hdr"><span className="card-title">{t('Recent Evidence')}</span></div>
          {(!c.recent_evidence || c.recent_evidence.length === 0) && <div className="page-sub">{t('No evidence submitted yet.')}</div>}
          {c.recent_evidence?.map((e, i) => (
            <div key={i} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid var(--border-l)' }}>
              <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--eva-blue2)', background: 'var(--soft)', padding: '2px 6px', borderRadius: 4 }}>{e.ref}</span>
              <span style={{ fontSize: 12, flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{e.title}</span>
              <span className="badge b-gray" style={{ fontSize: 9 }}>{e.status}</span>
            </div>
          ))}
        </div>
        <div className="detail-section">
          <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Client Info')}</span></div>
          {([['Plan', c.plan], ['Frameworks', c.frameworks.join(', ')],
            ['Monthly fee', `$${c.monthly_fee}/mo`], ['EVA cost', `$${c.eva_cost}/mo`], ['Margin', `$${c.margin}/mo`],
            ['Last active', c.last_activity]] as [string, string][]).map(([k, v]) => (
            <div key={k} className="meta-row"><span className="meta-key">{t(k)}</span><span className="meta-val">{v}</span></div>
          ))}
          <div className="meta-row" style={{ alignItems: 'center' }}>
            <span className="meta-key">{t('MSP Pre-review')}</span>
            <span className="meta-val" style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className={`badge ${c.msp_review ? 'b-purple' : 'b-gray'}`} style={{ fontSize: 9 }}>{c.msp_review ? t('Enabled') : t('Off')}</span>
              {canToggle && (
                <button className="tb-btn" style={{ fontSize: 11, padding: '2px 8px' }} disabled={toggleReview.isPending}
                  onClick={() => toggleReview.mutate(!c.msp_review)}>
                  {c.msp_review ? t('Turn off') : t('Turn on')}
                </button>
              )}
            </span>
          </div>
          {canToggle && (
            <div className="page-sub" style={{ marginTop: 6, fontSize: 11 }}>
              {t('When ON, this client’s evidence goes to your MSP review queue before EVA. When OFF, it goes straight to EVA.')}
            </div>
          )}
        </div>
      </div>
    </>
  )
}

export default function ClientsPage() {
  const [selected, setSelected] = useState<string | null>(null)
  return selected
    ? <ClientDetail id={selected} onBack={() => setSelected(null)} />
    : <ClientList onOpen={setSelected} />
}
