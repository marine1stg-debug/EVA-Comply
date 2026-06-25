import { useState, useEffect, useRef } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import {
  ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Legend,
} from 'recharts'
import { Calculator, Download, X, History, Star, Trash2 } from 'lucide-react'
import { api } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useClientContext } from '../store/clientContext'
import { useT, useI18n } from '../lib/i18n'

interface FwItem { id: string; name: string }
interface DomainRow {
  domain: string; controls: number; compliant: number; auto_level: number
  current: number; perceived: number | null; target: number; previous: number | null
  current_overridden: boolean; target_set: boolean; note: string | null; risk: string
}
interface MaturityResp {
  framework: FwItem; domains: DomainRow[]
  overall_current: number; overall_perceived: number | null; overall_target: number; overall_previous: number | null
  risk_score: number; scale_max: number; can_edit: boolean; snapshot_at: string | null
}

const RISK_BADGE: Record<string, string> = { low: 'b-green', medium: 'b-amber', high: 'b-orange', critical: 'b-red' }
const riskScoreColor = (s: number) => (s >= 60 ? '#DC2626' : s >= 30 ? '#D97706' : '#16A34A')

function Stars({ level }: { level: number }) {
  const n = Math.round(level)
  return (
    <span style={{ color: '#F59E0B', letterSpacing: 1 }}>
      {[1, 2, 3, 4, 5].map(i => <span key={i} style={{ opacity: i <= n ? 1 : 0.25 }}>★</span>)}
    </span>
  )
}

