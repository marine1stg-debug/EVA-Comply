import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Client {
  id: string; name: string; short: string; color: string; compliance: number
  controls_done: number; controls_total: number; evidence_pending: number; status: string
  frameworks: string[]; plan: string; monthly_fee: number; eva_cost: number; margin: number
}
interface Kpis {
  total_clients: number; active_clients: number; onboarding: number; avg_compliance: number
  ready: number; at_risk: number; total_pending: number; total_mrr: number; total_cost: number
  total_margin: number; margin_pct: number
}

interface MatRow { id: string; name: string; perceived: number | null; assessed: number; target: number; gap: number | null; has_data: boolean }

const progColor = (p: number) => (p >= 75 ? '#16A34A' : p >= 40 ? '#D97706' : '#DC2626')

export default function PortfolioPage() {
  const navigate = useNavigate()
  const t = useT()
  const { data, isLoading, isError, error } = useQuery<{ clients: Client[]; kpis: Kpis }>({
    queryKey: ['msp-portfolio'],
    queryFn: async () => (await api.get('/msp/portfolio')).data,
  })
  const { data: matp } = useQuery<{ clients: MatRow[] }>({
    queryKey: ['maturity-portfolio'],
    queryFn: async () => (await api.get('/maturity/portfolio')).data,
  })

  if (isLoading) return <div className="page-sub">{t('Loading portfolio…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('The portfolio view requires MSP access.') : t('Failed to load portfolio.')}
    </div>
  }
  if (!data) return null
  const { clients, kpis } = data

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('MSP Portfolio')}</div>
          <div className="page-sub">{t('{n} clients · compliance & margin overview', { n: kpis.total_clients })}</div>
        </div>
        <div className="page-actions"><button className="tb-btn" onClick={() => navigate('/clients')}>{t('👥 Manage Clients')}</button></div>
      </div>

      <div className="msp-kpi-grid fi">
        <div className="kpi-card blue" onClick={() => navigate('/clients')}>
          <div className="kpi-icon blue">🏢</div><div className="kpi-lbl">{t('Active Clients')}</div>
          <div className="kpi-val blue">{kpis.active_clients}</div>
          <div className="kpi-sub">{t('{total} total · {n} onboarding', { total: kpis.total_clients, n: kpis.onboarding })}</div>
        </div>
        <div className="kpi-card green">
          <div className="kpi-icon green">🛡</div><div className="kpi-lbl">{t('Avg Compliance')}</div>
          <div className="kpi-val green">{kpis.avg_compliance}%</div>
          <div className="kpi-sub">{t('{ready} audit-ready · {risk} at risk', { ready: kpis.ready, risk: kpis.at_risk })}</div>
        </div>
        <div className="kpi-card amber" onClick={() => navigate('/review')}>
          <div className="kpi-icon amber">⏳</div><div className="kpi-lbl">{t('Pending Reviews')}</div>
          <div className="kpi-val amber">{kpis.total_pending}</div>
          <div className="kpi-sub">{t('evidence items to review')}</div>
        </div>
        <div className="kpi-card purple">
          <div className="kpi-icon purple">💰</div><div className="kpi-lbl">{t('Monthly Margin')}</div>
          <div className="kpi-val purple">${kpis.total_margin.toLocaleString()}</div>
          <div className="kpi-sub">{t('{mrr} MRR · {cost} cost', { mrr: `$${kpis.total_mrr.toLocaleString()}`, cost: `$${kpis.total_cost.toLocaleString()}` })}</div>
        </div>
      </div>

      <div className="detail-section fi" style={{ marginBottom: 16 }}>
        <div className="card-hdr"><span className="card-title">{t('Client Compliance Overview')}</span>
          <span className="card-link" onClick={() => navigate('/clients')}>{t('Manage clients →')}</span></div>
        {clients.length === 0 && <div className="page-sub">{t('No clients yet.')}</div>}
        {clients.map(c => {
          const col = progColor(c.compliance)
          return (
            <div key={c.id} style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border-l)', cursor: 'pointer' }} onClick={() => navigate('/clients')}>
              <div className="client-avatar" style={{ background: c.color, width: 32, height: 32, fontSize: 11 }}>{c.short}</div>
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 3 }}>
                  <span style={{ fontSize: 12, fontWeight: 600 }}>{c.name}</span>
                  <span style={{ fontSize: 11, fontWeight: 700, color: col }}>{c.compliance}%</span>
                </div>
                <div className="portfolio-bar"><div className="pbar-seg" style={{ width: `${c.compliance}%`, background: col }} /></div>
                <div style={{ display: 'flex', gap: 10, marginTop: 3, flexWrap: 'wrap' }}>
                  <span style={{ fontSize: 10, color: 'var(--text3)' }}>{t('{a}/{b} controls', { a: c.controls_done, b: c.controls_total })}</span>
                  <span style={{ fontSize: 10, color: 'var(--text3)' }}>{c.frameworks.join(', ')}</span>
                  {c.evidence_pending > 0 && <span style={{ fontSize: 10, color: 'var(--amber)', fontWeight: 600 }}>{t('⏳ {n} pending', { n: c.evidence_pending })}</span>}
                </div>
              </div>
            </div>
          )
        })}
      </div>

      {matp && matp.clients.some(c => c.has_data) && (
        <div className="detail-section fi">
          <div className="card-hdr"><span className="card-title">{t('Maturity: Perceived vs Assessed')}</span></div>
          <table className="margin-table">
            <thead><tr><th>{t('Client')}</th><th>{t('Perceived')}</th><th>{t('Assessed')}</th><th>{t('Target')}</th><th>{t('Gap')}</th></tr></thead>
            <tbody>
              {matp.clients.map(c => {
                const gap = c.gap
                const gcls = gap == null ? '' : gap >= 0.5 ? 'margin-negative' : gap <= -0.5 ? '' : 'margin-positive'
                return (
                  <tr key={c.id}>
                    <td>{c.name}</td>
                    <td style={{ color: c.perceived != null ? '#0EA5E9' : 'var(--text3)', fontWeight: 600 }}>{c.perceived ?? '—'}{c.perceived != null ? '/5' : ''}</td>
                    <td style={{ color: '#16A34A', fontWeight: 600 }}>{c.assessed}/5</td>
                    <td style={{ color: 'var(--text3)' }}>{c.target}/5</td>
                    <td className={gcls}>{gap == null ? '—' : `${gap > 0 ? '+' : ''}${gap}`}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
          <div className="page-sub" style={{ fontSize: 10.5, marginTop: 6 }}>
            {t('Gap = client self-assessed minus auditor-assessed (out of 5). A large positive gap flags a client that may be over-rating its maturity.')}
          </div>
        </div>
      )}

      <div className="detail-section fi">
        <div className="card-hdr"><span className="card-title">{t('Revenue & Margin Summary')}</span></div>
        <table className="margin-table">
          <thead><tr><th>{t('Client')}</th><th>{t('Plan')}</th><th>{t('Client Price')}</th><th>{t('EVA Cost')}</th><th>{t('Your Margin')}</th><th>{t('Margin %')}</th></tr></thead>
          <tbody>
            {clients.map(c => {
              const pct = c.monthly_fee ? Math.round(c.margin / c.monthly_fee * 100) : 0
              return (
                <tr key={c.id}>
                  <td><div style={{ display: 'flex', alignItems: 'center', gap: 7 }}><div className="client-avatar" style={{ background: c.color, width: 22, height: 22, fontSize: 9, borderRadius: 6 }}>{c.short}</div>{c.name}</div></td>
                  <td><span className="badge b-blue">{c.plan}</span></td>
                  <td>${c.monthly_fee}/mo</td>
                  <td style={{ color: 'var(--text3)' }}>${c.eva_cost}/mo</td>
                  <td className={c.margin > 0 ? 'margin-positive' : 'margin-negative'}>${c.margin}/mo</td>
                  <td className={pct > 30 ? 'margin-positive' : pct > 15 ? '' : 'margin-negative'}>{pct}%</td>
                </tr>
              )
            })}
            <tr style={{ background: 'var(--surface)', fontWeight: 700 }}>
              <td colSpan={2}>{t('Total')}</td>
              <td>${kpis.total_mrr}/mo</td>
              <td style={{ color: 'var(--text3)' }}>${kpis.total_cost}/mo</td>
              <td className="margin-positive">${kpis.total_margin}/mo</td>
              <td className="margin-positive">{kpis.margin_pct}%</td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  )
}
