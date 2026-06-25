import { useRef, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { downloadEvidence } from '../lib/files'
import PreviewModal from '../components/PreviewModal'
import { useAuthStore } from '../store/auth'
import { useClientContext } from '../store/clientContext'
import { useT } from '../lib/i18n'

interface EvItem {
  id: string; title: string; icon: string; status: string; statusBadge: string; statusLabel: string
  ctrl_ref: string; by: string; date: string; size: string; freq: string; note: string | null
  can_submit: boolean; can_delete: boolean; has_file: boolean
}
interface EvResp { items: EvItem[]; counts: Record<string, number> }
interface CtrlItem { id: string; ref: string; title: string }

const FREQ_OPTS: [string, string][] = [
  ['once', 'One-time'], ['monthly', 'Monthly'], ['quarterly', 'Quarterly'],
  ['annual', 'Annual'], ['continuous', 'Continuous'],
]
const FILTERS: [string, string][] = [
  ['all', 'All'], ['accepted', 'Accepted'], ['submitted', 'Submitted'],
  ['needs_more', 'Needs more'], ['draft', 'Draft'],
]

export default function EvidencePage() {
  const qc = useQueryClient()
  const t = useT()
  const [filter, setFilter] = useState('all')
  const role = useAuthStore(s => s.user?.role || '')
  const isReviewer = ['super_admin', 'eva_auditor', 'msp_admin', 'msp_analyst'].includes(role)
  const clientId = useClientContext(s => s.clientId)

  // upload form state
  const [title, setTitle] = useState('')
  const [controlId, setControlId] = useState('')
  const [freq, setFreq] = useState('once')
  const [desc, setDesc] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [preview, setPreview] = useState<{ id: string; title: string } | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const { data, isLoading } = useQuery<EvResp>({
    queryKey: ['evidence'],
    queryFn: async () => (await api.get('/evidence/')).data,
  })
  const { data: controls } = useQuery<{ items: CtrlItem[] }>({
    queryKey: ['controls'],
    queryFn: async () => (await api.get('/controls/')).data,
  })

  const reset = () => { setTitle(''); setControlId(''); setFreq('once'); setDesc(''); setFile(null) }

  const upload = useMutation({
    mutationFn: async (submit: boolean) => {
      const fd = new FormData()
      fd.append('title', title)
      fd.append('control_id', controlId)
      fd.append('frequency', freq)
      fd.append('description', desc)
      fd.append('submit', String(submit))
      fd.append('file', file as File)
      return (await api.post('/evidence/upload', fd)).data
    },
    onSuccess: (_d, submit) => {
      toast.success(submit ? t('Uploaded & submitted for review') : t('Uploaded as draft'))
      reset()
      qc.invalidateQueries({ queryKey: ['evidence'] })
      qc.invalidateQueries({ queryKey: ['dashboard-summary'] })
      qc.invalidateQueries({ queryKey: ['controls'] })
    },
    onError: () => toast.error(t('Upload failed')),
  })

  const submitDraft = useMutation({
    mutationFn: async (id: string) => (await api.post(`/evidence/${id}/submit`)).data,
    onSuccess: () => { toast.success(t('Submitted for review')); qc.invalidateQueries({ queryKey: ['evidence'] }) },
    onError: () => toast.error(t('Submit failed')),
  })

  const remove = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/evidence/${id}`)).data,
    onSuccess: () => { toast.success(t('Draft deleted')); qc.invalidateQueries({ queryKey: ['evidence'] }) },
    onError: () => toast.error(t('Delete failed')),
  })

  const canUpload = Boolean(title.trim() && controlId && file) && !upload.isPending
  const items = (data?.items || []).filter(e =>
    filter === 'all' ? true
      : filter === 'submitted' ? ['client_submitted', 'msp_pending', 'eva_pending'].includes(e.status)
        : filter === 'needs_more' ? ['needs_more', 'rejected'].includes(e.status)
          : e.status === filter)
  const counts = data?.counts || { all: 0 }

  if (isReviewer && !clientId) return (
    <div className="detail-section" style={{ textAlign: 'center', padding: '48px 24px' }}>
      <div style={{ fontSize: 30 }}>🏢</div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>{t('Select a client to review')}</div>
      <div className="page-sub" style={{ marginTop: 4 }}>{t('Use the “Viewing client” selector in the top bar to load a client’s evidence.')}</div>
    </div>
  )

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Evidence')}</div>
          <div className="page-sub">{t('All evidence items across your assigned controls - {n} total', { n: counts.all })}</div>
        </div>
      </div>

      <div className="ev-page-grid fi">
        {/* Left: list */}
        <div>
          <div className="queue-filters">
            {FILTERS.map(([v, l]) => (
              <button key={v} onClick={() => setFilter(v)}
                style={{
                  padding: '5px 12px', borderRadius: 7,
                  border: `1px solid ${filter === v ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
                  background: filter === v ? 'var(--eva-blue2)' : 'var(--card)',
                  color: filter === v ? '#fff' : 'var(--text2)',
                  fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)',
                }}>
                {t(l)} <span style={{ opacity: .7 }}>({counts[v] || 0})</span>
              </button>
            ))}
          </div>

          {isLoading && <div className="page-sub">{t('Loading evidence…')}</div>}
          {!isLoading && items.length === 0 && (
            <div className="queue-empty">
              <div className="queue-empty-icon">📭</div>
              <div style={{ fontSize: 13, fontWeight: 500, color: 'var(--text2)' }}>{t('No evidence items match this filter')}</div>
            </div>
          )}

          {items.map(e => (
            <div key={e.id} className="ev-item-full">
              <div className="ev-item-hdr">
                <div className="ev-item-icon">{e.icon}</div>
                <span className="ev-item-name">{e.title}</span>
                <span className={`badge ${e.statusBadge}`}>{e.statusLabel}</span>
              </div>
              <div className="ev-item-meta">
                <span>🎯 {e.ctrl_ref}</span>
                <span>👤 {e.by}</span>
                <span>📅 {e.date}</span>
                <span>💾 {e.size}</span>
                <span>🔄 {e.freq}</span>
              </div>
              {e.note && <div className="ev-item-note">💬 {e.note}</div>}
              <div className="ev-item-actions">
                <button className="ev-action-btn" style={{ background: '#EDE9FE', color: '#5B21B6', borderColor: '#C4B5FD' }} disabled={!e.has_file} onClick={() => setPreview({ id: e.id, title: e.title })}>{t('👁 Preview')}</button>
                <button className="ev-action-btn download" disabled={!e.has_file} onClick={() => downloadEvidence(e.id, e.title)}>{t('⬇ Download')}</button>
                {e.can_submit && <button className="ev-action-btn submit" onClick={() => submitDraft.mutate(e.id)}>{t('✓ Submit')}</button>}
                {e.can_delete && <button className="ev-action-btn delete" onClick={() => remove.mutate(e.id)}>{t('🗑 Delete')}</button>}
              </div>
            </div>
          ))}
        </div>

        {/* Right: upload */}
        <div>
          <div className="ev-upload-card fi">
            <div className="card-hdr" style={{ marginBottom: 14 }}><span className="card-title">{t('Upload new evidence')}</span></div>
            <input ref={fileInput} type="file" hidden onChange={e => setFile(e.target.files?.[0] || null)} />
            <div className={`drop-zone ${dragging ? 'drag' : ''}`}
              onClick={() => fileInput.current?.click()}
              onDragOver={e => { e.preventDefault(); setDragging(true) }}
              onDragLeave={() => setDragging(false)}
              onDrop={e => { e.preventDefault(); setDragging(false); setFile(e.dataTransfer.files?.[0] || null) }}>
              <span className="drop-icon">{file ? '📎' : '📁'}</span>
              <div className="drop-title">{file ? file.name : t('Drop files here or click to browse')}</div>
              <div className="drop-sub">{file ? `${(file.size / 1024).toFixed(0)} KB` : t('Supports PDF, XLSX, PNG, DOCX, MP4')}</div>
              {!file && (
                <div className="file-type-chips">
                  {['PDF', 'XLSX', 'PNG', 'DOCX', 'MP4'].map(c => <span key={c} className="chip">{c}</span>)}
                </div>
              )}
            </div>

            <div className="ev-form">
              <div className="form-row">
                <label className="form-label">{t('Evidence title *')}</label>
                <input className="form-input" value={title} onChange={e => setTitle(e.target.value)} placeholder={t('e.g. Access Control Policy v2.4')} />
              </div>
              <div className="form-row">
                <label className="form-label">{t('Link to control *')}</label>
                <select className="form-select" value={controlId} onChange={e => setControlId(e.target.value)}>
                  <option value="">{t('Select a control…')}</option>
                  {(controls?.items || []).map(c => (
                    <option key={c.id} value={c.id}>{c.ref} - {c.title.slice(0, 40)}</option>
                  ))}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">{t('Collection frequency')}</label>
                <select className="form-select" value={freq} onChange={e => setFreq(e.target.value)}>
                  {FREQ_OPTS.map(([v, l]) => <option key={v} value={v}>{t(l)}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label className="form-label">{t('Description / notes')}</label>
                <textarea className="form-textarea" rows={3} value={desc} onChange={e => setDesc(e.target.value)} placeholder={t('What does this evidence demonstrate?')} />
              </div>
              <button className="submit-btn" style={{ justifyContent: 'center' }} disabled={!canUpload} onClick={() => upload.mutate(false)}>
                📤 {upload.isPending ? t('Uploading…') : t('Upload & save as draft')}
              </button>
              <button className="submit-btn" style={{ background: 'var(--green)', justifyContent: 'center' }} disabled={!canUpload} onClick={() => upload.mutate(true)}>
                {t('✓ Upload & submit for review')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {preview && <PreviewModal id={preview.id} title={preview.title} onClose={() => setPreview(null)} />}
    </>
  )
}
