import { useState, useMemo, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Plus, Download, Copy, Trash2, X, Image as ImageIcon, Check } from 'lucide-react'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Attach { id: string; content_type: string }
interface Req {
  id: string; title: string; body: string; category: string; category_label: string
  priority: string; status: string; status_label: string
  author_name: string; author_role: string | null; page_url: string | null
  resolution_note: string
  created_at: string | null; created_iso: string | null; attachments: Attach[]
}

const statusText = (s: string, t: (x: string) => string) =>
  t(s === 'open' ? 'Open' : s === 'in_progress' ? 'In progress' : s === 'done' ? 'Implemented' : "Won't fix")

const CAT_BADGE: Record<string, string> = { bug: 'b-red', idea: 'b-blue', question: 'b-amber', other: 'b-gray' }
const PRIO_BADGE: Record<string, string> = { high: 'b-red', medium: 'b-amber', low: 'b-gray' }
const STATUS_BADGE: Record<string, string> = { open: 'b-amber', in_progress: 'b-blue', done: 'b-green', wont_fix: 'b-gray' }
const STATUSES = ['open', 'in_progress', 'done', 'wont_fix']

// Plain-text form of a request, for pasting into Claude.
function asText(r: Req, t: (s: string) => string): string {
  const lines = [
    `[${r.category_label} · ${r.priority} · ${r.status_label}] ${r.title}`,
    r.page_url ? `${t('Where')}: ${r.page_url}` : '',
    `${t('By')} ${r.author_name}${r.author_role ? ` (${r.author_role.replace(/_/g, ' ')})` : ''}${r.created_at ? ` · ${r.created_at}` : ''}`,
    '',
    r.body || '(no description)',
    r.resolution_note ? `\n${t('Resolution')}: ${r.resolution_note}` : '',
    r.attachments.length ? `\n(${r.attachments.length} ${t('screenshot(s) attached - see the app or the Word export')})` : '',
  ]
  return lines.filter(l => l !== '').join('\n')
}

