import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { LOGO_LG } from '../assets/logo'
import { useT } from '../lib/i18n'
import { AgreementView } from '../components/AgreementGate'

interface Plan { key: string; name: string; price: number; tenant_type: string; frameworks: string | string[] }
interface Fw { id: string; name: string; version: string; controls: number }

const inputStyle: React.CSSProperties = {
  width: '100%', borderRadius: 8, padding: '9px 12px', fontSize: 13, outline: 'none',
  background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.09)', color: '#E2E8F0', marginBottom: 10,
}
const label = { fontSize: 11, fontWeight: 600, color: '#7094B8', marginBottom: 4, display: 'block' } as React.CSSProperties
const primaryBtn = { background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)' } as React.CSSProperties

export default function SignupPage() {
  const navigate = useNavigate()
  const t = useT()
  const setSession = useAuthStore(s => s.setSession)
  const qc = useQueryClient()
  const [showAgree, setShowAgree] = useState(false)
  const proceedRef = useRef<() => void>(() => {})
  const [step, setStep] = useState(1)
  const [org, setOrg] = useState(''); const [name, setName] = useState('')
  const [email, setEmail] = useState(''); const [password, setPassword] = useState('')
  const [plan, setPlan] = useState('')
  const [fwIds, setFwIds] = useState<string[]>([])
  const [opts, setOpts] = useState<{ plans: Plan[]; frameworks: Fw[]; stripe_enabled: boolean; billing_mode: string; trial_days: number } | null>(null)
  const [loading, setLoading] = useState(false)
  // verification
  const [vToken, setVToken] = useState(''); const [devCode, setDevCode] = useState<string | null>(null)
  const [code, setCode] = useState('')
  // Self-contained CAPTCHA (arithmetic challenge) to block bots at signup.
  const [capQ, setCapQ] = useState(''); const [capToken, setCapToken] = useState(''); const [capAns, setCapAns] = useState('')
  // promo code → per-signup billing behavior
  const [promo, setPromo] = useState('')
  const [promoInfo, setPromoInfo] = useState<{ valid: boolean; billing_mode?: string; hint?: string } | null>(null)

  const checkPromo = async () => {
    const c = promo.trim()
    if (!c) { setPromoInfo(null); return }
    try { setPromoInfo((await api.get(`/auth/promo/${encodeURIComponent(c)}`)).data) }
    catch { setPromoInfo({ valid: false }) }
  }

  const loadCaptcha = () => api.get('/auth/captcha').then(r => { setCapQ(r.data.question); setCapToken(r.data.captcha_token); setCapAns('') }).catch(() => {})

  useEffect(() => {
    api.get('/auth/signup-options').then(r => { setOpts(r.data); if (r.data.plans?.[0]) setPlan(r.data.plans.find((p: Plan) => p.tenant_type === 'single_client')?.key || r.data.plans[0].key) }).catch(() => {})
    loadCaptcha()
  }, [])

  const toggleFw = (id: string) => setFwIds(s => s.includes(id) ? s.filter(x => x !== id) : [...s, id])
  const selectedPlan = opts?.plans.find(p => p.key === plan)
  const allowedFw = !selectedPlan || selectedPlan.frameworks === 'all'
    ? (opts?.frameworks || [])
    : (opts?.frameworks || []).filter(f => (selectedPlan.frameworks as string[]).includes(f.id))

  const requestCode = async () => {
    setLoading(true)
    try {
      const { data } = await api.post('/auth/request-verification', { email })
      setVToken(data.verification_token); setDevCode(data.dev_code || null); setStep(2)
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Could not send code')) }
    finally { setLoading(false) }
  }

  const submit = async () => {
    setLoading(true)
    try {
      const { data } = await api.post('/auth/register', {
        email, password, display_name: name, org_name: org,
        tenant_type: 'single_client', plan, framework_ids: fwIds.filter(id => allowedFw.some(f => f.id === id)),
        verification_token: vToken, code, promo_code: promo.trim() || undefined,
        captcha_token: capToken, captcha_answer: capAns,
      })
      // MSP/Reseller accounts are created pending and can't sign in until EVA authorizes them.
      if (data.pending) {
        toast.success(t('Account created — awaiting EVA authorization. You’ll be notified once approved.'))
        navigate('/login')
        return
      }
      setSession(data.access_token, data.user)
      // What happens once the agreement is accepted (checkout or straight into the app).
      const proceed = async () => {
        // A valid promo code sets the billing mode; otherwise the platform default applies.
        const mode = (promoInfo?.valid && promoInfo.billing_mode) ? promoInfo.billing_mode : opts?.billing_mode
        // Card-required modes route through Stripe at signup; no-card trial goes straight in.
        const needsPay = mode === 'card_trial' || mode === 'charge_immediately'
        if (needsPay && opts?.stripe_enabled && (selectedPlan?.price || 0) > 0) {
          const co = (await api.post('/billing/checkout', {
            success_url: `${window.location.origin}/dashboard`, cancel_url: `${window.location.origin}/billing`,
          })).data
          if (co.url) { window.location.href = co.url; return }
        }
        toast.success(t('Welcome to EVA — your trial has started'))
        navigate('/dashboard')
      }
      // Require reading & accepting the agreement BEFORE entering the app.
      proceedRef.current = proceed
      await qc.invalidateQueries({ queryKey: ['agreement-me'] })
      setShowAgree(true)
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || t('Sign up failed'))
    } finally { setLoading(false) }
  }

  const step1Ok = org.trim() && name.trim() && email.trim() && password.length >= 12 && capAns.trim() && capToken

  if (showAgree) {
    return (
      <div className="modal-overlay" style={{ zIndex: 80, padding: 24 }}>
        <AgreementView onAccepted={() => proceedRef.current?.()} />
      </div>
    )
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-5" style={{ background: '#0B1629' }}>
      <div className="w-full max-w-md rounded-2xl p-7 shadow-2xl" style={{ background: '#111E35', border: '1px solid rgba(255,255,255,.07)' }}>
        <div className="text-center mb-5 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,.07)' }}>
          <img src={LOGO_LG} alt="EVA" className="mx-auto" style={{ width: 180 }} />
          <div className="text-xs mt-2" style={{ color: '#4A6A8A' }}>{t('Create your account · Step {step} of 4', { step })}</div>
        </div>

        {step === 1 && (
          <>
            <label style={label}>{t('Organization name')}</label>
            <input style={inputStyle} value={org} onChange={e => setOrg(e.target.value)} placeholder="NovLogix Inc." />
            <label style={label}>{t('Your name')}</label>
            <input style={inputStyle} value={name} onChange={e => setName(e.target.value)} placeholder="Jane Doe" />
            <label style={label}>{t('Email')}</label>
            <input style={inputStyle} type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="you@company.com" />
            <label style={label}>{t('Password (min 12 chars)')}</label>
            <input style={inputStyle} type="password" value={password} onChange={e => setPassword(e.target.value)} placeholder="••••••••" />
            <label style={label}>{t('Verification: what is {q}?', { q: capQ || '…' })}</label>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input style={{ ...inputStyle, flex: 1 }} inputMode="numeric" value={capAns}
                onChange={e => setCapAns(e.target.value.replace(/\D/g, ''))} placeholder="?" />
              <button type="button" onClick={loadCaptcha} title={t('New challenge')}
                style={{ ...inputStyle, width: 'auto', padding: '0 12px', cursor: 'pointer', color: '#4A6A8A' }}>↻</button>
            </div>
            <button className="w-full py-2.5 rounded-lg font-semibold text-white text-sm mt-1" disabled={!step1Ok || loading}
              style={{ ...primaryBtn, opacity: step1Ok && !loading ? 1 : .5 }} onClick={requestCode}>
              {loading ? t('Sending code…') : t('Continue')}
            </button>
          </>
        )}

        {step === 2 && (
          <>
            <div style={{ ...label, marginBottom: 8 }}>{t('Verify your email')}</div>
            <div className="text-xs mb-3" style={{ color: '#4A6A8A' }}>{t('We sent a 6-digit code to {email}.', { email })}</div>
            {devCode && (
              <div className="mb-3" style={{ background: 'rgba(59,188,255,.08)', border: '1px solid rgba(59,188,255,.2)', borderRadius: 8, padding: '8px 11px', fontSize: 12, color: '#7DD3FC' }}>
                {t('Dev mode (no email service): your code is')} <b style={{ fontFamily: 'monospace', letterSpacing: '.15em' }}>{devCode}</b>
              </div>
            )}
            <input style={{ ...inputStyle, fontFamily: 'monospace', letterSpacing: '.3em', textAlign: 'center', fontSize: 18 }} maxLength={6}
              value={code} onChange={e => setCode(e.target.value.replace(/\D/g, ''))} placeholder="000000" />
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="flex-1 py-2.5 rounded-lg text-sm" style={{ border: '1px solid rgba(255,255,255,.12)', color: '#7094B8' }} onClick={() => setStep(1)}>{t('← Back')}</button>
              <button className="flex-1 py-2.5 rounded-lg font-semibold text-white text-sm" disabled={code.length < 6} style={{ ...primaryBtn, opacity: code.length < 6 ? .5 : 1 }} onClick={() => setStep(3)}>{t('Verify & continue')}</button>
            </div>
          </>
        )}

        {step === 3 && (
          <>
            <div style={{ ...label, marginBottom: 8 }}>{t('Choose a plan')}</div>
            {(opts?.plans || []).map(p => (
              <div key={p.key} onClick={() => setPlan(p.key)} style={{
                padding: '12px 14px', borderRadius: 10, marginBottom: 8, cursor: 'pointer',
                border: `1px solid ${plan === p.key ? '#3BBCFF' : 'rgba(255,255,255,.09)'}`,
                background: plan === p.key ? 'rgba(59,188,255,.08)' : 'rgba(255,255,255,.03)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <span style={{ color: '#E2E8F0', fontWeight: 600, fontSize: 13 }}>{p.name}</span>
                    <span style={{ marginLeft: 8, fontSize: 9, fontWeight: 700, padding: '2px 7px', borderRadius: 10, background: p.tenant_type === 'msp' ? 'rgba(167,139,250,.15)' : 'rgba(59,188,255,.12)', color: p.tenant_type === 'msp' ? '#C4B5FD' : '#7DD3FC' }}>
                      {p.tenant_type === 'msp' ? 'MSP' : t('Single client')}
                    </span>
                  </div>
                  <span style={{ color: '#7DD3FC', fontWeight: 700 }}>${p.price}/mo</span>
                </div>
              </div>
            ))}
            <label style={{ ...label, marginTop: 6 }}>{t('Promo code (optional)')}</label>
            <input style={{ ...inputStyle, marginBottom: 4, textTransform: 'uppercase' }} value={promo}
              onChange={e => { setPromo(e.target.value); setPromoInfo(null) }} onBlur={checkPromo}
              placeholder={t('Enter a code if you have one')} />
            {promoInfo && (
              promoInfo.valid
                ? <div className="text-xs mb-2" style={{ color: '#34D399' }}>✓ {promoInfo.hint}</div>
                : <div className="text-xs mb-2" style={{ color: '#F87171' }}>{t('That code isn’t valid — you can continue without one.')}</div>
            )}
            <div className="text-xs mt-1 mb-3" style={{ color: '#4A6A8A' }}>
              {selectedPlan?.tenant_type === 'msp' ? t('MSP plans manage multiple client orgs — you’ll add clients after signup.') : opts?.stripe_enabled ? t('Next step takes you to secure Stripe checkout.') : t('Payment is simulated in this build — no card required.')}
            </div>
            <div style={{ display: 'flex', gap: 8 }}>
              <button className="flex-1 py-2.5 rounded-lg text-sm" style={{ border: '1px solid rgba(255,255,255,.12)', color: '#7094B8' }} onClick={() => setStep(2)}>{t('← Back')}</button>
              <button className="flex-1 py-2.5 rounded-lg font-semibold text-white text-sm" disabled={loading}
                style={{ ...(selectedPlan?.tenant_type === 'msp' ? { background: 'var(--green)' } : primaryBtn), opacity: loading ? .6 : 1 }}
                onClick={() => selectedPlan?.tenant_type === 'msp' ? submit() : setStep(4)}>
                {selectedPlan?.tenant_type === 'msp' ? (loading ? t('Creating…') : opts?.stripe_enabled ? t('Continue to payment') : t('Create MSP account')) : t('Continue')}
              </button>
            </div>
          </>
        )}

        {step === 4 && (
          <>
            <div style={{ ...label, marginBottom: 8 }}>{t('Frameworks to start with')}</div>
            <div className="text-xs mb-2" style={{ color: '#4A6A8A' }}>{t('Included in {plan}:', { plan: selectedPlan?.name || '' })}</div>
            {allowedFw.map(f => (
              <div key={f.id} onClick={() => toggleFw(f.id)} style={{
                padding: '10px 12px', borderRadius: 10, marginBottom: 8, cursor: 'pointer',
                border: `1px solid ${fwIds.includes(f.id) ? '#3BBCFF' : 'rgba(255,255,255,.09)'}`,
                background: fwIds.includes(f.id) ? 'rgba(59,188,255,.08)' : 'rgba(255,255,255,.03)',
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ color: '#E2E8F0', fontWeight: 600, fontSize: 13 }}>{f.name} <span style={{ color: '#4A6A8A', fontWeight: 400 }}>v{f.version}</span></div>
                    <div style={{ color: '#4A6A8A', fontSize: 11 }}>{t('{n} controls', { n: f.controls })}</div>
                  </div>
                  <span style={{ color: fwIds.includes(f.id) ? '#7DD3FC' : '#2E4A6B', fontSize: 18 }}>{fwIds.includes(f.id) ? '☑' : '☐'}</span>
                </div>
              </div>
            ))}
            <div style={{ display: 'flex', gap: 8, marginTop: 4 }}>
              <button className="flex-1 py-2.5 rounded-lg text-sm" style={{ border: '1px solid rgba(255,255,255,.12)', color: '#7094B8' }} onClick={() => setStep(3)}>{t('← Back')}</button>
              <button className="flex-1 py-2.5 rounded-lg font-semibold text-white text-sm" disabled={loading}
                style={{ background: 'var(--green)', opacity: loading ? .6 : 1 }} onClick={submit}>
                {loading ? t('Creating…') : opts?.stripe_enabled ? t('Continue to payment') : t('Create account')}
              </button>
            </div>
          </>
        )}

        <div className="text-xs text-center mt-5" style={{ color: '#3A5570' }}>
          {t('Already have an account?')} <span style={{ color: '#7DD3FC', cursor: 'pointer' }} onClick={() => navigate('/login')}>{t('Sign in')}</span>
        </div>
      </div>
    </div>
  )
}
