import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { LOGO_LG } from '../assets/logo'
import { useT } from '../lib/i18n'
import LangSwitch from '../components/LangSwitch'

interface Plan { key: string; name: string; price: number; tenant_type: string; highlights?: string[] }

export default function WelcomePage() {
  const navigate = useNavigate()
  const t = useT()
  const [plans, setPlans] = useState<Plan[]>([])
  useEffect(() => { api.get('/auth/signup-options').then(r => setPlans(r.data.plans)).catch(() => {}) }, [])

  const card = (p: Plan, highlight: boolean) => (
    <div key={p.key} style={{
      flex: 1, minWidth: 220, background: '#111E35', borderRadius: 16, padding: 24,
      border: `1px solid ${highlight ? '#3BBCFF' : 'rgba(255,255,255,.08)'}`,
      boxShadow: highlight ? '0 0 0 2px rgba(59,188,255,.18)' : 'none',
    }}>
      <div style={{ fontSize: 12, fontWeight: 700, letterSpacing: '.06em', textTransform: 'uppercase', color: p.tenant_type === 'msp' ? '#A78BFA' : '#7DD3FC' }}>
        {p.tenant_type === 'msp' ? t('For MSPs') : t('For organizations')}
      </div>
      <div style={{ fontSize: 20, fontWeight: 700, color: '#E2E8F0', marginTop: 6 }}>{p.name}</div>
      <div style={{ fontSize: 30, fontWeight: 700, color: '#fff', marginTop: 8 }}>${p.price}<span style={{ fontSize: 13, color: '#4A6A8A', fontWeight: 400 }}>{t('/mo')}</span></div>
      <ul style={{ listStyle: 'none', margin: '16px 0', padding: 0, fontSize: 13, color: '#94B3CE', lineHeight: 2 }}>
        {(p.highlights && p.highlights.length)
          ? p.highlights.map((h, i) => <li key={i}>✓ {h}</li>)
          : <>
              <li>{t('✓ Framework compliance tracking')}</li>
              <li>{t('✓ Evidence collection & review')}</li>
              <li>{t('✓ Expert EVA audit decisions')}</li>
              {p.tenant_type === 'msp' && <li>{t('✓ Multi-client portfolio + resale')}</li>}
            </>}
      </ul>
      <button onClick={() => navigate('/signup')} className="w-full py-2.5 rounded-lg font-semibold text-white text-sm"
        style={{ background: highlight ? 'linear-gradient(135deg,#1A8FD1,#3A2F8F)' : 'rgba(255,255,255,.06)', border: highlight ? 'none' : '1px solid rgba(255,255,255,.12)' }}>
        {t('Get started')}
      </button>
    </div>
  )

  return (
    <div style={{ minHeight: '100vh', background: '#0B1629', backgroundImage: 'linear-gradient(#3BBCFF 1px,transparent 1px),linear-gradient(90deg,#3BBCFF 1px,transparent 1px)', backgroundSize: '40px 40px' }}>
      <LangSwitch />
      <div style={{ maxWidth: 980, margin: '0 auto', padding: '28px 24px 60px' }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <img src={LOGO_LG} alt="EVA Technologies" style={{ width: 180 }} />
          <button onClick={() => navigate('/login')} className="text-sm" style={{ color: '#7DD3FC', background: 'none', border: '1px solid rgba(255,255,255,.12)', borderRadius: 8, padding: '7px 16px', cursor: 'pointer' }}>{t('Sign in')}</button>
        </div>

        <div style={{ textAlign: 'center', padding: '54px 0 34px' }}>
          <div style={{ fontSize: 40, fontWeight: 700, color: '#fff', letterSpacing: '-.02em', lineHeight: 1.15 }}>
            {t('Cybersecurity compliance, audited by experts.')}
          </div>
          <div style={{ fontSize: 15, color: '#94B3CE', marginTop: 14, maxWidth: 620, margin: '14px auto 0' }}>
            {t('Manage CMMC, NIST CSF and Cyber Canada in one place — collect evidence, get a three-tier review, and reach audit readiness faster.')}
          </div>
          <button onClick={() => navigate('/signup')} className="font-semibold text-white" style={{ marginTop: 24, padding: '12px 28px', borderRadius: 10, background: 'linear-gradient(135deg,#1A8FD1,#3A2F8F)', border: 'none', cursor: 'pointer', fontSize: 15 }}>
            {t('Start your compliance journey →')}
          </button>
        </div>

        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 20 }}>
          {plans.length === 0 && <div style={{ color: '#4A6A8A', fontSize: 13 }}>{t('Loading plans…')}</div>}
          {plans.map((p, i) => card(p, p.tenant_type === 'single_client' && i === 0))}
        </div>

        <div style={{ textAlign: 'center', color: '#3A5570', fontSize: 12, marginTop: 40 }}>
          {t('Managed Service Provider? Pick the MSP plan to onboard and bill your own clients.')}
        </div>
      </div>
    </div>
  )
}
