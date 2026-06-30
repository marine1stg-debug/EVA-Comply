import { useState, useEffect } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Activity, Mail, HardDrive, CreditCard, Shield, SlidersHorizontal, Check, X as XIcon, AlertTriangle, Save, Send } from 'lucide-react'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import EmailSettingsPage from './EmailSettings'

const KEEP = '__KEEP__'
const fieldS: React.CSSProperties = { width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border-l)', background: 'var(--card)', color: 'var(--text)', fontSize: 13 }
const labelS: React.CSSProperties = { fontSize: 11, color: 'var(--text3)', marginBottom: 4, display: 'block' }
const whyBox = (txt: string) => (
  <div className="card" style={{ padding: 12, marginBottom: 12, fontSize: 12.5, color: 'var(--text2)', lineHeight: 1.6, borderLeft: '3px solid var(--sky, #1A8FD1)' }}>{txt}</div>
)

// Readiness rows are sent from the backend as stable keys + values; we render
// the label/detail here so the whole panel is bilingual.
type TFn = (k: string, p?: Record<string, any>) => string
function readyLabel(c: { key: string }, t: TFn): string {
  switch (c.key) {
    case 'env_production': return t('Set ENVIRONMENT to production')
    case 'secret_key': return t('Strong SECRET_KEY (32+ characters)')
    case 'db_password': return t('Database password changed from the default')
    case 'email': return t('Email backend configured (not console)')
    case 'frontend_url': return t('Site URL set to your real HTTPS domain')
    case 'storage': return t('Durable object storage (R2/S3) for evidence')
    case 'stripe': return t('Stripe keys set (only if you charge for plans)')
    default: return c.key
  }
}
function readyDetail(c: { key: string; ok: boolean; meta: Record<string, any> }, t: TFn): string {
  const m = c.meta || {}
  switch (c.key) {
    case 'env_production': return c.ok ? t('Production mode is on.') : t('Currently “{env}”. Set to production before go-live.', { env: m.env })
    case 'secret_key': return c.ok ? t('Strong key in place.') : t('Generate one with: openssl rand -hex 32')
    case 'db_password': return c.ok ? t('Custom database password.') : t('Still using a default or sample password.')
    case 'email': return m.mode === 'inapp' ? t('Configured in-app.') : m.mode === 'env' ? t('Using the server .env backend: {b}', { b: m.backend }) : t('Not configured (console only - links would leak).')
    case 'frontend_url': return m.url ? t('Current: {url}', { url: m.url }) : t('Not set.')
    case 'storage': return c.ok ? t('Durable storage in use ({b}).', { b: m.backend }) : t('Backend: {b}. Local works but is not durable across rebuilds.', { b: m.backend })
    case 'stripe': return c.ok ? t('Stripe enabled.') : t('Not set (billing checkout disabled).')
    default: return ''
  }
}
function noteText(n: string, t: TFn): string {
  if (n === 'basic_auth') return t('The site password gate (BASIC_AUTH_USER / BASIC_AUTH_PASSWORD) is enforced by nginx and set in the server .env.')
  if (n === 'caddy_https') return t('HTTPS and your domain are managed by Caddy (caddy/Caddyfile).')
  return n
}

interface Chk { ok: boolean; key: string; required: boolean; meta: Record<string, any> }
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
      {tab === 'general' && <GeneralForm />}
      {tab === 'storage' && <StorageForm />}
      {tab === 'payments' && <PaymentsForm />}
      {tab === 'security' && <SecurityForm />}
    </div>
  )
}

// Shared loader for all config forms (React Query dedupes the GET).
function usePlatform() {
  const qc = useQueryClient()
  const q = useQuery<any>({ queryKey: ['platform-settings'], queryFn: async () => (await api.get('/platform-settings/')).data })
  const refresh = () => qc.invalidateQueries({ queryKey: ['platform-settings'] })
  return { data: q.data, isLoading: q.isLoading, refresh }
}

function SaveBtn({ pending, onClick }: { pending: boolean; onClick: () => void }) {
  const t = useT()
  return <button className="submit-btn" disabled={pending} onClick={onClick} style={{ justifyContent: 'center' }}><Save size={14} aria-hidden /> {pending ? t('Saving…') : t('Save')}</button>
}

function TestResult({ r }: { r: { ok: boolean; detail: string } | null }) {
  if (!r) return null
  return <div style={{ fontSize: 12.5, padding: '10px 12px', borderRadius: 8, marginTop: 8, background: r.ok ? 'rgba(22,163,74,.1)' : 'rgba(220,38,38,.1)', color: r.ok ? 'var(--green, #16A34A)' : 'var(--red, #DC2626)' }}>{r.ok ? '✓ ' : '✕ '}{r.detail}</div>
}

