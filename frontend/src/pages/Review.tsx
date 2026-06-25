import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import PreviewModal from '../components/PreviewModal'
import { useT } from '../lib/i18n'
import { Eye, ClipboardList, User, Calendar, HardDrive, MessageSquare } from 'lucide-react'

interface QItem {
  id: string; client: string; ctrl_ref: string; ctrl_name: string; ev_title: string
  ev_icon: string; by: string; submitted: string; size: string; framework: string; client_note: string
}
interface Action { action: string; label: string; cls: string }
interface QueueResp { stage: 'msp' | 'eva' | 'none'; actions: Action[]; items: QItem[]; clients: string[] }

export default function ReviewPage() {
  const qc = useQueryClient()
  const t = useT()
  const [clientFilter, setClientFilter] = useState('all')
  const [privacy, setPrivacy] = useState(false)
  const [notes, setNotes] = useState<Record<string, string>>({})
  const [preview, setPreview] = useState<{ id: string; title: string } | null>(null)

  const { data, isLoading, isError, error } = useQuery<QueueResp>({
    queryKey: ['review-queue'],
    queryFn: async () => (await api.get('/review/queue')).data,
  })

  const decide = useMutation({
    mutationFn: async ({ id, action }: { id: string; action: string }) =>
      (await api.post(`/review/${id}/decision`, { action, note: notes[id] || '' })).data,
    onSuccess: (_d, vars) => {
      toast.success(t('Decision recorded: {action}', { action: vars.action }))
      setNotes(n => { const c = { ...n }; delete c[vars.id]; return c })
      qc.invalidateQueries({ queryKey: ['review-queue'] })
      qc.invalidateQueries({ queryKey: ['evidence'] })
      qc.invalidateQueries({ queryKey: ['dashboard-summary'] })
      qc.invalidateQueries({ queryKey: ['controls'] })
    },
    onError: () => toast.error(t('Could not record decision')),
  })

  if (isLoading) return <div className="page-sub">{t('Loading review queue…')}</div>
  if (isError) {
    const status = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: status === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {status === 403 ? t('The review queue is available to MSP and EVA reviewer roles.') : t('Failed to load the review queue.')}
    </div>
  }
  if (!data) return null

  const { stage, actions, items, clients } = data
  const filtered = clientFilter === 'all' ? items : items.filter(i => i.client === clientFilter)
  const title = stage === 'msp' ? t('MSP Review Queue') : t('EVA Review Queue')
  const sub = stage === 'msp'
    ? t('{n} evidence items awaiting your pre-review before forwarding to EVA.', { n: items.length })
    : t('{n} evidence items awaiting EVA audit decision.', { n: items.length })
  const mask = (name: string) => (privacy && clientFilter !== name ? 'Client ●●●●●●' : name)

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{title}</div>
          <div className="page-sub">{sub}</div>
        </div>
        <div className="page-actions">
          <button onClick={() => setPrivacy(p => !p)}
            style={{
              display: 'inline-flex', alignItems: 'center', gap: 7, padding: '6px 12px', borderRadius: 7,
              border: `1px solid ${privacy ? '#EF4444' : 'var(--border-l)'}`,
              background: privacy ? '#FEE2E2' : 'var(--card)', color: privacy ? '#991B1B' : 'var(--text2)',
              fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)',
            }}>
            {privacy ? t('🔒 Privacy ON') : t('🔓 Privacy OFF')}
          </button>
        </div>
      </div>

      {clients.length > 1 && (
        <div className="queue-filters fi">
          <select className="filter-select" value={clientFilter} onChange={e => setClientFilter(e.target.value)} style={{ minWidth: 240, fontWeight: 600 }}>
            <option value="all">{t('All clients - {n} pending', { n: items.length })}</option>
            {clients.map(c => <option key={c} value={c}>{t('{name} - {n} pending', { name: mask(c), n: items.filter(i => i.client === c).length })}</option>)}
          </select>
          <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{t('{n} items showing', { n: filtered.length })}</span>
        </div>
      )}

      {filtered.map((q, i) => (
        <div key={q.id} className="queue-item fi" style={{ animationDelay: `${i * 0.05}s` }}>
          <div className="queue-item-hdr">
            <span className="queue-client" style={privacy && clientFilter !== q.client ? { filter: 'blur(4px)', userSelect: 'none' } : undefined}>{mask(q.client)}</span>
            <span className="queue-ref">{q.ctrl_ref}</span>
            <span style={{ fontSize: 16 }}>{q.ev_icon}</span>
            <span className="queue-ev-name">{q.ev_title}</span>
            <span className="badge b-amber">{stage === 'msp' ? t('Pending MSP Review') : t('Pending EVA Review')}</span>
            <span className="badge b-blue">{q.framework}</span>
          </div>
          <div className="queue-item-meta">
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><ClipboardList size={12} aria-hidden /> {q.ctrl_name}</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><User size={12} aria-hidden /> {q.by}</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><Calendar size={12} aria-hidden /> {q.submitted}</span>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}><HardDrive size={12} aria-hidden /> {q.size}</span>
          </div>
          {q.client_note && <div className="queue-client-note"><MessageSquare size={12} aria-hidden style={{ verticalAlign: 'text-bottom' }} /> <b>{q.by}:</b> "{q.client_note}"</div>}
          <div className="queue-actions">
            <button className="q-btn" style={{ background: '#EDE9FE', color: '#5B21B6', border: '1px solid #C4B5FD', display: 'inline-flex', alignItems: 'center', gap: 5 }}
              onClick={() => setPreview({ id: q.id, title: q.ev_title })}><Eye size={13} aria-hidden /> {t('Preview')}</button>
            {actions.map(a => (
              <button key={a.action} className={`q-btn ${a.cls}`} disabled={decide.isPending}
                onClick={() => decide.mutate({ id: q.id, action: a.action })}>
                {a.label}
              </button>
            ))}
            <input className="q-note" placeholder={stage === 'msp' ? t('Add MSP pre-review note…') : t('Add auditor note…')}
              value={notes[q.id] || ''} onChange={e => setNotes(n => ({ ...n, [q.id]: e.target.value }))} />
          </div>
        </div>
      ))}

      {filtered.length === 0 && (
        <div className="queue-empty">
          <div className="queue-empty-icon">✅</div>
          <div style={{ fontSize: 14, fontWeight: 500, color: 'var(--text2)' }}>{t('All caught up!')}</div>
          <div style={{ fontSize: 12, color: 'var(--text3)', marginTop: 4 }}>{t('No evidence items pending review.')}</div>
        </div>
      )}

      {preview && <PreviewModal id={preview.id} title={preview.title} onClose={() => setPreview(null)} />}
    </>
  )
}
