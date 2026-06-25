import { useState, useRef, useEffect, type ChangeEvent } from 'react'
import { useSearchParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useClientContext } from '../store/clientContext'
import { useUnsavedGuard } from '../store/unsavedGuard'
import { downloadEvidence, downloadPolicyTemplate } from '../lib/files'
import PreviewModal from '../components/PreviewModal'
import { Eye, Download, Trash2, FileText } from 'lucide-react'
import { useT, useI18n } from '../lib/i18n'
import { VideoPlayer, type VideoRef } from '../lib/video'
import { createPortal } from 'react-dom'

function HelpModal({ controlId, domain, onClose }: { controlId: string; domain: string; onClose: () => void }) {
  const t = useT()
  const { data, isLoading } = useQuery<any>({
    queryKey: ['help', controlId],
    queryFn: async () => (await api.get('/marketplace/help', { params: { control_id: controlId } })).data,
  })
  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 520 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Get help')}{domain ? ` — ${domain}` : ''}</span><button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          {isLoading ? <div className="page-sub">{t('Loading…')}</div>
            : !data || !data.providers?.length
              ? <div className="page-sub">{t('No matching providers yet — check back soon.')}</div>
              : <>
                  <div className="page-sub" style={{ marginBottom: 10 }}>
                    {data.exact ? t('Providers who can help, best match first:') : t('No exact match — here are available providers:')}
                  </div>
                  {data.providers.map((p: any) => (
                    <div key={p.id} style={{ border: '1px solid var(--border-l)', borderRadius: 8, padding: '10px 12px', marginBottom: 8 }}>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{p.name}</div>
                      {p.skills?.length > 0 && <div style={{ fontSize: 10.5, color: 'var(--text3)', marginTop: 2 }}>{p.skills.join(', ')}</div>}
                      <div style={{ display: 'flex', gap: 8, marginTop: 6 }}>
                        {p.contact_email && <a href={`mailto:${p.contact_email}`} className="ev-action-btn download">✉ {t('Contact')}</a>}
                        {p.website && <a href={p.website} target="_blank" rel="noreferrer" className="ev-action-btn">🌐 {t('Website')}</a>}
                      </div>
                    </div>
                  ))}
                </>}
        </div>
      </div>
    </div>,
    document.body,
  )
}

interface ListItem {
  id: string; ref: string; title: string; framework: string; domain: string; level: string
  priority: string; risk: string; category: string; status: string
  statusBadge: string; priorityBadge: string; coverage: number
  audit_status: string; audit_status_label: string; audit_status_badge: string
  returned_count: number; needs_action: boolean
  evidence_count: number; evidence_expected: number; owner: string | null; due: string | null
  policy_template?: string | null
}
interface ListResp {
  items: ListItem[]; domains: string[]; frameworks: string[]
  summary: { total_evidence: number; collected_evidence: number; complete: number; missing: number }
}
interface EvItem {
  id: string; title: string; status: string; statusBadge: string; by: string; date: string; note: string | null
  review_state: string; review_note: string | null; file_name: string | null; file_size: number | null; can_preview: boolean
}
interface StatusOption { value: string; label: string }
interface Detail {
  id: string; ref: string; title: string; domain: string; level: string; category: string; framework: string
  priority: string; priorityBadge: string; risk: string; riskBadge: string; status: string; statusBadge: string
  coverage: number; owner: string | null; due: string | null; plain_language: string; objective: string; description: string; discussion: string
  english?: { title: string; plain_language: string; objective: string; description: string; discussion: string; best_practices: string[]; expected_evidence: string[] }
  fr_available?: boolean
  video?: VideoRef
  can_coach?: boolean; under_review?: boolean; under_review_note?: string | null
  best_practices: string[]; expected_evidence: string[]; evidence_count: number; evidence_expected: number; evidence: EvItem[]
  mappings: Record<string, string[]>
  status_source: string; expected_valid: number; expected_total: number
  policy_template?: string | null
  audit_status: string; audit_status_label: string; audit_status_badge: string
  status_mode: string; status_note: string | null; previous_audit_notes: string | null
  audit_status_options: StatusOption[]; can_review: boolean
}
interface ExpEvidence { evidence_id: string; file_name: string | null; status: string; review_note: string | null; can_preview: boolean }
interface ExpItem { id: string; text: string; frequency: string; evidence_type: string; origin: string; satisfied: boolean; state: string; evidence: ExpEvidence | null }
interface EventItem { id: string; action: string; label: string; detail: string | null; actor: string; date: string }
interface SAOption { key: string; level: number; short: string; label: string }
interface SAQuestion { key: string; prompt: string; options: SAOption[] }
interface SAResp { questions: SAQuestion[]; english?: SAQuestion[]; fr_available?: boolean; answers: Record<string, number>; comment: string | null; perceived_level: number | null; scale_max: number }
interface ExpResp {
  items: ExpItem[]; coverage: number; status: string; statusBadge: string; status_source: string
  valid: number; total: number; frequencies: string[]; types: string[]
}
interface Reco {
  id: string; source: string; title: string; text: string; effort: string; impact: string
  current_level: number | null; target_level: number | null; gap: number | null
  status: string; quick_win: boolean; priority: number
}
interface RecResp { recommendations: Reco[]; can_generate: boolean; has_llm: boolean }
const FREQ_LABEL: Record<string, string> = {
  once: 'One-time', monthly: 'Monthly', quarterly: 'Quarterly',
  semi_annual: 'Semi-annual', annual: 'Annual', continuous: 'Continuous',
}
// Evidence types use a dedicated FR map (not the global t()) because some values
// like "Record"/"Report" collide with verbs/labels used elsewhere in the app.
const TYPE_FR: Record<string, string> = {
  Document: 'Document', Policy: 'Politique', Screenshot: 'Capture d’écran',
  Log: 'Journal', Configuration: 'Configuration', Report: 'Rapport',
  Record: 'Registre', Other: 'Autre',
}
const selStyle = { fontSize: 11, padding: '3px 6px', border: '1px solid var(--border-l)', borderRadius: 6, color: 'var(--text2)', background: 'var(--card)' }
const EE_STATE: Record<string, { bg: string; dot: string; badge: string; label: string }> = {
  missing:   { bg: 'rgba(220,38,38,.10)', dot: '#EF4444', badge: 'b-red',    label: 'missing' },
  submitted: { bg: 'rgba(37,99,235,.12)', dot: '#3B82F6', badge: 'b-blue',   label: 'submitted' },
  accepted:  { bg: 'rgba(22,163,74,.12)', dot: '#22C55E', badge: 'b-green',  label: 'accepted' },
  returned:  { bg: 'rgba(234,88,12,.12)', dot: '#F97316', badge: 'b-orange', label: 'returned — action needed' },
}

const STATUS_LABEL: Record<string, string> = {
  not_started: 'Not started', in_progress: 'In progress',
  implemented: 'Implemented', verified: 'Verified', non_applicable: 'N/A',
}
const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)
// Framework-mapping display: legacy seed keys → friendly labels; others shown as-is.
const MAP_LABEL: Record<string, string> = { nist_csf: 'NIST CSF', cyber_canada: 'Cyber Canada' }
const MAP_BADGE = ['b-blue', 'b-teal', 'b-green', 'b-amber', 'b-orange']
const progressColor = (p: number) => (p >= 80 ? '#16A34A' : p >= 40 ? '#D97706' : '#DC2626')