export default function MaturityPage() {
  const t = useT()
  const lang = useI18n(s => s.lang)
  const role = useAuthStore(s => s.user?.role || '')
  const isReviewer = ['super_admin', 'eva_auditor', 'msp_admin', 'msp_analyst'].includes(role)
  const clientId = useClientContext(s => s.clientId)
  const qc = useQueryClient()
  const [fwId, setFwId] = useState<string>('')
  const [helpOpen, setHelpOpen] = useState(false)
  const [snapOpen, setSnapOpen] = useState(false)

  const { data: fwList } = useQuery<{ frameworks: FwItem[]; needs_client: boolean }>({
    queryKey: ['maturity-frameworks', clientId],
    queryFn: async () => (await api.get('/maturity/frameworks')).data,
    enabled: !isReviewer || !!clientId,
  })

  useEffect(() => {
    const fws = fwList?.frameworks || []
    if (fws.length && !fws.find(f => f.id === fwId)) setFwId(fws[0].id)
  }, [fwList, fwId])

  const { data: m, isLoading } = useQuery<MaturityResp>({
    queryKey: ['maturity', fwId, clientId],
    queryFn: async () => (await api.get(`/maturity/${fwId}`)).data,
    enabled: !!fwId,
  })

  const patchDomain = useMutation({
    mutationFn: async (b: { domain: string; current_level?: number; target_level?: number; note?: string; clear_current?: boolean }) =>
      (await api.patch(`/maturity/${fwId}/domain`, b)).data,
    onSuccess: (d: MaturityResp) => qc.setQueryData(['maturity', fwId, clientId], d),
  })
  const snapshot = useMutation({
    mutationFn: async () => (await api.post(`/maturity/${fwId}/snapshot`, {})).data,
    onSuccess: (d: MaturityResp) => qc.setQueryData(['maturity', fwId, clientId], d),
  })

  if (isReviewer && !clientId) return (
    <div className="detail-section" style={{ textAlign: 'center', padding: '48px 24px' }}>
      <div style={{ fontSize: 30 }}>🏢</div>
      <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>{t('Select a client to view maturity')}</div>
      <div className="page-sub" style={{ marginTop: 4 }}>{t('Use the “Viewing client” selector in the top bar.')}</div>
    </div>
  )

  const fws = fwList?.frameworks || []
  if (fws.length === 0) return (
    <>
      <div className="detail-section" style={{ textAlign: 'center', padding: '48px 24px' }}>
        <div style={{ fontSize: 30 }}>📡</div>
        <div style={{ fontSize: 15, fontWeight: 600, marginTop: 8 }}>{t('No frameworks to assess')}</div>
        <div className="page-sub" style={{ marginTop: 4 }}>{t('This client isn’t subscribed to any framework yet.')}</div>
        <button className="tb-btn" style={{ ...helpBtnStyle, marginTop: 16 }} onClick={() => setHelpOpen(true)}>
          <Calculator size={14} aria-hidden /> {t('How maturity is calculated')}
        </button>
      </div>
      {helpOpen && <MaturityHelpModal admin={isReviewer} lang={lang} onClose={() => setHelpOpen(false)} />}
    </>
  )

  const radarData = (m?.domains || []).map(d => ({
    domain: d.domain, current: d.current, perceived: d.perceived ?? null, target: d.target,
    previous: d.previous ?? null,
  }))
  const hasPrev = (m?.domains || []).some(d => d.previous !== null)
  const hasPerc = (m?.domains || []).some(d => d.perceived !== null)

  return (
    <div className="fi">
      {/* Top metric cards */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 16, alignItems: 'center' }}>
        <div className="card" style={{ flex: '1 1 180px', display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ fontSize: 22 }}>🙋</div>
          <div>
            <div className="page-sub" style={{ fontSize: 11 }}>{t('Overall Perceived Maturity')}</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#0EA5E9' }}>{m?.overall_perceived ?? '-'}<span style={{ fontSize: 13, color: 'var(--text3)' }}> / {m?.scale_max ?? 5}</span></div>
            <div style={{ fontSize: 9, color: 'var(--text3)' }}>{t('client self-assessment')}</div>
          </div>
        </div>
        <div className="card" style={{ flex: '1 1 180px', display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ fontSize: 22 }}>🛡️</div>
          <div>
            <div className="page-sub" style={{ fontSize: 11 }}>{t('Assessed Maturity')}</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: '#16A34A' }}>{m?.overall_current ?? 0}<span style={{ fontSize: 13, color: 'var(--text3)' }}> / {m?.scale_max ?? 5}</span></div>
            <div style={{ fontSize: 9, color: 'var(--text3)' }}>{t('from evidence / auditor')}</div>
          </div>
        </div>
        <div className="card" style={{ flex: '1 1 150px', display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ fontSize: 22 }}>🎯</div>
          <div>
            <div className="page-sub" style={{ fontSize: 11 }}>{t('Target')}</div>
            <div style={{ fontSize: 26, fontWeight: 700 }}>{m?.overall_target ?? 0}<span style={{ fontSize: 13, color: 'var(--text3)' }}> / {m?.scale_max ?? 5}</span></div>
          </div>
        </div>
        <div className="card" style={{ flex: '1 1 160px', display: 'flex', alignItems: 'center', gap: 14 }}>
          <div style={{ fontSize: 22 }}>💠</div>
          <div>
            <div className="page-sub" style={{ fontSize: 11 }}>{t('Risk score')}</div>
            <div style={{ fontSize: 26, fontWeight: 700, color: riskScoreColor(m?.risk_score ?? 0) }}>{m?.risk_score ?? 0}<span style={{ fontSize: 13, color: 'var(--text3)' }}> / 100</span></div>
          </div>
        </div>
        <div style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 10 }}>
          <button className="tb-btn" onClick={() => setHelpOpen(true)}
            style={helpBtnStyle} title={t('How maturity is calculated')}>
            <Calculator size={14} aria-hidden /> {t('How maturity is calculated')}
          </button>
          <select value={fwId} onChange={e => setFwId(e.target.value)}
            style={{ fontSize: 13, padding: '7px 10px', border: '1px solid var(--border-l)', borderRadius: 8, background: 'var(--card)', fontWeight: 600 }}>
            {fws.map(f => <option key={f.id} value={f.id}>{f.name}</option>)}
          </select>
          {m?.can_edit && (
            <button className="tb-btn" disabled={snapshot.isPending} onClick={() => snapshot.mutate()}
              title={t("Freeze today's levels as the new 'Previous' baseline")}>{t('📸 Save snapshot')}</button>
          )}
          {m?.can_edit && (
            <button className="tb-btn" onClick={() => setSnapOpen(true)}
              title={t('View, choose, or reset saved snapshots')}><History size={13} aria-hidden /> {t('Snapshots')}</button>
          )}
        </div>
      </div>

      <div className="detail-wrap" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
        {/* Radar */}
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 2 }}>{t('Maturity')}</div>
          <div className="page-sub" style={{ fontSize: 11, marginBottom: 10 }}>{t('Area of Interest')}{m?.snapshot_at ? t(' · previous from {date}', { date: m.snapshot_at }) : ''}</div>
          {isLoading ? <div className="page-sub">{t('Loading…')}</div> : (
            <ResponsiveContainer width="100%" height={460}>
              <RadarChart data={radarData} cx="50%" cy="50%" outerRadius="72%">
                <PolarGrid />
                <PolarAngleAxis dataKey="domain" tick={{ fontSize: 9, fill: 'var(--text2)' }} />
                <PolarRadiusAxis domain={[0, m?.scale_max ?? 5]} tick={{ fontSize: 9 }} />
                {hasPerc && <Radar name={t('Perceived (self-assessed)')} dataKey="perceived" stroke="#0EA5E9" fill="#0EA5E9" fillOpacity={0.18} />}
                <Radar name={t('Assessed Maturity')} dataKey="current" stroke="#16A34A" fill="#16A34A" fillOpacity={0.22} />
                <Radar name={t('Target Maturity')} dataKey="target" stroke="#6366F1" strokeDasharray="4 3" fill="#6366F1" fillOpacity={0.04} />
                {hasPrev && <Radar name={t('Previous Maturity')} dataKey="previous" stroke="#EA580C" fill="#EA580C" fillOpacity={0} />}
                <Legend wrapperStyle={{ fontSize: 11 }} />
              </RadarChart>
            </ResponsiveContainer>
          )}
          <div style={{ fontSize: 11.5, color: 'var(--text2)', lineHeight: 1.6, background: 'var(--soft)', border: '1px solid var(--border-l)', borderRadius: 'var(--r)', padding: '10px 12px', marginTop: 8 }}>
            {t('A visual representation like the one above lets you quickly identify the domains that need attention and prioritise improvement where it matters most.')}
          </div>
        </div>

        {/* Domains table */}
        <div className="card">
          <div style={{ fontWeight: 700, marginBottom: 2 }}>{t('Domains')}</div>
          <div className="page-sub" style={{ fontSize: 11, marginBottom: 10 }}>{t('Score, target and risk')}{m?.can_edit ? t(' · editable') : ''}</div>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12.5 }}>
            <thead>
              <tr style={{ textAlign: 'left', color: 'var(--text3)', fontSize: 10, textTransform: 'uppercase', letterSpacing: '.04em' }}>
                <th style={{ padding: '6px 4px' }}>{t('Domain')}</th>
                <th style={{ padding: '6px 4px', width: 64 }}>{t('Perceived')}</th>
                <th style={{ padding: '6px 4px', width: 70 }}>{t('Assessed')}</th>
                <th style={{ padding: '6px 4px', width: 90 }}>{t('Rating')}</th>
                {m?.can_edit && <th style={{ padding: '6px 4px', width: 70 }}>{t('Target')}</th>}
                <th style={{ padding: '6px 4px', width: 64 }}>{t('Risk')}</th>
              </tr>
            </thead>
            <tbody>
              {(m?.domains || []).map(d => (
                <tr key={d.domain} style={{ borderTop: '1px solid var(--border-l)' }}>
                  <td style={{ padding: '7px 4px', color: 'var(--eva-blue2)', fontWeight: 500 }}>
                    {d.domain}
                    <div style={{ fontSize: 10, color: 'var(--text3)', fontWeight: 400 }}>
                      {t('{a}/{b} compliant', { a: d.compliant, b: d.controls })}{d.current_overridden ? t(' · manual') : t(' · auto')}
                    </div>
                  </td>
                  <td style={{ padding: '7px 4px', color: d.perceived !== null ? '#0EA5E9' : 'var(--text3)', fontWeight: 600 }}>
                    {d.perceived !== null ? d.perceived : '-'}
                  </td>
                  <td style={{ padding: '7px 4px' }}>
                    {m?.can_edit ? (
                      <select value={d.current} onChange={e => patchDomain.mutate({ domain: d.domain, current_level: Number(e.target.value) })}
                        style={lvlSel}>
                        {[0, 1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
                      </select>
                    ) : <span style={{ fontWeight: 600 }}>{d.current}</span>}
                  </td>
                  <td style={{ padding: '7px 4px' }}><Stars level={d.current} /></td>
                  {m?.can_edit && (
                    <td style={{ padding: '7px 4px' }}>
                      <select value={d.target} onChange={e => patchDomain.mutate({ domain: d.domain, target_level: Number(e.target.value) })}
                        style={lvlSel}>
                        {[0, 1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
                      </select>
                    </td>
                  )}
                  <td style={{ padding: '7px 4px' }}><span className={`badge ${RISK_BADGE[d.risk] || 'b-gray'}`} style={{ fontSize: 10 }}>{d.risk}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
          {m?.can_edit && (
            <div className="page-sub" style={{ fontSize: 10.5, marginTop: 8 }}>
              {t('Current is auto-seeded from compliance; change it to override. Set Target to define the goal used by the radar and risk score.')}
            </div>
          )}
        </div>
      </div>

      {helpOpen && <MaturityHelpModal admin={isReviewer} lang={lang} onClose={() => setHelpOpen(false)} />}
      {snapOpen && <SnapshotsModal fwId={fwId} clientId={clientId} onClose={() => setSnapOpen(false)} />}
    </div>
  )
}

interface SnapRow { id: string; taken_at: string | null; label: string | null; overall: number | null; is_baseline: boolean; is_effective: boolean }

/**
 * Manage saved maturity snapshots: see every dated baseline, pick which one is
 * the "Previous" comparison (pin/un-pin), delete one, or reset them all.
 */
function SnapshotsModal({ fwId, clientId, onClose }: { fwId: string; clientId: string | null; onClose: () => void }) {
  const t = useT()
  const qc = useQueryClient()
  const refreshRadar = () => qc.invalidateQueries({ queryKey: ['maturity', fwId, clientId] })

  const { data, isLoading } = useQuery<{ can_edit: boolean; snapshots: SnapRow[] }>({
    queryKey: ['maturity-snapshots', fwId, clientId],
    queryFn: async () => (await api.get(`/maturity/${fwId}/snapshots`)).data,
    enabled: !!fwId,
  })
  const after = () => { qc.invalidateQueries({ queryKey: ['maturity-snapshots', fwId, clientId] }); refreshRadar() }

  const pin = useMutation({
    mutationFn: async (id: string) => (await api.post(`/maturity/${fwId}/snapshots/${id}/baseline`, {})).data,
    onSuccess: after,
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/maturity/${fwId}/snapshots/${id}`)).data,
    onSuccess: after,
  })
  const reset = useMutation({
    mutationFn: async () => (await api.delete(`/maturity/${fwId}/snapshots`)).data,
    onSuccess: after,
  })

  const snaps = data?.snapshots || []

  return (
    <div className="modal-overlay" style={{ zIndex: 60 }} onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 560, width: '92%', display: 'flex', flexDirection: 'column', maxHeight: '86vh' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '14px 18px', borderBottom: '1px solid var(--border, rgba(255,255,255,.12))' }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{t('Saved snapshots')}</div>
          <button className="tb-btn" style={{ padding: 4 }} onClick={onClose}><X size={16} aria-hidden /></button>
        </div>
        <div style={{ padding: '14px 18px', overflowY: 'auto' }}>
          <div className="page-sub" style={{ fontSize: 11.5, marginBottom: 12 }}>
            {t('The snapshot marked “In use” draws the Previous line on the radar. Star a different date to compare against it, or delete the ones you don’t need.')}
          </div>
          {isLoading ? <div className="page-sub">{t('Loading…')}</div> : snaps.length === 0 ? (
            <div className="page-sub">{t('No snapshots yet. Use “Save snapshot” to freeze the current levels.')}</div>
          ) : (
            <div style={{ display: 'grid', gap: 8 }}>
              {snaps.map(s => (
                <div key={s.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '10px 12px', border: '1px solid var(--border-l)', borderRadius: 8, background: s.is_effective ? 'var(--soft)' : 'var(--card)' }}>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 13 }}>
                      {s.taken_at || '—'}
                      {s.label ? <span style={{ color: 'var(--text3)', fontWeight: 400 }}> · {s.label}</span> : null}
                    </div>
                    <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2, display: 'flex', gap: 6, alignItems: 'center' }}>
                      {s.overall !== null && <span>{t('Overall {n}/5', { n: s.overall })}</span>}
                      {s.is_effective && <span className="badge b-green" style={{ fontSize: 9 }}>{t('In use')}</span>}
                      {s.is_baseline && <span className="badge b-blue" style={{ fontSize: 9 }}>{t('Pinned')}</span>}
                    </div>
                  </div>
                  <button className="tb-btn" disabled={pin.isPending} onClick={() => pin.mutate(s.id)}
                    title={s.is_baseline ? t('Un-pin (use the most recent instead)') : t('Use this date as the comparison')}
                    style={{ color: s.is_baseline ? 'var(--sky, #1A8FD1)' : 'var(--text3)' }}>
                    <Star size={14} aria-hidden fill={s.is_baseline ? 'currentColor' : 'none'} />
                  </button>
                  <button className="tb-btn" disabled={del.isPending} onClick={() => { if (confirm(t('Delete this snapshot?'))) del.mutate(s.id) }}
                    title={t('Delete')} style={{ color: 'var(--red)' }}><Trash2 size={14} aria-hidden /></button>
                </div>
              ))}
            </div>
          )}
        </div>
        {snaps.length > 0 && (
          <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border, rgba(255,255,255,.12))', display: 'flex', justifyContent: 'flex-end' }}>
            <button className="tb-btn" disabled={reset.isPending} style={{ color: 'var(--red)' }}
              onClick={() => { if (confirm(t('Delete ALL snapshots for this framework? This removes the Previous comparison.'))) reset.mutate() }}>
              <Trash2 size={13} aria-hidden /> {t('Reset all')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/**
 * "How maturity is calculated" reference. Shows a real Word document, rendered
 * in-app: the client edition (no technical annex) for client users, the
 * internal edition (with the annex) for reviewers. EN/FR toggle + download.
 * The .docx files are static assets under /references (served by the frontend).
 */
function MaturityHelpModal({ admin, lang, onClose }: { admin: boolean; lang: string; onClose: () => void }) {
  const t = useT()
  const [fr, setFr] = useState(lang === 'fr')
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const hostRef = useRef<HTMLDivElement | null>(null)

  const fileFor = (asFr: boolean) =>
    `/references/maturity_how_it_works_${admin ? 'admin' : 'client'}_${asFr ? 'fr' : 'en'}.docx`

  useEffect(() => {
    let cancelled = false
    const el = hostRef.current
    if (!el) return
    setLoading(true); setError(false)
    el.innerHTML = ''
    ;(async () => {
      try {
        const res = await fetch(fileFor(fr), { credentials: 'same-origin' })
        if (!res.ok) throw new Error('not found')
        const blob = await res.blob()
        if (cancelled || !hostRef.current) return
        // Load the heavy Word renderer only when the modal is opened, so it
        // stays out of the main bundle and the app loads fast.
        const { renderAsync } = await import('docx-preview')
        if (cancelled || !hostRef.current) return
        await renderAsync(blob, hostRef.current, undefined, {
          className: 'docx', inWrapper: true, breakPages: true, experimental: true, useBase64URL: true,
        })
      } catch {
        if (!cancelled) setError(true)
      } finally {
        if (!cancelled) setLoading(false)
      }
    })()
    return () => { cancelled = true }
  }, [fr, admin])

  const download = async () => {
    try {
      const res = await fetch(fileFor(fr), { credentials: 'same-origin' })
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = fr ? 'Comment_la_maturite_est_calculee.docx' : 'How_Maturity_Is_Calculated.docx'
      a.click()
      URL.revokeObjectURL(url)
    } catch { /* ignore */ }
  }

  return (
    <div className="modal-overlay" style={{ zIndex: 60 }} onClick={onClose}>
      <div className="modal-card" style={{ maxWidth: 820, width: '92%', display: 'flex', flexDirection: 'column', maxHeight: '88vh' }} onClick={e => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 10, padding: '14px 18px', borderBottom: '1px solid var(--border, rgba(255,255,255,.12))' }}>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)', minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
            {t('How maturity is calculated')}
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6, flexShrink: 0 }}>
            <div style={{ display: 'flex', border: '1px solid var(--border, rgba(255,255,255,.15))', borderRadius: 8, overflow: 'hidden' }}>
              <button className="tb-btn" style={{ border: 'none', borderRadius: 0, background: !fr ? 'var(--accent, #2E5FA3)' : 'transparent', color: !fr ? '#fff' : 'var(--text2)' }} onClick={() => setFr(false)}>EN</button>
              <button className="tb-btn" style={{ border: 'none', borderRadius: 0, background: fr ? 'var(--accent, #2E5FA3)' : 'transparent', color: fr ? '#fff' : 'var(--text2)' }} onClick={() => setFr(true)}>FR</button>
            </div>
            <button className="tb-btn" onClick={download} title={t('Download')}><Download size={13} aria-hidden /></button>
            <button className="tb-btn" style={{ padding: 4 }} onClick={onClose}><X size={16} aria-hidden /></button>
          </div>
        </div>
        <div style={{ padding: '16px', overflowY: 'auto', background: '#e9edf3' }}>
          {loading && <div className="page-sub" style={{ padding: 12 }}>{t('Loading preview…')}</div>}
          {error && <div className="page-sub" style={{ color: 'var(--red)', padding: 12 }}>{t('Could not load this preview.')}</div>}
          <div ref={hostRef} className="docx-host" style={{ display: loading || error ? 'none' : 'block' }} />
        </div>
      </div>
    </div>
  )
}

const lvlSel = { fontSize: 12, padding: '3px 6px', border: '1px solid var(--border-l)', borderRadius: 6, background: 'var(--card)' }

// Highlighted accent pill so the maturity reference stands out from plain buttons.
const helpBtnStyle: React.CSSProperties = {
  display: 'inline-flex', alignItems: 'center', gap: 6, fontWeight: 600,
  color: '#fff', background: 'var(--sky, #1A8FD1)',
  border: '1px solid var(--sky, #1A8FD1)', borderRadius: 8,
  boxShadow: '0 1px 4px rgba(26,143,209,.35)',
}
