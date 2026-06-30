import { useState, useEffect } from 'react'
import { useQuery, useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { Mail, Send, Save } from 'lucide-react'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Settings {
  configured: boolean; backend: string; from_email: string
  smtp_host: string; smtp_port: number; smtp_user: string; smtp_tls: boolean
  has_password: boolean; has_sendgrid_key: boolean
  env_backend: string; env_from: string
}
const KEEP = '__KEEP__'

export default function EmailSettingsPage() {
  const t = useT()
  const [f, setF] = useState<Settings | null>(null)
  const [pw, setPw] = useState('')          // typed SMTP password (blank = keep)
  const [sgk, setSgk] = useState('')        // typed SendGrid key (blank = keep)
  const [testResult, setTestResult] = useState<{ ok: boolean; detail: string } | null>(null)

  const { data, isError, error } = useQuery<Settings>({
    queryKey: ['email-settings'],
    queryFn: async () => (await api.get('/email-settings/')).data,
  })
  useEffect(() => { if (data) setF(data) }, [data])

  const save = useMutation({
    mutationFn: async () => {
      const body = {
        backend: f!.backend, from_email: f!.from_email, smtp_host: f!.smtp_host,
        smtp_port: f!.smtp_port, smtp_user: f!.smtp_user, smtp_tls: f!.smtp_tls,
        smtp_password: pw ? pw : KEEP,
        sendgrid_api_key: sgk ? sgk : KEEP,
      }
      return (await api.put('/email-settings/', body)).data as Settings
    },
    onSuccess: (d) => { setF(d); setPw(''); setSgk(''); toast.success(t('Email settings saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })

  const test = useMutation({
    mutationFn: async () => (await api.post('/email-settings/test', {})).data as { ok: boolean; detail: string; to: string },
    onMutate: () => setTestResult(null),
    onSuccess: (r) => { setTestResult({ ok: r.ok, detail: r.detail }); r.ok ? toast.success(t('Test email sent')) : toast.error(t('Test failed')) },
    onError: (e: any) => setTestResult({ ok: false, detail: e?.response?.data?.detail || 'Error' }),
  })

  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: 'var(--red)' }}>{s === 403 ? t('Super Admin access required.') : t('Failed to load email settings.')}</div>
  }
  if (!f) return <div className="page-sub">{t('Loading…')}</div>

  const up = (patch: Partial<Settings>) => setF(prev => ({ ...(prev as Settings), ...patch }))
  const input: React.CSSProperties = { width: '100%', padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border-l)', background: 'var(--card)', color: 'var(--text)', fontSize: 13 }
  const label: React.CSSProperties = { fontSize: 11, color: 'var(--text3)', marginBottom: 4, display: 'block' }

  return (
    <div style={{ maxWidth: 640 }}>
      <div className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Mail size={18} aria-hidden /> {t('Email (SMTP)')}</div>
      <div className="page-sub" style={{ marginBottom: 14 }}>
        {t('Configure how the app sends invites, verification, and notifications. Overrides the server defaults when saved.')}
      </div>

      {!f.configured && (
        <div className="card" style={{ padding: 12, marginBottom: 14, fontSize: 12, color: 'var(--text2)', borderLeft: '3px solid var(--sky, #1A8FD1)' }}>
          {t('Not configured in-app yet - the app is using the server settings (backend: {b}, from: {e}).', { b: f.env_backend, e: f.env_from })}
        </div>
      )}

      <div className="card" style={{ padding: 18, display: 'grid', gap: 12 }}>
        <div>
          <label style={label}>{t('Provider')}</label>
          <select value={f.backend} onChange={e => up({ backend: e.target.value })} style={input}>
            <option value="smtp">{t('SMTP server')}</option>
            <option value="sendgrid">{t('SendGrid (API)')}</option>
            <option value="console">{t('Console (no real email - logs only)')}</option>
          </select>
        </div>

        <div>
          <label style={label}>{t('From address')}</label>
          <input value={f.from_email} onChange={e => up({ from_email: e.target.value })} placeholder="noreply@yourdomain.com" style={input} />
        </div>

        {f.backend === 'smtp' && <>
          <div style={{ display: 'flex', gap: 10 }}>
            <div style={{ flex: 2 }}>
              <label style={label}>{t('SMTP host')}</label>
              <input value={f.smtp_host} onChange={e => up({ smtp_host: e.target.value })} placeholder="smtp.ionos.com" style={input} />
            </div>
            <div style={{ flex: 1 }}>
              <label style={label}>{t('Port')}</label>
              <input type="number" value={f.smtp_port} onChange={e => up({ smtp_port: Number(e.target.value) })} placeholder="587" style={input} />
            </div>
          </div>
          <div>
            <label style={label}>{t('Username')}</label>
            <input value={f.smtp_user} onChange={e => up({ smtp_user: e.target.value })} placeholder="noreply@yourdomain.com" style={input} />
          </div>
          <div>
            <label style={label}>{t('Password')} {f.has_password && <span style={{ color: 'var(--green, #16A34A)' }}>· {t('set')}</span>}</label>
            <input type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder={f.has_password ? t('Leave blank to keep current') : '••••••••'} style={input} />
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, color: 'var(--text2)' }}>
            <input type="checkbox" checked={f.smtp_tls} onChange={e => up({ smtp_tls: e.target.checked })} />
            {t('Use STARTTLS (recommended, port 587)')}
          </label>
        </>}

        {f.backend === 'sendgrid' && (
          <div>
            <label style={label}>{t('SendGrid API key')} {f.has_sendgrid_key && <span style={{ color: 'var(--green, #16A34A)' }}>· {t('set')}</span>}</label>
            <input type="password" value={sgk} onChange={e => setSgk(e.target.value)} placeholder={f.has_sendgrid_key ? t('Leave blank to keep current') : 'SG.xxxx'} style={input} />
          </div>
        )}

        <div style={{ display: 'flex', gap: 8, marginTop: 4, flexWrap: 'wrap' }}>
          <button className="submit-btn" disabled={save.isPending} onClick={() => save.mutate()} style={{ justifyContent: 'center' }}>
            <Save size={14} aria-hidden /> {save.isPending ? t('Saving…') : t('Save')}
          </button>
          <button className="tb-btn" disabled={test.isPending} onClick={() => test.mutate()}>
            <Send size={13} aria-hidden /> {test.isPending ? t('Sending…') : t('Send test email')}
          </button>
        </div>

        {testResult && (
          <div style={{ fontSize: 12.5, padding: '10px 12px', borderRadius: 8, background: testResult.ok ? 'rgba(22,163,74,.1)' : 'rgba(220,38,38,.1)', color: testResult.ok ? 'var(--green, #16A34A)' : 'var(--red, #DC2626)' }}>
            {testResult.ok ? '✓ ' : '✕ '}{testResult.detail}
          </div>
        )}
      </div>

      <div className="page-sub" style={{ fontSize: 11, marginTop: 12, lineHeight: 1.6 }}>
        {t('Tip: most providers (IONOS, Microsoft 365, Google) use STARTTLS on port 587, and require the From address to match the username you authenticate with. The test email is sent to your own address.')}
      </div>
    </div>
  )
}
