import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuthStore } from '../store/auth'
import { useT } from '../lib/i18n'
import Ico from './Ico'

interface Step { icon: string; title: string; desc: string; to: string; cta: string }

const STEPS_BY_ROLE: Record<string, Step[]> = {
  msp: [
    { icon: '🏢', title: 'Add your first client', desc: 'Create a client org, set its price and frameworks.', to: '/clients', cta: 'Add client' },
    { icon: '👁', title: 'Pre-review their evidence', desc: 'Approve or flag client uploads before they reach EVA.', to: '/review', cta: 'Open queue' },
    { icon: '📊', title: 'Track portfolio compliance', desc: 'See every client’s readiness and your margin.', to: '/portfolio', cta: 'View portfolio' },
  ],
  client: [
    { icon: '☰', title: 'Review your controls', desc: 'See what each framework requires, in plain language.', to: '/controls', cta: 'Open controls' },
    { icon: '📄', title: 'Upload evidence', desc: 'Attach a document and submit it for review.', to: '/evidence', cta: 'Add evidence' },
    { icon: '↺', title: 'Keep evidence current', desc: 'Track renewals so nothing expires before the audit.', to: '/renewals', cta: 'View renewals' },
  ],
  eva: [
    { icon: '👁', title: 'Work the review queue', desc: 'Accept, reject, or request more on submitted evidence.', to: '/review', cta: 'Open queue' },
    { icon: '🏛', title: 'Manage tenants', desc: 'Suspend, reactivate, and inspect every organization.', to: '/tenants', cta: 'Manage tenants' },
    { icon: '🏷', title: 'Configure plans & pricing', desc: 'Set what each package costs and includes.', to: '/plans', cta: 'Edit plans' },
  ],
}

function groupFor(role: string): keyof typeof STEPS_BY_ROLE {
  if (['msp_admin', 'msp_analyst'].includes(role)) return 'msp'
  if (['super_admin', 'eva_auditor'].includes(role)) return 'eva'
  return 'client'
}

export default function GettingStarted() {
  const navigate = useNavigate()
  const t = useT()
  const user = useAuthStore(s => s.user)
  const key = `eva-gs-dismissed-${user?.id || 'anon'}`
  const [dismissed, setDismissed] = useState<boolean>(() => {
    try { return localStorage.getItem(key) === '1' } catch { return false }
  })
  if (dismissed || !user) return null

  const steps = STEPS_BY_ROLE[groupFor(user.role)]
  const close = () => { try { localStorage.setItem(key, '1') } catch { /* ignore */ } setDismissed(true) }

  return (
    <div className="detail-section fi" style={{ marginBottom: 20, borderColor: 'var(--border-l)', background: 'var(--soft)' }}>
      <div className="card-hdr" style={{ marginBottom: 10 }}>
        <span className="card-title" style={{ color: 'var(--brand)', display: 'inline-flex', alignItems: 'center', gap: 6 }}><Ico e="👋" size={15} /> {t('Getting started')}</span>
        <span className="card-link" onClick={close}>{t('Dismiss')}</span>
      </div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3,1fr)', gap: 12 }}>
        {steps.map((s, i) => (
          <div key={i} style={{ border: '1px solid var(--border-l)', borderRadius: 10, padding: 14, background: 'var(--card)', display: 'flex', flexDirection: 'column' }}>
            <div style={{ fontSize: 22, color: 'var(--brand)' }}><Ico e={s.icon} size={22} /></div>
            <div style={{ fontSize: 13, fontWeight: 600, color: 'var(--text)', marginTop: 6 }}>{i + 1}. {t(s.title)}</div>
            <div style={{ fontSize: 11, color: 'var(--text3)', marginTop: 3, lineHeight: 1.5, flex: 1 }}>{t(s.desc)}</div>
            <button className="tb-btn pri" style={{ marginTop: 10, justifyContent: 'center', fontSize: 11 }} onClick={() => navigate(s.to)}>{t(s.cta)}</button>
          </div>
        ))}
      </div>
    </div>
  )
}
