import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Rec {
  id: string; control_id: string; control_ref: string; control_title: string
  domain: string; risk: string; source: string; title: string; text: string
  effort: string; impact: string; current_level: number | null; target_level: number | null
  gap: number | null; status: string; quick_win: boolean; priority: number; is_top10: boolean
}
interface Resp {
  recommendations: Rec[]; top10: Rec[]; quick_wins: Rec[]; top10_pinned?: boolean
  counts: { total?: number; open?: number; in_progress?: number; done?: number; quick_wins?: number; top10?: number }
  needs_client: boolean; can_generate: boolean; has_llm: boolean
}

const EFFORT_BADGE: Record<string, string> = { low: 'b-green', medium: 'b-gray', high: 'b-red' }
const IMPACT_BADGE: Record<string, string> = { high: 'b-blue', medium: 'b-gray', low: 'b-gray' }
const STATUS_BADGE: Record<string, string> = { open: 'b-gray', in_progress: 'b-blue', done: 'b-green', dismissed: 'b-gray' }
const STATUSES = ['open', 'in_progress', 'done', 'dismissed']

export default function RecommendationsPage() {
  const qc = useQueryClient()
  const navigate = useNavigate()
  const t = useT()
  const [filter, setFilter] = useState<string>('active')

  const { data, isLoading } = useQuery<Resp>({
    queryKey: ['recommendations'],
    queryFn: async () => (await api.get('/recommendations/')).data,
  })

  const gen = useMutation({
    mutationFn: async (source: 'premade' | 'ai') => (await api.post('/recommendations/generate', { source })).data,
    onSuccess: (r: any) => {
      const w = r.warning_count ? t(' ({n} skipped)', { n: r.warning_count }) : ''
      toast.success(t('Generated {n} recommendations across {c} gapped controls', { n: r.created, c: r.gapped_controls }) + w)
      qc.invalidateQueries({ queryKey: ['recommendations'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Generation failed')),
  })

  const setStatus = useMutation({
    mutationFn: async (v: { id: string; status: string }) => (await api.patch(`/recommendations/${v.id}`, { status: v.status })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendations'] }),
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/recommendations/${id}`)).data,
    onSuccess: () => { toast.success(t('Removed')); qc.invalidateQueries({ queryKey: ['recommendations'] }) },
  })
  const pin = useMutation({
    mutationFn: async (v: { id: string; on: boolean }) => (await api.patch(`/recommendations/${v.id}`, { is_top10: v.on })).data,
    onSuccess: () => qc.invalidateQueries({ queryKey: ['recommendations'] }),
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Update failed')),
  })
  const autoTop10 = useMutation({
    mutationFn: async () => (await api.post('/recommendations/auto-top10')).data,
    onSuccess: (r: any) => { toast.success(t('AI flagged {n} Top 10 priorities', { n: r.flagged })); qc.invalidateQueries({ queryKey: ['recommendations'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not auto-pick')),
  })
  const delAll = useMutation({
    mutationFn: async () => (await api.delete('/recommendations/all')).data,
    onSuccess: (r: any) => { toast.success(t('Deleted {n} recommendations', { n: r.deleted })); qc.invalidateQueries({ queryKey: ['recommendations'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not delete')),
  })
  const confirmDelAll = () => {
    if (window.confirm(t('Delete ALL recommendations for this client? This cannot be undone.'))) delAll.mutate()
  }

  if (isLoading) return <div className="page-sub">{t('Loading recommendations…')}</div>
  if (!data) return null
  if (data.needs_client) return <div className="page-sub">{t('Select a client to view recommendations.')}</div>

  const all = data.recommendations
  const filtered = filter === 'all' ? all
    : filter === 'active' ? all.filter(r => r.status !== 'done' && r.status !== 'dismissed')
      : filter === 'quick' ? all.filter(r => r.quick_win && r.status !== 'done' && r.status !== 'dismissed')
        : all.filter(r => r.status === filter)

  const LevelTag = ({ r }: { r: Rec }) => r.gap != null
    ? <span style={{ fontSize: 10, color: 'var(--text3)' }}>L{r.current_level}→{r.target_level}</span> : null

  const RecRow = ({ r, rank }: { r: Rec; rank?: number }) => (
    <div style={{ display: 'flex', gap: 10, padding: '10px 0', borderBottom: '1px solid var(--border-l)' }}>
      {rank != null && <div style={{ fontSize: 16, fontWeight: 800, color: 'var(--text3)', width: 24, textAlign: 'center' }}>{rank}</div>}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
          <span className="badge b-gray" style={{ fontSize: 9, cursor: 'pointer' }} onClick={() => navigate(`/controls?control=${r.control_id}`)}>{r.control_ref}</span>
          <span style={{ fontSize: 12.5, fontWeight: 600 }}>{r.title}</span>
          {r.quick_win && <span className="badge b-green" style={{ fontSize: 9 }}>{t('⚡ Quick win')}</span>}
          {r.source === 'ai' && <span className="badge b-blue" style={{ fontSize: 9 }}>✦ AI</span>}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--text2)', marginTop: 3 }}>{r.text}</div>
        <div style={{ display: 'flex', gap: 6, marginTop: 5, alignItems: 'center', flexWrap: 'wrap' }}>
          <span className={`badge ${IMPACT_BADGE[r.impact]}`} style={{ fontSize: 9 }}>{t('Impact: {v}', { v: r.impact })}</span>
          <span className={`badge ${EFFORT_BADGE[r.effort]}`} style={{ fontSize: 9 }}>{t('Effort: {v}', { v: r.effort })}</span>
          <LevelTag r={r} />
          <span style={{ fontSize: 10, color: 'var(--text3)' }}>· {r.domain}</span>
          <div style={{ flex: 1 }} />
          {r.is_top10 && <span className="badge b-amber" style={{ fontSize: 9 }}>{t('★ Top 10')}</span>}
          {data.can_generate ? (
            <>
              <button className="ev-action-btn" title={r.is_top10 ? 'Remove from Top 10' : 'Pin to Top 10'}
                style={{ color: r.is_top10 ? '#B45309' : 'var(--text3)' }}
                onClick={() => pin.mutate({ id: r.id, on: !r.is_top10 })}>{r.is_top10 ? '★' : '☆'}</button>
              <select value={r.status} onChange={e => setStatus.mutate({ id: r.id, status: e.target.value })}
                className={`badge ${STATUS_BADGE[r.status]}`} style={{ fontSize: 9, cursor: 'pointer', border: 'none' }}>
                {STATUSES.map(s => <option key={s} value={s}>{s.replace('_', ' ')}</option>)}
              </select>
              <button className="ev-action-btn" title="Remove" onClick={() => del.mutate(r.id)}>✕</button>
            </>
          ) : <span className={`badge ${STATUS_BADGE[r.status]}`} style={{ fontSize: 9 }}>{r.status.replace('_', ' ')}</span>}
        </div>
      </div>
    </div>
  )

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Recommendations')}</div>
          <div className="page-sub">{t('Remediation actions to close maturity gaps - prioritized, with Top 10 and quick wins.')}</div>
        </div>
        {data.can_generate && (
          <div className="page-actions">
            <button className="tb-btn" disabled={gen.isPending} onClick={() => gen.mutate('premade')}>
              {gen.isPending ? t('Working…') : t('📋 Generate from library')}
            </button>
            <button className="submit-btn" disabled={gen.isPending || !data.has_llm}
              title={data.has_llm ? 'Analyze self-assessments with the AI connector' : 'Enable the AI connector first (Admin → AI Connector)'}
              onClick={() => gen.mutate('ai')}>
              {gen.isPending ? t('Analyzing…') : t('✦ Generate with AI')}
            </button>
            {all.length > 0 && (
              <button className="tb-btn" disabled={autoTop10.isPending} title="Rank by impact × gap × risk and flag the top 10"
                onClick={() => autoTop10.mutate()}>{autoTop10.isPending ? t('Ranking…') : t('★ Auto-pick Top 10')}</button>
            )}
            {all.length > 0 && (
              <button className="tb-btn" disabled={delAll.isPending} title={t('Delete all generated recommendations')}
                style={{ color: 'var(--danger, #DC2626)' }}
                onClick={confirmDelAll}>{delAll.isPending ? t('Deleting…') : t('🗑 Delete all')}</button>
            )}
          </div>
        )}
      </div>

      {all.length === 0 ? (
        <div className="detail-section fi">
          <div className="page-sub">
            {t('No recommendations yet. {extra}', { extra: data.can_generate
              ? t('Generate them from the curated library, or run the AI analysis once the connector is enabled. Recommendations are created for every control where the client’s self-assessment sits below target.')
              : t('A reviewer can generate these from the recommendation library or AI analysis.') })}
          </div>
        </div>
      ) : (
        <>
          <div className="msp-kpi-grid fi" style={{ marginBottom: 16 }}>
            <div className="kpi-card blue"><div className="kpi-lbl">{t('Total')}</div><div className="kpi-val blue">{data.counts.total}</div><div className="kpi-sub">{t('recommendations')}</div></div>
            <div className="kpi-card green"><div className="kpi-lbl">{t('Quick wins')}</div><div className="kpi-val green">{data.counts.quick_wins}</div><div className="kpi-sub">{t('low effort · high impact')}</div></div>
            <div className="kpi-card amber"><div className="kpi-lbl">{t('Open')}</div><div className="kpi-val amber">{data.counts.open}</div><div className="kpi-sub">{t('{n} in progress', { n: data.counts.in_progress ?? 0 })}</div></div>
            <div className="kpi-card purple"><div className="kpi-lbl">{t('Done')}</div><div className="kpi-val purple">{data.counts.done}</div><div className="kpi-sub">{t('resolved')}</div></div>
          </div>

          {data.top10.length > 0 && (
            <div className="detail-section fi" style={{ marginBottom: 16 }}>
              <div className="card-hdr"><span className="card-title">{t('★ Top 10 priorities')}</span>
                <span className="page-sub" style={{ fontSize: 10.5 }}>
                  {data.top10_pinned ? t('curated - pinned or AI-selected') : t('ranked by impact × gap × risk (use ★ Auto-pick or pin to curate)')}
                </span></div>
              {data.top10.map((r, i) => <RecRow key={r.id} r={r} rank={i + 1} />)}
            </div>
          )}

          {data.quick_wins.length > 0 && (
            <div className="detail-section fi" style={{ marginBottom: 16 }}>
              <div className="card-hdr"><span className="card-title">{t('⚡ Quick wins')}</span>
                <span className="page-sub" style={{ fontSize: 10.5 }}>{t('low effort, high impact - do these first')}</span></div>
              {data.quick_wins.map(r => <RecRow key={r.id} r={r} />)}
            </div>
          )}

          <div className="detail-section fi">
            <div className="card-hdr">
              <span className="card-title">{t('All recommendations')}</span>
              <select value={filter} onChange={e => setFilter(e.target.value)} className="form-input" style={{ width: 'auto', fontSize: 12 }}>
                <option value="active">{t('Active')}</option>
                <option value="quick">{t('Quick wins')}</option>
                <option value="open">{t('Open')}</option>
                <option value="in_progress">{t('In progress')}</option>
                <option value="done">{t('Done')}</option>
                <option value="dismissed">{t('Dismissed')}</option>
                <option value="all">{t('All')}</option>
              </select>
            </div>
            {filtered.length === 0 ? <div className="page-sub">{t('Nothing matches this filter.')}</div>
              : filtered.map(r => <RecRow key={r.id} r={r} />)}
          </div>
        </>
      )}
    </>
  )
}
