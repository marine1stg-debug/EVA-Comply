import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import { useAuthStore } from '../store/auth'

interface RType { key: string; name: string; desc: string; formats: string[]; icon: string }

export default function ReportsPage() {
  const t = useT()
  const role = useAuthStore(s => s.user?.role || '')
  const canAggregate = ['super_admin', 'msp_admin', 'msp_analyst'].includes(role)
  const { data, isLoading, isError } = useQuery<{ types: RType[] }>({
    queryKey: ['report-types'],
    queryFn: async () => (await api.get('/reports/')).data,
  })
  const [busy, setBusy] = useState<string | null>(null)

  async function download(res: any, fallback: string) {
    const cd = res.headers['content-disposition'] || ''
    const m = /filename="([^"]+)"/.exec(cd)
    const name = m ? m[1] : fallback
    const url = URL.createObjectURL(res.data)
    const a = document.createElement('a')
    a.href = url; a.download = name; a.click()
    URL.revokeObjectURL(url)
  }

  async function generateAggregate(format: string) {
    setBusy(`aggregate:${format}`)
    try {
      const res = await api.post('/reports/aggregate', { format }, { responseType: 'blob' })
      await download(res, `portfolio.${format}`)
      toast.success(t('Report downloaded'))
    } catch (e: any) {
      let msg = t('Could not generate report')
      try { msg = JSON.parse(await e?.response?.data?.text())?.detail || msg } catch { /* keep default */ }
      toast.error(msg)
    } finally { setBusy(null) }
  }

  async function generate(key: string, format: string) {
    setBusy(`${key}:${format}`)
    try {
      const res = await api.post('/reports/generate', { report_type: key, format }, { responseType: 'blob' })
      await download(res, `${key}.${format}`)
      toast.success(t('Report downloaded'))
    } catch (e: any) {
      // blob error responses need decoding
      let msg = t('Could not generate report')
      try { msg = JSON.parse(await e?.response?.data?.text())?.detail || msg } catch { /* keep default */ }
      toast.error(msg)
    } finally {
      setBusy(null)
    }
  }

  if (isLoading) return <div className="page-sub">{t('Loading reports…')}</div>
  if (isError || !data) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load reports.')}</div>

  const fmtLabel: Record<string, string> = { pdf: '⬇ PDF', docx: '⬇ Word', xlsx: '⬇ Excel' }

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Reports')}</div>
          <div className="page-sub">{t('Generate and download compliance reports for the selected client.')}</div>
        </div>
      </div>

      {canAggregate && (
        <div className="detail-section fi" style={{ marginBottom: 16 }}>
          <div className="card-hdr" style={{ marginBottom: 6 }}><span className="card-title">{t('Portfolio report')}</span></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
            <div className="page-sub" style={{ flex: 1, minWidth: 240 }}>
              {t('Aggregate compliance across your whole client base (super admins: across all clients) - overall and per-client.')}
            </div>
            <button className="tb-btn pri" disabled={busy !== null} onClick={() => generateAggregate('pdf')}>
              {busy === 'aggregate:pdf' ? t('Generating…') : '⬇ PDF'}
            </button>
            <button className="tb-btn" disabled={busy !== null} onClick={() => generateAggregate('docx')}>
              {busy === 'aggregate:docx' ? t('Generating…') : '⬇ Word'}
            </button>
          </div>
        </div>
      )}

      <div className="fw-lib-grid fi">
        {data.types.map(r => (
          <div key={r.key} className="fw-lib-card">
            <div className="fw-lib-icon" style={{ background: 'var(--soft)' }}>{r.icon}</div>
            <div className="fw-lib-name">{t(r.name)}</div>
            <div className="fw-lib-version">{r.formats.map(f => f.toUpperCase()).join(' · ')}</div>
            <div className="fw-lib-desc">{t(r.desc)}</div>
            <div className="fw-lib-actions" style={{ gap: 6 }}>
              {r.formats.map(f => (
                <button key={f} className={`tb-btn ${f === 'pdf' ? 'pri' : ''}`}
                  style={{ flex: 1, justifyContent: 'center', fontSize: 11 }}
                  disabled={busy !== null} onClick={() => generate(r.key, f)}>
                  {busy === `${r.key}:${f}` ? t('Generating…') : (fmtLabel[f] || f.toUpperCase())}
                </button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </>
  )
}
