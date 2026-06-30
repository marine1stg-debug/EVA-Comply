import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Activity, Mail, HardDrive, CreditCard, Shield, SlidersHorizontal, Check, X as XIcon, AlertTriangle } from 'lucide-react'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import EmailSettingsPage from './EmailSettings'

interface Chk { ok: boolean; label: string; detail: string; required: boolean }
interface Readiness {
  environment: string; production: boolean
  required_done: number; required_total: number; all_required_ok: boolean
  checklist: Chk[]; notes: string[]
}

type TabKey = 'readiness' | 'general' | 'email' | 'storage' | 'payments' | 'security'

export default function SystemSettingsPage() {
  const t = useT()
  const [tab, setTab] = useState<TabKey>('readiness')

  const tabs: { key: TabKey; label: string; icon: any }[] = [
    { key: 'readiness', label: t('Readiness'), icon: Activity },
    { key: 'general', label: t('General'), icon: SlidersHorizontal },
    { key: 'email', label: t('Email (SMTP)'), icon: Mail },
    { key: 'storage', label: t('Storage'), icon: HardDrive },
    { key: 'payments', label: t('Payments'), icon: CreditCard },
    { key: 'security', label: t('Security'), icon: Shield },
  ]

  return (
    <div>
      <div className="page-title">{t('System Settings')}</div>
      <div className="page-sub" style={{ marginBottom: 14 }}>{t('Configure the deployment and check that it is production-ready. Super Admin only.')}</div>

      <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 16, borderBottom: '1px solid var(--border-l)', paddingBottom: 10 }}>
        {tabs.map(({ key, label, icon: I }) => (
          <button key={key} onClick={() => setTab(key)}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 12.5, fontWeight: 600, padding: '7px 12px', borderRadius: 8, cursor: 'pointer',
              border: '1px solid ' + (tab === key ? 'var(--sky, #1A8FD1)' : 'var(--border-l)'),
              background: tab === key ? 'var(--sky, #1A8FD1)' : 'var(--card)', color: tab === key ? '#fff' : 'var(--text2)' }}>
            <I size={14} aria-hidden /> {label}
          </button>
        ))}
      </div>

      {tab === 'readiness' && <ReadinessTab />}
      {tab === 'email' && <EmailSettingsPage />}
      {tab === 'general' && <InfoTab title={t('General')} why={t('Site URL, app name, support email, and the per-type sender addresses (noreply / cases / invoicing). The Site URL is used to build invite and reset links, so it must match your real domain.')}
        env={['FRONTEND_URL', 'EMAIL_FROM_NOREPLY', 'EMAIL_FROM_CASES', 'EMAIL_FROM_INVOICING']} />}
      {tab === 'storage' && <InfoTab title={t('Storage')}
        why={t('Where uploaded evidence and policy files are stored. The default "local" keeps files in a container volume - it works, but it is NOT durable: a bad rebuild or moving servers can lose them. Recommended (not required): point this at Cloudflare R2 or S3 so evidence is stored off-box and survives anything that happens to the server.')}
        env={['STORAGE_BACKEND', 'R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET_NAME']} />}
      {tab === 'payments' && <InfoTab title={t('Payments')} why={t('Stripe keys for paid subscriptions. Only needed if you charge customers for plans. Without them, plan checkout is simply disabled and everything else works.')}
        env={['STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET']} />}
      {tab === 'security' && <InfoTab title={t('Security')} why={t('Session length, minimum password length, and whether MFA is required. Sensible defaults are already in place (8-hour sessions, 12-character minimum). These will become editable here in the next update.')}
        env={['ACCESS_TOKEN_EXPIRE_MINUTES', 'REFRESH_TOKEN_EXPIRE_DAYS']} />}
    </div>
  )
}

function ReadinessTab() {
  const t = useT()
  const { data, isLoading, isError } = useQuery<Readiness>({
    queryKey: ['system-readiness'],
    queryFn: async () => (await api.get('/system/readiness')).data,
  })
  if (isLoading) return <div className="page-sub">{t('Loading…')}</div>
  if (isError || !data) return <div className="page-sub" style={{ color: 'var(--red)' }}>{t('Could not load readiness.')}</div>

  return (
    <div style={{ maxWidth: 720 }}>
      <div className="card" style={{ padding: 16, marginBottom: 14, display: 'flex', alignItems: 'center', gap: 14 }}>
        <div style={{ fontSize: 30 }}>{data.all_required_ok ? '✅' : '⚠️'}</div>
        <div>
          <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>
            {data.all_required_ok ? t('Production-ready') : t('Setup incomplete')}
          </div>
          <div className="page-sub" style={{ fontSize: 12 }}>
            {t('{a} of {b} required items done', { a: data.required_done, b: data.required_total })} · {t('Environment')}: <b>{data.environment}</b>
          </div>
        </div>
      </div>

      <div style={{ fontSize: 12, fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '.04em', margin: '4px 0 8px' }}>
        {t('.env requirements')}
      </div>
      <div style={{ display: 'grid', gap: 8 }}>
        {data.checklist.map((c, i) => (
          <div key={i} className="card" style={{ padding: '10px 12px', display: 'flex', alignItems: 'flex-start', gap: 10 }}>
            <span style={{ flexShrink: 0, width: 22, height: 22, borderRadius: '50%', display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
              background: c.ok ? 'rgba(22,163,74,.14)' : c.required ? 'rgba(220,38,38,.12)' : 'rgba(217,119,6,.14)',
              color: c.ok ? 'var(--green, #16A34A)' : c.required ? 'var(--red, #DC2626)' : 'var(--amber, #D97706)' }}>
              {c.ok ? <Check size={13} /> : c.required ? <XIcon size={13} /> : <AlertTriangle size={12} />}
            </span>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)' }}>
                {c.label} {!c.required && <span style={{ fontSize: 10, color: 'var(--text3)', fontWeight: 500 }}>· {t('recommended')}</span>}
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text2)', marginTop: 2 }}>{c.detail}</div>
            </div>
          </div>
        ))}
      </div>

      {data.notes?.length > 0 && (
        <div className="card" style={{ padding: 12, marginTop: 14, fontSize: 11.5, color: 'var(--text2)', lineHeight: 1.6, background: 'var(--soft)' }}>
          {data.notes.map((n, i) => <div key={i}>• {n}</div>)}
        </div>
      )}
    </div>
  )
}

function InfoTab({ title, why, env }: { title: string; why: string; env: string[] }) {
  const t = useT()
  return (
    <div style={{ maxWidth: 640 }}>
      <div className="card" style={{ padding: 16, marginBottom: 12 }}>
        <div style={{ fontSize: 14, fontWeight: 700, color: 'var(--text)', marginBottom: 6 }}>{title}</div>
        <div style={{ fontSize: 13, color: 'var(--text2)', lineHeight: 1.6 }}>{why}</div>
      </div>
      <div className="card" style={{ padding: 14, borderLeft: '3px solid var(--sky, #1A8FD1)' }}>
        <div style={{ fontSize: 11, fontWeight: 700, color: 'var(--text3)', textTransform: 'uppercase', letterSpacing: '.04em', marginBottom: 6 }}>
          {t('Set in the server .env for now')}
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
          {env.map(e => <code key={e} style={{ fontSize: 11.5, background: 'var(--card2, #0d1626)', border: '1px solid var(--border-l)', borderRadius: 6, padding: '2px 7px', color: 'var(--text)' }}>{e}</code>)}
        </div>
        <div style={{ fontSize: 11.5, color: 'var(--text3)', marginTop: 10 }}>{t('Editable in-app in an upcoming update.')}</div>
      </div>
    </div>
  )
}
