import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Provider {
  id: string; name: string; contact_name: string; contact_email: string; website: string
  skills: string[]; priority_weight: number; status: string; notes: string
}
interface Resp { providers: Provider[]; skills: string[] }

const STATUS_BADGE: Record<string, string> = { active: 'b-green', pending: 'b-amber', suspended: 'b-gray' }

function ProviderModal({ provider, skills, onClose }: { provider: Provider | null; skills: string[]; onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const isNew = !provider
  const [name, setName] = useState(provider?.name || '')
  const [contactName, setContactName] = useState(provider?.contact_name || '')
  const [email, setEmail] = useState(provider?.contact_email || '')
  const [website, setWebsite] = useState(provider?.website || '')
  const [weight, setWeight] = useState(provider?.priority_weight ?? 0)
  const [status, setStatus] = useState(provider?.status || 'active')
  const [sel, setSel] = useState<string[]>(provider?.skills || [])
  const body = () => ({ name, contact_name: contactName, contact_email: email, website, priority_weight: weight, status, skills: sel })
  const save = useMutation({
    mutationFn: async () => isNew
      ? (await api.post('/marketplace/providers', body())).data
      : (await api.put(`/marketplace/providers/${provider!.id}`, body())).data,
    onSuccess: () => { toast.success(t('Saved')); qc.invalidateQueries({ queryKey: ['providers'] }); onClose() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const toggle = (s: string) => setSel(v => v.includes(s) ? v.filter(x => x !== s) : [...v, s])
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 560 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{isNew ? t('New provider') : t('Edit provider')}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
            <div className="form-row" style={{ flex: 2, minWidth: 200 }}><label className="form-label">{t('Provider name')}</label><input className="form-input" value={name} onChange={e => setName(e.target.value)} /></div>
            <div className="form-row" style={{ width: 120 }}><label className="form-label">{t('Priority weight')}</label><input className="form-input" type="number" value={weight} onChange={e => setWeight(Number(e.target.value))} /></div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 8 }}>
            <div className="form-row" style={{ flex: 1, minWidth: 160 }}><label className="form-label">{t('Contact name')}</label><input className="form-input" value={contactName} onChange={e => setContactName(e.target.value)} /></div>
            <div className="form-row" style={{ flex: 1, minWidth: 160 }}><label className="form-label">{t('Contact email')}</label><input className="form-input" value={email} onChange={e => setEmail(e.target.value)} /></div>
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', marginTop: 8, alignItems: 'flex-end' }}>
            <div className="form-row" style={{ flex: 2, minWidth: 200 }}><label className="form-label">{t('Website')}</label><input className="form-input" value={website} onChange={e => setWebsite(e.target.value)} placeholder="https://" /></div>
            <div className="form-row" style={{ width: 150 }}><label className="form-label">{t('Status')}</label>
              <select className="form-select" value={status} onChange={e => setStatus(e.target.value)}>
                <option value="active">{t('Active')}</option><option value="pending">{t('Pending')}</option><option value="suspended">{t('Suspended')}</option>
              </select>
            </div>
          </div>
          <div className="form-label" style={{ marginTop: 14 }}>{t('Skills (control domains they cover)')}</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginTop: 4, maxHeight: 180, overflow: 'auto' }}>
            {skills.map(s => (
              <label key={s} onClick={() => toggle(s)} style={{ cursor: 'pointer', fontSize: 11, padding: '4px 9px', borderRadius: 14,
                border: `1px solid ${sel.includes(s) ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
                background: sel.includes(s) ? 'var(--soft)' : 'var(--card)', color: sel.includes(s) ? 'var(--brand)' : 'var(--text2)' }}>
                {sel.includes(s) ? '✓ ' : ''}{s}
              </label>
            ))}
            {skills.length === 0 && <span className="page-sub">{t('No control domains found yet.')}</span>}
          </div>
          <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 16 }} disabled={!name.trim() || save.isPending} onClick={() => save.mutate()}>
            {save.isPending ? t('Saving…') : isNew ? t('Create provider') : t('Save changes')}
          </button>
        </div>
      </div>
    </div>
  )
}

function CustomSkills() {
  const qc = useQueryClient()
  const t = useT()
  const [name, setName] = useState('')
  const { data } = useQuery<{ skills: { id: string; name: string }[] }>({
    queryKey: ['custom-skills'], queryFn: async () => (await api.get('/marketplace/custom-skills')).data,
  })
  const after = () => { qc.invalidateQueries({ queryKey: ['custom-skills'] }); qc.invalidateQueries({ queryKey: ['providers'] }) }
  const add = useMutation({
    mutationFn: async () => (await api.post('/marketplace/custom-skills', { name })).data,
    onSuccess: () => { toast.success(t('Skill added')); setName(''); after() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/marketplace/custom-skills/${id}`)).data,
    onSuccess: after,
  })
  return (
    <div className="detail-section fi" style={{ marginBottom: 16 }}>
      <div className="card-hdr" style={{ marginBottom: 8 }}><span className="card-title">{t('Custom skills')}</span>
        <span className="page-sub" style={{ fontSize: 10.5 }}>{t('Extra skills beyond control domains (e.g. Backup, DRP)')}</span></div>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 10 }}>
        {(data?.skills || []).map(s => (
          <span key={s.id} style={{ fontSize: 11, padding: '4px 9px', borderRadius: 14, border: '1px solid var(--border-l)', background: 'var(--soft)', color: 'var(--text2)', display: 'inline-flex', gap: 6, alignItems: 'center' }}>
            {s.name}
            <span style={{ cursor: 'pointer', color: 'var(--text3)' }} onClick={() => del.mutate(s.id)}>✕</span>
          </span>
        ))}
        {(data?.skills || []).length === 0 && <span className="page-sub">{t('No custom skills yet.')}</span>}
      </div>
      <div style={{ display: 'flex', gap: 8 }}>
        <input className="form-input" style={{ maxWidth: 320, fontSize: 12 }} value={name} onChange={e => setName(e.target.value)}
          placeholder={t('e.g. Backup & Recovery, DRP, vCISO…')} onKeyDown={e => { if (e.key === 'Enter' && name.trim()) add.mutate() }} />
        <button className="tb-btn" disabled={!name.trim() || add.isPending} onClick={() => add.mutate()}>{t('+ Add skill')}</button>
      </div>
    </div>
  )
}

