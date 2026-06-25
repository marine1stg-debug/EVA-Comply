import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import { useClientContext } from '../store/clientContext'

interface FwCard {
  id: string; name: string; version: string; desc: string; type: string; status: string
  controls: number; domains: number; levels: string[]; orgs_using: number; last_updated: string
  icon: string; color: string; bg: string
}
interface LibResp { frameworks: FwCard[]; counts: { system: number; custom: number }; client_scoped?: boolean }
interface Domain { name: string; count: number }
interface Sample { ref: string; title: string; priority: string; priorityBadge: string }
interface Detail extends Omit<FwCard, 'domains'> {
  domains: Domain[]; domains_count: number; samples: Sample[]
}

const cap = (s: string) => s.charAt(0).toUpperCase() + s.slice(1)

/* ───────── Import wizard ───────── */
interface Preview {
  columns: string[]; row_count: number; sample: Record<string, string>[]
  auto_mapping: Record<string, string>; fields: string[]
}
const FIELD_LABEL: Record<string, string> = {
  ref: 'Ref / ID', title: 'Title', domain: 'Domain / family', level: 'Level',
  priority: 'Priority', risk: 'Risk', description: 'Requirement text', objective: 'Objective',
  plain_language: 'Plain language', best_practices: 'Best practices',
  expected_evidence: 'Expected evidence', discussion: 'Discussion', mappings: 'Mappings (JSON)',
}
const REQUIRED = ['ref', 'title']
const sel = { fontSize: 12, padding: '5px 8px', border: '1px solid var(--border-l)', borderRadius: 6, background: 'var(--card)', minWidth: 150 }

