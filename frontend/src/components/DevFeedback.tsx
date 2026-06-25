import { useEffect, useRef, useState, useCallback } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Crop, X, Image as ImageIcon, Send, GripHorizontal } from 'lucide-react'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

/**
 * Floating, draggable capture + quick-request tool (Super Admin only). Opened by
 * the camera button in the top bar or the keyboard shortcut. Lets you select a
 * region of the app (rendered with html2canvas), paste a screenshot, write a
 * note, and log it to the Improvement/Request list - all without leaving the page.
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
  const [capturing, setCapturing] = useState(false)
  const [hideUI, setHideUI] = useState(false)        // hide our own UI during capture
  const [sel, setSel] = useState<{ x: number; y: number; w: number; h: number } | null>(null)
  const dragStart = useRef<{ mx: number; my: number; px: number; py: number } | null>(null)
  const selStart = useRef<{ x: number; y: number } | null>(null)

  const reset = () => { setTitle(''); setBody(''); setCategory('bug'); setPriority('medium'); shots.forEach(s => URL.revokeObjectURL(s.url)); setShots([]) }
  const close = () => { setOpen(false); setCapturing(false) }

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

  // ── region capture (html2canvas) ────────────────────────────────────────
  const beginCapture = () => { setCapturing(true); setSel(null) }
  const onSelDown = (e: React.PointerEvent) => { selStart.current = { x: e.clientX, y: e.clientY }; setSel({ x: e.clientX, y: e.clientY, w: 0, h: 0 }) }
  const onSelMove = (e: React.PointerEvent) => {
    if (!selStart.current) return
    const s = selStart.current
    setSel({ x: Math.min(s.x, e.clientX), y: Math.min(s.y, e.clientY), w: Math.abs(e.clientX - s.x), h: Math.abs(e.clientY - s.y) })
  }
  const onSelUp = useCallback(async () => {
    const region = sel
    selStart.current = null
    setCapturing(false)
    if (!region || region.w < 8 || region.h < 8) { setSel(null); return }
    setHideUI(true)
    // Let the overlay/panel disappear from the DOM paint before snapshotting.
    await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))
    try {
      const html2canvas = (await import('html2canvas')).default
      const canvas = await html2canvas(document.body, {
        x: region.x + window.scrollX, y: region.y + window.scrollY,
        width: region.w, height: region.h,
        scale: Math.min(2, window.devicePixelRatio || 1),
        useCORS: true, logging: false, scrollX: 0, scrollY: 0,
        windowWidth: document.documentElement.scrollWidth,
        windowHeight: document.documentElement.scrollHeight,
      })
      const blob: Blob | null = await new Promise(res => canvas.toBlob(b => res(b), 'image/png'))
      if (blob) { addShot(blob); toast.success(t('Region captured')) }
      else toast.error(t('Capture failed - try pasting a screenshot instead'))
    } catch {
      toast.error(t('Capture failed - try pasting a screenshot instead'))
    } finally {
      setHideUI(false); setSel(null)
    }
  }, [sel]) // eslint-disable-line react-hooks/exhaustive-deps

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
      {/* Region-select overlay */}
      {capturing && (
        <div onPointerDown={onSelDown} onPointerMove={onSelMove} onPointerUp={onSelUp}
          style={{ position: 'fixed', inset: 0, zIndex: 2147483646, cursor: 'crosshair', background: 'rgba(13,42,67,.18)' }}>
          <div style={{ position: 'fixed', top: 14, left: '50%', transform: 'translateX(-50%)', background: 'var(--eva-blue2, #1A8FD1)', color: '#fff', padding: '6px 14px', borderRadius: 999, fontSize: 12, fontWeight: 600 }}>
            {t('Drag to select an area to capture')}
          </div>
          {sel && <div style={{ position: 'fixed', left: sel.x, top: sel.y, width: sel.w, height: sel.h, border: '2px solid #1A8FD1', background: 'rgba(26,143,209,.12)' }} />}
        </div>
      )}

      {/* Floating panel */}
      <div style={{ position: 'fixed', left: pos.x, top: pos.y, width: 340, maxWidth: '94vw', zIndex: 2147483645,
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

          <button className="tb-btn" onClick={beginCapture} style={{ justifyContent: 'center' }}>
            <Crop size={14} aria-hidden /> {t('Capture an area')}
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
            <ImageIcon size={11} aria-hidden /> {t('Tip: take an OS screenshot and paste it here, or capture an area above.')}
          </div>

          <button className="submit-btn" onClick={submit} disabled={busy} style={{ justifyContent: 'center' }}>
            <Send size={14} aria-hidden /> {busy ? t('Saving…') : t('Log request')}
          </button>
        </div>
      </div>
    </>
  )
}
