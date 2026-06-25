import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Crop, X, Image as ImageIcon, Send, GripHorizontal } from 'lucide-react'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

/**
 * Floating, draggable capture + quick-request tool (Super Admin only). Opened by
 * the bug button in the top bar or the keyboard shortcut. Capture is done with
 * the browser's native screen-capture API, so the screenshot is the REAL pixels
 * (never a faded DOM re-render); you then crop to the area you want. You can also
 * paste an OS screenshot. Logs to the Improvement/Request list.
 *
 * Shortcut: Ctrl/Cmd + Shift + E (cross-platform, avoids new-tab/devtools chords).
 */
interface Shot { id: string; url: string; blob: Blob }
const CATS = ['bug', 'idea', 'question', 'other']
const PRIOS = ['low', 'medium', 'high']

export default function DevFeedback() {
  const t = useT()
  const qc = useQueryClient()
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState({ x: window.innerWidth - 380, y: 84 })
  const [title, setTitle] = useState('')
  const [body, setBody] = useState('')
  const [category, setCategory] = useState('bug')
  const [priority, setPriority] = useState('medium')
  const [shots, setShots] = useState<Shot[]>([])
  const [busy, setBusy] = useState(false)
  const [hideUI, setHideUI] = useState(false)          // hide the panel while grabbing the frame
  const [frame, setFrame] = useState<string | null>(null)  // captured still (data URL) → crop mode
  const [sel, setSel] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
  const dragStart = useRef<{ mx: number; my: number; px: number; py: number } | null>(null)
  const selStart = useRef<{ x: number; y: number } | null>(null)
  const imgRef = useRef<HTMLImageElement | null>(null)

  const reset = () => { setTitle(''); setBody(''); setCategory('bug'); setPriority('medium'); shots.forEach(s => URL.revokeObjectURL(s.url)); setShots([]) }
  const close = () => { setOpen(false); setFrame(null); setSel(null) }

  // ── open via shortcut / top-bar button ──────────────────────────────────
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && (e.key === 'e' || e.key === 'E')) {
        e.preventDefault(); setOpen(o => !o)
      }
    }
    const onOpen = () => setOpen(true)
    window.addEventListener('keydown', onKey)
    window.addEventListener('eva-open-devtool', onOpen as EventListener)
    return () => { window.removeEventListener('keydown', onKey); window.removeEventListener('eva-open-devtool', onOpen as EventListener) }
  }, [])

  // ── paste a screenshot from the clipboard ───────────────────────────────
  useEffect(() => {
    if (!open) return
    const onPaste = (e: ClipboardEvent) => {
      const items = e.clipboardData?.items
      if (!items) return
      for (const it of items) {
        if (it.type.startsWith('image/')) {
          const blob = it.getAsFile()
          if (blob) { addShot(blob); toast.success(t('Screenshot pasted')) }
        }
      }
    }
    window.addEventListener('paste', onPaste)
    return () => window.removeEventListener('paste', onPaste)
  }, [open]) // eslint-disable-line react-hooks/exhaustive-deps

  const addShot = (blob: Blob) => setShots(s => [...s, { id: Math.random().toString(36).slice(2), url: URL.createObjectURL(blob), blob }])
  const removeShot = (id: string) => setShots(s => { const f = s.find(x => x.id === id); if (f) URL.revokeObjectURL(f.url); return s.filter(x => x.id !== id) })

  // ── drag the panel by its header ────────────────────────────────────────
  const onHeaderDown = (e: React.PointerEvent) => {
    dragStart.current = { mx: e.clientX, my: e.clientY, px: pos.x, py: pos.y }
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }
  const onHeaderMove = (e: React.PointerEvent) => {
    if (!dragStart.current) return
    const d = dragStart.current
    setPos({ x: Math.max(0, Math.min(window.innerWidth - 60, d.px + (e.clientX - d.mx))), y: Math.max(0, Math.min(window.innerHeight - 40, d.py + (e.clientY - d.my))) })
  }
  const onHeaderUp = () => { dragStart.current = null }

  // ── native screen capture → still image → crop ──────────────────────────
  const captureScreen = async () => {
    const md: any = navigator.mediaDevices
    if (!md?.getDisplayMedia) { toast.error(t('Screen capture not supported - paste a screenshot instead')); return }
    let stream: MediaStream | null = null
    try {
      // Hide our panel so it isn't part of the captured frame.
      setHideUI(true)
      await new Promise(r => setTimeout(r, 120))
      stream = await md.getDisplayMedia({ video: { displaySurface: 'browser' }, audio: false, preferCurrentTab: true })
      const video = document.createElement('video')
      video.srcObject = stream as MediaStream
      await video.play()
      await new Promise(r => setTimeout(r, 250))  // let the picker close + first frames flow
      const canvas = document.createElement('canvas')
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      canvas.getContext('2d')!.drawImage(video, 0, 0)
      setFrame(canvas.toDataURL('image/png'))
      setSel(null)
    } catch (e: any) {
      if (e?.name !== 'NotAllowedError') toast.error(t('Screen capture not available - paste a screenshot instead'))
    } finally {
      stream?.getTracks().forEach(tk => tk.stop())
      setHideUI(false)
    }
  }

  const onSelDown = (e: React.PointerEvent) => {
    selStart.current = { x: e.clientX, y: e.clientY }
    setSel({ x: e.clientX, y: e.clientY, w: 0, h: 0 })
    ;(e.target as HTMLElement).setPointerCapture(e.pointerId)
  }
  const onSelMove = (e: React.PointerEvent) => {
    if (!selStart.current) return
    const s = selStart.current
    setSel({ x: Math.min(s.x, e.clientX), y: Math.min(s.y, e.clientY), w: Math.abs(e.clientX - s.x), h: Math.abs(e.clientY - s.y) })
  }
  const onSelUp = () => { selStart.current = null }

  const cropFromImg = (region: { x: number; y: number; w: number; h: number } | null): Promise<Blob | null> => {
    const img = imgRef.current
    if (!img) return Promise.resolve(null)
    const rect = img.getBoundingClientRect()
    const scaleX = img.naturalWidth / rect.width
    const scaleY = img.naturalHeight / rect.height
    let sx = 0, sy = 0, sw = img.naturalWidth, sh = img.naturalHeight
    if (region && region.w > 6 && region.h > 6) {
      const left = Math.max(region.x, rect.left), top = Math.max(region.y, rect.top)
      const right = Math.min(region.x + region.w, rect.right), bottom = Math.min(region.y + region.h, rect.bottom)
      sx = (left - rect.left) * scaleX; sy = (top - rect.top) * scaleY
      sw = Math.max(1, (right - left) * scaleX); sh = Math.max(1, (bottom - top) * scaleY)
    }
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(sw); canvas.height = Math.round(sh)
    canvas.getContext('2d')!.drawImage(img, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height)
    return new Promise(res => canvas.toBlob(b => res(b), 'image/png'))
  }

  const useCrop = async (whole: boolean) => {
    const blob = await cropFromImg(whole ? null : sel)
    if (blob) { addShot(blob); toast.success(t('Screenshot added')) }
    setFrame(null); setSel(null)
  }

  const submit = async () => {
    const finalTitle = (title.trim() || body.trim().slice(0, 60) || 'Untitled request')
    if (!body.trim() && !shots.length && !title.trim()) { toast.error(t('Add a note or a screenshot first')); return }
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('title', finalTitle)
      fd.append('body', body)
      fd.append('category', category)
      fd.append('priority', priority)
      fd.append('page_url', window.location.pathname)
      shots.forEach((s, i) => fd.append('files', s.blob, `screenshot_${i + 1}.png`))
      await api.post('/improvements/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      qc.invalidateQueries({ queryKey: ['improvements'] })
      toast.success(t('Request logged'))
      reset()
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || t('Could not save the request'))
    } finally { setBusy(false) }
  }

  if (!open) return null

  const fieldStyle: React.CSSProperties = { width: '100%', padding: '7px 9px', borderRadius: 8, border: '1px solid var(--border-l)', background: 'var(--card)', color: 'var(--text)', fontSize: 12.5 }

  return (
    <>
      {/* Crop overlay (shown on a captured still — pixel-perfect, no re-render) */}
      {frame && (
        <div data-eva-devtool="1" style={{ position: 'fixed', inset: 0, zIndex: 2147483646, background: 'rgba(0,0,0,.66)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 12 }}>
          <div style={{ color: '#fff', fontSize: 13, fontWeight: 600 }}>{t('Drag to select the area to keep')}</div>
          <img ref={imgRef} src={frame} draggable={false}
            onPointerDown={onSelDown} onPointerMove={onSelMove} onPointerUp={onSelUp}
            style={{ maxWidth: '92vw', maxHeight: '76vh', cursor: 'crosshair', userSelect: 'none', borderRadius: 6, boxShadow: '0 8px 30px rgba(0,0,0,.5)' }} />
          {sel && sel.w > 1 && <div style={{ position: 'fixed', left: sel.x, top: sel.y, width: sel.w, height: sel.h, border: '2px solid #1A8FD1', background: 'rgba(26,143,209,.15)', pointerEvents: 'none' }} />}
          <div style={{ display: 'flex', gap: 8 }}>
            <button className="submit-btn" onClick={() => useCrop(false)} style={{ justifyContent: 'center' }}>{t('Use selection')}</button>
            <button className="tb-btn" style={{ color: '#fff', borderColor: 'rgba(255,255,255,.4)' }} onClick={() => useCrop(true)}>{t('Use whole image')}</button>
            <button className="tb-btn" style={{ color: '#fff', borderColor: 'rgba(255,255,255,.4)' }} onClick={() => { setFrame(null); setSel(null) }}>{t('Cancel')}</button>
          </div>
        </div>
      )}

      {/* Floating panel */}
      <div data-eva-devtool="1" style={{ position: 'fixed', left: pos.x, top: pos.y, width: 340, maxWidth: '94vw', zIndex: 2147483645,
        background: 'var(--card2, var(--card))', border: '1px solid var(--border, rgba(0,0,0,.15))', borderRadius: 12,
        boxShadow: '0 12px 40px rgba(0,0,0,.28)', display: hideUI ? 'none' : 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div onPointerDown={onHeaderDown} onPointerMove={onHeaderMove} onPointerUp={onHeaderUp}
          style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '9px 12px', cursor: 'grab', background: 'var(--eva-blue2, #1A8FD1)', color: '#fff', touchAction: 'none' }}>
          <GripHorizontal size={14} aria-hidden />
          <span style={{ fontSize: 13, fontWeight: 700, flex: 1 }}>{t('New request')}</span>
          <button onClick={close} style={{ background: 'transparent', border: 'none', color: '#fff', cursor: 'pointer', padding: 2 }}><X size={16} aria-hidden /></button>
        </div>

        <div style={{ padding: 12, display: 'grid', gap: 8 }}>
          <input value={title} onChange={e => setTitle(e.target.value)} placeholder={t('Short title')} style={fieldStyle} />
          <textarea value={body} onChange={e => setBody(e.target.value)} rows={4} placeholder={t('Describe what to fix or improve… (you can paste a screenshot here)')} style={{ ...fieldStyle, resize: 'vertical' }} />
          <div style={{ display: 'flex', gap: 8 }}>
            <select value={category} onChange={e => setCategory(e.target.value)} style={{ ...fieldStyle, flex: 1 }}>
              {CATS.map(c => <option key={c} value={c}>{t(c === 'bug' ? 'Bug / fix' : c === 'idea' ? 'Improvement' : c === 'question' ? 'Question' : 'Other')}</option>)}
            </select>
            <select value={priority} onChange={e => setPriority(e.target.value)} style={{ ...fieldStyle, flex: 1 }}>
              {PRIOS.map(p => <option key={p} value={p}>{t(p === 'low' ? 'Low' : p === 'medium' ? 'Medium' : 'High')}</option>)}
            </select>
          </div>

          <button className="tb-btn" onClick={captureScreen} style={{ justifyContent: 'center' }}>
            <Crop size={14} aria-hidden /> {t('Capture screenshot')}
          </button>

          {shots.length > 0 && (
            <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
              {shots.map(s => (
                <div key={s.id} style={{ position: 'relative' }}>
                  <img src={s.url} alt="" style={{ width: 64, height: 48, objectFit: 'cover', borderRadius: 6, border: '1px solid var(--border-l)' }} />
                  <button onClick={() => removeShot(s.id)} title={t('Remove')}
                    style={{ position: 'absolute', top: -6, right: -6, width: 18, height: 18, borderRadius: '50%', border: 'none', background: '#DC2626', color: '#fff', cursor: 'pointer', fontSize: 10, lineHeight: '18px', padding: 0 }}>×</button>
                </div>
              ))}
            </div>
          )}

          <div style={{ fontSize: 10.5, color: 'var(--text3)', display: 'flex', alignItems: 'center', gap: 4 }}>
            <ImageIcon size={11} aria-hidden /> {t('Tip: capture the screen and crop, or paste an OS screenshot here.')}
          </div>

          <button className="submit-btn" onClick={submit} disabled={busy} style={{ justifyContent: 'center' }}>
            <Send size={14} aria-hidden /> {busy ? t('Saving…') : t('Log request')}
          </button>
        </div>
      </div>
    </>
  )
}
