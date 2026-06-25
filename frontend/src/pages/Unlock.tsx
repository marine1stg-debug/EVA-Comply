import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { LOGO_LG } from '../assets/logo'
import { useT } from '../lib/i18n'
import LangSwitch from '../components/LangSwitch'

export default function UnlockPage() {
  const navigate = useNavigate()
  const t = useT()
  const token = new URLSearchParams(window.location.search).get('token') || ''
  const [state, setState] = useState<'working' | 'ok' | 'error'>('working')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    if (!token) { setState('error'); setMsg(t('Missing unlock token.')); return }
    api.post('/auth/unlock', { token })
      .then(() => setState('ok'))
      .catch(e => { setState('error'); setMsg(e?.response?.data?.detail || t('This unlock link is invalid or has expired.')) })
  }, [token])

  return (
    <div className="min-h-screen flex items-center justify-center p-5" style={{ background: '#0B1629' }}>
      <LangSwitch />
      <div className="w-full max-w-sm rounded-2xl p-7 shadow-2xl text-center" style={{ background: '#111E35', border: '1px solid rgba(255,255,255,.07)' }}>
        <div className="mb-5 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,.07)' }}>
          <img src={LOGO_LG} alt="EVA" className="mx-auto" style={{ width: 180 }} />
          <div className="text-xs mt-2" style={{ color: '#4A6A8A' }}>{t('Unlock your account')}</div>
        </div>
        {state === 'working' && <div className="page-sub" style={{ color: '#4A6A8A' }}>{t('Unlocking…')}</div>}
        {state === 'ok' && (
          <>
            <div style={{ fontSize: 38 }}>🔓</div>
            <div className="text-sm mt-2 mb-4" style={{ color: '#CBD5E1' }}>{t('Your account is unlocked. You can sign in now.')}</div>
            <button className="w-full py-2.5 rounded-lg font-semibold text-white text-sm"
              style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)' }} onClick={() => navigate('/login')}>
              {t('Go to sign in')}
            </button>
          </>
        )}
        {state === 'error' && (
          <>
            <div style={{ background: 'rgba(220,38,38,.1)', border: '1px solid rgba(220,38,38,.25)', borderRadius: 8, padding: '10px 12px', fontSize: 12, color: '#FCA5A5' }}>{msg}</div>
            <button className="w-full py-2.5 rounded-lg font-semibold text-white text-sm mt-4"
              style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)' }} onClick={() => navigate('/login')}>
              {t('Go to sign in')}
            </button>
          </>
        )}
      </div>
    </div>
  )
}
