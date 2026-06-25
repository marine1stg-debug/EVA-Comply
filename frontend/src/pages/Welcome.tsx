import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { LOGO_LG } from '../assets/logo'
import { useT, useI18n } from '../lib/i18n'
import { PUBLIC_BG } from '../lib/publicBg'

interface Plan { key: string; name: string; price: number; tenant_type: string; highlights?: string[] }

const CARD: React.CSSProperties = {
  background: '#111E35', border: '1px solid rgba(255,255,255,.08)', borderRadius: 16,
  boxShadow: '0 10px 30px rgba(0,0,0,.25)',
}

export default function WelcomePage() {
  const navigate = useNavigate()
  const t = useT()
  const { lang, setLang } = useI18n()
  const [plans, setPlans] = useState<Plan[]>([])
  useEffect(() => { api.get('/auth/signup-options').then(r => setPlans(r.data.plans)).catch(() => {}) }, [])

  const seg = (active: boolean): React.CSSProperties => ({
    border: 'none', cursor: 'pointer', padding: '5px 12px', fontSize: 12, fontWeight: 700,
    background: active ? '#1A8FD1' : 'transparent', color: active ? '#fff' : '#7DD3FC',
  })

  const card = (p: Plan, highlight: boolean) => (
    <div key={p.key} style={{
      ...CARD, flex: 1, minWidth: 220, padding: 24,
      border: `1px solid ${highlight ? '#3BBCFF' : 'rgba(255,255,255,.08)'}`,
      boxShadow: highlight ? '0 0 0 2px rgba(59,188,255,.18), 0 10px 30px rgba(0,0,0,.25)' : CARD.boxShadow,
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
    <div style={{ minHeight: '100vh', ...PUBLIC_BG }}>
      <div style={{ maxWidth: 980, margin: '0 auto', padding: '24px 20px 60px' }}>

        {/* Header card - logo + language + sign in, on a panel so the logo reads clearly */}
        <div style={{ ...CARD, display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '14px 20px', flexWrap: 'wrap' }}>
          <img src={LOGO_LG} alt="EVA Technologies" style={{ width: 168, height: 'auto' }} />
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ display: 'flex', border: '1px solid rgba(255,255,255,.15)', borderRadius: 999, overflow: 'hidden' }}>
              <button type="button" style={seg(lang === 'en')} onClick={() => setLang('en')}>EN</button>
              <button type="button" style={seg(lang === 'fr')} onClick={() => setLang('fr')}>FR</button>
            </div>
            <button onClick={() => navigate('/login')} className="text-sm"
              style={{ color: '#7DD3FC', background: 'rgba(255,255,255,.04)', border: '1px solid rgba(255,255,255,.12)', borderRadius: 8, padding: '7px 16px', cursor: 'pointer' }}>{t('Sign in')}</button>
          </div>
        </div>

        {/* Hero card - headline + subtitle + CTA inside a panel for readability */}
        <div style={{ ...CARD, textAlign: 'center', padding: '44px 28px', marginTop: 16 }}>
          <div style={{ fontSize: 38, fontWeight: 700, color: '#fff', letterSpacing: '-.02em', lineHeight: 1.15 }}>
            {t('Cybersecurity compliance, audited by experts.')}
          </div>
          <div style={{ fontSize: 15, color: '#A9C4DD', marginTop: 14, maxWidth: 620, margin: '14px auto 0' }}>
            {t('Manage CMMC, NIST CSF and Cyber Canada in one place - collect evidence, get a three-tier review, and reach audit readiness faster.')}
          </div>
          <button onClick={() => navigate('/signup')} className="font-semibold text-white" style={{ marginTop: 24, padding: '12px 28px', borderRadius: 10, background: 'linear-gradient(135deg,#1A8FD1,#3A2F8F)', border: 'none', cursor: 'pointer', fontSize: 15 }}>
            {t('Start your compliance journey →')}
          </button>
        </div>

        {/* Plan cards */}
        <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginTop: 16 }}>
          {plans.length === 0 && <div style={{ ...CARD, padding: 24, color: '#4A6A8A', fontSize: 13, flex: 1, textAlign: 'center' }}>{t('Loading plans…')}</div>}
          {plans.map((p, i) => card(p, p.tenant_type === 'single_client' && i === 0))}
        </div>

        {/* Footer note - boxed pill instead of bare text over the grid */}
        <div style={{ textAlign: 'center', marginTop: 22 }}>
          <span style={{ display: 'inline-block', ...CARD, borderRadius: 999, padding: '9px 18px', color: '#94B3CE', fontSize: 12 }}>
            {t('Managed Service Provider? Pick the MSP plan to onboard and bill your own clients.')}
          </span>
        </div>
      </div>
    </div>
  )
}
