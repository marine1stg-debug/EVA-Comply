import { useEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT, useI18n } from '../lib/i18n'
import { VideoPlayer, type VideoRef } from '../lib/video'

// Modals must render at <body> level: the page sections use a CSS animation that
// leaves a lingering transform, which would otherwise anchor position:fixed here.
function Modal({ onClose, maxWidth = 560, title, children }: { onClose: () => void; maxWidth?: number; title: string; children: React.ReactNode }) {
  const t = useT()
  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{title}</span><button className="ev-action-btn" onClick={onClose}>{t('✕') || '✕'}</button></div>
        <div className="modal-body">{children}</div>
      </div>
    </div>,
    document.body,
  )
}

interface FwOpt { id: string; name: string }
interface CtrlVideo { id: string; ref: string; title: string; domain: string; video: VideoRef }
interface Payload {
  framework: { id: string; name: string; version: string; video: VideoRef }
  controls: CtrlVideo[]
  can_edit: boolean
}

/* ── Webcam recorder modal (with a teleprompter brief beside the camera) ── */
function RecordModal({ uploadPath, onClose, onSaved, briefId }: { uploadPath: string; onClose: () => void; onSaved: () => void; briefId?: string }) {
  const t = useT()
  const { lang } = useI18n()
  const { data: brief } = useQuery<any>({
    queryKey: ['ctrl-brief', briefId, lang], enabled: !!briefId,
    queryFn: async () => (await api.get(`/videos/control/${briefId}/brief`)).data,
  })
  const script = brief ? (lang === 'fr' ? brief.script_fr : brief.script_en) : ''
  const videoRef = useRef<HTMLVideoElement>(null)
  const recRef = useRef<MediaRecorder | null>(null)
  const chunks = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const [phase, setPhase] = useState<'idle' | 'recording' | 'review'>('idle')
  const [blob, setBlob] = useState<Blob | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [err, setErr] = useState('')

  useEffect(() => {
    navigator.mediaDevices?.getUserMedia({ video: true, audio: true })
      .then(stream => { streamRef.current = stream; if (videoRef.current) { videoRef.current.srcObject = stream; videoRef.current.muted = true; videoRef.current.play().catch(() => {}) } })
      .catch(() => setErr(t('Cannot access camera/microphone. Check browser permissions.')))
    return () => { streamRef.current?.getTracks().forEach(tr => tr.stop()); if (previewUrl) URL.revokeObjectURL(previewUrl) }
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const start = () => {
    if (!streamRef.current) return
    chunks.current = []
    const mr = new MediaRecorder(streamRef.current, { mimeType: 'video/webm' })
    mr.ondataavailable = e => { if (e.data.size) chunks.current.push(e.data) }
    mr.onstop = () => {
      const b = new Blob(chunks.current, { type: 'video/webm' })
      setBlob(b); setPreviewUrl(URL.createObjectURL(b)); setPhase('review')
    }
    recRef.current = mr; mr.start(); setPhase('recording')
  }
  const stop = () => recRef.current?.stop()
  const upload = async () => {
    if (!blob) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('file', new File([blob], 'recording.webm', { type: 'video/webm' }))
      await api.post(uploadPath, fd)
      toast.success(t('Video saved')); onSaved(); onClose()
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Upload failed')) }
    finally { setUploading(false) }
  }

  const RequirementPanel = () => (
    <div style={{ flex: '1 1 280px', minWidth: 240, maxHeight: 420, overflow: 'auto', paddingLeft: 14, borderLeft: '1px solid var(--border-l)' }}>
      {brief?.description && <div style={{ marginBottom: 10 }}><div className="plain-hdr">{t('📋 Requirement')}</div>
        <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{brief.description}</div></div>}
      {brief?.objective && <div style={{ marginBottom: 10 }}><div className="plain-hdr">{t('🎯 Objective')}</div>
        <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{brief.objective}</div></div>}
      {brief?.best_practices && <div><div className="plain-hdr">{t('✅ Key points to cover')}</div>
        <div style={{ fontSize: 12, color: 'var(--text2)', lineHeight: 1.55, whiteSpace: 'pre-wrap' }}>{brief.best_practices}</div></div>}
    </div>
  )
  const ScriptPanel = () => (
    <div style={{ width: '100%', maxHeight: '38vh', overflow: 'auto', borderTop: '1px solid var(--border-l)', paddingTop: 12, marginTop: 4 }}>
      <div className="plain-hdr">{t('🎬 What to say — Suggestion (Script)')}</div>
      {script
        ? <div style={{ fontSize: 16, color: 'var(--text)', lineHeight: 1.95, whiteSpace: 'pre-wrap', marginTop: 6 }}>{script}</div>
        : <div className="page-sub" style={{ marginTop: 4 }}>{t('No script yet — generate it from the Control preview.')}</div>}
    </div>
  )

  return (
    <Modal title={t('Record a video')} onClose={onClose} maxWidth={briefId ? 1000 : 560}>
      {err ? <div className="page-sub" style={{ color: 'var(--red)' }}>{err}</div> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {/* Top: camera + requirement side by side */}
          <div style={{ display: 'flex', gap: 14, flexWrap: 'wrap', alignItems: 'flex-start' }}>
            <div style={{ flex: briefId ? '1 1 380px' : 1, maxWidth: '100%' }}>
              {phase !== 'review'
                ? <video ref={videoRef} style={{ width: '100%', borderRadius: 8, background: '#000', maxHeight: 320 }} playsInline />
                : <video src={previewUrl || undefined} controls style={{ width: '100%', borderRadius: 8, background: '#000', maxHeight: 320 }} />}
              <div style={{ display: 'flex', gap: 8, marginTop: 12, justifyContent: 'center' }}>
                {phase === 'idle' && <button className="submit-btn" onClick={start}>● {t('Start recording')}</button>}
                {phase === 'recording' && <button className="tb-btn" style={{ color: 'var(--red)' }} onClick={stop}>■ {t('Stop')}</button>}
                {phase === 'review' && <>
                  <button className="tb-btn" onClick={() => setPhase('idle')}>↺ {t('Re-record')}</button>
                  <button className="submit-btn" disabled={uploading} onClick={upload}>{uploading ? t('Saving…') : t('Use this recording')}</button>
                </>}
              </div>
            </div>
            {briefId && <RequirementPanel />}
          </div>
          {/* Bottom: full-width script teleprompter */}
          {briefId && <ScriptPanel />}
        </div>
      )}
    </Modal>
  )
}

/* ── Recording brief — shows the control so the recorder knows what to cover ── */
function BriefModal({ controlId, onClose }: { controlId: string; onClose: () => void }) {
  const t = useT()
  const { lang } = useI18n()
  const qc = useQueryClient()
  const { data } = useQuery<any>({ queryKey: ['ctrl-brief', controlId, lang], queryFn: async () => (await api.get(`/videos/control/${controlId}/brief`)).data })
  const [gen, setGen] = useState(false)
  const [draft, setDraft] = useState('')
  const [dirty, setDirty] = useState(false)
  const [showPrompt, setShowPrompt] = useState(false)
  const [instructions, setInstructions] = useState('')
  const Section = ({ title, text }: { title: string; text?: string }) => text
    ? <div style={{ marginTop: 12 }}><div className="plain-hdr">{title}</div>
        <div style={{ fontSize: 12.5, color: 'var(--text2)', lineHeight: 1.6, whiteSpace: 'pre-wrap' }}>{text}</div></div>
    : null
  const script = lang === 'fr' ? (data?.script_fr || '') : (data?.script_en || '')
  useEffect(() => { if (!dirty) setDraft(script) }, [script, lang]) // eslint-disable-line react-hooks/exhaustive-deps
  const generate = async () => {
    setGen(true)
    try {
      await api.post(`/videos/control/${controlId}/script/generate`, { lang, instructions })
      setDirty(false); setShowPrompt(false)
      await qc.invalidateQueries({ queryKey: ['ctrl-brief', controlId] })
      toast.success(t('Script generated'))
    } catch { toast.error(t('Generation failed')) }
    finally { setGen(false) }
  }
  const save = async () => {
    try {
      await api.put(`/videos/control/${controlId}/script`, lang === 'fr' ? { script_fr: draft } : { script_en: draft })
      setDirty(false)
      await qc.invalidateQueries({ queryKey: ['ctrl-brief', controlId] })
      toast.success(t('Saved'))
    } catch { toast.error(t('Save failed')) }
  }
  const delVideo = async () => {
    if (!window.confirm(t('Delete this video? You can record or link a new one afterwards.'))) return
    try {
      await api.delete(`/videos/control/${controlId}/video`)
      await qc.invalidateQueries({ queryKey: ['ctrl-brief', controlId] })
      await qc.invalidateQueries({ queryKey: ['fw-videos'] })
      toast.success(t('Video deleted'))
    } catch { toast.error(t('Delete failed')) }
  }
  return (
    <Modal title={t('Recording brief') + (data ? ` — ${data.ref}` : '')} onClose={onClose} maxWidth={980}>
      {!data ? <div className="page-sub">{t('Loading…')}</div> : (
        <>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 14, fontWeight: 600 }}>{data.title}</span>
            {data.video?.kind && <span className="badge b-green" style={{ fontSize: 9 }}>{data.video.kind === 'file' ? t('🎥 recorded') : t('🔗 link')}</span>}
            {data.video?.kind && <button className="ev-action-btn delete" onClick={delVideo}>🗑 {t('Delete video')}</button>}
          </div>
          <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
            {/* Left: the control context (narrower) */}
            <div style={{ flex: '0 0 320px', minWidth: 260, maxHeight: 480, overflow: 'auto' }}>
              <Section title={t('📋 Requirement')} text={data.description} />
              <Section title={t('🎯 Objective')} text={data.objective} />
              <Section title={t('💡 In plain language')} text={data.plain_language} />
              <Section title={t('✅ Key points to cover')} text={data.best_practices} />
              <Section title={t('📎 Expected evidence')} text={data.evidence_best_practices} />
            </div>

            {/* Right: the editable script (wider) */}
            <div style={{ flex: '1 1 480px', minWidth: 300, borderLeft: '1px solid var(--border-l)', paddingLeft: 16 }}>
              <div className="plain-hdr">{t('🎬 What to say — Suggestion (Script)')} · {lang.toUpperCase()}</div>
              <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 6 }}>
                <button className="ev-action-btn" disabled={!draft} onClick={() => { navigator.clipboard?.writeText(draft); toast.success(t('Copied')) }}>{t('Copy')}</button>
                <button className="tb-btn" onClick={() => setShowPrompt(s => !s)}>✦ {draft ? t('Regenerate') : t('Generate script')}</button>
                <button className="submit-btn" disabled={!dirty} onClick={save}>{t('Save')}</button>
              </div>

              {showPrompt && (
                <div style={{ marginTop: 8, padding: '10px 12px', background: 'var(--soft)', border: '1px solid var(--border-l)', borderRadius: 8 }}>
                  <div className="form-label">{t('Instructions / suggestions for the AI (optional)')}</div>
                  <textarea className="form-textarea" rows={2} style={{ width: '100%', boxSizing: 'border-box' }} value={instructions} onChange={e => setInstructions(e.target.value)}
                    placeholder={t('e.g. make it shorter, add an analogy about keys, mention multi-factor authentication…')} />
                  <div style={{ display: 'flex', gap: 8, marginTop: 8 }}>
                    <button className="submit-btn" disabled={gen} onClick={generate}>{gen ? t('Generating…') : t('Generate')}</button>
                    <button className="tb-btn" onClick={() => setShowPrompt(false)}>{t('Cancel')}</button>
                  </div>
                </div>
              )}

              <textarea className="form-textarea" rows={14} style={{ marginTop: 8, lineHeight: 1.6, width: '100%' }}
                placeholder={t('No script yet — generate or write it here.')}
                value={draft} onChange={e => { setDraft(e.target.value); setDirty(true) }} />
            </div>
          </div>
        </>
      )}
    </Modal>
  )
}

