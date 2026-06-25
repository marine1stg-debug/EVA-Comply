import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import SupportThread, { type SupportCommentT } from '../components/SupportThread'

interface Config { enabled: boolean; categories: string[]; intro: string; can_configure: boolean }
interface Org { id: string; name: string; self: boolean }
interface Case {
  id: string; subject: string; category: string; message: string; status: string
  response: string | null; created_at: string; org_name?: string; comments: SupportCommentT[]
  has_attachment?: boolean; attachment_name?: string | null
}

const STATUS_BADGE: Record<string, string> = {
  open: 'b-amber', in_progress: 'b-blue', resolved: 'b-green', closed: 'b-gray',
}
const STATUS_LABEL: Record<string, string> = {
  open: 'Open', in_progress: 'In progress', resolved: 'Resolved', closed: 'Closed',
}

async function downloadAttachment(id: string, name: string) {
  const res = await api.get(`/support/cases/${id}/attachment`, { responseType: 'blob' })
  const url = URL.createObjectURL(res.data)
  const a = document.createElement('a'); a.href = url; a.download = name || 'attachment'; a.click()
  URL.revokeObjectURL(url)
}

export default function SupportPage() {
  const t = useT()
  const qc = useQueryClient()
  const { data: cfg } = useQuery<Config>({ queryKey: ['support-config'], queryFn: async () => (await api.get('/support/config')).data })
  const { data, isLoading } = useQuery<{ cases: Case[] }>({ queryKey: ['support-cases-mine'], queryFn: async () => (await api.get('/support/cases')).data })
  const { data: orgsData } = useQuery<{ orgs: Org[] }>({ queryKey: ['support-orgs'], queryFn: async () => (await api.get('/support/orgs')).data })
  const orgs = orgsData?.orgs || []

  const [category, setCategory] = useState('')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [orgId, setOrgId] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)
  useEffect(() => {
    if (!orgId && orgs.length) setOrgId((orgs.find(o => o.self) || orgs[0]).id)
  }, [orgsData]) // eslint-disable-line react-hooks/exhaustive-deps

  const submit = useMutation({
    mutationFn: async () => {
      const fd = new FormData()
      fd.append('subject', subject)
      fd.append('message', message)
      fd.append('category', category || (cfg?.categories?.[0] || 'Question'))
      if (orgId) fd.append('org_id', orgId)
      if (file) fd.append('file', file)
      return (await api.post('/support/cases', fd)).data
    },
    onSuccess: () => {
      toast.success(t('Request sent - the EVA team will review it'))
      setSubject(''); setMessage(''); setFile(null)
      if (fileInput.current) fileInput.current.value = ''
      qc.invalidateQueries({ queryKey: ['support-cases-mine'] })
      qc.invalidateQueries({ queryKey: ['notifications'] })
      qc.invalidateQueries({ queryKey: ['dash-support-open'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not send request')),
  })

  const ok = subject.trim() && message.trim()
  const cats = cfg?.categories || []
  const allCases = data?.cases || []
  const [filter, setFilter] = useState<string>('active')
  const cases = allCases.filter(c =>
    filter === 'all' ? true
      : filter === 'active' ? (c.status === 'open' || c.status === 'in_progress')
        : c.status === filter)
  const counts = {
    active: allCases.filter(c => c.status === 'open' || c.status === 'in_progress').length,
    closed: allCases.filter(c => c.status === 'closed' || c.status === 'resolved').length,
  }

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Contact Support')}</div>
          <div className="page-sub">{cfg?.intro ? t(cfg.intro) : t('Send the EVA team a request and track its status here.')}</div>
        </div>
      </div>

      <div className="fi" style={{ maxWidth: 820, display: 'flex', flexDirection: 'column', gap: 18 }}>
        {/* New request */}
        <div className="ev-upload-card">
          <div className="card-hdr" style={{ marginBottom: 12 }}><span className="card-title">{t('New request')}</span></div>
          {cfg && !cfg.enabled ? (
            <div className="page-sub">{t('Contact Support is currently unavailable. Please try again later.')}</div>
          ) : (
            <div className="ev-form">
              <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
                {orgs.length > 1 && (
                  <div className="form-row" style={{ flex: 1, minWidth: 180 }}>
                    <label className="form-label">{t('Request for')}</label>
                    <select className="form-select" value={orgId} onChange={e => setOrgId(e.target.value)}>
                      {orgs.map(o => <option key={o.id} value={o.id}>{o.name}{o.self ? ` ${t('(you)')}` : ''}</option>)}
                    </select>
                  </div>
                )}
                <div className="form-row" style={{ flex: 1, minWidth: 180 }}>
                  <label className="form-label">{t('Category')}</label>
                  <select className="form-select" value={category} onChange={e => setCategory(e.target.value)}>
                    {cats.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
              </div>
              <div className="form-row">
                <label className="form-label">{t('Subject')}</label>
                <input className="form-input" value={subject} onChange={e => setSubject(e.target.value)} placeholder={t('Brief summary of your request')} />
              </div>
              <div className="form-row">
                <label className="form-label">{t('Message')}</label>
                <textarea className="form-textarea" rows={5} value={message} onChange={e => setMessage(e.target.value)} placeholder={t('Describe your question or issue in detail…')} />
              </div>
              <div className="form-row">
                <label className="form-label">{t('Screenshot (optional)')}</label>
                <input ref={fileInput} type="file" accept="image/*,.pdf" style={{ display: 'none' }}
                  onChange={e => setFile(e.target.files?.[0] || null)} />
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                  <button type="button" className="tb-btn" onClick={() => fileInput.current?.click()}>
                    📎 {t('Choose a file')}
                  </button>
                  <span style={{ fontSize: 11.5, color: 'var(--text3)' }}>
                    {file ? `${file.name} (${(file.size / 1024).toFixed(0)} KB)` : t('No file selected')}
                  </span>
                  {file && (
                    <button type="button" className="ev-action-btn" title={t('Remove')}
                      onClick={() => { setFile(null); if (fileInput.current) fileInput.current.value = '' }}>✕</button>
                  )}
                </div>
              </div>
              <button className="submit-btn" style={{ justifyContent: 'center' }} disabled={!ok || submit.isPending} onClick={() => submit.mutate()}>
                {submit.isPending ? t('Sending…') : t('Send request')}
              </button>
            </div>
          )}
        </div>

        {/* My requests - below the new-request form */}
        <div>
          <div className="card-hdr" style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className="card-title">{t('Your requests')} ({cases.length})</span>
            <div style={{ flex: 1 }} />
            <select value={filter} onChange={e => setFilter(e.target.value)} className="form-input" style={{ width: 'auto', fontSize: 12 }}>
              <option value="active">{t('Open & in progress')} ({counts.active})</option>
              <option value="open">{t('Open')}</option>
              <option value="in_progress">{t('In progress')}</option>
              <option value="resolved">{t('Resolved')}</option>
              <option value="closed">{t('Closed')}</option>
              <option value="all">{t('All')} ({allCases.length})</option>
            </select>
          </div>
          {isLoading && <div className="page-sub">{t('Loading…')}</div>}
          {!isLoading && cases.length === 0 && (
            <div className="queue-empty"><div className="queue-empty-icon">📭</div><div className="page-sub">{t('No requests match this filter.')}</div></div>
          )}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {cases.map(c => {
              const done = c.status === 'closed' || c.status === 'resolved'
              return (
              <div key={c.id} className="ev-item-full" style={{ padding: '14px 16px', borderLeft: `3px solid ${done ? 'var(--border-l)' : 'var(--eva-blue2)'}`, opacity: done ? 0.72 : 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                  <span style={{ fontSize: 13.5, fontWeight: 600, flex: 1, minWidth: 0, textDecoration: done ? 'none' : 'none' }}>{c.subject}</span>
                  <span className={`badge ${STATUS_BADGE[c.status] || 'b-gray'}`}>{done ? '✓ ' : ''}{t(STATUS_LABEL[c.status] || c.status)}</span>
                </div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', fontSize: 10.5, color: 'var(--text3)', marginBottom: 8 }}>
                  <span className="badge b-gray" style={{ fontSize: 9 }}>{c.category}</span>
                  {c.org_name && <span>· {c.org_name}</span>}
                  <span>· {c.created_at}</span>
                </div>
                <div style={{ fontSize: 12.5, color: 'var(--text)', lineHeight: 1.55, background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 8, padding: '9px 11px' }}>{c.message}</div>
                {c.has_attachment && (
                  <button className="ev-action-btn download" style={{ marginTop: 8 }}
                    onClick={() => downloadAttachment(c.id, c.attachment_name || 'attachment')}>
                    📎 {c.attachment_name || t('Attachment')}
                  </button>
                )}
                <SupportThread caseId={c.id} comments={c.comments || []} invalidateKey={['support-cases-mine']} />
              </div>
            )})}
          </div>
        </div>
      </div>
    </>
  )
}