/* ───────────────────────── LIST ───────────────────────── */
function ControlsList({ onOpen }: { onOpen: (id: string) => void }) {
  const t = useT()
  const [search, setSearch] = useState('')
  const [framework, setFramework] = useState('')
  const [domain, setDomain] = useState('')
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [review, setReview] = useState('')
  const role = useAuthStore(s => s.user?.role || '')
  const isReviewer = ['super_admin', 'eva_auditor', 'msp_admin', 'msp_analyst'].includes(role)
  const clientId = useClientContext(s => s.clientId)
  const lang = useI18n(s => s.lang)
  const [exporting, setExporting] = useState(false)

  // Quick export: an Excel evidence register + all evidence files, zipped
  // (same bundle as Reports › Evidence Register), scoped to the current client.
  const exportEvidence = async () => {
    setExporting(true)
    try {
      const res = await api.post('/reports/generate', { report_type: 'evidence', format: 'xlsx' }, { responseType: 'blob' })
      const cd = res.headers['content-disposition'] || ''
      const m = /filename="([^"]+)"/.exec(cd)
      const name = m ? m[1] : `evidence_export_${new Date().toISOString().slice(0, 10)}.zip`
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a'); a.href = url; a.download = name; a.click()
      URL.revokeObjectURL(url)
      toast.success(t('Export ready'))
    } catch (e: any) {
      let msg = t('Could not export')
      try { msg = JSON.parse(await e?.response?.data?.text())?.detail || msg } catch { /* keep */ }
      toast.error(msg)
    } finally { setExporting(false) }
  }

  const { data, isLoading, isError } = useQuery<ListResp>({
    queryKey: ['controls', lang],
    queryFn: async () => (await api.get('/controls/')).data,
    enabled: !isReviewer || !!clientId,
  })

  if (isReviewer && !clientId) return (
    <div className="detail-section" style={{ textAlign: 'center', padding: '48px 24px' }}>
      <div style={{ fontSize: 30 }}>🏢</div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>{t('Select a client to review')}</div>
      <div className="page-sub" style={{ marginTop: 4 }}>{t('Use the “Viewing client” selector in the top bar to load a client’s controls.')}</div>
    </div>
  )
  if (isLoading) return <div className="page-sub">{t('Loading controls…')}</div>
  if (isError || !data) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load controls.')}</div>

  const { summary } = data
  const evPct = summary.total_evidence ? Math.round(summary.collected_evidence / summary.total_evidence * 100) : 0
  const filtered = data.items.filter(c => {
    if (framework && c.framework !== framework) return false
    if (search && !c.title.toLowerCase().includes(search.toLowerCase()) && !c.ref.toLowerCase().includes(search.toLowerCase())) return false
    if (domain && c.domain !== domain) return false
    if (status && c.audit_status !== status) return false
    if (priority && c.priority !== priority) return false
    if (review === 'needs_action' && !c.needs_action) return false
    return true
  })
  const needsActionTotal = data.items.filter(c => c.needs_action).length

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Controls')}</div>
          <div className="page-sub">{t('Track implementation and evidence across every control.')}</div>
        </div>
        <div className="page-actions">
          <button className="tb-btn pri" disabled={exporting} onClick={exportEvidence}
            title={t('Download an Excel evidence register + a ZIP of all evidence files for this client')}>
            📊 {exporting ? t('Exporting…') : t('Export evidence (XLSX + ZIP)')}
          </button>
        </div>
      </div>

      {/* Evidence summary */}
      <div className="ev-summary-bar fi">
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)' }}>📎 {t('Evidence collected')}</span>
        <div className="ev-bar-track"><div className="ev-bar-fill" style={{ width: `${evPct}%` }} /></div>
        <span style={{ fontSize: 12, fontWeight: 600, color: 'var(--eva-blue2)' }}>{t('{a} of {b}', { a: summary.collected_evidence, b: summary.total_evidence })}</span>
        <span className="badge b-green">{t('{n} complete', { n: summary.complete })}</span>
        <span className="badge b-red">{t('{n} missing', { n: summary.missing })}</span>
      </div>

      {/* Framework selector */}
      {data.frameworks.length > 0 && (
        <div className="tab-bar fi" style={{ marginBottom: 12, display: 'inline-flex' }}>
          <button className={`tab ${framework === '' ? 'active' : ''}`} style={{ flex: 'none', padding: '6px 14px' }} onClick={() => setFramework('')}>{t('All frameworks')}</button>
          {data.frameworks.map(f => (
            <button key={f} className={`tab ${framework === f ? 'active' : ''}`} style={{ flex: 'none', padding: '6px 14px' }} onClick={() => setFramework(f)}>{f}</button>
          ))}
        </div>
      )}

      {/* Filters */}
      <div className="filter-bar fi">
        <div className="search-box">
          <span className="search-icon">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
          </span>
          <input placeholder={t('Search controls…')} value={search} onChange={e => setSearch(e.target.value)} />
        </div>
        <select className="filter-select" value={domain} onChange={e => setDomain(e.target.value)}>
          <option value="">{t('All domains')}</option>
          {data.domains.map(d => <option key={d} value={d}>{d}</option>)}
        </select>
        <select className="filter-select" value={status} onChange={e => setStatus(e.target.value)}>
          <option value="">{t('All statuses')}</option>
          <option value="not_started">{t('Not Started')}</option>
          <option value="in_progress">{t('In Progress')}</option>
          <option value="compliant">{t('Compliant')}</option>
          <option value="non_compliant">{t('Non-Compliant')}</option>
          <option value="not_applicable">{t('Not Applicable')}</option>
        </select>
        <select className="filter-select" value={priority} onChange={e => setPriority(e.target.value)}>
          <option value="">{t('All priorities')}</option>
          <option value="high">{t('High')}</option>
          <option value="medium">{t('Medium')}</option>
          <option value="low">{t('Low')}</option>
        </select>
        <select className="filter-select" value={review} onChange={e => setReview(e.target.value)}
          style={needsActionTotal > 0 && review !== 'needs_action' ? { borderColor: '#FCA5A5', color: '#991B1B', fontWeight: 600 } : undefined}>
          <option value="">{t('Auditor review')}</option>
          <option value="needs_action">{needsActionTotal > 0 ? t('↩ Returned to me ({n})', { n: needsActionTotal }) : t('↩ Returned to me')}</option>
        </select>
        <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{t('{filtered} of {total} controls', { filtered: filtered.length, total: data.items.length })}</span>
      </div>

      {/* Table */}
      <div className="ctrl-table fi">
        {filtered.map(c => (
          <div key={c.id} className="ctrl-row" onClick={() => onOpen(c.id)}>
            <span className="ctrl-ref">{c.ref}</span>
            <div className="ctrl-info">
              <div className="ctrl-title">
                {c.title}
                {c.policy_template && <span title={`Policy template available: ${c.policy_template}`} style={{ marginLeft: 6, cursor: 'help' }}>📄</span>}
              </div>
              <div className="ctrl-meta">
                <span className="ctrl-domain">{c.domain}</span>
                <span style={{ color: '#CBD5E1', fontSize: 10 }}>·</span>
                <div className="prog-mini">
                  <div className="prog-mini-bar"><div className="prog-mini-fill" style={{ width: `${c.coverage}%`, background: progressColor(c.coverage) }} /></div>
                  <span className="prog-mini-pct">{c.coverage}%</span>
                </div>
                <span className="ev-count">📎 {c.evidence_count}/{c.evidence_expected}</span>
                {c.needs_action && (
                  <span className="badge b-red" style={{ fontSize: 9 }} title="The auditor returned evidence for you to address">{t('↩ Returned ({n})', { n: c.returned_count })}</span>
                )}
              </div>
            </div>
            <div className="ctrl-right">
              <span className={`badge ${c.audit_status_badge}`}>{c.audit_status_label}</span>
              <span className={`badge ${c.priorityBadge}`}>{cap(c.priority)}</span>
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#CBD5E1" strokeWidth="2"><polyline points="9 18 15 12 9 6" /></svg>
            </div>
          </div>
        ))}
        {filtered.length === 0 && <div style={{ textAlign: 'center', padding: 32, color: 'var(--text3)', fontSize: 13 }}>{t('No controls match the current filters.')}</div>}
      </div>
    </>
  )
}

