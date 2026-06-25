import { useRef, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Preview { columns: string[]; row_count: number; sample: Record<string, string>[]; auto_mapping: Record<string, string>; fields: string[] }
interface Result { framework_id: string; name: string; created: number; errors: { row: number; error: string }[]; total_rows: number }

const FIELD_LABEL: Record<string, string> = {
  ref: 'Control Ref *', title: 'Title *', domain: 'Domain', level: 'Level',
  priority: 'Priority', risk: 'Risk', description: 'Description', objective: 'Objective', plain_language: 'Plain language',
}

const Stepper = ({ step }: { step: number }) => {
  const t = useT()
  return (
  <div style={{ display: 'flex', gap: 8, marginBottom: 18 }} className="fi">
    {[t('Upload'), t('Map columns'), t('Review'), t('Done')].map((l, i) => {
      const n = i + 1, active = n === step, done = n < step
      return (
        <div key={l} style={{ display: 'flex', alignItems: 'center', gap: 8, flex: 1 }}>
          <div style={{ width: 24, height: 24, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 11, fontWeight: 700, flexShrink: 0, color: '#fff', background: done ? 'var(--green)' : active ? 'var(--eva-blue2)' : '#CBD5E1' }}>{done ? '✓' : n}</div>
          <span style={{ fontSize: 12, fontWeight: active ? 600 : 400, color: active ? 'var(--text)' : 'var(--text3)' }}>{l}</span>
          {i < 3 && <div style={{ flex: 1, height: 2, background: 'var(--border-l)' }} />}
        </div>
      )
    })}
  </div>
  )
}

export default function ImportPage() {
  const qc = useQueryClient()
  const t = useT()
  const [step, setStep] = useState(1)
  const [name, setName] = useState('')
  const [version, setVersion] = useState('1.0')
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<Preview | null>(null)
  const [mapping, setMapping] = useState<Record<string, string>>({})
  const [result, setResult] = useState<Result | null>(null)
  const fileInput = useRef<HTMLInputElement>(null)

  const previewMut = useMutation({
    mutationFn: async () => {
      const fd = new FormData(); fd.append('file', file as File)
      return (await api.post('/frameworks/import/preview', fd)).data as Preview
    },
    onSuccess: (p) => { setPreview(p); setMapping(p.auto_mapping || {}); setStep(2) },
    onError: () => toast.error(t('Could not read the file')),
  })

  const importMut = useMutation({
    mutationFn: async () => {
      const fd = new FormData()
      fd.append('name', name); fd.append('version', version)
      fd.append('mapping', JSON.stringify(mapping)); fd.append('file', file as File)
      return (await api.post('/frameworks/import', fd)).data as Result
    },
    onSuccess: (r) => { setResult(r); setStep(4); toast.success(t('Imported {n} controls', { n: r.created })); qc.invalidateQueries({ queryKey: ['frameworks'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Import failed')),
  })

  const reset = () => { setStep(1); setName(''); setVersion('1.0'); setFile(null); setPreview(null); setMapping({}); setResult(null) }
  const mappedOk = mapping.ref && mapping.title

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Import Framework')}</div>
          <div className="page-sub">{t('Upload a CSV or XLSX of controls and map the columns.')}</div>
        </div>
      </div>

      <Stepper step={step} />

      {/* Step 1 — upload */}
      {step === 1 && (
        <div className="ev-upload-card fi" style={{ maxWidth: 560 }}>
          <div className="form-row"><label className="form-label">{t('Framework name *')}</label>
            <input className="form-input" value={name} onChange={e => setName(e.target.value)} placeholder="e.g. ISO 27001:2022" /></div>
          <div className="form-row" style={{ marginTop: 10 }}><label className="form-label">{t('Version')}</label>
            <input className="form-input" value={version} onChange={e => setVersion(e.target.value)} /></div>
          <input ref={fileInput} type="file" accept=".csv,.xlsx,.xlsm" hidden onChange={e => setFile(e.target.files?.[0] || null)} />
          <div className="drop-zone" style={{ marginTop: 14 }} onClick={() => fileInput.current?.click()}>
            <span className="drop-icon">{file ? '📎' : '📁'}</span>
            <div className="drop-title">{file ? file.name : t('Click to choose a CSV or XLSX')}</div>
            <div className="drop-sub">{file ? `${(file.size / 1024).toFixed(0)} KB` : t('First row must be column headers')}</div>
          </div>
          <button className="submit-btn" style={{ marginTop: 16, justifyContent: 'center' }}
            disabled={!name.trim() || !file || previewMut.isPending} onClick={() => previewMut.mutate()}>
            {previewMut.isPending ? t('Reading…') : t('Next → Map columns')}
          </button>
        </div>
      )}

      {/* Step 2 — mapping */}
      {step === 2 && preview && (
        <div className="detail-section fi" style={{ maxWidth: 640 }}>
          <div className="card-hdr"><span className="card-title">{t('Map your columns ({n} rows)', { n: preview.row_count })}</span></div>
          {preview.fields.map(f => (
            <div key={f} style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
              <span style={{ fontSize: 12, color: 'var(--text2)', minWidth: 130 }}>{t(FIELD_LABEL[f] || f)}</span>
              <select className="form-select" style={{ flex: 1 }} value={mapping[f] || ''} onChange={e => setMapping(m => ({ ...m, [f]: e.target.value }))}>
                <option value="">{t('— not mapped —')}</option>
                {preview.columns.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
          ))}
          {!mappedOk && <div className="page-sub" style={{ color: 'var(--amber)', marginTop: 6 }}>{t('Ref and Title are required.')}</div>}
          <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
            <button className="tb-btn" onClick={() => setStep(1)}>{t('← Back')}</button>
            <button className="submit-btn" disabled={!mappedOk} onClick={() => setStep(3)}>{t('Next → Review')}</button>
          </div>
        </div>
      )}

      {/* Step 3 — review */}
      {step === 3 && preview && (
        <div className="detail-section fi">
          <div className="card-hdr"><span className="card-title">{t('Review — {n} controls into “{name}” v{version}', { n: preview.row_count, name, version })}</span></div>
          <table className="tenant-table">
            <thead><tr>{preview.fields.filter(f => mapping[f]).map(f => <th key={f}>{f}</th>)}</tr></thead>
            <tbody>
              {preview.sample.map((r, i) => (
                <tr key={i}>{preview.fields.filter(f => mapping[f]).map(f => <td key={f}>{r[mapping[f]]}</td>)}</tr>
              ))}
            </tbody>
          </table>
          <div className="page-sub" style={{ marginTop: 8 }}>{t('Showing first {n} of {total} rows.', { n: preview.sample.length, total: preview.row_count })}</div>
          <div style={{ display: 'flex', gap: 8, marginTop: 14 }}>
            <button className="tb-btn" onClick={() => setStep(2)}>{t('← Back')}</button>
            <button className="submit-btn" style={{ background: 'var(--green)' }} disabled={importMut.isPending} onClick={() => importMut.mutate()}>
              {importMut.isPending ? t('Importing…') : t('✓ Publish framework')}
            </button>
          </div>
        </div>
      )}

      {/* Step 4 — done */}
      {step === 4 && result && (
        <div className="detail-section fi" style={{ maxWidth: 560, textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>✅</div>
          <div style={{ fontSize: 16, fontWeight: 600 }}>{t('{name} imported', { name: result.name })}</div>
          <div className="page-sub" style={{ marginTop: 4 }}>{t('{n} of {total} rows created as controls.', { n: result.created, total: result.total_rows })}</div>
          {result.errors.length > 0 && (
            <div className="page-sub" style={{ color: 'var(--amber)', marginTop: 8 }}>
              {t('{n} rows skipped (missing ref/title).', { n: result.errors.length })}
            </div>
          )}
          <button className="submit-btn" style={{ marginTop: 16, justifyContent: 'center' }} onClick={reset}>{t('Import another')}</button>
        </div>
      )}
    </>
  )
}