function ImportWizard({ onClose }: { onClose: () => void }) {
  const qc = useQueryClient()
  const t = useT()
  const [file, setFile] = useState<File | null>(null)
  const [name, setName] = useState('')
  const [version, setVersion] = useState('1.0')
  const [preview, setPreview] = useState<Preview | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const [result, setResult] = useState<{ created: number; total: number; errors: number } | null>(null)

  const readFile = async (f: File) => {
    setFile(f); setErr(null); setPreview(null); setResult(null)
    if (!name.trim()) setName(f.name.replace(/\.(csv|xlsx|xlsm)$/i, '').replace(/[_-]+/g, ' ').trim())
    setBusy(true)
    try {
      const fd = new FormData(); fd.append('file', f)
      const { data } = await api.post('/frameworks/import/preview', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setPreview(data); setMapping({ ...(data.auto_mapping || {}) })
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t('Could not read that file. Use a CSV or XLSX with a header row.'))
    } finally { setBusy(false) }
  }

  const setMap = (field: string, col: string) =>
    setMapping(m => { const n = { ...m }; if (col) n[field] = col; else delete n[field]; return n })

  const submit = async () => {
    if (!file) return
    if (!mapping.ref || !mapping.title) { setErr(t('Map at least the Ref and Title columns.')); return }
    setBusy(true); setErr(null)
    try {
      const fd = new FormData()
      fd.append('name', name.trim() || 'Imported framework')
      fd.append('version', version.trim() || '1.0')
      fd.append('mapping', JSON.stringify(mapping))
      fd.append('file', file)
      const { data } = await api.post('/frameworks/import', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setResult({ created: data.created, total: data.total_rows, errors: (data.errors || []).length })
      qc.invalidateQueries({ queryKey: ['frameworks'] })
    } catch (e: any) {
      setErr(e?.response?.data?.detail || t('Import failed.'))
    } finally { setBusy(false) }
  }

  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: 20 }}>
      <div onClick={e => e.stopPropagation()} style={{ background: 'var(--card)', borderRadius: 12, width: 'min(720px, 100%)', maxHeight: '88vh', overflowY: 'auto', boxShadow: '0 20px 60px rgba(0,0,0,.25)' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '16px 20px', borderBottom: '1px solid var(--border-l)' }}>
          <span style={{ fontSize: 15, fontWeight: 600 }}>{t('Import custom framework')}</span>
          <button onClick={onClose} style={{ border: 'none', background: 'none', fontSize: 20, cursor: 'pointer', color: 'var(--text3)' }}>✕</button>
        </div>

        <div style={{ padding: 20 }}>
          {result ? (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <div style={{ fontSize: 34 }}>✅</div>
              <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>{t('Imported {n} controls', { n: result.created })}</div>
              <div className="page-sub" style={{ marginTop: 4 }}>
                {t('{n} rows processed', { n: result.total })}{result.errors ? t(' · {n} skipped (missing ref/title)', { n: result.errors }) : ''}.
              </div>
              <button onClick={onClose} style={{ marginTop: 16, padding: '8px 18px', borderRadius: 8, border: 'none', background: 'var(--eva-blue2)', color: '#fff', cursor: 'pointer', fontSize: 13 }}>{t('Done')}</button>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 14 }}>
                <label style={{ flex: 1, minWidth: 180 }}>
                  <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 4 }}>{t('Framework name')}</div>
                  <input value={name} onChange={e => setName(e.target.value)} placeholder="e.g. ISO 27001:2022"
                    style={{ width: '100%', fontSize: 13, padding: '7px 10px', border: '1px solid var(--border-l)', borderRadius: 7 }} />
                </label>
                <label style={{ width: 110 }}>
                  <div style={{ fontSize: 11, color: 'var(--text3)', marginBottom: 4 }}>{t('Version')}</div>
                  <input value={version} onChange={e => setVersion(e.target.value)}
                    style={{ width: '100%', fontSize: 13, padding: '7px 10px', border: '1px solid var(--border-l)', borderRadius: 7 }} />
                </label>
              </div>

              <label style={{ display: 'block', border: '2px dashed #CBD5E1', borderRadius: 10, padding: '18px', textAlign: 'center', cursor: 'pointer', marginBottom: 14 }}>
                <input type="file" accept=".csv,.xlsx,.xlsm" style={{ display: 'none' }}
                  onChange={e => { const f = e.target.files?.[0]; if (f) readFile(f) }} />
                <div style={{ fontSize: 26, opacity: .4 }}>⬆️</div>
                <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text2)' }}>{file ? file.name : t('Choose a CSV or XLSX file')}</div>
                <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>{t('First row must be column headers')}</div>
              </label>

              {busy && <div className="page-sub">{t('Working…')}</div>}
              {err && <div style={{ fontSize: 12, color: 'var(--red)', background: '#FEF2F2', border: '1px solid #FECACA', borderRadius: 7, padding: '8px 10px', marginBottom: 12 }}>{err}</div>}

              {preview && (
                <>
                  <div style={{ fontSize: 12, color: 'var(--text2)', marginBottom: 8 }}>
                    {t('{rows} rows · {cols} columns detected. Map your columns to fields below', { rows: preview.row_count, cols: preview.columns.length })}
                    {' ('}<span style={{ color: 'var(--red)' }}>*</span> {t('required):')}
                  </div>
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px 14px', marginBottom: 14 }}>
                    {preview.fields.map(f => (
                      <div key={f} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
                        <span style={{ fontSize: 12, color: 'var(--text2)' }}>
                          {t(FIELD_LABEL[f] || f)}{REQUIRED.includes(f) && <span style={{ color: 'var(--red)' }}> *</span>}
                        </span>
                        <select value={mapping[f] || ''} onChange={e => setMap(f, e.target.value)} style={sel}>
                          <option value="">{t('— none —')}</option>
                          {preview.columns.map(c => <option key={c} value={c}>{c}</option>)}
                        </select>
                      </div>
                    ))}
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
                    <button onClick={onClose} style={{ padding: '8px 16px', borderRadius: 8, border: '1px solid var(--border-l)', background: 'var(--card)', cursor: 'pointer', fontSize: 13 }}>{t('Cancel')}</button>
                    <button onClick={submit} disabled={busy || !mapping.ref || !mapping.title}
                      style={{ padding: '8px 18px', borderRadius: 8, border: 'none', background: 'var(--eva-blue2)', color: '#fff', cursor: 'pointer', fontSize: 13, opacity: (busy || !mapping.ref || !mapping.title) ? .5 : 1 }}>
                      {t('Import {n} controls', { n: preview.row_count })}
                    </button>
                  </div>
                </>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  )
}