export default function ServiceProvidersPage() {
  const qc = useQueryClient()
  const t = useT()
  const [editing, setEditing] = useState<Provider | null | undefined>(undefined)
  const { data, isLoading, isError, error } = useQuery<Resp>({
    queryKey: ['providers'], queryFn: async () => (await api.get('/marketplace/providers')).data,
  })
  const authorize = useMutation({
    mutationFn: async (id: string) => (await api.post(`/marketplace/providers/${id}/authorize`)).data,
    onSuccess: () => { toast.success(t('Provider authorized')); qc.invalidateQueries({ queryKey: ['providers'] }) },
    onError: () => toast.error(t('Update failed')),
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/marketplace/providers/${id}`)).data,
    onSuccess: () => { toast.success(t('Provider deleted')); qc.invalidateQueries({ queryKey: ['providers'] }) },
    onError: () => toast.error(t('Delete failed')),
  })

  if (isLoading) return <div className="page-sub">{t('Loading…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('The provider marketplace requires Super Admin access.') : t('Failed to load providers.')}
    </div>
  }
  if (!data) return null

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Service Providers')}</div>
          <div className="page-sub">{t('Partners who can help clients implement controls. Authorize them, set a priority weight, and the skills they cover.')}</div>
        </div>
        <div className="page-actions"><button className="tb-btn pri" onClick={() => setEditing(null)}>{t('+ Add provider')}</button></div>
      </div>

      <CustomSkills />

      <div className="detail-section fi">
        <table className="tenant-table">
          <thead><tr><th>{t('Provider')}</th><th>{t('Skills')}</th><th>{t('Weight')}</th><th>{t('Status')}</th><th>{t('Actions')}</th></tr></thead>
          <tbody>
            {data.providers.map(p => (
              <tr key={p.id}>
                <td>
                  <div style={{ fontWeight: 600 }}>{p.name}</div>
                  <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>{p.contact_email}{p.website ? ` · ${p.website}` : ''}</div>
                </td>
                <td style={{ fontSize: 11, maxWidth: 280 }}>{(p.skills || []).join(', ') || '-'}</td>
                <td style={{ fontWeight: 700 }}>{p.priority_weight}</td>
                <td><span className={`badge ${STATUS_BADGE[p.status] || 'b-gray'}`}>{t(p.status)}</span></td>
                <td>
                  <div style={{ display: 'flex', gap: 5, flexWrap: 'wrap' }}>
                    {p.status === 'pending' && <button className="ev-action-btn" style={{ fontSize: 10, padding: '3px 8px', background: '#DCFCE7', color: '#166534', borderColor: '#86EFAC' }} onClick={() => authorize.mutate(p.id)}>✓ {t('Authorize')}</button>}
                    <button className="ev-action-btn" style={{ fontSize: 10, padding: '3px 8px' }} onClick={() => setEditing(p)}>{t('Edit')}</button>
                    <button className="ev-action-btn delete" style={{ fontSize: 10, padding: '3px 8px' }} onClick={() => { if (window.confirm(t('Delete {name}?', { name: p.name }))) del.mutate(p.id) }}>{t('Delete')}</button>
                  </div>
                </td>
              </tr>
            ))}
            {data.providers.length === 0 && <tr><td colSpan={5}><div className="page-sub">{t('No providers yet.')}</div></td></tr>}
          </tbody>
        </table>
      </div>

      {editing !== undefined && <ProviderModal provider={editing} skills={data.skills} onClose={() => setEditing(undefined)} />}
    </>
  )
}
