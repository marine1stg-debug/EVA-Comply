import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Item {
  id: string; ev_title: string; ctrl_ref: string; ctrl_name: string; freq: string
  owner: string; due: string; days_left: number; status: string
}
interface Resp { items: Item[]; counts: { expired: number; soon: number; ok: number } }

const dot = { expired: '#DC2626', soon: '#D97706', ok: '#16A34A' } as Record<string, string>

function Row({ r }: { r: Item }) {
  const t = useT()
  const dueText = r.days_left < 0 ? t('{n}d overdue', { n: Math.abs(r.days_left) }) : r.days_left === 0 ? t('Due today') : t('{n}d remaining', { n: r.days_left })
  const badge = r.status === 'expired' ? 'b-red' : r.status === 'soon' ? 'b-amber' : 'b-green'
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 12, padding: '12px 14px', background: 'var(--card)', border: '1px solid var(--border-l)', borderRadius: 'var(--rl)', marginBottom: 8 }} className="fi">
      <div style={{ width: 8, height: 8, borderRadius: '50%', background: dot[r.status], flexShrink: 0 }} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ fontSize: 13, fontWeight: 500 }}>{r.ev_title}</div>
        <div style={{ fontSize: 10, color: 'var(--text3)' }}>{r.ctrl_ref} · {r.ctrl_name} · {r.freq} · 👤 {r.owner}</div>
      </div>
      <span className={`badge ${badge}`}>{dueText}</span>
      <button className="ev-action-btn download">{t('📤 Renew')}</button>
    </div>
  )
}

export default function RenewalsPage() {
  const t = useT()
  const { data, isLoading, isError } = useQuery<Resp>({
    queryKey: ['renewals'],
    queryFn: async () => (await api.get('/evidence/renewals')).data,
  })
  if (isLoading) return <div className="page-sub">{t('Loading renewals…')}</div>
  if (isError || !data) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Failed to load renewals.')}</div>

  const expired = data.items.filter(i => i.status === 'expired')
  const soon = data.items.filter(i => i.status === 'soon')
  const ok = data.items.filter(i => i.status === 'ok')

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Renewals')}</div>
          <div className="page-sub">{t('Periodic evidence that needs renewal - keep your audit package current.')}</div>
        </div>
      </div>

      <div className="stat-grid fi" style={{ gridTemplateColumns: 'repeat(3,1fr)' }}>
        <div className="stat-card red"><div className="stat-lbl">{t('⛔ Expired - renew now')}</div><div className="stat-val red">{data.counts.expired}</div></div>
        <div className="stat-card amber"><div className="stat-lbl">{t('⚠️ Expiring within 30 days')}</div><div className="stat-val amber">{data.counts.soon}</div></div>
        <div className="stat-card green"><div className="stat-lbl">{t('✅ Up to date')}</div><div className="stat-val green">{data.counts.ok}</div></div>
      </div>

      {data.items.length === 0 && <div className="queue-empty"><div className="queue-empty-icon">📭</div><div className="page-sub">{t('No periodic evidence yet - uploads with a recurring frequency appear here.')}</div></div>}
      {expired.length > 0 && <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--red)', margin: '4px 0 8px' }} className="fi">{t('⛔ Expired - immediate action required')}</div>}
      {expired.map(r => <Row key={r.id} r={r} />)}
      {soon.length > 0 && <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--amber)', margin: '14px 0 8px' }} className="fi">{t('⚠️ Expiring soon')}</div>}
      {soon.map(r => <Row key={r.id} r={r} />)}
      {ok.length > 0 && <div style={{ fontSize: 12, fontWeight: 600, color: 'var(--green)', margin: '14px 0 8px' }} className="fi">{t('✅ Up to date')}</div>}
      {ok.map(r => <Row key={r.id} r={r} />)}
    </>
  )
}
