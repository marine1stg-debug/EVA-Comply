import { useState, useEffect } from 'react'
import { Outlet, useNavigate, useLocation } from 'react-router-dom'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { useAuthStore } from '../store/auth'
import { useClientContext } from '../store/clientContext'
import { useUnsavedGuard } from '../store/unsavedGuard'
import { api } from '../lib/api'
import { useT, useI18n } from '../lib/i18n'
import { LOGO_LG } from '../assets/logo'
import { LOGO_LIGHT } from '../assets/logoLight'
import NotificationBell from './NotificationBell'
import AgreementGate from './AgreementGate'
import Ico from './Ico'

interface ClientLite { id: string; name: string; compliance: number; pending_review: number }

function ClientSelector() {
  const qc = useQueryClient()
  const t = useT()
  const { clientId, setClient } = useClientContext()
  const { data } = useQuery<{ clients: ClientLite[] }>({
    queryKey: ['review-clients'],
    queryFn: async () => (await api.get('/review/clients')).data,
  })
  const clients = data?.clients || []
  // Drop a stale selection that isn't in *this* user's scoped client list
  // (e.g. a client persisted from a previous login as a different role).
  useEffect(() => {
    if (data && clientId && !clients.some(c => c.id === clientId)) {
      setClient(null, null)
      qc.invalidateQueries()
    }
  }, [data]) // eslint-disable-line react-hooks/exhaustive-deps
  const onChange = async (id: string) => {
    // Unsaved changes on the current screen (e.g. a control's self-assessment)?
    // Offer to save them BEFORE switching — the save must run while the current
    // client is still active, so we await it first.
    const g = useUnsavedGuard.getState()
    if (g.dirty) {
      const save = window.confirm(t('You have unsaved changes. Save them before switching client? (Cancel to discard)'))
      if (save && g.save) {
        try { await g.save() } catch { /* surfaced by the page */ }
      }
      g.clear()
    }
    const c = clients.find(x => x.id === id)
    setClient(id || null, c?.name || null)
    qc.invalidateQueries()  // refetch every client-scoped screen for the new selection
  }
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
      <span style={{ fontSize: 11, color: 'var(--text3)' }}>{t('Viewing client')}</span>
      <select value={clientId || ''} onChange={e => onChange(e.target.value)}
        style={{ fontSize: 12, fontWeight: 600, padding: '6px 10px', borderRadius: 8, cursor: 'pointer',
          border: `1px solid ${clientId ? 'rgba(37,99,235,.45)' : 'rgba(220,38,38,.5)'}`,
          background: clientId ? 'var(--soft)' : 'rgba(220,38,38,.12)', color: 'var(--text)' }}>
        <option value="">{t('— Select a client —')}</option>
        {clients.map(c => <option key={c.id} value={c.id}>{c.name}{c.pending_review ? ` (${t('{n} to review', { n: c.pending_review })})` : ''}</option>)}
      </select>
    </div>
  )
}

interface Trial { trialing: boolean; days_left: number | null; locked: boolean; status: string }
interface Entitlements { features: Record<string, boolean>; unlimited: boolean; trial?: Trial; org_name?: string }

const ROLE_COLORS: Record<string, string> = {
  super_admin: '#7C3AED', eva_auditor: '#2563EB', msp_admin: '#0D9488',
  msp_analyst: '#0891B2', client_admin: '#D97706', contributor: '#16A34A', viewer: '#64748B'
}

interface NavItem { path: string; icon: string; label: string; show: boolean }
interface NavSection { label: string | null; items: NavItem[] }

/* Inline icons */
const IcBell = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
)
const IcGear = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
  </svg>
)
const IcSearch = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round"><circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" /></svg>
)
const IcHelp = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10" /><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3" /><line x1="12" y1="17" x2="12.01" y2="17" /></svg>
)
const IcSupport = () => (
  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></svg>
)
const IcSun = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="4" /><path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" /></svg>
)
const IcMoon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" /></svg>
)
const IcLogout = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" /><polyline points="16 17 21 12 16 7" /><line x1="21" y1="12" x2="9" y2="12" /></svg>
)

function useTheme(): [string, () => void] {
  const [theme, setTheme] = useState<string>(() =>
    (typeof document !== 'undefined' && document.documentElement.getAttribute('data-theme')) || 'light')
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    try { localStorage.setItem('eva-theme', theme) } catch { /* ignore */ }
  }, [theme])
  return [theme, () => setTheme(t => (t === 'dark' ? 'light' : 'dark'))]
}

