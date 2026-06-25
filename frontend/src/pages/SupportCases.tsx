import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import SupportThread, { type SupportCommentT } from '../components/SupportThread'

interface Case {
  id: string; subject: string; category: string; message: string; status: string
  response: string | null; requester_name: string; requester_email: string; org_name: string; created_at: string
  comments: SupportCommentT[]
}
interface Config { enabled: boolean; categories: string[]; intro: string; can_configure: boolean }

const STATUS_BADGE: Record<string, string> = {
  open: 'b-amber', in_progress: 'b-blue', resolved: 'b-green', closed: 'b-gray',
}
const STATUS_LABEL: Record<string, string> = {
  open: 'Open', in_progress: 'In progress', resolved: 'Resolved', closed: 'Closed',
}
const STATUSES = ['open', 'in_progress', 'resolved', 'closed']

function ConfigCard() {
  const t = useT()
  const qc = useQueryClient()
  const { data } = useQuery<Config>({ queryKey: ['support-config'], queryFn: async () => (await api.get('/support/config')).data })
  const [enabled, setEnabled] = useState(true)
  const [cats, setCats] = useState('')
  const [intro, setIntro] = useState('')
  useEffect(() => { if (data) { setEnabled(data.enabled); setCats(data.categories.join(', ')); setIntro(data.intro) } }, [data])

  const save = useMutation({
    mutationFn: async () => (await api.put('/support/config', {
      enabled, categories: cats.split(',').map(c => c.trim()).filter(Boolean), intro,
    })).data,
    onSuccess: () => { toast.success(t('Support settings saved')); qc.invalidateQueries({ queryKey: ['support-config'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  if (!data || !data.can_configure) return null

  return (
    <div className="detail-section fi" style={{ marginBottom: 16, maxWidth: 720 }}>
      <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Contact Support settings')}</span>
        <span className={`badge ${enabled ? 'b-green' : 'b-gray'}`}>{enabled ? t('Enabled') : t('Disabled')}</span></div>
      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12, color: 'var(--text2)', marginBottom: 10 }}>
        <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} /> {t('Enable Contact Support for all users')}
      </label>
      <div className="form-row"><label className="form-label">{t('Request categories (comma-separated)')}</label>
        <input className="form-input" value={cats} onChange={e => setCats(e.target.value)} /></div>
      <div className="form-row" style={{ marginTop: 8 }}><label className="form-label">{t('Intro message shown on the form')}</label>
        <textarea className="form-textarea" rows={2} value={intro} onChange={e => setIntro(e.target.value)} /></div>
      <button className="submit-btn" style={{ marginTop: 12 }} disabled={save.isPending} onClick={() => save.mutate()}>
        {save.isPending ? t('Saving…') : t('Save settings')}
      </button>
    </div>
  )
}

function CaseRow({ c }: { c: Case }) {
  const t = useT()
  const qc = useQueryClient()
  const [status, setStatus] = useState(c.status)
  const setStatusMut = useMutation({
    mutationFn: async (s: string) => (await api.patch(`/support/cases/${c.id}`, { status: s })).data,
    onSuccess: () => {
      toast.success(t('Case updated'))
      qc.invalidateQueries({ queryKey: ['support-cases'] })
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['dash-support-open'] })
    },
    onError: () => toast.error(t('Save failed')),
  })
  const done = c.status === 'closed' || c.status === 'resolved'
  return (
    <div className="queue-item" style={{ borderLeft: `3px solid ${done ? 'var(--border-l)' : 'var(--eva-blue2)'}`, opacity: done ? 0.72 : 1 }}>
      <div className="queue-item-hdr">
        <span className="queue-client">{c.org_name || '-'}</span>
        <span className="badge b-gray" style={{ fontSize: 9 }}>{c.category}</span>
        <span className="queue-ev-name">{c.subject}</span>
        <span className={`badge ${STATUS_BADGE[c.status] || 'b-gray'}`}>{done ? '✓ ' : ''}{t(STATUS_LABEL[c.status] || c.status)}</span>
      </div>
      <div className="queue-item-meta">
        <span>👤 {c.requester_name}</span><span>✉ {c.requester_email}</span><span>📅 {c.created_at}</span>
      </div>
      <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.5, marginBottom: 4 }}>{c.message}</div>

      <SupportThread caseId={c.id} comments={c.comments || []} invalidateKey={['support-cases']} />

      <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 10 }}>
        <span style={{ fontSize: 11, color: 'var(--text3)' }}>{t('Status')}</span>
        <select className="filter-select" value={status}
          onChange={e => { setStatus(e.target.value); setStatusMut.mutate(e.target.value) }}>
          {STATUSES.map(s => <option key={s} value={s}>{t(STATUS_LABEL[s] || s)}</option>)}
        </select>
      </div>
    </div>
  )
}

export default function SupportCasesPage() {
  const t = useT()
  const [filter, setFilter] = useState('awaiting')
  const { data, isLoading, isError, error } = useQuery<{ cases: Case[]; is_admin: boolean }>({
    queryKey: ['support-cases'],
    queryFn: async () => (await api.get('/support/cases')).data,
  })

  if (isLoading) return <div className="page-sub">{t('Loading support cases…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('The support console requires EVA reviewer access.') : t('Failed to load support cases.')}
    </div>
  }
  if (!data) return null

  const awaiting = data.cases.filter(c => c.status === 'open' || c.status === 'in_progress')
  const cases = data.cases.filter(c =>
    filter === 'all' ? true
      : filter === 'awaiting' ? (c.status === 'open' || c.status === 'in_progress')
        : c.status === filter)

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Support Console')}</div>
          <div className="page-sub">{t('Review and respond to support requests from clients and MSPs.')}</div>
        </div>
      </div>

      <ConfigCard />

      <div className="filter-bar fi">
        <select className="filter-select" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="awaiting">{t('Awaiting our reply')} ({awaiting.length})</option>
          <option value="open">{t('Open')}</option>
          <option value="in_progress">{t('In progress')}</option>
          <option value="resolved">{t('Resolved')}</option>
          <option value="closed">{t('Closed')}</option>
          <option value="all">{t('All statuses')} ({data.cases.length})</option>
        </select>
        <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{t('{n} cases', { n: cases.length })}</span>
      </div>

      {cases.length === 0 && (
        <div className="queue-empty"><div className="queue-empty-icon">✅</div><div className="page-sub">{t('No cases match this filter.')}</div></div>
      )}
      {cases.map(c => <CaseRow key={c.id} c={c} />)}
    </>
  )
}
