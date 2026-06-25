import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { LOGO_LG } from '../assets/logo'
import { useT } from '../lib/i18n'
import LangSwitch from '../components/LangSwitch'
import { PUBLIC_BG } from '../lib/publicBg'

interface Info { email: string; display_name: string; org_name: string; role: string; already_active: boolean }

const inputStyle: React.CSSProperties = {
  width: '100%', borderRadius: 8, padding: '9px 12px', fontSize: 13, outline: 'none',
  background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.09)', color: '#E2E8F0', marginBottom: 10,
}

export default function AcceptInvitePage() {
  const navigate = useNavigate()
  const t = useT()
  const setSession = useAuthStore(s => s.setSession)
  const token = new URLSearchParams(window.location.search).get('token') || ''
  const [info, setInfo] = useState<Info | null>(null)
  const [err, setErr] = useState('')
  const [pw, setPw] = useState(''); const [pw2, setPw2] = useState('')
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (!token) { setErr(t('Missing invite token.')); return }
    api.get(`/auth/invite-info?token=${encodeURIComponent(token)}`)
      .then(r => setInfo(r.data))
      .catch(e => setErr(e?.response?.data?.detail || t('This invite link is invalid or has expired.')))
  }, [token])

  const submit = async () => {
    if (pw.length < 12) return toast.error(t('Password must be at least 12 characters'))
    if (pw !== pw2) return toast.error(t('Passwords don’t match'))
    setLoading(true)
    try {
      const { data } = await api.post('/auth/accept-invite', { token, password: pw })
      setSession(data.access_token, data.user)
      toast.success(t('Welcome to EVA'))
      navigate('/dashboard')
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Could not accept invite')) }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-5" style={PUBLIC_BG}>
      <LangSwitch />
      <div className="w-full max-w-sm rounded-2xl p-7 shadow-2xl" style={{ background: '#111E35', border: '1px solid rgba(255,255,255,.07)' }}>
        <div className="text-center mb-5 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,.07)' }}>
          <img src={LOGO_LG} alt="EVA" className="mx-auto" style={{ width: 180 }} />
          <div className="text-xs mt-2" style={{ color: '#4A6A8A' }}>{t('Accept your invitation')}</div>
        </div>

        {err && <div style={{ background: 'rgba(220,38,38,.1)', border: '1px solid rgba(220,38,38,.25)', borderRadius: 8, padding: '10px 12px', fontSize: 12, color: '#FCA5A5' }}>{err}</div>}

        {!err && info && (
          <>
            <div className="text-sm mb-4" style={{ color: '#CBD5E1' }}>
              {t('You’ve been invited to join')} <b>{info.org_name}</b> {t('as')} <b>{t(info.role.replace(/_/g, ' '))}</b>.
              <div className="text-xs mt-1" style={{ color: '#4A6A8A' }}>{info.email}</div>
            </div>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#7094B8', marginBottom: 4, display: 'block' }}>{t('Set a password')}</label>
            <input style={inputStyle} type="password" value={pw} onChange={e => setPw(e.target.value)} placeholder={t('min 12 chars')} />
            <input style={inputStyle} type="password" value={pw2} onChange={e => setPw2(e.target.value)} placeholder={t('confirm password')} />
            <button className="w-full py-2.5 rounded-lg font-semibold text-white text-sm mt-1" disabled={loading}
              style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)', opacity: loading ? .6 : 1 }} onClick={submit}>
              {loading ? t('Setting up…') : t('Accept & enter EVA')}
            </button>
          </>
        )}
        {!err && !info && <div className="page-sub" style={{ color: '#4A6A8A' }}>{t('Loading invite…')}</div>}
      </div>
    </div>
  )
}