/* ── One editable video target (framework overview or a control) ── */
function VideoEditor({ label, sub, video, linkPath, uploadPath, deletePath, onChanged, briefId }: {
  label: string; sub?: string; video: VideoRef; linkPath: string; uploadPath: string; deletePath: string; onChanged: () => void; briefId?: string
}) {
  const t = useT()
  const [url, setUrl] = useState(video.kind === 'link' ? (video.url || '') : '')
  const [recording, setRecording] = useState(false)
  const [open, setOpen] = useState(false)
  const [brief, setBrief] = useState(false)
  const saveLink = useMutation({
    mutationFn: async (value: string) => (await api.put(linkPath, { url: value })).data,
    onSuccess: () => { toast.success(t('Saved')); onChanged() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const del = useMutation({
    mutationFn: async () => (await api.delete(deletePath)).data,
    onSuccess: () => { toast.success(t('Video deleted')); setUrl(''); setOpen(false); onChanged() },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Delete failed')),
  })
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
        <div style={{ minWidth: 0, flex: 1 }}>
          <div style={{ fontSize: 12.5, fontWeight: 600 }}>{label}{video.kind && <span className="badge b-green" style={{ fontSize: 9, marginLeft: 6 }}>{video.kind === 'file' ? t('🎥 recorded') : t('🔗 link')}</span>}</div>
          {sub && <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>{sub}</div>}
        </div>
        {briefId && <button className="ev-action-btn" style={{ background: 'var(--soft)', color: 'var(--brand)', borderColor: 'var(--border-l)' }}
          onClick={() => setBrief(true)} title={t('See the control & key points to cover')}>👁 {t('Control preview')}</button>}
        <input className="form-input" style={{ flex: 2, minWidth: 200, fontSize: 12 }} placeholder={t('Paste Vimeo / YouTube / URL')}
          value={url} onChange={e => setUrl(e.target.value)} />
        <button className="tb-btn" disabled={saveLink.isPending} onClick={() => saveLink.mutate(url)}>{t('Save link')}</button>
        <button className="tb-btn" onClick={() => setRecording(true)}>🎥 {t('Record')}</button>
        {video.kind && <button className="ev-action-btn" onClick={() => setOpen(o => !o)}>{open ? t('Hide') : t('Preview')}</button>}
        {video.kind && <button className="ev-action-btn delete" disabled={del.isPending}
          onClick={() => { if (window.confirm(t('Delete this video? You can record or link a new one afterwards.'))) del.mutate() }}>🗑 {t('Delete video')}</button>}
      </div>
      {open && video.kind && <VideoPlayer video={video} />}
      {recording && <RecordModal uploadPath={uploadPath} briefId={briefId} onClose={() => setRecording(false)} onSaved={onChanged} />}
      {brief && briefId && <BriefModal controlId={briefId} onClose={() => setBrief(false)} />}
    </div>
  )
}

function ReuseView() {
  const t = useT()
  const qc = useQueryClient()
  const { data, isLoading } = useQuery<{ suggestions: any[] }>({
    queryKey: ['reuse-suggestions'], queryFn: async () => (await api.get('/videos/reuse/suggestions')).data,
  })
  const [sel, setSel] = useState<Record<string, boolean>>({})
  const k = (s: any) => `${s.source.control_id}|${s.target.control_id}`
  const apply = useMutation({
    mutationFn: async (pairs: any[]) => (await api.post('/videos/reuse/apply', { pairs })).data,
    onSuccess: (r: any) => { toast.success(t('{n} videos applied', { n: r.applied })); qc.invalidateQueries({ queryKey: ['reuse-suggestions'] }); qc.invalidateQueries({ queryKey: ['fw-videos'] }); setSel({}) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  if (isLoading) return <div className="page-sub">{t('Loading…')}</div>
  if (!data) return null
  const sugg = data.suggestions || []
  const chosen = sugg.filter(s => sel[k(s)])
  return (
    <div className="detail-section fi">
      <div className="card-hdr" style={{ marginBottom: 8 }}>
        <span className="card-title">{t('Reuse videos across frameworks')}</span>
        <span className="page-sub" style={{ fontSize: 10.5 }}>{t('{n} suggested matches', { n: sugg.length })}</span>
      </div>
      <div className="page-sub" style={{ marginBottom: 10 }}>{t('These controls in other frameworks match a control that already has a video. Confirm which ones should reuse it.')}</div>
      {sugg.length === 0 ? <div className="page-sub">{t('No reuse opportunities found.')}</div> : (
        <>
          <div style={{ display: 'flex', gap: 8, marginBottom: 10 }}>
            <button className="tb-btn" onClick={() => setSel(Object.fromEntries(sugg.map(s => [k(s), true])))}>{t('Select all')}</button>
            <button className="tb-btn" onClick={() => setSel({})}>{t('Clear')}</button>
            <button className="submit-btn" style={{ marginLeft: 'auto' }} disabled={!chosen.length || apply.isPending}
              onClick={() => apply.mutate(chosen.map(s => ({ source_control_id: s.source.control_id, target_control_id: s.target.control_id })))}>
              {apply.isPending ? t('Applying…') : t('Apply {n} selected', { n: chosen.length })}
            </button>
          </div>
          <div className="ev-table-wrap">
            <table className="ev-table">
              <thead><tr><th></th><th>{t('Video from')}</th><th>{t('Apply to')}</th><th>{t('Match')}</th></tr></thead>
              <tbody>
                {sugg.map(s => (
                  <tr key={k(s)}>
                    <td><input type="checkbox" checked={!!sel[k(s)]} onChange={e => setSel(m => ({ ...m, [k(s)]: e.target.checked }))} /></td>
                    <td><div style={{ fontWeight: 600, fontSize: 12 }}>{s.source.ref}</div>
                      <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>{s.source.framework} · {s.source.video.kind === 'file' ? t('🎥 recorded') : t('🔗 link')}</div></td>
                    <td><div style={{ fontWeight: 600, fontSize: 12 }}>{s.target.ref} — {s.target.title}</div>
                      <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>{s.target.framework}</div></td>
                    <td><span className="badge b-gray" style={{ fontSize: 9 }}>{s.reason === 'mapping' ? t('mapping') : t('same title')}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </div>
  )
}

export default function TrainingPage() {
  const t = useT()
  const { lang } = useI18n()
  const qc = useQueryClient()
  const [mode, setMode] = useState<'videos' | 'reuse'>('videos')
  const [fwId, setFwId] = useState('')
  const [fws, setFws] = useState<FwOpt[]>([])
  const [q, setQ] = useState('')
  useEffect(() => {
    api.get('/auth/signup-options').then(r => {
      const list: FwOpt[] = r.data.frameworks || []
      setFws(list); if (list[0]) setFwId(list[0].id)
    }).catch(() => {})
  }, [])

  const { data, isLoading } = useQuery<Payload>({
    queryKey: ['fw-videos', fwId, lang],
    queryFn: async () => (await api.get(`/videos/framework/${fwId}`)).data,
    enabled: !!fwId,
  })
  const refresh = () => qc.invalidateQueries({ queryKey: ['fw-videos', fwId] })
  const genAll = useMutation({
    mutationFn: async () => (await api.post(`/videos/framework/${fwId}/scripts/generate`, { lang })).data,
    onSuccess: (r: any) => { toast.success(t('Generated {n} scripts', { n: r.created })) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Generation failed')),
  })
  const controls = (data?.controls || []).filter(c =>
    !q || c.ref.toLowerCase().includes(q.toLowerCase()) || c.title.toLowerCase().includes(q.toLowerCase()))
  const withVideo = (data?.controls || []).filter(c => c.video.kind).length

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Training videos')}</div>
          <div className="page-sub">{t('Add an overview video per framework and a short video per control. Paste a Vimeo/YouTube link or record from your webcam.')}</div>
        </div>
      </div>

      <div className="aq-filters fi">
        {([['videos', '🎬 ' + t('Videos')], ['reuse', '♻ ' + t('Reuse across frameworks')]] as const).map(([v, l]) => (
          <button key={v} onClick={() => setMode(v)}
            style={{ padding: '5px 14px', borderRadius: 7, border: `1px solid ${mode === v ? 'var(--eva-blue2)' : 'var(--border-l)'}`,
              background: mode === v ? 'var(--eva-blue2)' : 'var(--card)', color: mode === v ? '#fff' : 'var(--text2)',
              fontSize: 11, fontWeight: 600, cursor: 'pointer', fontFamily: 'var(--font)' }}>{l}</button>
        ))}
      </div>

      {mode === 'reuse' ? <ReuseView /> : (
        <>
          <div className="filter-bar fi">
            <select className="filter-select" value={fwId} onChange={e => setFwId(e.target.value)}>
              {fws.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
            </select>
            {data && <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{t('{n} of {total} controls have a video', { n: withVideo, total: data.controls.length })}</span>}
            {data?.can_edit && <button className="tb-btn" disabled={genAll.isPending} title={t('Generate a script for every control that doesn’t have one')}
              onClick={() => genAll.mutate()}>✦ {genAll.isPending ? t('Generating…') : t('Generate all scripts')}</button>}
          </div>

          {(
            <>
              {isLoading && <div className="page-sub">{t('Loading…')}</div>}
              {data && !data.can_edit && <div className="detail-section fi"><div className="page-sub">{t('Only the Super Admin can edit training videos.')}</div></div>}
              {data && data.can_edit && (
                <>
                  <div className="detail-section fi" style={{ marginBottom: 16 }}>
            <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Framework overview video')}</span></div>
            <VideoEditor label={data.framework.name} sub={data.framework.version}
              video={data.framework.video}
              linkPath={`/videos/framework/${data.framework.id}/link`}
              uploadPath={`/videos/framework/${data.framework.id}/upload`}
              deletePath={`/videos/framework/${data.framework.id}/video`}
              onChanged={refresh} />
          </div>

          <div className="detail-section fi">
            <div className="card-hdr" style={{ marginBottom: 10 }}>
              <span className="card-title">{t('Per-control videos')}</span>
              <input className="form-input" style={{ width: 220, fontSize: 12 }} placeholder={t('Filter controls…')} value={q} onChange={e => setQ(e.target.value)} />
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              {controls.map(c => (
                <div key={c.id} style={{ borderTop: '1px solid var(--border-l)', paddingTop: 12 }}>
                  <VideoEditor label={`${c.ref} — ${c.title}`} sub={c.domain} video={c.video}
                    linkPath={`/videos/control/${c.id}/link`}
                    uploadPath={`/videos/control/${c.id}/upload`}
                    deletePath={`/videos/control/${c.id}/video`}
                    briefId={c.id}
                    onChanged={refresh} />
                </div>
              ))}
              {controls.length === 0 && <div className="page-sub">{t('No controls match this filter.')}</div>}
            </div>
          </div>
                </>
              )}
            </>
          )}
        </>
      )}
    </>
  )
}
