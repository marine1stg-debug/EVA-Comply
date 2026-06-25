import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { LOGO_LG } from '../assets/logo'
import { useT } from '../lib/i18n'
import LangSwitch from '../components/LangSwitch'
import { PUBLIC_BG } from '../lib/publicBg'

const inputStyle: React.CSSProperties = {
  width: '100%', borderRadius: 8, padding: '9px 12px', fontSize: 13, outline: 'none',
  background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.09)', color: '#E2E8F0', marginBottom: 10,
}

export default function ProviderSignupPage() {
  const navigate = useNavigate()
  const t = useT()
  const [skills, setSkills] = useState<string[]>([])
  const [sel, setSel] = useState<string[]>([])
  const [name, setName] = useState(''); const [contact, setContact] = useState('')
  const [email, setEmail] = useState(''); const [website, setWebsite] = useState('')
  const [done, setDone] = useState(false); const [loading, setLoading] = useState(false)
  useEffect(() => { api.get('/marketplace/public/skills').then(r => setSkills(r.data.skills || [])).catch(() => {}) }, [])
  const toggle = (s: string) => setSel(v => v.includes(s) ? v.filter(x => x !== s) : [...v, s])
  const submit = async () => {
    if (!name.trim() || !email.trim()) return toast.error(t('Name and contact email are required'))
    setLoading(true)
    try {
      await api.post('/marketplace/register', { name, contact_name: contact, contact_email: email, website, skills: sel })
      setDone(true)
    } catch (e: any) { toast.error(e?.response?.data?.detail || t('Sign up failed')) }
    finally { setLoading(false) }
  }

  return (
    <div className="min-h-screen flex items-center justify-center p-5" style={PUBLIC_BG}>
      <LangSwitch />
      <div className="w-full max-w-md rounded-2xl p-7 shadow-2xl" style={{ background: '#111E35', border: '1px solid rgba(255,255,255,.07)' }}>
        <div className="text-center mb-5 pb-4" style={{ borderBottom: '1px solid rgba(255,255,255,.07)' }}>
          <img src={LOGO_LG} alt="EVA" className="mx-auto" style={{ width: 180 }} />
          <div className="text-xs mt-2" style={{ color: '#4A6A8A' }}>{t('Join the service-provider marketplace')}</div>
        </div>
        {done ? (
          <div style={{ textAlign: 'center' }}>
            <div style={{ fontSize: 34 }}>✅</div>
            <div className="text-sm mt-2 mb-4" style={{ color: '#CBD5E1' }}>{t('Thanks! Your application is awaiting EVA authorization. We’ll be in touch.')}</div>
            <button className="w-full py-2.5 rounded-lg font-semibold text-white text-sm"
              style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)' }} onClick={() => navigate('/login')}>{t('Back to sign in')}</button>
          </div>
        ) : (
          <>
            <div style={{ background: 'rgba(26,143,209,.08)', border: '1px solid rgba(26,143,209,.25)', borderRadius: 10, padding: '12px 14px', marginBottom: 16, fontSize: 12.5, color: '#A9C4DD', lineHeight: 1.6 }}>
              🤝 {t('Become an EVA partner: get listed in the marketplace and matched with clients who need help on specific controls — a steady stream of qualified leads. Showcase your skills, get found exactly when a client is stuck, and grow your compliance practice.')}
            </div>
            <label style={{ fontSize: 11, fontWeight: 600, color: '#7094B8', display: 'block', marginBottom: 4 }}>{t('Company / provider name')}</label>
            <input style={inputStyle} value={name} onChange={e => setName(e.target.value)} />
            <label style={{ fontSize: 11, fontWeight: 600, color: '#7094B8', display: 'block', marginBottom: 4 }}>{t('Contact name')}</label>
            <input style={inputStyle} value={contact} onChange={e => setContact(e.target.value)} />
            <label style={{ fontSize: 11, fontWeight: 600, color: '#7094B8', display: 'block', marginBottom: 4 }}>{t('Contact email')}</label>
            <input style={inputStyle} type="email" value={email} onChange={e => setEmail(e.target.value)} />
            <label style={{ fontSize: 11, fontWeight: 600, color: '#7094B8', display: 'block', marginBottom: 4 }}>{t('Website')}</label>
            <input style={inputStyle} value={website} onChange={e => setWebsite(e.target.value)} placeholder="https://" />
            <label style={{ fontSize: 11, fontWeight: 600, color: '#7094B8', display: 'block', margin: '6px 0 6px' }}>{t('Skills you can offer')}</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 160, overflow: 'auto', marginBottom: 12 }}>
              {skills.map(s => (
                <span key={s} onClick={() => toggle(s)} style={{ cursor: 'pointer', fontSize: 11, padding: '4px 9px', borderRadius: 14,
                  border: `1px solid ${sel.includes(s) ? '#1A8FD1' : 'rgba(255,255,255,.12)'}`,
                  background: sel.includes(s) ? 'rgba(26,143,209,.18)' : 'transparent', color: sel.includes(s) ? '#7DD3FC' : '#7094B8' }}>
                  {sel.includes(s) ? '✓ ' : ''}{s}
                </span>
              ))}
            </div>
            <button className="w-full py-2.5 rounded-lg font-semibold text-white text-sm" disabled={loading}
              style={{ background: 'linear-gradient(135deg, #1A8FD1, #3A2F8F)', opacity: loading ? .6 : 1 }} onClick={submit}>
              {loading ? t('Submitting…') : t('Apply to join')}
            </button>
            <div className="text-xs text-center mt-3" style={{ color: '#3A5570' }}>
              <span style={{ color: '#7DD3FC', cursor: 'pointer' }} onClick={() => navigate('/login')}>{t('Back to sign in')}</span>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