function GeneralForm() {
  const t = useT()
  const { data, isLoading, refresh } = usePlatform()
  const [g, setG] = useState<any>(null)
  useEffect(() => { if (data) setG({ ...data.general }) }, [data])
  const save = useMutation({
    mutationFn: async () => (await api.put('/platform-settings/general', g)).data,
    onSuccess: () => { refresh(); toast.success(t('Saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  if (isLoading || !g) return <div className="page-sub">{t('Loading…')}</div>
  const up = (k: string, v: string) => setG((p: any) => ({ ...p, [k]: v }))
  const F = (k: string, label: string, ph = '') => (
    <div><label style={labelS}>{label}</label><input value={g[k] || ''} onChange={e => up(k, e.target.value)} placeholder={ph} style={fieldS} /></div>
  )
  return (
    <div style={{ maxWidth: 600 }}>
      {whyBox(t('Site URL, app name, support email, and per-type sender addresses. The Site URL builds invite and reset links, so it must match your real domain. Blank fields fall back to the server .env ({u}).', { u: data.env.site_url || 'unset' }))}
      <div className="card" style={{ padding: 18, display: 'grid', gap: 12 }}>
        {F('site_url', t('Site URL'), 'https://compliance.yourdomain.com')}
        {F('app_name', t('App name'), 'EVA Comply')}
        {F('support_email', t('Support email'), 'support@yourdomain.com')}
        {F('from_noreply', t('Sender · noreply'), 'noreply@yourdomain.com')}
        {F('from_cases', t('Sender · support cases'), 'support@yourdomain.com')}
        {F('from_invoicing', t('Sender · invoicing'), 'billing@yourdomain.com')}
        <div><SaveBtn pending={save.isPending} onClick={() => save.mutate()} /></div>
      </div>
    </div>
  )
}

function StorageForm() {
  const t = useT()
  const { data, isLoading, refresh } = usePlatform()
  const [s, setS] = useState<any>(null)
  const [secret, setSecret] = useState('')
  const [res, setRes] = useState<{ ok: boolean; detail: string } | null>(null)
  useEffect(() => { if (data) setS({ ...data.storage }) }, [data])
  const save = useMutation({
    mutationFn: async () => (await api.put('/platform-settings/storage', { ...s, r2_secret_access_key: secret ? secret : KEEP })).data,
    onSuccess: () => { refresh(); setSecret(''); toast.success(t('Saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const test = useMutation({
    mutationFn: async () => (await api.post('/platform-settings/storage/test', {})).data,
    onMutate: () => setRes(null), onSuccess: (r) => setRes(r),
    onError: (e: any) => setRes({ ok: false, detail: e?.response?.data?.detail || 'Error' }),
  })
  if (isLoading || !s) return <div className="page-sub">{t('Loading…')}</div>
  const up = (k: string, v: string) => setS((p: any) => ({ ...p, [k]: v }))
  const isR2 = (s.backend || data.env.storage_backend) === 'r2' || (s.backend || data.env.storage_backend) === 's3'
  return (
    <div style={{ maxWidth: 600 }}>
      {whyBox(t('Where uploaded evidence and policy files are stored. The default "local" keeps files in a container volume - it works, but it is NOT durable: a bad rebuild or moving servers can lose them. Recommended (not required): use Cloudflare R2 or S3 so evidence survives anything that happens to the server.'))}
      <div className="card" style={{ padding: 18, display: 'grid', gap: 12 }}>
        <div>
          <label style={labelS}>{t('Backend')}</label>
          <select value={s.backend || ''} onChange={e => up('backend', e.target.value)} style={fieldS}>
            <option value="">{t('Use server default')} ({data.env.storage_backend})</option>
            <option value="local">{t('Local disk (not durable)')}</option>
            <option value="r2">Cloudflare R2</option>
            <option value="s3">Amazon S3</option>
          </select>
        </div>
        {isR2 && <>
          <div><label style={labelS}>{t('R2 account ID')} <span style={{ color: 'var(--text3)' }}>({t('R2 only')})</span></label><input value={s.r2_account_id || ''} onChange={e => up('r2_account_id', e.target.value)} style={fieldS} /></div>
          <div><label style={labelS}>{t('Access key ID')}</label><input value={s.r2_access_key_id || ''} onChange={e => up('r2_access_key_id', e.target.value)} style={fieldS} /></div>
          <div><label style={labelS}>{t('Secret access key')} {s.has_secret && <span style={{ color: 'var(--green, #16A34A)' }}>· {t('set')}</span>}</label><input type="password" value={secret} onChange={e => setSecret(e.target.value)} placeholder={s.has_secret ? t('Leave blank to keep current') : '••••••••'} style={fieldS} /></div>
          <div><label style={labelS}>{t('Bucket')}</label><input value={s.r2_bucket || ''} onChange={e => up('r2_bucket', e.target.value)} placeholder="eva-uploads" style={fieldS} /></div>
        </>}
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <SaveBtn pending={save.isPending} onClick={() => save.mutate()} />
          <button className="tb-btn" disabled={test.isPending} onClick={() => test.mutate()}><Send size={13} aria-hidden /> {test.isPending ? t('Testing…') : t('Test storage')}</button>
        </div>
        <TestResult r={res} />
      </div>
    </div>
  )
}

function PaymentsForm() {
  const t = useT()
  const { data, isLoading, refresh } = usePlatform()
  const [sk, setSk] = useState('')
  const [wh, setWh] = useState('')
  const [res, setRes] = useState<{ ok: boolean; detail: string } | null>(null)
  const save = useMutation({
    mutationFn: async () => (await api.put('/platform-settings/payments', { stripe_secret_key: sk ? sk : KEEP, stripe_webhook_secret: wh ? wh : KEEP })).data,
    onSuccess: () => { refresh(); setSk(''); setWh(''); toast.success(t('Saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const test = useMutation({
    mutationFn: async () => (await api.post('/platform-settings/payments/test', {})).data,
    onMutate: () => setRes(null), onSuccess: (r) => setRes(r),
    onError: (e: any) => setRes({ ok: false, detail: e?.response?.data?.detail || 'Error' }),
  })
  if (isLoading || !data) return <div className="page-sub">{t('Loading…')}</div>
  return (
    <div style={{ maxWidth: 600 }}>
      {whyBox(t('Stripe keys for paid subscriptions. Only needed if you charge for plans. Without them, plan checkout is disabled and everything else works.'))}
      <div className="card" style={{ padding: 18, display: 'grid', gap: 12 }}>
        <div><label style={labelS}>{t('Stripe secret key')} {data.payments.has_secret_key && <span style={{ color: 'var(--green, #16A34A)' }}>· {t('set')}</span>}</label><input type="password" value={sk} onChange={e => setSk(e.target.value)} placeholder={data.payments.has_secret_key ? t('Leave blank to keep current') : 'sk_live_…'} style={fieldS} /></div>
        <div><label style={labelS}>{t('Stripe webhook secret')} {data.payments.has_webhook_secret && <span style={{ color: 'var(--green, #16A34A)' }}>· {t('set')}</span>}</label><input type="password" value={wh} onChange={e => setWh(e.target.value)} placeholder={data.payments.has_webhook_secret ? t('Leave blank to keep current') : 'whsec_…'} style={fieldS} /></div>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <SaveBtn pending={save.isPending} onClick={() => save.mutate()} />
          <button className="tb-btn" disabled={test.isPending} onClick={() => test.mutate()}><Send size={13} aria-hidden /> {test.isPending ? t('Testing…') : t('Test Stripe')}</button>
        </div>
        <TestResult r={res} />
      </div>
    </div>
  )
}

function SecurityForm() {
  const t = useT()
  const { data, isLoading, refresh } = usePlatform()
  const [sec, setSec] = useState<any>(null)
  useEffect(() => { if (data) setSec({ ...data.security }) }, [data])
  const save = useMutation({
    mutationFn: async () => (await api.put('/platform-settings/security', {
      session_minutes: sec.session_minutes ? Number(sec.session_minutes) : null,
      min_password_length: sec.min_password_length ? Number(sec.min_password_length) : null,
    })).data,
    onSuccess: () => { refresh(); toast.success(t('Saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  if (isLoading || !sec) return <div className="page-sub">{t('Loading…')}</div>
  return (
    <div style={{ maxWidth: 600 }}>
      {whyBox(t('Session length and minimum password length. Leave a field blank to use the server default ({m} min session, {p}-character minimum).', { m: data.env.session_minutes, p: data.env.min_password_length }))}
      <div className="card" style={{ padding: 18, display: 'grid', gap: 12 }}>
        <div><label style={labelS}>{t('Session length (minutes)')}</label><input type="number" value={sec.session_minutes ?? ''} onChange={e => setSec((p: any) => ({ ...p, session_minutes: e.target.value }))} placeholder={String(data.env.session_minutes)} style={fieldS} /></div>
        <div><label style={labelS}>{t('Minimum password length')}</label><input type="number" value={sec.min_password_length ?? ''} onChange={e => setSec((p: any) => ({ ...p, min_password_length: e.target.value }))} placeholder={String(data.env.min_password_length)} style={fieldS} /></div>
        <div><SaveBtn pending={save.isPending} onClick={() => save.mutate()} /></div>
      </div>
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
                {readyLabel(c, t)} {!c.required && <span style={{ fontSize: 10, color: 'var(--text3)', fontWeight: 500 }}>· {t('recommended')}</span>}
              </div>
              <div style={{ fontSize: 11.5, color: 'var(--text2)', marginTop: 2 }}>{readyDetail(c, t)}</div>
            </div>
          </div>
        ))}
      </div>

      {data.notes?.length > 0 && (
        <div className="card" style={{ padding: 12, marginTop: 14, fontSize: 11.5, color: 'var(--text2)', lineHeight: 1.6, background: 'var(--soft)' }}>
          {data.notes.map((n, i) => <div key={i}>• {noteText(n, t)}</div>)}
        </div>
      )}
    </div>
  )
}