/* ───────── Library grid ───────── */
function Library({ onOpen }: { onOpen: (id: string) => void }) {
  const t = useT()
  const clientName = useClientContext(s => s.clientName)
  const [importing, setImporting] = useState(false)
  const { data, isLoading, isError, error } = useQuery<LibResp>({
    queryKey: ['frameworks'],
    queryFn: async () => (await api.get('/frameworks/')).data,
  })

  if (isLoading) return <div className="page-sub">{t('Loading frameworks…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('The framework library requires admin access.') : t('Failed to load frameworks.')}
    </div>
  }
  if (!data) return null

  const system = data.frameworks.filter(f => f.type === 'system')
  const custom = data.frameworks.filter(f => f.type === 'custom')

  const Card = (fw: FwCard) => (
    <div key={fw.id} className={`fw-lib-card ${fw.type}`} onClick={() => onOpen(fw.id)}>
      <span className={`fw-lib-badge ${fw.type === 'system' ? 'b-blue' : 'b-teal'}`}>{fw.type === 'system' ? t('Built-in') : t('Custom')}</span>
      <div className="fw-lib-icon" style={{ background: fw.bg }}>{fw.icon}</div>
      <div className="fw-lib-name">{fw.name}</div>
      <div className="fw-lib-version">v{fw.version} · {t('Updated {date}', { date: fw.last_updated })}</div>
      <div className="fw-lib-desc">{fw.desc}</div>
      <div className="fw-lib-stats">
        <div className="fw-lib-stat"><div className="fw-lib-stat-val" style={{ color: fw.color }}>{fw.controls}</div><div className="fw-lib-stat-lbl">{t('Controls')}</div></div>
        <div className="fw-lib-stat"><div className="fw-lib-stat-val">{fw.domains}</div><div className="fw-lib-stat-lbl">{t('Domains')}</div></div>
        <div className="fw-lib-stat"><div className="fw-lib-stat-val">{fw.orgs_using}</div><div className="fw-lib-stat-lbl">{t('Orgs Using')}</div></div>
      </div>
      <div className="fw-lib-actions">
        <button className="tb-btn" style={{ flex: 1, justifyContent: 'center', fontSize: 10 }}>{t('View Controls')}</button>
      </div>
    </div>
  )

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Framework Library')}</div>
          <div className="page-sub">
            {data.client_scoped
              ? t('Frameworks assigned to {client}', { client: clientName || t('this client') })
              : t('{system} built-in frameworks · {custom} custom imports', { system: data.counts.system, custom: data.counts.custom })}
          </div>
        </div>
      </div>

      {data.client_scoped && data.frameworks.length === 0 && (
        <div className="detail-section fi" style={{ textAlign: 'center', padding: '40px 24px' }}>
          <div style={{ fontSize: 28 }}>📚</div>
          <div className="page-sub" style={{ marginTop: 6 }}>{t('No frameworks assigned to this client yet.')}</div>
        </div>
      )}

      {system.length > 0 && <>
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)', marginBottom: 10 }} className="fi">{t('Built-in Frameworks')}</div>
        <div className="fw-lib-grid fi">{system.map(Card)}</div>
      </>}

      {(custom.length > 0 || !data.client_scoped) && (
        <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--text2)', marginBottom: 10, marginTop: 4 }} className="fi">{t('Custom Imports')}</div>
      )}
      <div className="fw-lib-grid fi">
        {custom.map(Card)}
        {!data.client_scoped && (
          <div className="fw-lib-card" onClick={() => setImporting(true)}
            style={{ border: '2px dashed #CBD5E1', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', minHeight: 200, cursor: 'pointer' }}>
            <div style={{ fontSize: 36, marginBottom: 10, opacity: .3 }}>+</div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text3)' }}>{t('Import Custom Framework')}</div>
            <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 4, textAlign: 'center', maxWidth: 160 }}>{t('Upload a CSV or XLSX catalog')}</div>
          </div>
        )}
      </div>

      {importing && <ImportWizard onClose={() => setImporting(false)} />}
    </>
  )
}