export default function Shell() {
  const { user, logout } = useAuthStore()
  const navigate = useNavigate()
  const loc = useLocation()
  const [theme, toggleTheme] = useTheme()
  const t = useT()
  const qc = useQueryClient()
  const { lang, toggle: toggleLang } = useI18n()
  // Switching language must refetch every server-localized query (titles,
  // domains, maturity, frameworks, recommendations, expected evidence, …)
  // so the whole UI reloads in the new language, not just the toggle.
  const switchLang = () => { toggleLang(); qc.invalidateQueries() }
  const clientName = useClientContext(s => s.clientName)

  const role = user?.role || ''
  const canReview = ['msp_admin', 'msp_analyst', 'eva_auditor', 'super_admin'].includes(role)
  const canUsers = ['super_admin', 'msp_admin', 'client_admin'].includes(role)
  const canTenants = role === 'super_admin'
  const canFrameworks = ['super_admin', 'msp_admin'].includes(role)
  const canMsp = ['super_admin', 'msp_admin', 'msp_analyst'].includes(role)
  const canBilling = ['super_admin', 'msp_admin', 'client_admin'].includes(role)
  const canEva = ['super_admin', 'eva_auditor'].includes(role)

  // Entitlements drive feature-module visibility (default to shown while loading)
  const { data: ent } = useQuery<Entitlements>({
    queryKey: ['entitlements'],
    queryFn: async () => (await api.get('/auth/entitlements')).data,
  })
  const feat = (k: string) => !ent || ent.unlimited || !!ent.features?.[k]

  const sections: NavSection[] = [
    { label: 'Overview', items: [
      { path: '/dashboard', icon: '⊞', label: 'Dashboard', show: true },
    ]},
    { label: canReview ? 'Client compliance' : 'Compliance', items: [
      { path: '/controls', icon: '☰', label: 'Controls', show: true },
      { path: '/evidence', icon: '📄', label: 'Evidence', show: true },
      { path: '/maturity', icon: '◎', label: 'Maturity', show: true },
      { path: '/recommendations', icon: '✦', label: 'Recommendations', show: true },
      { path: '/renewals', icon: '↺', label: 'Renewals', show: true },
      { path: '/reports', icon: '⬇', label: 'Reports', show: feat('reports') },
    ]},
    { label: 'Review', items: [
      { path: '/review', icon: '👁', label: 'Review Queue', show: canReview },
    ]},
    { label: 'MSP', items: [
      { path: '/portfolio', icon: '📊', label: 'Portfolio', show: canMsp },
      { path: '/clients', icon: '🏢', label: 'Clients', show: canMsp },
      { path: '/partner', icon: '💰', label: 'Margin & Revenue', show: canMsp },
    ]},
    { label: 'Frameworks', items: [
      { path: '/frameworks', icon: '📚', label: 'Library', show: canFrameworks },
      { path: '/import', icon: '⬆', label: 'Import', show: canFrameworks && feat('import') },
    ]},
    { label: 'Administration', items: [
      { path: '/tenants', icon: '🏛', label: 'Tenants', show: canTenants },
      { path: '/support-cases', icon: '🎧', label: 'Support Console', show: canEva },
      { path: '/plans', icon: '🏷', label: 'Plans & Pricing', show: canTenants },
      { path: '/training', icon: '🎬', label: 'Training Videos', show: canTenants },
      { path: '/marketplace', icon: '🛠', label: 'Service Providers', show: canTenants },
      { path: '/ai-settings', icon: '✦', label: 'AI Connector', show: canTenants },
      { path: '/users', icon: '👤', label: 'Users & Roles', show: canUsers },
      { path: '/billing', icon: '💳', label: 'Billing', show: canBilling },
      { path: '/audit-logs', icon: '📋', label: 'Audit Logs', show: !!role },
      { path: '/backup', icon: '🗄', label: 'Backup & Restore', show: canTenants },
      { path: '/settings', icon: '⚙', label: 'Settings', show: true },
    ]},
  ]

  const initials = user?.display_name ? user.display_name.split(' ').map((n: string) => n[0]).join('').slice(0, 2) : '?'
  const roleColor = ROLE_COLORS[role] || '#64748B'

  // On phones, surface the isolated mobile quick view (cases + incident).
  const [isMobile, setIsMobile] = useState(typeof window !== 'undefined' && window.innerWidth < 768)
  useEffect(() => {
    const h = () => setIsMobile(window.innerWidth < 768)
    window.addEventListener('resize', h)
    return () => window.removeEventListener('resize', h)
  }, [])

  return (
    <div className="app-shell">
      {isMobile && (
        <div onClick={() => navigate('/m')} style={{ cursor: 'pointer', background: 'var(--eva-blue2)', color: '#fff',
          padding: '8px 14px', fontSize: 13, fontWeight: 600, textAlign: 'center' }}>
          📱 {t('Open the mobile quick view (cases & incidents)')} →
        </div>
      )}
      {/* ── TOP BAR (utilities only — page nav lives in the sidebar) ── */}
      <header className="topbar">
        <div className="brand" onClick={() => navigate('/dashboard')}>
          <img className="brand-logo" src={theme === 'dark' ? LOGO_LG : LOGO_LIGHT} alt="EVA Comply" />
        </div>

        <div className="top-search">
          <span className="si"><IcSearch /></span>
          <input placeholder={t('Search controls, evidence, clients…')}
            onKeyDown={e => { if (e.key === 'Enter') navigate('/controls') }} />
        </div>

        <div className="top-client">
          <span className="tc-icon">🏢</span>
          <span className="tc-name">{canReview ? (clientName || t('No client selected')) : (ent?.org_name || user?.display_name || '')}</span>
        </div>

        <div className="top-right">
          {canReview && <ClientSelector />}
          {ent?.trial?.trialing && !ent.trial.locked && (
            <button onClick={() => navigate('/billing')}
              style={{ fontSize: 11, fontWeight: 600, padding: '6px 12px', borderRadius: 8, cursor: 'pointer',
                background: (ent.trial.days_left ?? 0) <= 3 ? 'rgba(220,38,38,.12)' : 'rgba(217,119,6,.12)',
                color: (ent.trial.days_left ?? 0) <= 3 ? 'var(--red)' : 'var(--amber)',
                border: `1px solid ${(ent.trial.days_left ?? 0) <= 3 ? 'rgba(220,38,38,.3)' : 'rgba(217,119,6,.3)'}` }}>
              ⏳ {t(ent.trial.days_left === 1 ? 'Trial — {days} day left · Subscribe' : 'Trial — {days} days left · Subscribe', { days: ent.trial.days_left ?? 0 })}
            </button>
          )}
          <button className="lang-toggle" title={lang === 'fr' ? 'Switch to English' : 'Passer en français'} onClick={switchLang}>
            <span className={lang === 'en' ? 'on' : ''}>EN</span>
            <span className={lang === 'fr' ? 'on' : ''}>FR</span>
          </button>
          <button className="icon-btn" title={theme === 'dark' ? t('Switch to light mode') : t('Switch to dark mode')} onClick={toggleTheme}>
            {theme === 'dark' ? <IcSun /> : <IcMoon />}
          </button>
          <NotificationBell />
          <button className="icon-btn" title={t('Settings')} onClick={() => navigate('/settings')}><IcGear /></button>
          <button className="avatar-btn" title={`${user?.display_name} — account & sign out`}
            style={{ background: `linear-gradient(135deg, ${roleColor}, #1E293B)` }}
            onClick={() => navigate('/users')}>
            {initials}
          </button>
        </div>
      </header>

      {/* ── BODY: sidebar + main ── */}
      <div className="body-row">
        <aside className="sidebar-l">
          <div className="side-ctx">
            <div className="side-ctx-title"><span className="bn-eva">EVA</span> Comply</div>
            <div className="side-ctx-sub">{t('Risk & Compliance')}</div>
          </div>

          {user && (
            <div className="side-role">
              <span style={{ display: 'inline-block', width: 8, height: 8, borderRadius: '50%', background: roleColor }} />
              <span>{t(role.replace(/_/g, ' '))}</span>
            </div>
          )}

          <nav className="side-nav">
            {sections.map((sec, si) => {
              const items = sec.items.filter(i => i.show)
              if (!items.length) return null
              return (
                <div key={si}>
                  {sec.label && <div className="side-section">{t(sec.label)}</div>}
                  {items.map(item => {
                    const active = loc.pathname === item.path
                    return (
                      <button key={item.path} className={`side-item ${active ? 'active' : ''}`} onClick={() => navigate(item.path)}>
                        <span className="ic"><Ico e={item.icon} size={15} /></span>
                        <span>{t(item.label)}</span>
                      </button>
                    )
                  })}
                </div>
              )
            })}
          </nav>

          <div className="side-foot">
            <button className="side-link" onClick={() => navigate('/help')}><IcHelp /> {t('Help Center')}</button>
            <button className="side-link" onClick={() => navigate('/support')}><IcSupport /> {t('Contact Support')}</button>
            {user && (
              <div className="side-account">
                <span className="sa-avatar" style={{ background: `linear-gradient(135deg, ${roleColor}, #1E293B)` }}>{initials}</span>
                <div className="sa-meta">
                  <span className="sa-name">{user.display_name}</span>
                  <span className="sa-role">{t(role.replace(/_/g, ' '))}</span>
                </div>
                <button className="sa-signout" onClick={logout} title={t('Sign out')}><IcLogout /></button>
              </div>
            )}
          </div>
        </aside>

        <main className="main-scroll">
          <Outlet />
        </main>
      </div>

      <AgreementGate />

      {ent?.trial?.locked && loc.pathname !== '/billing' && (
        <div className="modal-overlay" style={{ zIndex: 60 }}>
          <div className="modal-card" style={{ maxWidth: 440 }}>
            <div className="modal-body" style={{ padding: 28, textAlign: 'center' }}>
              <div style={{ fontSize: 40 }}>🔒</div>
              <div style={{ fontSize: 18, fontWeight: 700, marginTop: 8, color: 'var(--text)' }}>{t('Your trial has ended')}</div>
              <div className="page-sub" style={{ marginTop: 6 }}>{t('Subscribe to restore full access to your compliance workspace.')}</div>
              <button className="submit-btn" style={{ marginTop: 18, width: '100%', justifyContent: 'center' }} onClick={() => navigate('/billing')}>{t('View plans & subscribe')}</button>
              <button className="tb-btn" style={{ marginTop: 8, width: '100%', justifyContent: 'center' }} onClick={logout}>{t('Sign out')}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
