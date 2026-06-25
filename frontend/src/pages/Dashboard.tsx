import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import { useClientContext } from '../store/clientContext'
import GettingStarted from '../components/GettingStarted'

interface Stat { pct: number; done: number; total: number; evid: number; gaps: number }
interface Fw { key: string; name: string; desc: string; tier: string; controls: number; domains: number; pct: number; badge: string; icon: string; color: string; bg: string }
interface Ctrl { ref: string; name: string; domain: string; risk: string; riskLabel: string }
interface Status { label: string; count: number; col: string }
interface Activity { dot: string; who: string; title: string; ref: string; status: string; time: string }
interface Summary {
  user: { name: string; role: string }
  stats: Stat
  frameworks: Fw[]
  priorityControls: Ctrl[]
  byStatus: Status[]
  activity: Activity[]
}

interface MatSummary {
  has_data: boolean; perceived: number | null; assessed: number; target: number
  gap: number | null; risk_score: number; scale_max: number; needs_client?: boolean
}

const riskColor = (pct: number) => (pct >= 75 ? '#16A34A' : pct >= 40 ? '#D97706' : '#DC2626')
const badgeClass = (b: string) =>
  b === 'Active' ? 'b-blue' : b === 'In Progress' ? 'b-amber' : 'b-gray'

