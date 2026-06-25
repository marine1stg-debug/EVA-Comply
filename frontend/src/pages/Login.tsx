import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { api } from '../lib/api'
import { LOGO_LG } from '../assets/logo'
import { useT } from '../lib/i18n'
import LangSwitch from '../components/LangSwitch'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const navigate = useNavigate()
  const t = useT()
  const { login, verifyMFA } = useAuthStore()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mfaStep, setMfaStep] = useState(false)
  const [mfaCode, setMfaCode] = useState('')
  const [tempToken, setTempToken] = useState('')
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      const result = await login(email, password)
      if (result.requires_mfa) {
        setTempToken(result.temp_token || '')
        setMfaStep(true)
      } else {
        navigate('/dashboard')
      }
    } catch (err: any) {
      toast.error(err?.response?.data?.detail || t('Invalid email or password'))
    } finally {
      setLoading(false)
    }
  }

  const requestUnlock = async () => {
    if (!email.trim()) return toast.error(t('Enter your email first'))
    try {
      await api.post('/auth/request-unlock', { email })
      toast.success(t('If the account is locked, an unlock link has been emailed.'))
    } catch { toast.error(t('Something went wrong')) }
  }

  const handleMFA = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await verifyMFA(mfaCode, tempToken)
      navigate('/dashboard')
    } catch {
      toast.error(t('Invalid MFA code'))
    } finally {
      setLoading(false)
    }
  }


  return (
    <div className="min-h-screen flex items-center justify-center p-5"
      style={{ background: '#0B1629', backgroundImage: 'linear-gradient(#3BBCFF 1px,transparent 1px),linear-gradient(90deg,#3BBCFF 1px,transparent 1px)', backgroundSize: '36px 36px', backgroundOpacity: '.03' }}>
      <LangSwitch />
      <div className="w-full max-w-sm rounded-2xl p-7 shadow-2xl" style={{ background: '#111E35', border: '1px solid rgba(255,255,255,.07)' }}>

        {/* Logo */}
        <div className="text-center mb-6 pb-5" style={{ borderBottom: '1px solid rgba(255,255,255,.07)' }}>
          <img src={LOGO_LG} alt="EVA Technologies" className="mx-auto" style={{ width: 200, height: 'auto' }} />
          <div className="text-xs mt-2" style={{ color: '#4A6A8A' }}>{t('Cybersecurity Audit Portal')}</div>
        </div>

        {!mfaStep ? (
          <>
            <form onSubmit={handleLogin} className="flex flex-col gap-3">
              <div>
                <label className="text-xs font-semibold block mb-1" style={{ color: '#7094B8' }}>{t('Email')}</label>
                <input type="email" value={email} onChange={e => setEmail(e.target.value)}
                  className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                  style={{ background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.09)', color: '#E2E8F0' }}
                  placeholder="you@company.com" required />
              </div>
              <div>
                <label className="text-xs font-semibold block mb-1" style={{ color: '#7094B8' }}>{t('Password')}</label>
                <input type="password" value={password} onChange={e => setPassword(e.target.value)}
                  className="w-full rounded-lg px-3 py-2 text-sm outline-none"
                  style={{ background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.09)', color: '#E2E8F0' }}
                  placeholder="••••••••" required />
              </div>
              <button type="submit" disabled={loading}
                className="w-full py-2.5 rounded-lg font-semibold text-white text-sm mt-1"
                style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)', opacity: loading ? .7 : 1 }}>
                {loading ? t('Signing in…') : t('Sign in')}
              </button>
            </form>

            <div className="text-xs text-center mt-3" style={{ color: '#3A5570' }}>
              {t('New organization?')} <span style={{ color: '#7DD3FC', cursor: 'pointer' }} onClick={() => navigate('/signup')}>{t('Create an account')}</span> · <span style={{ color: '#7DD3FC', cursor: 'pointer' }} onClick={() => navigate('/welcome')}>{t('See plans')}</span>
            </div>
            <div className="text-xs text-center mt-2" style={{ color: '#3A5570' }}>
              <span style={{ color: '#7DD3FC', cursor: 'pointer' }} onClick={requestUnlock}>{t('Account locked? Email me an unlock link')}</span>
            </div>
            <div className="text-xs text-center mt-2" style={{ color: '#3A5570' }}>
              {t('A service provider?')} <span style={{ color: '#7DD3FC', cursor: 'pointer' }} onClick={() => navigate('/provider-signup')}>{t('Apply to the marketplace')}</span>
            </div>
          </>
        ) : (
          <form onSubmit={handleMFA} className="flex flex-col gap-4">
            <div className="text-center">
              <div className="text-base font-semibold text-white mb-1">{t('Two-Factor Auth')}</div>
              <div className="text-xs" style={{ color: '#4A6A8A' }}>{t('Enter the 6-digit code from your authenticator app')}</div>
            </div>
            <input type="text" inputMode="numeric" maxLength={6} value={mfaCode}
              onChange={e => setMfaCode(e.target.value.replace(/\D/g, ''))}
              className="w-full rounded-lg px-3 py-3 text-center text-2xl font-bold tracking-widest outline-none"
              style={{ background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.09)', color: '#E2E8F0', fontFamily: 'monospace' }}
              placeholder="______" autoFocus />
            <button type="submit" disabled={loading || mfaCode.length < 6}
              className="w-full py-2.5 rounded-lg font-semibold text-white text-sm"
              style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)', opacity: (loading || mfaCode.length < 6) ? .5 : 1 }}>
              {loading ? t('Verifying…') : t('Verify')}
            </button>
            <div className="text-xs text-center" style={{ color: '#3A5570' }}>
              {t('Demo: enter any 6 digits (MFA not enforced in dev mode)')}
            </div>
            <button type="button" onClick={() => { setMfaStep(false); setMfaCode('') }}
              className="text-xs text-center w-full" style={{ color: '#3A5570', background: 'none', border: 'none', cursor: 'pointer' }}>
              {t('← Back to sign in')}
            </button>
          </form>
        )}
      </div>
    </div>
  )
}