export default function ImprovementsPage() {
  const t = useT()
  const qc = useQueryClient()
  const [filter, setFilter] = useState('')
  const [open, setOpen] = useState<Req | null>(null)

  const { data, isLoading, isError, error } = useQuery<{ requests: Req[] }>({
    queryKey: ['improvements'],
    queryFn: async () => (await api.get('/improvements/')).data,
  })

  const patchReq = useMutation({
    mutationFn: async (v: { id: string; status?: string; resolution_note?: string }) => {
      const { id, ...fields } = v
      return (await api.patch(`/improvements/${id}`, fields)).data as Req
    },
    onSuccess: (d) => { qc.invalidateQueries({ queryKey: ['improvements'] }); if (open && d?.id === open.id) setOpen(d) },
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/improvements/${id}`)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['improvements'] }); setOpen(null); toast.success(t('Request deleted')) },
  })

  const copy = async (r: Req) => {
    try { await navigator.clipboard.writeText(asText(r, t)); toast.success(t('Copied to clipboard')) }
    catch { toast.error(t('Could not copy')) }
  }

  const exportAll = async () => {
    try {
      const res = await api.get('/improvements/export', { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url; a.download = 'EVA_Improvement_Log.docx'; a.click()
      URL.revokeObjectURL(url)
    } catch { toast.error(t('Export failed')) }
  }

  const list = useMemo(() => (data?.requests || []).filter(r => !filter || r.status === filter), [data, filter])

  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: 'var(--red)' }}>{s === 403 ? t('This tool is restricted to Super Admins.') : t('Failed to load requests.')}</div>
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div className="page-title">{t('Improvement / Requests')}</div>
          <div className="page-sub">{t('Internal log of fixes and ideas for the EVA team. Capture a screenshot with the camera button (top bar) or the keyboard shortcut.')}</div>
        </div>
        <div style={{ display: 'flex', gap: 8 }}>
          <button className="tb-btn" onClick={() => window.dispatchEvent(new CustomEvent('eva-open-devtool'))}>
            <Plus size={14} aria-hidden /> {t('New request')}
          </button>
          <button className="tb-btn" onClick={exportAll} disabled={!list.length}>
            <Download size={14} aria-hidden /> {t('Export all (Word)')}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', margin: '14px 0', alignItems: 'center' }}>
        <select className="filter-select" value={filter} onChange={e => setFilter(e.target.value)}>
          <option value="">{t('All statuses')}</option>
          {STATUSES.map(s => <option key={s} value={s}>{statusText(s, t)}</option>)}
        </select>
        <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{t('{n} request(s)', { n: list.length })}</span>
      </div>

      {isLoading ? <div className="page-sub">{t('Loading…')}</div> : !list.length ? (
        <div className="detail-section" style={{ textAlign: 'center', padding: '40px 24px' }}>
          <div style={{ fontSize: 28 }}>📝</div>
          <div style={{ fontSize: 14, fontWeight: 600, marginTop: 8 }}>{t('No requests yet')}</div>
          <div className="page-sub" style={{ marginTop: 4 }}>{t('Click “New request” or use the capture shortcut to log the first one.')}</div>
        </div>
      ) : (
        <div style={{ display: 'grid', gap: 10 }}>
          {list.map(r => (
            <div key={r.id} className="card" style={{ padding: 14 }}>
              <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12 }}>
                <div style={{ flex: 1, minWidth: 0, cursor: 'pointer' }} onClick={() => setOpen(r)}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 600, color: 'var(--text)' }}>{r.title}</span>
                    <span className={`badge ${STATUS_BADGE[r.status] || 'b-gray'}`} style={{ fontSize: 10 }}>{r.status_label}</span>
                    <span className={`badge ${CAT_BADGE[r.category] || 'b-gray'}`} style={{ fontSize: 10 }}>{r.category_label}</span>
                    <span className={`badge ${PRIO_BADGE[r.priority] || 'b-gray'}`} style={{ fontSize: 10 }}>{r.priority}</span>
                    {r.attachments.length > 0 && <span style={{ fontSize: 10, color: 'var(--text3)', display: 'inline-flex', alignItems: 'center', gap: 3 }}><ImageIcon size={11} aria-hidden /> {r.attachments.length}</span>}
                  </div>
                  {r.body && <div style={{ fontSize: 12.5, color: 'var(--text2)', marginTop: 4, display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{r.body}</div>}
                  <div style={{ fontSize: 10.5, color: 'var(--text3)', marginTop: 6 }}>
                    {r.author_name}{r.author_role ? ` · ${t(r.author_role.replace(/_/g, ' '))}` : ''}{r.created_at ? ` · ${r.created_at}` : ''}
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 6, flexShrink: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
                  <select value={r.status} onChange={e => patchReq.mutate({ id: r.id, status: e.target.value })}
                    style={{ fontSize: 11, padding: '4px 6px', borderRadius: 6, border: '1px solid var(--border-l)', background: 'var(--card)' }}>
                    {STATUSES.map(s => <option key={s} value={s}>{statusText(s, t)}</option>)}
                  </select>
                  <button className="tb-btn" onClick={() => copy(r)} title={t('Copy for Claude')}><Copy size={13} aria-hidden /></button>
                  <button className="tb-btn" style={{ color: 'var(--red)' }} onClick={() => { if (confirm(t('Delete this request?'))) del.mutate(r.id) }} title={t('Delete')}><Trash2 size={13} aria-hidden /></button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {open && <RequestDetail r={open} onClose={() => setOpen(null)} onCopy={() => copy(open)}
        onStatus={s => patchReq.mutate({ id: open.id, status: s })}
        onSaveNote={(note, markImplemented) => patchReq.mutate({ id: open.id, resolution_note: note, ...(markImplemented ? { status: 'done' } : {}) })}
        onDelete={() => { if (confirm(t('Delete this request?'))) del.mutate(open.id) }} />}
    </div>
  )
}

function RequestDetail({ r, onClose, onCopy, onStatus, onSaveNote, onDelete }: {
  r: Req; onClose: () => void; onCopy: () => void; onStatus: (s: string) => void
  onSaveNote: (note: string, markImplemented: boolean) => void; onDelete: () => void
}) {
  const t = useT()
  const [note, setNote] = useState(r.resolution_note || '')
  useEffect(() => { setNote(r.resolution_note || '') }, [r.resolution_note])
  // Attachments are behind a JWT-protected endpoint, so an <img src> won't work
  // (no Authorization header). Fetch each as a blob and render an object URL.
  const [urls, setUrls] = useState<Record<string, string>>({})
  useEffect(() => {
    let cancelled = false
    const made: string[] = []
    ;(async () => {
      for (const a of r.attachments) {
        try {
          const res = await api.get(`/improvements/${r.id}/attachments/${a.id}`, { responseType: 'blob' })
          if (cancelled) return
          const u = URL.createObjectURL(res.data); made.push(u)
          setUrls(prev => ({ ...prev, [a.id]: u }))
        } catch { /* skip */ }
      }
    })()
    return () => { cancelled = true; made.forEach(u => URL.revokeObjectURL(u)) }
  }, [r.id]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <div className="modal-overlay" style={{ zIndex: 60 }} onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 760, width: '92%', display: 'flex', flexDirection: 'column', maxHeight: '88vh' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '14px 18px', borderBottom: '1px solid var(--border, rgba(255,255,255,.12))' }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{r.title}</div>
          <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
            <select value={r.status} onChange={e => onStatus(e.target.value)}
              style={{ fontSize: 11, padding: '4px 6px', borderRadius: 6, border: '1px solid var(--border-l)', background: 'var(--card)' }}>
              {STATUSES.map(s => <option key={s} value={s}>{statusText(s, t)}</option>)}
            </select>
            <button className="tb-btn" onClick={onCopy} title={t('Copy for Claude')}><Copy size={13} aria-hidden /></button>
            <button className="tb-btn" style={{ color: 'var(--red)' }} onClick={onDelete} title={t('Delete')}><Trash2 size={13} aria-hidden /></button>
            <button className="tb-btn" style={{ padding: 4 }} onClick={onClose}><X size={16} aria-hidden /></button>
          </div>
        </div>
        <div style={{ padding: 18, overflowY: 'auto' }}>
          <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 10 }}>
            <span className={`badge ${CAT_BADGE[r.category] || 'b-gray'}`} style={{ fontSize: 10 }}>{r.category_label}</span>
            <span className={`badge ${PRIO_BADGE[r.priority] || 'b-gray'}`} style={{ fontSize: 10 }}>{r.priority}</span>
            {r.page_url && <span className="badge b-gray" style={{ fontSize: 10 }}>{r.page_url}</span>}
          </div>
          <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 12 }}>
            {r.author_name}{r.author_role ? ` · ${t(r.author_role.replace(/_/g, ' '))}` : ''}{r.created_at ? ` · ${r.created_at}` : ''}
          </div>
          <div style={{ fontSize: 13.5, color: 'var(--text)', lineHeight: 1.6, whiteSpace: 'pre-wrap', marginBottom: 16 }}>{r.body || t('(no description)')}</div>
          {r.attachments.map(a => (
            urls[a.id]
              ? <img key={a.id} src={urls[a.id]} alt="screenshot"
                  style={{ maxWidth: '100%', borderRadius: 8, border: '1px solid var(--border-l)', marginBottom: 10, display: 'block' }} />
              : <div key={a.id} className="page-sub" style={{ fontSize: 11, marginBottom: 10 }}>{t('Loading…')}</div>
          ))}

          {/* Resolution / closing note */}
          <div style={{ marginTop: 16, paddingTop: 14, borderTop: '1px solid var(--border-l)' }}>
            <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>{t('Resolution note')}</div>
            <textarea value={note} onChange={e => setNote(e.target.value)} rows={3}
              placeholder={t('How it was implemented, the commit, or any closing note…')}
              style={{ width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border-l)', background: 'var(--card)', color: 'var(--text)', fontSize: 12.5, resize: 'vertical' }} />
            <div style={{ display: 'flex', gap: 8, marginTop: 8, flexWrap: 'wrap' }}>
              <button className="submit-btn" onClick={() => onSaveNote(note, true)} style={{ justifyContent: 'center' }}>
                <Check size={14} aria-hidden /> {t('Mark implemented')}
              </button>
              <button className="tb-btn" onClick={() => onSaveNote(note, false)}>{t('Save note')}</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