/* ───────── Detail ───────── */
function FrameworkDetail({ id, onBack }: { id: string; onBack: () => void }) {
  const navigate = useNavigate()
  const t = useT()
  const { data: fw, isLoading, isError } = useQuery<Detail>({
    queryKey: ['framework', id],
    queryFn: async () => (await api.get(`/frameworks/${id}`)).data,
  })

  if (isLoading) return <div className="page-sub">{t('Loading framework…')}</div>
  if (isError || !fw) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load framework.')}</div>

  const maxCount = Math.max(1, ...fw.domains.map(d => d.count))

  return (
    <>
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 16, flexWrap: 'wrap' }} className="fi">
        <button className="tb-btn" style={{ padding: '4px 10px', fontSize: 11 }} onClick={onBack}>← {t('Library')}</button>
        <div style={{ width: 32, height: 32, borderRadius: 9, background: fw.bg, display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 18 }}>{fw.icon}</div>
        <span style={{ fontSize: 16, fontWeight: 600, color: 'var(--text)' }}>{fw.name}</span>
        <span className={`badge ${fw.type === 'system' ? 'b-blue' : 'b-teal'}`}>{fw.type === 'system' ? t('Built-in') : t('Custom Import')}</span>
        <span className={`badge ${fw.status === 'active' ? 'b-green' : 'b-amber'}`}>{fw.status}</span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 280px', gap: 14 }} className="fi">
        <div className="detail-section">
          <div className="card-hdr"><span className="card-title">{t('Controls by Domain')}</span></div>
          {fw.domains.length === 0 && <div className="page-sub">{t('No controls loaded for this framework yet.')}</div>}
          {fw.domains.map(d => {
            const pct = Math.round(d.count / maxCount * 100)
            return (
              <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 9 }}>
                <span style={{ fontSize: 11, color: 'var(--text2)', minWidth: 150, flexShrink: 0 }}>{d.name}</span>
                <div style={{ flex: 1, height: 6, background: 'var(--surface-2)', borderRadius: 3, overflow: 'hidden' }}>
                  <div style={{ width: `${pct}%`, height: '100%', background: fw.color, borderRadius: 3 }} />
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: fw.color, minWidth: 32, textAlign: 'right' }}>{d.count}</span>
              </div>
            )
          })}

          {fw.samples.length > 0 && (
            <div style={{ marginTop: 14, paddingTop: 12, borderTop: '1px solid var(--border-l)' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)', marginBottom: 10, textTransform: 'uppercase', letterSpacing: '.04em' }}>{t('Sample Controls')}</div>
              {fw.samples.map(c => (
                <div key={c.ref} style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', borderBottom: '1px solid var(--border-l)' }}>
                  <span style={{ fontFamily: 'var(--mono)', fontSize: 10, color: 'var(--eva-blue2)', background: 'var(--soft)', padding: '2px 6px', borderRadius: 4, flexShrink: 0 }}>{c.ref}</span>
                  <span style={{ fontSize: 12, color: 'var(--text)', flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{c.title}</span>
                  <span className={`badge ${c.priorityBadge}`} style={{ fontSize: 9 }}>{cap(c.priority)}</span>
                </div>
              ))}
              {fw.controls > fw.samples.length && (
                <div style={{ textAlign: 'center', padding: 10, fontSize: 11, color: 'var(--text3)' }}>
                  {t('+ {n} more →', { n: fw.controls - fw.samples.length })} <span style={{ color: 'var(--eva-blue2)', cursor: 'pointer' }} onClick={() => navigate('/controls')}>{t('View in Controls list')}</span>
                </div>
              )}
            </div>
          )}
        </div>

        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div className="detail-section">
            <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Framework Info')}</span></div>
            {([
              ['Name', fw.name], ['Version', `v${fw.version}`], ['Type', fw.type === 'system' ? t('Built-in') : t('Custom import')],
              ['Controls', String(fw.controls)], ['Domains', String(fw.domains_count)], ['Levels', String(fw.levels.length)],
              ['Orgs Using', String(fw.orgs_using)], ['Last Updated', fw.last_updated], ['Status', fw.status],
            ] as [string, string][]).map(([k, v]) => (
              <div key={k} className="meta-row"><span className="meta-key">{t(k)}</span><span className="meta-val">{v}</span></div>
            ))}
          </div>
          <div className="detail-section">
            <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{t('Levels / Tiers')}</span></div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
              {fw.levels.length === 0 && <span className="page-sub">{t('None defined.')}</span>}
              {fw.levels.map(l => <span key={l} className="badge b-gray">{l}</span>)}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}

export default function FrameworksPage() {
  const [selected, setSelected] = useState<string | null>(null)
  return selected
    ? <FrameworkDetail id={selected} onBack={() => setSelected(null)} />
    : <Library onOpen={setSelected} />
}
