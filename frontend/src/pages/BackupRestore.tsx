import { useState } from 'react'
import { createPortal } from 'react-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Cat { key: string; label: string; client_scoped: boolean; tables: string[]; rows: number }
interface Client { id: string; name: string; type: string }
interface Options { categories: Cat[]; clients: Client[] }
interface Snap {
  id: string; label: string; scope: string; categories: string[]; client_ids: string[]
  total_rows: number; size_bytes: number; created_by: string; created_at: string
}
type RestoreTarget =
  | { kind: 'snapshot'; snap: Snap; cats: string[] }
  | { kind: 'file'; file: File; cats: string[] }

function dl(blob: Blob, name: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a'); a.href = url; a.download = name; a.click()
  URL.revokeObjectURL(url)
}

/* ── Modal: pick exactly which categories to restore ── */
function RestoreModal({ target, labelOf, onClose, onDone }:
  { target: RestoreTarget; labelOf: (k: string) => string; onClose: () => void; onDone: () => void }) {
  const t = useT()
  const [pick, setPick] = useState<Record<string, boolean>>(
    Object.fromEntries(target.cats.map(c => [c, true])))
  const [busy, setBusy] = useState(false)
  const chosen = target.cats.filter(c => pick[c])

  const run = async () => {
    if (!chosen.length) { toast.error(t('Choose at least one category')); return }
    if (!window.confirm(t('Restore the selected data? It merges (adds and updates, never deletes).'))) return
    setBusy(true)
    try {
      let applied = 0
      if (target.kind === 'snapshot') {
        applied = (await api.post('/backup/restore/snapshot', { snapshot_id: target.snap.id, categories: chosen })).data.applied
      } else {
        const fd = new FormData(); fd.append('file', target.file); fd.append('categories', chosen.join(','))
        applied = (await api.post('/backup/restore/upload', fd)).data.applied
      }
      toast.success(t('Restored {n} records', { n: applied })); onDone(); onClose()
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Restore failed')) }
    finally { setBusy(false) }
  }

  return createPortal(
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 460 }} onClick={e => e.stopPropagation()}>
        <div className="modal-hdr"><span className="card-title">{t('Choose what to restore')}</span>
          <button className="ev-action-btn" onClick={onClose}>✕</button></div>
        <div className="modal-body">
          <div className="page-sub" style={{ marginBottom: 10 }}>
            {target.kind === 'snapshot' ? target.snap.label : target.file.name}
          </div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 8 }}>
            <button className="tb-btn" onClick={() => setPick(Object.fromEntries(target.cats.map(c => [c, true])))}>{t('Select all')}</button>
            <button className="tb-btn" onClick={() => setPick({})}>{t('Clear')}</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 320, overflow: 'auto' }}>
            {target.cats.map(c => (
              <label key={c} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, cursor: 'pointer' }}>
                <input type="checkbox" checked={!!pick[c]} onChange={e => setPick(m => ({ ...m, [c]: e.target.checked }))} />
                {labelOf(c)}
              </label>
            ))}
            {!target.cats.length && <div className="page-sub">{t('This backup lists no categories - everything in the file will be restored.')}</div>}
          </div>
          <div style={{ display: 'flex', gap: 8, marginTop: 14, justifyContent: 'flex-end' }}>
            <button className="tb-btn" onClick={onClose}>{t('Cancel')}</button>
            <button className="submit-btn" disabled={busy} onClick={run}>↺ {busy ? t('Restoring…') : t('Restore selected')}</button>
          </div>
        </div>
      </div>
    </div>,
    document.body,
  )
}