/* ───────────────────────── DETAIL ───────────────────────── */
function MiniRing({ pct }: { pct: number }) {
  const t = useT()
  const r = 27, c = 2 * Math.PI * r, col = progressColor(pct)
  return (
    <div style={{ position: 'relative', width: 70, height: 70, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width="70" height="70" viewBox="0 0 70 70" style={{ transform: 'rotate(-90deg)' }}>
        <circle cx="35" cy="35" r={r} fill="none" stroke="#F1F5F9" strokeWidth="7" />
        <circle cx="35" cy="35" r={r} fill="none" stroke={col} strokeWidth="7" strokeDasharray={c} strokeDashoffset={c * (1 - pct / 100)} strokeLinecap="round" />
      </svg>
      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', textAlign: 'center' }}>
        <div style={{ fontSize: 14, fontWeight: 600, color: col }}>{pct}%</div>
        <div style={{ fontSize: 8, color: 'var(--text3)' }}>{t('Coverage').toLowerCase()}</div>
      </div>
    </div>
  )
}

function StatusEditor({ c, onSave, onCancel, busy }: {
  c: Detail
  onSave: (mode: 'auto' | 'manual', status?: string, note?: string) => void
  onCancel: () => void
  busy: boolean
}) {
  const t = useT()
  const [sel, setSel] = useState(c.audit_status)
  const [note, setNote] = useState(c.status_note || '')
  return (
    <div style={{ width: '100%', marginTop: 8, background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 'var(--r)', padding: 12 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
        <select value={sel} onChange={e => setSel(e.target.value)} style={{ ...selStyle, fontSize: 12, padding: '5px 8px' }}>
          {c.audit_status_options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <input value={note} onChange={e => setNote(e.target.value)} placeholder={t('Comment (optional)')}
          style={{ flex: 1, minWidth: 180, fontSize: 12, padding: '5px 8px', border: '1px solid var(--border-l)', borderRadius: 6 }} />
        <button disabled={busy} onClick={() => onSave('manual', sel, note)}
          style={{ fontSize: 11, fontWeight: 600, padding: '5px 12px', borderRadius: 6, border: '1px solid var(--eva-blue2)', background: 'var(--eva-blue2)', color: '#fff', cursor: 'pointer' }}>{t('Save')}</button>
        <button disabled={busy} onClick={onCancel}
          style={{ fontSize: 11, padding: '5px 10px', borderRadius: 6, border: '1px solid var(--border-l)', background: 'var(--card)', cursor: 'pointer' }}>{t('Cancel')}</button>
      </div>
      {c.status_mode === 'manual' && (
        <button disabled={busy} onClick={() => onSave('auto')}
          style={{ marginTop: 8, fontSize: 11, color: 'var(--text3)', background: 'none', border: 'none', cursor: 'pointer', textDecoration: 'underline' }}>
          {t('↺ Revert to auto (derive from evidence)')}
        </button>
      )}
    </div>
  )
}

function ControlDetail({ id, onBack, onOpen }: { id: string; onBack: () => void; onOpen: (id: string) => void }) {
  const t = useT()
  const role = useAuthStore(s => s.user?.role || '')
  const isAuditor = ['super_admin', 'eva_auditor'].includes(role)
  const isMSP = ['msp_admin', 'msp_analyst'].includes(role)
  const [tab, setTab] = useState<'overview' | 'evidence' | 'expected' | 'reco' | 'history'>('overview')
  const [preview, setPreview] = useState<{ id: string; title: string } | null>(null)
  const [discOpen, setDiscOpen] = useState(false)
  const [bpOpen, setBpOpen] = useState(false)
  const [eeOpen, setEeOpen] = useState(false)
  const [newExp, setNewExp] = useState('')
  const [reviewing, setReviewing] = useState<{ id: string; note: string } | null>(null)
  const [statusEdit, setStatusEdit] = useState(false)
  const [auditNote, setAuditNote] = useState('')
  const [showHelp, setShowHelp] = useState(false)
  const [saDraft, setSaDraft] = useState<{ answers: Record<string, number>; comment: string }>({ answers: {}, comment: '' })
  const collectingId = useRef<string | null>(null)
  const fileInput = useRef<HTMLInputElement | null>(null)
  // Add a standalone, documented evidence item from the Evidence tab.
  const eviFile = useRef<HTMLInputElement | null>(null)
  const [newEvi, setNewEvi] = useState<{ title: string; note: string }>({ title: '', note: '' })
  const qc = useQueryClient()
  const lang = useI18n(s => s.lang)
  const clientId = useClientContext(s => s.clientId)

  // Prev/Next navigation across controls, in the (cached) list order.
  const listIds: string[] = (((qc.getQueryData(['controls', lang]) as ListResp | undefined)?.items) || []).map(x => x.id)
  const idx = listIds.indexOf(id)
  const prevId = idx > 0 ? listIds[idx - 1] : null
  const nextId = idx >= 0 && idx < listIds.length - 1 ? listIds[idx + 1] : null
  const goTo = (nid: string | null) => {
    if (!nid) return
    // Land at the top of the next control (matters when using the bottom prev/next bar)
    document.querySelector('.main-scroll')?.scrollTo({ top: 0 })
    const g = useUnsavedGuard.getState()
    if (g.dirty) {
      const save = window.confirm(t('You have unsaved changes. Save them before moving to another control? (Cancel to discard)'))
      if (save && g.save) { g.save().catch(() => {}).finally(() => { g.clear(); onOpen(nid) }); return }
      g.clear()
    }
    onOpen(nid)
  }
  const [showEn, setShowEn] = useState(false)
  const [saEn, setSaEn] = useState(false)

  const { data: c, isLoading, isError } = useQuery<Detail>({
    queryKey: ['control', id, lang],
    queryFn: async () => (await api.get(`/controls/${id}`)).data,
  })

  const { data: exp } = useQuery<ExpResp>({
    queryKey: ['expected', id, lang],
    queryFn: async () => (await api.get(`/controls/${id}/expected-evidence`)).data,
  })

  const { data: tpl } = useQuery<{ available: string[] }>({
    queryKey: ['policy-templates'],
    queryFn: async () => (await api.get('/policy-templates/')).data,
  })
  const templateReady = (name?: string | null) => !!name && (tpl?.available || []).includes(name)

  const afterExp = (data: ExpResp) => {
    // Write to the real (language-scoped) key so the expected-evidence panel
    // updates instantly, then invalidate to refetch and stay in sync. The old
    // 2-part key never matched ['expected', id, lang], so the panel went stale
    // until a full browser refresh.
    qc.setQueryData(['expected', id, lang], data)
    qc.invalidateQueries({ queryKey: ['expected', id] })
    qc.invalidateQueries({ queryKey: ['control', id] })
    qc.invalidateQueries({ queryKey: ['controls'] })
  }
  const addExp = useMutation({
    mutationFn: async (text: string) => (await api.post(`/controls/${id}/expected-evidence`, { text })).data,
    onSuccess: (d: ExpResp) => { afterExp(d); setNewExp('') },
  })
  const patchExp = useMutation({
    mutationFn: async (v: { ee: string; body: Partial<ExpItem> }) =>
      (await api.patch(`/controls/${id}/expected-evidence/${v.ee}`, v.body)).data,
    onSuccess: afterExp,
  })
  const delExp = useMutation({
    mutationFn: async (ee: string) => (await api.delete(`/controls/${id}/expected-evidence/${ee}`)).data,
    onSuccess: afterExp,
  })
  const collectExp = useMutation({
    mutationFn: async (v: { ee: string; file: File }) => {
      const fd = new FormData()
      fd.append('file', v.file)
      return (await api.post(`/controls/${id}/expected-evidence/${v.ee}/collect`, fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })).data
    },
    onSuccess: (d: ExpResp) => { afterExp(d); qc.invalidateQueries({ queryKey: ['events', id] }) },
  })
  const { data: sa } = useQuery<SAResp>({
    queryKey: ['self-assess', id, lang],
    queryFn: async () => (await api.get(`/controls/${id}/self-assessment`)).data,
  })
  useEffect(() => {
    if (sa) setSaDraft({ answers: { ...sa.answers }, comment: sa.comment || '' })
  }, [sa])
  const saveSA = useMutation({
    mutationFn: async (b: { answers: Record<string, number>; comment: string }) =>
      (await api.put(`/controls/${id}/self-assessment`, b)).data,
    onSuccess: (d: SAResp) => {
      qc.setQueryData(['self-assess', id], d)
      qc.invalidateQueries({ queryKey: ['maturity'] })
    },
  })
  // Unsaved-changes guard: the self-assessment draft differs from what's saved.
  const saDirty = !!sa && (
    JSON.stringify(saDraft.answers || {}) !== JSON.stringify(sa.answers || {}) ||
    (saDraft.comment || '') !== (sa.comment || '')
  )
  useEffect(() => {
    useUnsavedGuard.getState().setGuard(saDirty, () => saveSA.mutateAsync(saDraft))
    return () => useUnsavedGuard.getState().clear()
  }, [saDirty, saDraft]) // eslint-disable-line react-hooks/exhaustive-deps
  // When the reviewer switches client while viewing a control, leave the control
  // and return to the (new client's) controls list. Saving, if needed, has
  // already been handled by the client selector before the switch.
  const startClient = useRef(clientId)
  useEffect(() => {
    if (clientId !== startClient.current) { startClient.current = clientId; onBack() }
  }, [clientId]) // eslint-disable-line react-hooks/exhaustive-deps
  const { data: events } = useQuery<{ events: EventItem[] }>({
    queryKey: ['events', id],
    queryFn: async () => (await api.get(`/controls/${id}/events`)).data,
  })
  // Recommendations for this control (maturity-gap remediation).
  const { data: recos } = useQuery<RecResp>({
    queryKey: ['reco', id],
    queryFn: async () => (await api.get(`/recommendations/control/${id}`)).data,
  })
  const genReco = useMutation({
    mutationFn: async (source: 'premade' | 'ai') => (await api.post(`/recommendations/control/${id}/generate`, { source })).data,
    onSuccess: (r: any) => {
      toast.success(r.created ? `Added ${r.created} recommendation${r.created === 1 ? '' : 's'}` : 'No gap — control is at or above target')
      qc.invalidateQueries({ queryKey: ['reco', id] })
      qc.invalidateQueries({ queryKey: ['recommendations'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || 'Generation failed'),
  })
  const recoStatus = useMutation({
    mutationFn: async (v: { rid: string; status: string }) => (await api.patch(`/recommendations/${v.rid}`, { status: v.status })).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['reco', id] }); qc.invalidateQueries({ queryKey: ['recommendations'] }) },
  })
  const recoDel = useMutation({
    mutationFn: async (rid: string) => (await api.delete(`/recommendations/${rid}`)).data,
    onSuccess: () => { qc.invalidateQueries({ queryKey: ['reco', id] }); qc.invalidateQueries({ queryKey: ['recommendations'] }) },
  })
  const delEvi = useMutation({
    mutationFn: async (eid: string) => (await api.delete(`/evidence/${eid}`)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['control', id] })
      qc.invalidateQueries({ queryKey: ['expected', id] })
      qc.invalidateQueries({ queryKey: ['events', id] })
      qc.invalidateQueries({ queryKey: ['controls'] })
    },
  })
  const addEvidence = useMutation({
    mutationFn: async () => {
      const f = eviFile.current?.files?.[0]
      if (!f) throw new Error('no-file')
      const fd = new FormData()
      fd.append('file', f)
      fd.append('title', newEvi.title.trim())
      fd.append('description', newEvi.note.trim())
      return (await api.post(`/controls/${id}/evidence`, fd)).data
    },
    onSuccess: () => {
      toast.success(t('Evidence added'))
      setNewEvi({ title: '', note: '' })
      if (eviFile.current) eviFile.current.value = ''
      qc.invalidateQueries({ queryKey: ['control', id] })
      qc.invalidateQueries({ queryKey: ['events', id] })
      qc.invalidateQueries({ queryKey: ['controls'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not add evidence')),
  })
  const metaMut = useMutation({
    mutationFn: async (body: { risk?: string; priority?: string }) =>
      (await api.patch(`/controls/${id}/meta`, body)).data,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['control', id] })
      qc.invalidateQueries({ queryKey: ['controls'] })
    },
  })
  const underReview = useMutation({
    mutationFn: async (v: { under_review: boolean; note?: string }) =>
      (await api.post(`/controls/${id}/under-review`, v)).data,
    onSuccess: () => {
      toast.success(t('Updated'))
      qc.invalidateQueries({ queryKey: ['control', id] })
      qc.invalidateQueries({ queryKey: ['events', id] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const afterReview = () => {
    qc.invalidateQueries({ queryKey: ['control', id] })
    qc.invalidateQueries({ queryKey: ['expected', id] })
    qc.invalidateQueries({ queryKey: ['events', id] })
    qc.invalidateQueries({ queryKey: ['controls'] })
  }
  // Per-evidence-item Approve / Flag (evidence-centric review).
  const reviewEvi = useMutation({
    mutationFn: async (v: { eid: string; decision: 'accept' | 'return'; note?: string }) =>
      (await api.post(`/controls/${id}/evidence/${v.eid}/review`, { decision: v.decision, note: v.note })).data,
    onSuccess: () => { afterReview(); setReviewing(null) },
  })
  // Editable control status (auto-derived or manual override + comment).
  const setStatus = useMutation({
    mutationFn: async (v: { mode: 'auto' | 'manual'; status?: string; note?: string }) =>
      (await api.patch(`/controls/${id}/status`, v)).data,
    onSuccess: () => { afterReview(); setStatusEdit(false) },
  })
  const onCollectClick = (ee: string) => { collectingId.current = ee; fileInput.current?.click() }
  const onFileChosen = (e: ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    const ee = collectingId.current
    if (f && ee) collectExp.mutate({ ee, file: f })
    e.target.value = ''
    collectingId.current = null
  }

  if (isLoading) return <div className="page-sub">{t('Loading control…')}</div>
  if (isError || !c) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load control.')}</div>

  // Per-control "View in English": when in FR and a translation exists, allow
  // flipping just this control's content to the English companion.
  const cc: any = showEn && c.english ? { ...c, ...c.english } : c
  const canViewEn = !!c.fr_available && !!c.english
  const enToggle = canViewEn ? (
    <button className="tb-btn" style={{ padding: '3px 10px', fontSize: 11 }} onClick={() => setShowEn(s => !s)}
      title={t('Show this control in the other language')}>
      🌐 {showEn ? t('Voir en français') : t('View in English')}
    </button>
  ) : null

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16 }} className="fi">
        <button className="tb-btn" onClick={onBack} style={{ padding: '4px 10px', fontSize: 11 }}>← {t('Back')}</button>
        <span style={{ fontSize: 11, color: 'var(--text3)' }}>{t('Controls')} › {c.ref}</span>
        {listIds.length > 1 && (
          <div style={{ display: 'flex', gap: 4, alignItems: 'center' }}>
            <button className="tb-btn" disabled={!prevId} onClick={() => goTo(prevId)} title={t('Previous control')}
              style={{ padding: '4px 9px', fontSize: 11, opacity: prevId ? 1 : 0.4 }}>← {t('Previous')}</button>
            <button className="tb-btn" disabled={!nextId} onClick={() => goTo(nextId)} title={t('Next control')}
              style={{ padding: '4px 9px', fontSize: 11, opacity: nextId ? 1 : 0.4 }}>{t('Next')} →</button>
            {idx >= 0 && <span style={{ fontSize: 10, color: 'var(--text3)' }}>{idx + 1}/{listIds.length}</span>}
          </div>
        )}
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
          {enToggle}
          <span className={`badge ${c.audit_status_badge}`} style={{ fontSize: 11, padding: '3px 10px' }}>{c.audit_status_label}</span>
          {isAuditor && <span className="badge b-purple" style={{ fontSize: 11, padding: '3px 10px' }}>{t('EVA Review Active')}</span>}
        </div>
      </div>

      <div className="detail-wrap">
        <div className="detail-main">
          {/* Header card */}
          <div className="ctrl-header-card fi">
            <div className="ctrl-hdr-top">
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6, flexWrap: 'wrap' }}>
                  <span className="ctrl-ref-big">{c.ref}</span>
                  <span className={`badge ${c.priorityBadge}`}>{t('{priority} Priority', { priority: t(cap(c.priority)) })}</span>
                  <span className={`badge ${c.riskBadge}`}>{t('{risk} Risk', { risk: t(cap(c.risk)) })}</span>
                  <span className="badge b-blue">{t(c.level)}</span>
                </div>
                <div className="ctrl-title-big">{cc.title}</div>
                <div className="ctrl-tags">
                  <span className="badge b-blue">{c.domain}</span>
                  <span className="badge b-purple">{c.category}</span>
                  <span className="badge b-gray">{c.framework}</span>
                  {c.policy_template && (
                    templateReady(c.policy_template)
                      ? <button onClick={() => downloadPolicyTemplate(c.policy_template!)}
                          title={`Download the ${c.policy_template} template (.docx)`}
                          className="badge" style={{ background: '#DBEAFE', color: '#1E40AF', border: '1px solid #BFDBFE', cursor: 'pointer' }}>
                          📄 {c.policy_template} {t('Template')} ⬇
                        </button>
                      : <span className="badge" title={`Requires a documented policy. Template "${c.policy_template}" not uploaded yet.`}
                          style={{ background: '#FEF3C7', color: '#92400E', cursor: 'help' }}>
                          📄 {c.policy_template} {t('Template')}
                        </span>
                  )}
                </div>
              </div>
              <div style={{ textAlign: 'center', flexShrink: 0 }}>
                <MiniRing pct={c.coverage} />
                <div style={{ fontSize: 9, color: 'var(--text3)', marginTop: 2 }}>{c.expected_valid}/{c.expected_total || c.evidence_expected} {t('evidence')}</div>
              </div>
            </div>

            {/* Status row — auto-derived from evidence, or manual override */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border-l)', flexWrap: 'wrap' }}>
              <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.05em' }}>{t('Status')}</span>
              <span className={`badge ${c.audit_status_badge}`}>{c.audit_status_label}</span>
              <span style={{ fontSize: 10, color: 'var(--text3)' }}>
                {c.status_mode === 'manual' ? t('set manually') : t('auto from evidence')}
              </span>
              {c.status_mode === 'manual' && c.status_note && (
                <span style={{ fontSize: 11, color: 'var(--text2)', fontStyle: 'italic' }}>“{c.status_note}”</span>
              )}
              {c.can_review && !statusEdit && (
                <button onClick={() => setStatusEdit(true)}
                  style={{ marginLeft: 'auto', fontSize: 11, fontWeight: 600, color: 'var(--eva-blue2)', background: 'none', border: 'none', cursor: 'pointer' }}>
                  ✎ {t('Change status')}
                </button>
              )}
              {c.can_review && statusEdit && (
                <StatusEditor c={c} onCancel={() => setStatusEdit(false)}
                  onSave={(mode, status, note) => setStatus.mutate({ mode, status, note })}
                  busy={setStatus.isPending} />
              )}
            </div>

            {/* Under review (coach challenge) */}
            {(c.under_review || c.can_coach) && (
              <div style={{ marginTop: 10, padding: '10px 12px', borderRadius: 8,
                border: `1px solid ${c.under_review ? '#FDE68A' : 'var(--border-l)'}`,
                background: c.under_review ? '#FFFBEB' : 'var(--surface)', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                {c.under_review
                  ? <span style={{ fontSize: 12, color: '#92400E' }}>🔎 <b>{t('Under review')}</b>{c.under_review_note ? ` — ${c.under_review_note}` : ''}</span>
                  : <span style={{ fontSize: 12, color: 'var(--text3)' }}>{t('As a coach, you can challenge this control and send it back under review.')}</span>}
                {c.can_coach && (
                  <div style={{ marginLeft: 'auto', display: 'flex', gap: 6 }}>
                    {c.under_review
                      ? <button className="tb-btn" disabled={underReview.isPending} onClick={() => underReview.mutate({ under_review: false })}>✓ {t('Clear review')}</button>
                      : <button className="tb-btn" disabled={underReview.isPending}
                          onClick={() => { const note = window.prompt(t('What should the responder clarify or fix?')); if (note !== null) underReview.mutate({ under_review: true, note }) }}>
                          🔎 {t('Challenge / send back')}
                        </button>}
                  </div>
                )}
              </div>
            )}

            {/* Get help from the marketplace when the control isn't compliant */}
            {c.audit_status !== 'compliant' && (
              <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={{ fontSize: 11.5, color: 'var(--text3)' }}>{t('Need a hand with this control?')}</span>
                <button className="tb-btn" onClick={() => setShowHelp(true)}>🛟 {t('Get help')}</button>
              </div>
            )}
          </div>

          {showHelp && <HelpModal controlId={c.id} domain={c.domain} onClose={() => setShowHelp(false)} />}

          {/* Tabs */}
          <div className="card fi">
            <div className="tab-bar">
              {(['overview', 'evidence', 'expected', 'reco', 'history'] as const).map(tb => (
                <button key={tb} className={`tab ${tab === tb ? 'active' : ''}`} onClick={() => setTab(tb)}>
                  {tb === 'overview' ? `${t('Overview')}${sa?.perceived_level != null ? ` · ${t('self {n}/5', { n: sa.perceived_level })}` : ''}`
                    : tb === 'evidence' ? `${t('Evidence')} (${c.evidence_count}/${c.evidence_expected})`
                      : tb === 'expected' ? `${t('Expected evidence')} (${exp ? `${exp.valid}/${exp.total}` : '…'})`
                        : tb === 'reco' ? `${t('Recommendations')}${recos?.recommendations.length ? ` (${recos.recommendations.length})` : ''}`
                          : t('History')}
                </button>
              ))}
            </div>

            {tab === 'overview' && (
              <div>
                {cc.description && (
                  <div className="req-block" style={{ marginTop: 4 }}>
                    <div className="req-label blue"><span>📌</span> {t('Requirement')}</div>
                    <div className="req-box blue">
                      {cc.description.split('\n').map((ln: string, i: number) => {
                        const t = ln.trim()
                        if (!t) return null
                        const sub = /^\d+\./.test(t)        // 1. 2. 3. → sub-item
                        const top = /^[a-z]\./i.test(t)     // a. b. c. → top-level item
                        const m = t.match(/^([a-z0-9]+\.)\s*(.*)$/i)
                        const label = m ? m[1] : ''
                        const body = m ? m[2] : t
                        return (
                          <div key={i} style={{ display: 'flex', gap: 8, paddingLeft: sub ? 26 : 0, marginBottom: 5 }}>
                            {label && <span style={{ color: '#2563EB', fontWeight: 700, minWidth: sub ? 18 : 16 }}>{label}</span>}
                            <span style={{ fontWeight: top ? 600 : 500 }}>{body}</span>
                          </div>
                        )
                      })}
                    </div>
                  </div>
                )}
                {cc.objective && (
                  <div className="req-block" style={{ marginTop: 16 }}>
                    <div className="req-label amber"><span>🎯</span> {t('Objective')}</div>
                    <div className="req-box amber">{cc.objective}</div>
                  </div>
                )}
                {(cc.best_practices.length > 0 || cc.expected_evidence.length > 0) && (
                  <div style={{ display: 'flex', gap: 10, marginTop: 14, flexWrap: 'wrap', alignItems: 'flex-start' }}>
                    {cc.best_practices.length > 0 && (
                      <div style={{ flex: '1 1 240px', minWidth: 0 }}>
                        <button type="button" onClick={() => setBpOpen(o => !o)}
                          style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', background: '#F0FDF4', border: '1px solid #BBF7D0', borderLeft: '4px solid #16A34A', borderRadius: 'var(--r)', padding: '9px 12px', cursor: 'pointer', fontSize: 11, fontWeight: 700, color: '#166534', textTransform: 'uppercase', letterSpacing: '.05em', textAlign: 'left' }}>
                          <span style={{ transform: bpOpen ? 'rotate(90deg)' : 'none', transition: 'transform .15s', display: 'inline-block' }}>▸</span>
                          ★ {t('Best practices')}
                          <span style={{ marginLeft: 'auto', fontWeight: 600, textTransform: 'none', letterSpacing: 0, color: '#16A34A' }}>{bpOpen ? t('Hide') : t('Show ({n})', { n: cc.best_practices.length })}</span>
                        </button>
                        {bpOpen && (
                          <div style={{ background: 'var(--card)', border: '1px solid #BBF7D0', borderTop: 'none', borderLeft: '4px solid #16A34A', borderRadius: 'var(--r)', padding: '10px 12px', marginTop: -1 }}>
                            {cc.best_practices.map((bp: string, i: number) => (
                              <div key={i} className="bp-item"><span className="bp-check" style={{ color: '#16A34A' }}>★</span><span>{bp}</span></div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                    {cc.expected_evidence.length > 0 && (
                      <div style={{ flex: '1 1 240px', minWidth: 0 }}>
                        <button type="button" onClick={() => setEeOpen(o => !o)}
                          style={{ display: 'flex', alignItems: 'center', gap: 8, width: '100%', background: '#F0FDF4', border: '1px solid #BBF7D0', borderLeft: '4px solid #16A34A', borderRadius: 'var(--r)', padding: '9px 12px', cursor: 'pointer', fontSize: 11, fontWeight: 700, color: '#166534', textTransform: 'uppercase', letterSpacing: '.05em', textAlign: 'left' }}>
                          <span style={{ transform: eeOpen ? 'rotate(90deg)' : 'none', transition: 'transform .15s', display: 'inline-block' }}>▸</span>
                          📎 {t('Expected evidence')}
                          <span style={{ marginLeft: 'auto', fontWeight: 600, textTransform: 'none', letterSpacing: 0, color: '#16A34A' }}>{eeOpen ? t('Hide') : t('Show ({n})', { n: cc.expected_evidence.length })}</span>
                        </button>
                        {eeOpen && (
                          <div style={{ background: 'var(--card)', border: '1px solid #BBF7D0', borderTop: 'none', borderLeft: '4px solid #16A34A', borderRadius: 'var(--r)', padding: '10px 12px', marginTop: -1 }}>
                            {cc.expected_evidence.map((bp: string, i: number) => (
                              <div key={i} className="bp-item"><span className="bp-check" style={{ color: '#16A34A' }}>✓</span><span>{bp}</span></div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
                {cc.discussion && (
                  <div style={{ marginTop: 18 }}>
                    <button
                      type="button"
                      onClick={() => setDiscOpen(o => !o)}
                      style={{
                        display: 'flex', alignItems: 'center', gap: 8, width: '100%',
                        background: 'var(--surface)', border: '1px solid var(--border-l)',
                        borderRadius: 'var(--r)', padding: '9px 12px', cursor: 'pointer',
                        fontSize: 11, fontWeight: 600, color: 'var(--text2)',
                        textTransform: 'uppercase', letterSpacing: '.05em', textAlign: 'left',
                      }}
                    >
                      <span style={{ transform: discOpen ? 'rotate(90deg)' : 'none', transition: 'transform .15s', display: 'inline-block' }}>▸</span>
                      {t('Discussion — standard guidance')}
                      <span style={{ marginLeft: 'auto', fontWeight: 500, textTransform: 'none', letterSpacing: 0, color: 'var(--text3)' }}>
                        {discOpen ? t('Hide') : t('Read')}
                      </span>
                    </button>
                    {discOpen && (
                      <div style={{
                        fontSize: 12, color: 'var(--text2)', lineHeight: 1.7,
                        background: 'var(--surface)', borderRadius: 'var(--r)', padding: '10px 12px',
                        border: '1px solid var(--border-l)', borderTop: 'none', marginTop: -1,
                        maxHeight: 220, overflowY: 'auto',
                      }}>
                        {cc.discussion.split('\n\n').map((p: string, i: number) => <p key={i} style={{ marginBottom: 8 }}>{p}</p>)}
                      </div>
                    )}
                  </div>
                )}

                {/* Self-assessment — embedded here so the client rates against the requirement/objective above */}
                <div style={{ marginTop: 20, paddingTop: 16, borderTop: '2px solid var(--border-l)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                    <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.05em' }}>◎ {t('Self-assessment')}</span>
                    {sa?.perceived_level != null && <span className="badge b-blue" style={{ fontSize: 9 }}>{t('Perceived {n}/{max}', { n: sa.perceived_level, max: sa.scale_max })}</span>}
                  </div>
                  <div className="page-sub" style={{ fontSize: 11.5, marginBottom: 14 }}>
                    {t('Based on the requirement and objective above, rate your organisation’s maturity for this control. This feeds the')} <strong style={{ color: '#0EA5E9' }}>{t('Perceived')}</strong> {t('ring on the Maturity radar; the auditor’s')} <strong style={{ color: '#16A34A' }}>{t('Assessed')}</strong> {t('rating is derived from evidence separately.')}
                  </div>
                  {sa?.fr_available && (
                    <button className="tb-btn" style={{ padding: '2px 8px', fontSize: 10, marginBottom: 8 }} onClick={() => setSaEn(s => !s)}>
                      🌐 {saEn ? t('Voir en français') : t('View in English')}
                    </button>
                  )}
                  {((saEn && sa?.english ? sa.english : sa?.questions) || []).map(q => (
                    <div key={q.key} style={{ marginBottom: 16 }}>
                      <div style={{ fontSize: 12.5, fontWeight: 600, marginBottom: 8 }}>{q.prompt}</div>
                      {q.options.map(o => {
                        const sel = saDraft.answers[q.key] === o.level
                        return (
                          <label key={o.key} style={{ display: 'flex', gap: 10, alignItems: 'flex-start', padding: '9px 11px', border: `1px solid ${sel ? 'var(--eva-blue2)' : 'var(--border-l)'}`, background: sel ? 'var(--soft)' : 'var(--card)', borderRadius: 'var(--r)', marginBottom: 6, cursor: 'pointer' }}>
                            <input type="radio" name={`${id}-${q.key}`} checked={sel}
                              onChange={() => setSaDraft(s => ({ ...s, answers: { ...s.answers, [q.key]: o.level } }))} style={{ marginTop: 3 }} />
                            <span style={{ flex: 1, fontSize: 12.5, lineHeight: 1.5 }}>
                              <span style={{ fontWeight: 600, color: 'var(--text2)' }}>{o.short}:</span> {o.label}
                            </span>
                          </label>
                        )
                      })}
                    </div>
                  ))}
                  <div style={{ marginTop: 10 }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 6 }}>{t('Comments / Additional info')}</div>
                    <textarea value={saDraft.comment} onChange={e => setSaDraft(s => ({ ...s, comment: e.target.value }))} rows={3}
                      placeholder={t('Add context for your answers — scope, exceptions, planned improvements…')}
                      style={{ width: '100%', fontSize: 12.5, padding: 9, border: '1px solid var(--border-l)', borderRadius: 6, resize: 'vertical', fontFamily: 'inherit', background: 'var(--card)', color: 'var(--text)' }} />
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 12 }}>
                    <button disabled={saveSA.isPending} onClick={() => saveSA.mutate(saDraft)}
                      style={{ fontSize: 12, fontWeight: 600, padding: '7px 16px', borderRadius: 8, border: '1px solid var(--eva-blue2)', background: 'var(--eva-blue2)', color: '#fff', cursor: 'pointer' }}>{t('Save assessment')}</button>
                    {sa?.perceived_level != null && <span style={{ fontSize: 12, color: 'var(--text2)' }}>{t('Perceived maturity:')} <strong style={{ color: '#0EA5E9' }}>{sa.perceived_level} / {sa.scale_max}</strong></span>}
                  </div>
                </div>

                {cc.plain_language && (
                  <div className="plain-box" style={{ marginTop: 18 }}>
                    <div className="plain-hdr">{t('💡 In plain language')}</div>
                    {cc.plain_language}
                  </div>
                )}

                {c.video?.kind && (
                  <div style={{ marginTop: 18 }}>
                    <div className="plain-hdr" style={{ marginBottom: 8 }}>{t('🎬 Training video')}</div>
                    <VideoPlayer video={c.video} />
                  </div>
                )}
              </div>
            )}

            {tab === 'evidence' && (
              <div>
                <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 12 }}>
                  {t('Evidence items ({n} of {m})', { n: c.evidence.length, m: c.evidence_expected })}
                </div>
                {c.evidence.map(e => {
                  const rs = EE_STATE[e.review_state] || EE_STATE.submitted
                  const open = reviewing?.id === e.id
                  return (
                  <div key={e.id} style={{ border: '1px solid var(--border-l)', borderLeft: `3px solid ${rs.dot}`, borderRadius: 'var(--r)', marginBottom: 8, background: rs.bg }}>
                    <div className="ev-item" style={{ border: 'none', background: 'transparent', marginBottom: 0 }}>
                      <div className="ev-icon-box"><FileText size={16} aria-hidden /></div>
                      <div className="ev-info">
                        <div className="ev-name">{e.title}</div>
                        <div className="ev-meta">{t('Uploaded {date} by {by}', { date: e.date, by: e.by })}{e.file_name ? ` · ${e.file_name}` : ''}</div>
                        {e.review_state === 'returned' && e.review_note && (
                          <div style={{ marginTop: 4, fontSize: 11.5, color: '#F97316' }}>↩ {t('Returned: {note}', { note: e.review_note })}</div>
                        )}
                        {e.review_state === 'accepted' && e.review_note && (
                          <div style={{ marginTop: 4, fontSize: 11.5, color: '#22C55E' }}>✓ {e.review_note}</div>
                        )}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
                        <button className="ev-action-btn" title={t('Preview')} style={{ background: '#EDE9FE', color: '#5B21B6', borderColor: '#C4B5FD' }} onClick={() => setPreview({ id: e.id, title: e.title })}><Eye size={14} aria-hidden /></button>
                        <button className="ev-action-btn download" title={t('Download')} onClick={() => downloadEvidence(e.id, e.title)}><Download size={14} aria-hidden /></button>
                        <button className="ev-action-btn" title={t('Remove evidence')} disabled={delEvi.isPending}
                          style={{ background: '#FEE2E2', color: '#991B1B', borderColor: '#FECACA' }}
                          onClick={() => { if (window.confirm('Remove this evidence? Its expected-evidence item returns to “missing”.')) delEvi.mutate(e.id) }}><Trash2 size={14} aria-hidden /></button>
                        <span className={`badge ${rs.badge}`}>{rs.label}</span>
                        {c.can_review && !open && (
                          <button onClick={() => setReviewing({ id: e.id, note: e.review_note || '' })}
                            style={{ fontSize: 11, fontWeight: 600, padding: '4px 10px', borderRadius: 6, border: '1px solid var(--eva-blue2)', background: 'var(--card)', color: 'var(--eva-blue2)', cursor: 'pointer', whiteSpace: 'nowrap' }}>
                            {t('Review')}
                          </button>
                        )}
                      </div>
                    </div>
                    {c.can_review && open && (
                      <div style={{ padding: '0 14px 12px 14px' }}>
                        <textarea value={reviewing!.note} onChange={ev => setReviewing({ id: e.id, note: ev.target.value })}
                          rows={2} placeholder={t('Comment (required when flagging an issue)')}
                          style={{ width: '100%', fontSize: 12, padding: 9, border: '1px solid var(--border-l)', borderRadius: 6, resize: 'vertical', fontFamily: 'inherit' }} />
                        <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                          <button disabled={reviewEvi.isPending || !reviewing!.note.trim()}
                            onClick={() => reviewEvi.mutate({ eid: e.id, decision: 'return', note: reviewing!.note.trim() })}
                            style={{ fontSize: 11, fontWeight: 600, padding: '5px 12px', borderRadius: 6, border: '1px solid #FDBA74', background: '#FFEDD5', color: '#9A3412', cursor: 'pointer', opacity: reviewing!.note.trim() ? 1 : 0.5 }}>{t('⚑ Flag issue')}</button>
                          <button disabled={reviewEvi.isPending}
                            onClick={() => reviewEvi.mutate({ eid: e.id, decision: 'accept', note: reviewing!.note.trim() || undefined })}
                            style={{ fontSize: 11, fontWeight: 600, padding: '5px 12px', borderRadius: 6, border: '1px solid var(--eva-blue2)', background: 'var(--eva-blue2)', color: '#fff', cursor: 'pointer' }}>{t('🛡 Approve')}</button>
                          <button onClick={() => setReviewing(null)}
                            style={{ fontSize: 11, padding: '5px 10px', borderRadius: 6, border: '1px solid var(--border-l)', background: 'var(--card)', cursor: 'pointer' }}>{t('Cancel')}</button>
                        </div>
                      </div>
                    )}
                  </div>
                )})}
                {c.evidence.length === 0 && <div className="page-sub" style={{ marginBottom: 12 }}>{t('No evidence uploaded yet.')}</div>}
                <div style={{ marginTop: 10, border: '1px solid var(--border-l)', borderRadius: 'var(--r)', padding: 12, background: 'var(--surface)' }}>
                  <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.05em', marginBottom: 8 }}>
                    ＋ {t('Add an additional evidence')}
                  </div>
                  <input value={newEvi.title} onChange={e => setNewEvi(s => ({ ...s, title: e.target.value }))}
                    placeholder={t('Evidence title (e.g. “Q2 access review export”)')}
                    style={{ width: '100%', fontSize: 12, padding: '8px 10px', border: '1px solid var(--border-l)', borderRadius: 6, marginBottom: 8, boxSizing: 'border-box' }} />
                  <textarea value={newEvi.note} onChange={e => setNewEvi(s => ({ ...s, note: e.target.value }))}
                    rows={2} placeholder={t('Describe what this evidence shows (optional)')}
                    style={{ width: '100%', fontSize: 12, padding: '8px 10px', border: '1px solid var(--border-l)', borderRadius: 6, marginBottom: 8, resize: 'vertical', fontFamily: 'inherit', boxSizing: 'border-box' }} />
                  <div style={{ display: 'flex', gap: 8, alignItems: 'center', flexWrap: 'wrap' }}>
                    <input ref={eviFile} type="file" style={{ fontSize: 12 }} />
                    <button className="submit-btn" disabled={addEvidence.isPending || !newEvi.title.trim()}
                      title={t('Upload a file and document it as evidence for this control')}
                      onClick={() => { if (!eviFile.current?.files?.[0]) { toast.error(t('Choose a file first')); return } addEvidence.mutate() }}
                      style={{ fontSize: 12, padding: '8px 14px', opacity: (addEvidence.isPending || !newEvi.title.trim()) ? 0.5 : 1 }}>
                      {addEvidence.isPending ? t('Adding…') : t('Add evidence')}
                    </button>
                    <span className="upload-sub" style={{ fontSize: 10.5, color: 'var(--text3)' }}>{t('PDF, images, spreadsheets — up to 50 MB')}</span>
                  </div>
                </div>
              </div>
            )}

            {tab === 'expected' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, background: 'var(--surface)', border: '1px solid var(--border-l)', borderRadius: 'var(--r)', padding: '10px 12px' }}>
                  <span className={`badge ${exp?.statusBadge || 'b-gray'}`}>{t(STATUS_LABEL[exp?.status || c.status] || exp?.status || c.status)}</span>
                  <span style={{ fontSize: 12, color: 'var(--text2)' }}>{t('{valid} of {total} accepted', { valid: exp?.valid ?? 0, total: exp?.total ?? 0 })}</span>
                  <div style={{ flex: 1, height: 8, background: 'var(--surface-2)', borderRadius: 6, overflow: 'hidden' }}>
                    <div style={{ width: `${exp?.coverage ?? 0}%`, height: '100%', background: 'var(--eva-blue2)' }} />
                  </div>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{exp?.coverage ?? 0}%</span>
                  <span style={{ fontSize: 10, color: 'var(--text3)' }}>{exp?.status_source === 'auditor' ? t('set by auditor') : t('auto')}</span>
                </div>

                <input ref={fileInput} type="file" onChange={onFileChosen} style={{ display: 'none' }} />
                {(exp?.items || []).map(it => {
                  const st = EE_STATE[it.state] || EE_STATE.missing
                  return (
                  <div key={it.id} style={{ padding: '11px 14px', border: '1px solid var(--border-l)', borderRadius: 'var(--r)', marginBottom: 8, background: st.bg }}>
                    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 10 }}>
                      <span style={{ flexShrink: 0, marginTop: 1, fontSize: 13, color: st.dot }}>●</span>
                      <div style={{ flex: 1, fontSize: 12.5, color: 'var(--text)', lineHeight: 1.5 }}>{it.text}</div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                        <span className={`badge ${st.badge}`} style={{ fontSize: 10 }}>{t(st.label)}</span>
                        {it.evidence?.can_preview && (
                          <button title={t('Preview {name}', { name: it.evidence.file_name || 'evidence' })}
                            onClick={() => setPreview({ id: it.evidence!.evidence_id, title: it.evidence!.file_name || it.text })}
                            style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'var(--text2)', display: 'inline-flex' }}><Eye size={15} aria-hidden /></button>
                        )}
                        <button onClick={() => onCollectClick(it.id)} disabled={collectExp.isPending}
                          style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'var(--eva-blue2)', fontSize: 12, fontWeight: 600, whiteSpace: 'nowrap' }}>
                          {it.evidence ? t('↻ Replace') : t('+ Collect')}
                        </button>
                        {it.origin === 'custom' && <button onClick={() => delExp.mutate(it.id)} title="Remove item" style={{ border: 'none', background: 'none', cursor: 'pointer', color: 'var(--text3)', fontSize: 14 }}>✕</button>}
                      </div>
                    </div>

                    {it.state === 'returned' && it.evidence?.review_note && (
                      <div style={{ marginTop: 8, marginLeft: 23, fontSize: 11.5, color: '#F97316', background: 'rgba(234,88,12,.12)', border: '1px solid rgba(234,88,12,.35)', borderRadius: 6, padding: '6px 9px' }}>
                        ↩ {t('Returned by reviewer: {note}', { note: it.evidence.review_note })}
                      </div>
                    )}

                    <div style={{ display: 'flex', gap: 16, marginTop: 8, paddingLeft: 23, alignItems: 'center', flexWrap: 'wrap' }}>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '.04em' }}>
                        {t('Frequency')}
                        <select value={it.frequency} onChange={e => patchExp.mutate({ ee: it.id, body: { frequency: e.target.value } })} style={selStyle}>
                          {(exp?.frequencies || []).map(f => <option key={f} value={f}>{t(FREQ_LABEL[f] || f)}</option>)}
                        </select>
                      </label>
                      <label style={{ display: 'flex', alignItems: 'center', gap: 6, fontSize: 10, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '.04em' }}>
                        {t('Type')}
                        <select value={it.evidence_type} onChange={e => patchExp.mutate({ ee: it.id, body: { evidence_type: e.target.value } })} style={selStyle}>
                          {(exp?.types || []).map(ty => <option key={ty} value={ty}>{lang === 'fr' ? (TYPE_FR[ty] || ty) : ty}</option>)}
                        </select>
                      </label>
                      {it.origin === 'custom' && <span className="badge b-gray" style={{ fontSize: 10 }}>{t('custom')}</span>}
                    </div>
                  </div>
                  )
                })}
                {exp && exp.items.length === 0 && <div className="page-sub" style={{ marginBottom: 10 }}>{t('No expected evidence defined yet — add the first item below.')}</div>}

                <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                  <input value={newExp} onChange={e => setNewExp(e.target.value)} placeholder={t('Add an expected evidence item for this client…')}
                    onKeyDown={e => { if (e.key === 'Enter' && newExp.trim()) addExp.mutate(newExp.trim()) }}
                    style={{ flex: 1, fontSize: 12, padding: '8px 10px', border: '1px solid var(--border-l)', borderRadius: 'var(--r)' }} />
                  <button disabled={!newExp.trim() || addExp.isPending} onClick={() => newExp.trim() && addExp.mutate(newExp.trim())}
                    style={{ fontSize: 12, padding: '8px 14px', borderRadius: 'var(--r)', border: 'none', background: 'var(--eva-blue2)', color: '#fff', cursor: newExp.trim() ? 'pointer' : 'default', opacity: newExp.trim() ? 1 : 0.5 }}>
                    {t('+ Add')}
                  </button>
                </div>
              </div>
            )}

            {tab === 'reco' && (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8, marginBottom: 8 }}>
                  <div className="page-sub" style={{ fontSize: 12 }}>{t('Remediation actions to close this control’s maturity gap.')}</div>
                  {recos?.can_generate && (
                    <div style={{ display: 'flex', gap: 6 }}>
                      <button className="tb-btn" disabled={genReco.isPending} onClick={() => genReco.mutate('premade')}>{t('📋 From library')}</button>
                      <button className="tb-btn" disabled={genReco.isPending || !recos?.has_llm}
                        title={recos?.has_llm ? 'Analyze this control’s self-assessment with AI' : 'Enable the AI connector first'}
                        onClick={() => genReco.mutate('ai')}>{t('✦ With AI')}</button>
                    </div>
                  )}
                </div>
                {(!recos || recos.recommendations.length === 0) && (
                  <div className="page-sub">{t('No recommendations yet. {extra}', { extra: recos?.can_generate ? t('Generate them from the library or AI analysis above.') : t('A reviewer can generate these.') })}</div>
                )}
                {(recos?.recommendations || []).map(r => (
                  <div key={r.id} style={{ padding: '10px 0', borderBottom: '1px solid var(--border-l)' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                      <span style={{ fontSize: 12.5, fontWeight: 600 }}>{r.title}</span>
                      {r.quick_win && <span className="badge b-green" style={{ fontSize: 9 }}>{t('⚡ Quick win')}</span>}
                      {r.source === 'ai' && <span className="badge b-blue" style={{ fontSize: 9 }}>✦ AI</span>}
                    </div>
                    <div style={{ fontSize: 11.5, color: 'var(--text2)', marginTop: 3 }}>{r.text}</div>
                    <div style={{ display: 'flex', gap: 6, marginTop: 5, alignItems: 'center', flexWrap: 'wrap' }}>
                      <span className={`badge ${r.impact === 'high' ? 'b-blue' : 'b-gray'}`} style={{ fontSize: 9 }}>{t('Impact: {v}', { v: r.impact })}</span>
                      <span className={`badge ${r.effort === 'low' ? 'b-green' : r.effort === 'high' ? 'b-red' : 'b-gray'}`} style={{ fontSize: 9 }}>{t('Effort: {v}', { v: r.effort })}</span>
                      {r.gap != null && <span style={{ fontSize: 10, color: 'var(--text3)' }}>L{r.current_level}→{r.target_level}</span>}
                      <div style={{ flex: 1 }} />
                      {recos?.can_generate ? (
                        <>
                          <select value={r.status} onChange={e => recoStatus.mutate({ rid: r.id, status: e.target.value })}
                            className={`badge ${r.status === 'done' ? 'b-green' : r.status === 'in_progress' ? 'b-blue' : 'b-gray'}`}
                            style={{ fontSize: 9, cursor: 'pointer', border: 'none' }}>
                            {['open', 'in_progress', 'done', 'dismissed'].map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
                          </select>
                          <button className="ev-action-btn" title="Remove" onClick={() => recoDel.mutate(r.id)}>✕</button>
                        </>
                      ) : <span className={`badge ${r.status === 'done' ? 'b-green' : 'b-gray'}`} style={{ fontSize: 9 }}>{r.status.replace('_', ' ')}</span>}
                    </div>
                  </div>
                ))}
              </div>
            )}

            {tab === 'history' && (
              <div>
                {(!events || events.events.length === 0) && <div className="page-sub">{t('No history yet.')}</div>}
                {(events?.events || []).map(ev => {
                  const icon = ev.action === 'accepted' ? '✅' : ev.action === 'returned' ? '↩️'
                    : ev.action === 'deleted' ? '🗑️' : ev.action === 'collected' ? '📤' : '•'
                  return (
                    <div key={ev.id} className="hist-item">
                      <span className="hist-icon">{icon}</span>
                      <div className="hist-text">
                        {ev.label}{ev.detail ? ` — ${ev.detail}` : ''}
                        <div style={{ fontSize: 10, color: 'var(--text3)' }}>{t('by {actor}', { actor: ev.actor })}</div>
                      </div>
                      <div className="hist-time">{ev.date}</div>
                    </div>
                  )
                })}
              </div>
            )}
          </div>
        </div>

        {/* Sidebar */}
        <div className="detail-sidebar">
          <div className="card fi">
            <div className="card-hdr"><span className="card-title">{t('Control info')}</span></div>
            <div className="meta-row"><span className="meta-key">{t('Status')}</span><span className={`badge ${c.audit_status_badge}`}>{c.audit_status_label}</span></div>
            <div className="meta-row"><span className="meta-key">{t('Owner')}</span><span className="meta-val">{c.owner || t('Unassigned')}</span></div>
            <div className="meta-row"><span className="meta-key">{t('Due')}</span><span className="meta-val">{c.due || t('No due date')}</span></div>
            <div className="meta-row">
              <span className="meta-key">{t('Risk')}</span>
              {isAuditor
                ? <select value={c.risk} disabled={metaMut.isPending} onChange={e => metaMut.mutate({ risk: e.target.value })} style={selStyle}>
                    {['critical', 'high', 'medium', 'low'].map(r => <option key={r} value={r}>{cap(r)}</option>)}
                  </select>
                : <span className={`badge ${c.riskBadge}`}>{c.risk}</span>}
            </div>
            <div className="meta-row">
              <span className="meta-key">{t('Priority')}</span>
              {isAuditor
                ? <select value={c.priority} disabled={metaMut.isPending} onChange={e => metaMut.mutate({ priority: e.target.value })} style={selStyle}>
                    {['high', 'medium', 'low'].map(p => <option key={p} value={p}>{cap(p)}</option>)}
                  </select>
                : <span className={`badge ${c.priorityBadge}`}>{cap(c.priority)}</span>}
            </div>
            <div className="meta-row"><span className="meta-key">{t('Coverage')}</span><span className="meta-val">{c.coverage}%</span></div>
            <div className="meta-row"><span className="meta-key">{t('Category')}</span><span className="meta-val">{c.category}</span></div>
            {isAuditor && <div style={{ fontSize: 10, color: 'var(--text3)', marginTop: 4 }}>{t('Risk & priority are EVA-curated for this control across all clients.')}</div>}
          </div>

          {isAuditor && (
            <div className="card fi" style={{ border: '1px solid #C4B5FD' }}>
              <div className="card-hdr"><span className="card-title" style={{ color: 'var(--purple)' }}>{t('Auditor decision')}</span></div>
              <div className="decision-grid">
                <button className="dec-btn d-accept" disabled={setStatus.isPending}
                  onClick={() => setStatus.mutate({ mode: 'manual', status: 'compliant', note: auditNote.trim() || undefined }, { onSuccess: () => setAuditNote('') })}>{t('✓ Accept')}</button>
                <button className="dec-btn d-reject" disabled={setStatus.isPending}
                  onClick={() => setStatus.mutate({ mode: 'manual', status: 'non_compliant', note: auditNote.trim() || undefined }, { onSuccess: () => setAuditNote('') })}>{t('✗ Reject')}</button>
                <button className="dec-btn d-more" disabled={setStatus.isPending}
                  onClick={() => setStatus.mutate({ mode: 'manual', status: 'in_progress', note: auditNote.trim() || undefined }, { onSuccess: () => setAuditNote('') })}>{t('⏳ Needs more')}</button>
                <button className="dec-btn d-na" disabled={setStatus.isPending}
                  onClick={() => setStatus.mutate({ mode: 'manual', status: 'not_applicable', note: auditNote.trim() || undefined }, { onSuccess: () => setAuditNote('') })}>{t('— Not applicable')}</button>
              </div>
              <textarea className="auditor-note" rows={3} placeholder={t('Auditor notes…')}
                value={auditNote} onChange={e => setAuditNote(e.target.value)} />
            </div>
          )}

          {isMSP && (
            <div className="card fi" style={{ border: '1px solid #86EFAC' }}>
              <div className="card-hdr"><span className="card-title" style={{ color: 'var(--teal)' }}>{t('MSP Pre-review')}</span></div>
              <div className="decision-grid">
                <button className="dec-btn d-accept">{t('✓ Approve')}</button>
                <button className="dec-btn d-reject">{t('⚑ Flag')}</button>
                <button className="dec-btn d-na" style={{ gridColumn: '1/-1' }}>{t('↩ Return to client')}</button>
              </div>
              <textarea className="auditor-note" rows={3} placeholder={t('MSP review note…')} />
            </div>
          )}

          <div className="card fi">
            <div className="card-hdr"><span className="card-title">{t('Training video')}</span></div>
            {c.video?.kind
              ? <VideoPlayer video={c.video} />
              : <>
                  <div className="video-thumb"><div className="play-icon">▶</div></div>
                  <div style={{ fontSize: 10, color: 'var(--text3)', textAlign: 'center', marginTop: 6 }}>{t('No training video yet')}</div>
                </>}
          </div>

          {c.mappings && Object.keys(c.mappings).length > 0 && (
            <div className="card fi">
              <div className="card-hdr"><span className="card-title">{t('Framework mappings')}</span></div>
              {Object.entries(c.mappings).map(([fam, refs], i) => (
                <div className="map-row" key={fam}>
                  <span className="map-fw">{MAP_LABEL[fam] || fam}</span>
                  <div className="map-refs">
                    {refs.map(m => <span key={m} className={`badge ${MAP_BADGE[i % MAP_BADGE.length]}`}>{m}</span>)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Bottom prev/next — mirrors the top toolbar so long controls can be
          navigated without scrolling back up. */}
      {listIds.length > 1 && (
        <div className="fi" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, marginTop: 18, paddingTop: 14, borderTop: '1px solid var(--border-l)' }}>
          <button className="tb-btn" disabled={!prevId} onClick={() => goTo(prevId)} title={t('Previous control')}
            style={{ padding: '5px 12px', fontSize: 11, opacity: prevId ? 1 : 0.4 }}>← {t('Previous')}</button>
          {idx >= 0 && <span style={{ fontSize: 11, color: 'var(--text3)' }}>{idx + 1}/{listIds.length}</span>}
          <button className="tb-btn" disabled={!nextId} onClick={() => goTo(nextId)} title={t('Next control')}
            style={{ padding: '5px 12px', fontSize: 11, opacity: nextId ? 1 : 0.4 }}>{t('Next')} →</button>
        </div>
      )}

      {preview && <PreviewModal id={preview.id} title={preview.title} onClose={() => setPreview(null)} />}
    </>
  )
}

/* ───────────────────────── PAGE ───────────────────────── */
export default function ControlsPage() {
  const [params, setParams] = useSearchParams()
  const deep = params.get('control')
  const [selected, setSelected] = useState<string | null>(deep)
  useEffect(() => { if (deep && deep !== selected) setSelected(deep) }, [deep])
  const open = (cid: string | null) => {
    setSelected(cid)
    if (!cid && params.get('control')) { params.delete('control'); setParams(params, { replace: true }) }
  }
  return selected
    ? <ControlDetail id={selected} onBack={() => open(null)} onOpen={open} />
    : <ControlsList onOpen={open} />
}