// SVG progress ring matching the mockup
function Ring({ pct, size = 120, stroke = 11 }: { pct: number; size?: number; stroke?: number }) {
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const off = c - (pct / 100) * c
  const col = riskColor(pct)
  return (
    <div style={{ position: 'relative', width: size, height: size, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} style={{ transform: 'rotate(-90deg)' }}>
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="var(--surface-2)" strokeWidth={stroke} />
        <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke={col} strokeWidth={stroke}
          strokeDasharray={c} strokeDashoffset={off} strokeLinecap="round" />
      </svg>
      <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%,-50%)', textAlign: 'center', pointerEvents: 'none' }}>
        <div style={{ fontSize: 22, fontWeight: 600, color: col, lineHeight: 1 }}>{pct}%</div>
        <div style={{ fontSize: 9, color: '#94A3B8', marginTop: 2 }}>score</div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const navigate = useNavigate()
  const t = useT()
  const clientId = useClientContext(s => s.clientId)
  const { data, isLoading, isError } = useQuery<Summary>({
    queryKey: ['dashboard-summary'],
    queryFn: async () => (await api.get('/dashboard/summary')).data,
  })
  const { data: mat } = useQuery<MatSummary>({
    queryKey: ['maturity-summary'],
    queryFn: async () => (await api.get('/maturity/summary')).data,
  })
  const { data: support } = useQuery<{ cases: { status: string }[] }>({
    queryKey: ['dash-support-open'],
    queryFn: async () => (await api.get('/support/cases')).data,
  })

  if (isLoading) return <div className="page-sub">{t('Loading dashboard…')}</div>
  if (isError || !data) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load dashboard.')}</div>

  const { user, stats, frameworks, priorityControls, byStatus, activity } = data
  const first = user.name.split(' ')[0]
  const openTickets = (support?.cases || []).filter(c => c.status === 'open' || c.status === 'in_progress').length
  const isEva = ['super_admin', 'eva_auditor'].includes(user.role)
  // Reviewers (EVA / MSP) with no client selected see a portfolio rollup across
  // all their clients - label it as such so it's not mistaken for one org.
  const isReviewer = ['super_admin', 'eva_auditor', 'msp_admin', 'msp_analyst'].includes(user.role)
  const portfolioView = isReviewer && !clientId
  // EVA always sees the support box (entry to the console); others only when there's something open.
  const showSupport = isEva || openTickets > 0

  return (
    <>
      <GettingStarted />

      {/* Header */}
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Welcome back, {name}', { name: first })} 👋</div>
          <div className="page-sub">{portfolioView ? t('Compliance posture across all your clients.') : t("Here's your compliance posture at a glance.")}</div>
        </div>
        <div>
          <button className="tb-btn" onClick={() => navigate('/evidence')}>📊 {t('Generate report')}</button>
        </div>
      </div>

      {/* Stat cards */}
      <div className="stat-grid fi2" style={{ gridTemplateColumns: showSupport ? 'repeat(5, 1fr)' : undefined }}>
        <div className="stat-card blue" onClick={() => navigate('/controls')}>
          <div className="stat-icon blue">🛡</div>
          <div className="stat-lbl">{t('Compliance')}</div>
          <div className="stat-val blue">{stats.pct}%</div>
          <div className="stat-sub">{t('Overall readiness score')}</div>
        </div>
        <div className="stat-card green" onClick={() => navigate('/controls')}>
          <div className="stat-icon green">✅</div>
          <div className="stat-lbl">{t('Controls done')}</div>
          <div className="stat-val green">{stats.done}</div>
          <div className="stat-sub">{t('of {n} controls', { n: stats.total })}</div>
        </div>
        <div className="stat-card amber" onClick={() => navigate('/evidence')}>
          <div className="stat-icon amber">⏳</div>
          <div className="stat-lbl">{t('Evidence pending')}</div>
          <div className="stat-val amber">{stats.evid}</div>
          <div className="stat-sub">{t('{n} items', { n: stats.evid })}</div>
        </div>
        <div className="stat-card red" onClick={() => navigate('/controls')}>
          <div className="stat-icon red">⚠️</div>
          <div className="stat-lbl">{t('Critical gaps')}</div>
          <div className="stat-val red">{stats.gaps}</div>
          <div className="stat-sub">{t('{n} high risk', { n: stats.gaps })}</div>
        </div>
        {showSupport && (
          <div className="stat-card amber" onClick={() => navigate(isEva ? '/support-cases' : '/support')}
            style={{ background: openTickets > 0 ? 'rgba(217,119,6,.06)' : undefined }}>
            <div className="stat-icon" style={{ background: openTickets > 0 ? 'rgba(217,119,6,.16)' : 'var(--soft)' }}>🎧</div>
            <div className="stat-lbl">{t('Open support')}</div>
            <div className={openTickets > 0 ? 'stat-val amber' : 'stat-val'}>{openTickets}</div>
            <div className="stat-sub">{isEva ? t('Open console →') : t('View →')}</div>
          </div>
        )}
      </div>

      {/* Maturity: perceived vs assessed */}
      {mat?.has_data && (() => {
        const sm = mat.scale_max || 5
        const Bar = ({ label, val, color }: { label: string; val: number | null; color: string }) => (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
            <span style={{ width: 86, fontSize: 11, color: 'var(--text2)' }}>{label}</span>
            <div style={{ flex: 1, height: 9, background: 'var(--surface-2)', borderRadius: 6, overflow: 'hidden' }}>
              <div style={{ width: `${((val ?? 0) / sm) * 100}%`, height: '100%', background: color }} />
            </div>
            <span style={{ width: 46, textAlign: 'right', fontSize: 12, fontWeight: 600, color }}>{val ?? '-'}/{sm}</span>
          </div>
        )
        const gap = mat.gap
        const gapTxt = gap == null ? t('No self-assessment yet')
          : gap >= 0.5 ? t('Client rates itself {gap} above assessed', { gap })
            : gap <= -0.5 ? t('Assessed exceeds perceived by {gap}', { gap: Math.abs(gap) })
              : t('Perceived and assessed are aligned')
        const gapCol = gap == null ? 'b-gray' : gap >= 0.5 ? 'b-amber' : gap <= -0.5 ? 'b-blue' : 'b-green'
        return (
          <div className="card fi2" style={{ marginBottom: 16, cursor: 'pointer' }} onClick={() => navigate('/maturity')}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <div style={{ fontWeight: 700 }}>{t('Maturity: perceived vs assessed')}</div>
              <span style={{ fontSize: 11, color: 'var(--eva-blue2)', fontWeight: 600 }}>{t('View radar →')}</span>
            </div>
            <Bar label={t('Perceived')} val={mat.perceived} color="#0EA5E9" />
            <Bar label={t('Assessed')} val={mat.assessed} color="#16A34A" />
            <Bar label={t('Target')} val={mat.target} color="#6366F1" />
            <span className={`badge ${gapCol}`} style={{ marginTop: 4, fontSize: 11 }}>{gapTxt}</span>
          </div>
        )
      })()}

      {/* Frameworks heading */}
      <div style={{ marginBottom: 8 }} className="fi2">
        <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--text)' }}>{t('Frameworks')}</div>
        <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 2 }}>{t('Select a framework to view its controls.')}</div>
      </div>

      {/* Framework cards */}
      <div className="fw-grid fi3">
        {frameworks.map(fw => (
          <div key={fw.key} className="fw-card" onClick={() => navigate('/controls')} style={{ borderTop: `3px solid ${fw.color}` }}>
            <span className={`fw-card-badge ${badgeClass(fw.badge)}`}>{fw.badge}</span>
            <div className="fw-card-icon" style={{ background: fw.bg }}>{fw.icon}</div>
            <div className="fw-card-name">{fw.name}</div>
            <div className="fw-card-desc">{fw.desc}</div>
            <div className="fw-card-stats">
              <div className="fw-stat">
                <div className="fw-stat-val" style={{ color: fw.color }}>{fw.controls}</div>
                <div className="fw-stat-lbl">{t('Controls')}</div>
              </div>
              <div className="fw-stat">
                <div className="fw-stat-val">{fw.domains}</div>
                <div className="fw-stat-lbl">{t('Domains')}</div>
              </div>
              <div className="fw-stat">
                <div className="fw-stat-val" style={{ color: riskColor(fw.pct) }}>{fw.pct}%</div>
                <div className="fw-stat-lbl">{t('Progress')}</div>
              </div>
            </div>
            <div className="fw-prog">
              <div className="fw-prog-meta">
                <span style={{ fontSize: 10, color: 'var(--text3)' }}>{t('Level: {tier}', { tier: fw.tier })}</span>
                <span style={{ fontSize: 10, fontWeight: 600, color: fw.color }}>{fw.pct}%</span>
              </div>
              <div className="fw-prog-bar"><div className="fw-prog-fill" style={{ width: `${fw.pct}%`, background: fw.color }} /></div>
            </div>
          </div>
        ))}
      </div>

      {/* Bottom row */}
      <div className="row-3 fi3">
        {/* Priority controls */}
        <div className="card">
          <div className="card-hdr">
            <span className="card-title">{t('Priority controls to action')}</span>
            <span className="card-link" onClick={() => navigate('/controls')}>{t('View all')}</span>
          </div>
          <div className="ctrl-list">
            {priorityControls.length === 0 && <div className="page-sub">{t('Nothing outstanding - nice work.')}</div>}
            {priorityControls.map(c => (
              <div key={c.ref} className="ctrl-row-d" onClick={() => navigate('/controls')}>
                <span className="ctrl-ref">{c.ref}</span>
                <span className="ctrl-name">{c.name}</span>
                <span className="ctrl-domain">{c.domain}</span>
                <span className={`badge ${c.risk}`}>{c.riskLabel}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Readiness ring */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 600, color: 'var(--text2)', textTransform: 'uppercase', letterSpacing: '.05em' }}>{t('Audit Readiness')}</div>
          <Ring pct={stats.pct} />
          <div style={{ width: '100%' }}>
            {byStatus.map(s => (
              <div key={s.label} className="prog-row" style={{ marginBottom: 6 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 5, flex: 1 }}>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: s.col, display: 'inline-block', flexShrink: 0 }} />
                  <span style={{ fontSize: 11, color: 'var(--text2)' }}>{s.label}</span>
                </div>
                <span style={{ fontSize: 11, fontWeight: 600, color: 'var(--text)', width: 28, textAlign: 'right' }}>{s.count}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Alerts + Activity */}
        <div className="card" style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
          <div className="card-hdr" style={{ marginBottom: 10 }}>
            <span className="card-title">{t('Evidence alerts')}</span>
          </div>
          <div className="alert-row warn">
            <span className="alert-icon">⚠️</span>
            <div className="alert-content">
              <div className="alert-title">{t('Evidence expiring soon')}</div>
              <div className="alert-sub">{t('Some evidence reaches its renewal window.')}</div>
            </div>
          </div>
          <div className="alert-row info">
            <span className="alert-icon">🔍</span>
            <div className="alert-content">
              <div className="alert-title">{t('{n} awaiting review', { n: stats.evid })}</div>
              <div className="alert-sub">{t('Items submitted and pending a decision.')}</div>
            </div>
          </div>
          <div className="alert-row danger">
            <span className="alert-icon">🚨</span>
            <div className="alert-content">
              <div className="alert-title">{t('{n} critical gaps identified', { n: stats.gaps })}</div>
              <div className="alert-sub">{t('High-risk controls not yet implemented.')}</div>
            </div>
          </div>

          <div className="card-hdr" style={{ marginTop: 14, marginBottom: 8 }}>
            <span className="card-title">{t('Recent activity')}</span>
          </div>
          {activity.length === 0 && <div className="page-sub">{t('No recent activity.')}</div>}
          {activity.slice(0, 3).map((a, i) => (
            <div key={i} className="activity-item">
              <div className="activity-dot" style={{ background: a.dot }} />
              <div className="activity-text"><b>{a.who}</b> · <b>{a.title}</b> for {a.ref} ({a.status})</div>
              <div className="activity-time">{a.time}</div>
            </div>
          ))}
        </div>
      </div>
    </>
  )
}