export default function BackupRestorePage() {
  const t = useT()
  const qc = useQueryClient()
  const { data: opts } = useQuery<Options>({ queryKey: ['backup-options'], queryFn: async () => (await api.get('/backup/options')).data })
  const { data: snaps } = useQuery<{ snapshots: Snap[] }>({ queryKey: ['backup-snaps'], queryFn: async () => (await api.get('/backup/snapshots')).data })

  const [cats, setCats] = useState<Record<string, boolean>>({})
  const [clients, setClients] = useState<Record<string, boolean>>({})
  const [label, setLabel] = useState('')
  const [busy, setBusy] = useState(false)
  const [restore, setRestore] = useState<RestoreTarget | null>(null)

  const allCats = opts?.categories || []
  const allClients = opts?.clients || []
  const labelOf = (k: string) => allCats.find(c => c.key === k)?.label || k
  const chosenCats = Object.keys(cats).filter(k => cats[k])
  const chosenClients = Object.keys(clients).filter(k => clients[k])
  const anyClientScoped = allCats.some(c => cats[c.key] && c.client_scoped)

  const body = () => ({ label, categories: chosenCats, client_ids: chosenClients })

  const saveSnap = async () => {
    if (!chosenCats.length) { toast.error(t('Choose at least one category')); return }
    setBusy(true)
    try {
      await api.post('/backup/snapshot', { ...body(), store: true, download: false })
      toast.success(t('Snapshot saved')); qc.invalidateQueries({ queryKey: ['backup-snaps'] })
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Backup failed')) }
    finally { setBusy(false) }
  }
  const downloadNew = async (fmt: 'json' | 'zip' = 'json') => {
    if (!chosenCats.length) { toast.error(t('Choose at least one category')); return }
    setBusy(true)
    try {
      const r = await api.post('/backup/snapshot', { ...body(), store: false, download: true, fmt }, { responseType: 'blob' })
      const ext = fmt === 'zip' ? 'zip' : 'json'
      const mime = fmt === 'zip' ? 'application/zip' : 'application/json'
      dl(new Blob([r.data], { type: mime }), `eva-backup-${new Date().toISOString().slice(0, 10)}.${ext}`)
    } catch { toast.error(t('Backup failed')) }
    finally { setBusy(false) }
  }
  const downloadSnap = async (s: Snap, fmt: 'json' | 'zip' = 'json') => {
    const r = await api.get(`/backup/snapshots/${s.id}/download`, { params: { fmt }, responseType: 'blob' })
    const ext = fmt === 'zip' ? 'zip' : 'json'
    const mime = fmt === 'zip' ? 'application/zip' : 'application/json'
    dl(new Blob([r.data], { type: mime }), s.label.replace(/[^A-Za-z0-9]+/g, '_') + '.' + ext)
  }
  const downloadFrameworks = async () => {
    setBusy(true)
    try {
      const r = await api.get('/backup/frameworks.zip', { responseType: 'blob' })
      dl(new Blob([r.data], { type: 'application/zip' }), `eva-frameworks-${new Date().toISOString().slice(0, 10)}.zip`)
    } catch { toast.error(t('Download failed')) }
    finally { setBusy(false) }
  }
  const [fullBusy, setFullBusy] = useState(false)
  const downloadFull = async () => {
    setFullBusy(true)
    try {
      const r = await api.get('/backup/full', { responseType: 'blob' })
      dl(new Blob([r.data], { type: 'application/zip' }), `eva-full-backup-${new Date().toISOString().slice(0, 10)}.zip`)
      toast.success(t('Full backup downloaded'))
    } catch { toast.error(t('Backup failed')) }
    finally { setFullBusy(false) }
  }
  const delSnap = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/backup/snapshots/${id}`)).data,
    onSuccess: () => { toast.success(t('Deleted')); qc.invalidateQueries({ queryKey: ['backup-snaps'] }) },
  })

  // Open the restore picker for an uploaded file (parse its categories first).
  const pickFile = (f: File | null) => {
    if (!f) return
    const reader = new FileReader()
    reader.onload = () => {
      let fileCats: string[] = []
      try { fileCats = (JSON.parse(String(reader.result)).categories) || [] } catch { /* ignore */ }
      if (!fileCats.length) fileCats = allCats.map(c => c.key)  // fall back to all known
      setRestore({ kind: 'file', file: f, cats: fileCats })
    }
    reader.readAsText(f)
  }

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Backup & Restore')}</div>
          <div className="page-sub">{t('Export selected data to a file or a server snapshot, and restore by merging it back (never deletes).')}</div>
        </div>
      </div>

      <div className="card fi" style={{ padding: 16, marginBottom: 14, borderLeft: '3px solid var(--eva-blue2, #1A8FD1)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
          <div style={{ minWidth: 0 }}>
            <div style={{ fontWeight: 700, color: 'var(--text)' }}>{t('Full backup (everything)')}</div>
            <div className="page-sub" style={{ marginTop: 2 }}>{t('Download one .zip with the entire database (all data) plus every uploaded file - evidence and policy documents.')}</div>
          </div>
          <button className="submit-btn" disabled={fullBusy} onClick={downloadFull} style={{ flexShrink: 0 }}>
            ⬇ {fullBusy ? t('Preparing…') : t('Download full backup')}
          </button>
        </div>
      </div>

      {/* ── Create ── */}
      <div className="detail-section fi" style={{ marginBottom: 16 }}>
        <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Create a backup')}</span></div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span className="form-label" style={{ margin: 0 }}>{t('What to include')}</span>
          <button className="tb-btn" style={{ marginLeft: 'auto' }} onClick={() => setCats(Object.fromEntries(allCats.map(c => [c.key, true])))}>{t('Select all')}</button>
          <button className="tb-btn" onClick={() => setCats({})}>{t('Clear')}</button>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill,minmax(260px,1fr))', gap: 8, marginBottom: 14 }}>
          {allCats.map(c => (
            <label key={c.key} className="card" style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', cursor: 'pointer' }}>
              <input type="checkbox" checked={!!cats[c.key]} onChange={e => setCats(m => ({ ...m, [c.key]: e.target.checked }))} />
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: 12.5, fontWeight: 600 }}>{c.label}</div>
                <div style={{ fontSize: 10.5, color: 'var(--text3)' }}>
                  {c.rows} {t('rows')}{c.client_scoped ? ` · ${t('per-client')}` : ` · ${t('global')}`}
                </div>
              </div>
            </label>
          ))}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span className="form-label" style={{ margin: 0 }}>{t('Clients (leave empty = all clients)')}</span>
          {anyClientScoped && <>
            <button className="tb-btn" style={{ marginLeft: 'auto' }} onClick={() => setClients(Object.fromEntries(allClients.map(c => [c.id, true])))}>{t('Select all')}</button>
            <button className="tb-btn" onClick={() => setClients({})}>{t('Clear')}</button>
          </>}
        </div>
        {!anyClientScoped && <div className="page-sub" style={{ marginBottom: 8 }}>{t('Pick a per-client category above to filter by client.')}</div>}
        {anyClientScoped && (
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 14 }}>
            {allClients.map(cl => (
              <label key={cl.id} className={`t-type ${clients[cl.id] ? 't-client' : 't-client-direct'}`} style={{ cursor: 'pointer', padding: '4px 10px', fontSize: 11 }}>
                <input type="checkbox" style={{ marginRight: 6 }} checked={!!clients[cl.id]} onChange={e => setClients(m => ({ ...m, [cl.id]: e.target.checked }))} />
                {cl.name}
              </label>
            ))}
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
          <input className="form-input" style={{ flex: 1, minWidth: 220 }} placeholder={t('Label (optional)')} value={label} onChange={e => setLabel(e.target.value)} />
          <button className="tb-btn" disabled={busy} onClick={() => downloadNew('json')}>⬇ {t('Download JSON')}</button>
          <button className="tb-btn" disabled={busy} onClick={() => downloadNew('zip')}>⬇ {t('Download ZIP')}</button>
          <button className="submit-btn" disabled={busy} onClick={saveSnap}>💾 {t('Save server snapshot')}</button>
        </div>
      </div>

      {/* ── Server snapshots ── */}
      <div className="detail-section fi" style={{ marginBottom: 16 }}>
        <div className="card-hdr" style={{ marginBottom: 8 }}><span className="card-title">{t('Server snapshots')}</span></div>
        {!(snaps?.snapshots || []).length ? <div className="page-sub">{t('No snapshots yet.')}</div> : (
          <div className="ev-table-wrap">
            <table className="ev-table">
              <thead><tr><th>{t('Label')}</th><th>{t('Scope')}</th><th>{t('Rows')}</th><th>{t('Created')}</th><th></th></tr></thead>
              <tbody>
                {snaps!.snapshots.map(s => (
                  <tr key={s.id}>
                    <td style={{ fontWeight: 600, fontSize: 12 }}>{s.label}</td>
                    <td style={{ fontSize: 11, color: 'var(--text3)' }}>{s.scope}</td>
                    <td>{s.total_rows}</td>
                    <td style={{ fontSize: 11, color: 'var(--text3)' }}>{s.created_at}<br />{s.created_by}</td>
                    <td style={{ whiteSpace: 'nowrap' }}>
                      <button className="ev-action-btn" onClick={() => downloadSnap(s, 'json')}>⬇ {t('JSON')}</button>
                      <button className="ev-action-btn" onClick={() => downloadSnap(s, 'zip')}>⬇ {t('ZIP')}</button>
                      <button className="ev-action-btn" onClick={() => setRestore({ kind: 'snapshot', snap: s, cats: s.categories || [] })}>↺ {t('Restore')}</button>
                      <button className="ev-action-btn delete" disabled={delSnap.isPending}
                        onClick={() => { if (window.confirm(t('Delete this snapshot?'))) delSnap.mutate(s.id) }}>🗑</button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* ── Framework catalogs ── */}
      <div className="detail-section fi" style={{ marginBottom: 16 }}>
        <div className="card-hdr" style={{ marginBottom: 8 }}><span className="card-title">{t('Framework catalogs')}</span></div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
          <div className="page-sub" style={{ flex: 1, minWidth: 240 }}>
            {t('Download all framework catalogs (English + French .xlsx) as a single zip - CMMC L1, CMMC L2, ITSP.10.171 and NIST SP 800-171 R3.')}
          </div>
          <button className="submit-btn" disabled={busy} onClick={downloadFrameworks}>⬇ {t('Download catalogs (.zip)')}</button>
        </div>
      </div>

      {/* ── Restore from file ── */}
      <div className="detail-section fi">
        <div className="card-hdr" style={{ marginBottom: 8 }}><span className="card-title">{t('Restore from a file')}</span></div>
        <div className="page-sub" style={{ marginBottom: 10 }}>{t('Upload a backup file, then choose exactly which categories to restore. Restore merges data (adds and updates, never deletes).')}</div>
        <input type="file" accept="application/json,.json" onChange={e => { pickFile(e.target.files?.[0] || null); e.target.value = '' }} />
      </div>

      {restore && <RestoreModal target={restore} labelOf={labelOf} onClose={() => setRestore(null)} onDone={() => qc.invalidateQueries()} />}
    </>
  )
}
