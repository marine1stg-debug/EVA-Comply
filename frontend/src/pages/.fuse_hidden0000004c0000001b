import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useAuthStore } from '../store/auth'
import { useT, useI18n } from '../lib/i18n'
import { HELP_ARTICLES, HELP_CATEGORIES, audiencesForRole, audiencesForPersona, PERSONA_OPTIONS, type HelpArticle, type Audience, type Persona } from '../lib/helpContent'
import Ico from '../components/Ico'

function Body({ text }: { text: string }) {
  // Split on blank lines into paragraphs; lines starting with "• " become a list.
  const blocks = text.split('\n\n')
  return (
    <>
      {blocks.map((b, i) => {
        const lines = b.split('\n')
        if (lines.every(l => l.startsWith('• '))) {
          return <ul key={i} style={{ margin: '0 0 12px', paddingLeft: 18 }}>{lines.map((l, j) => <li key={j} style={{ marginBottom: 4 }}>{l.slice(2)}</li>)}</ul>
        }
        return <p key={i} style={{ margin: '0 0 12px', lineHeight: 1.65, color: 'var(--text2)', fontSize: 13 }}>{b}</p>
      })}
    </>
  )
}

export default function HelpCenterPage() {
  const t = useT()
  const { lang } = useI18n()
  const role = useAuthStore(s => s.user?.role || '')
  const isEva = ['super_admin', 'eva_auditor'].includes(role)
  const [persona, setPersona] = useState<Persona>('me')
  const [q, setQ] = useState('')
  const [open, setOpen] = useState<HelpArticle | null>(null)

  // EVA staff can preview each user's view; everyone else sees their own scope.
  const myAud = (isEva && persona !== 'me') ? audiencesForPersona(persona) : audiencesForRole(role)

  // Dynamic note for clients whose MSP pre-reviews their evidence. Shown to a
  // real MSP-managed client (entitlements flag), or when EVA previews "MSP's client".
  const { data: ent } = useQuery<{ msp_review?: boolean; msp_managed?: boolean }>({
    queryKey: ['entitlements'], queryFn: async () => (await api.get('/auth/entitlements')).data,
  })
  const showMspNote = (isEva && persona === 'msp_client') || (!isEva && !!ent?.msp_review)

  const L = (b: { en: string; fr: string }) => (lang === 'fr' ? b.fr : b.en)
  const inScope = (a: HelpArticle) => a.audience.some(x => myAud.includes(x as Audience))
  const matches = (a: HelpArticle) => {
    if (!q.trim()) return true
    const s = q.toLowerCase()
    return L(a.title).toLowerCase().includes(s) || L(a.summary).toLowerCase().includes(s) || L(a.body).toLowerCase().includes(s)
  }
  const visible = HELP_ARTICLES.filter(a => inScope(a) && matches(a))

  if (open) {
    return (
      <>
        <div className="page-hdr fi">
          <div>
            <button className="tb-btn" style={{ marginBottom: 8 }} onClick={() => setOpen(null)}>← {t('Back to Help Center')}</button>
            <div className="page-title" style={{ display: 'flex', alignItems: 'center', gap: 8 }}><Ico e={open.icon} size={18} /> {L(open.title)}</div>
            <div className="page-sub">{L(open.summary)}</div>
          </div>
        </div>
        <div className="detail-section fi" style={{ maxWidth: 760 }}>
          <Body text={L(open.body)} />
        </div>
      </>
    )
  }

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Help Center')}</div>
          <div className="page-sub">{t('Your owner’s manual for EVA Comply — guides tailored to your role.')}</div>
        </div>
      </div>

      <div className="filter-bar fi" style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'center' }}>
        <input className="form-input" style={{ maxWidth: 320, fontSize: 13 }} placeholder={t('Search help…')} value={q} onChange={e => setQ(e.target.value)} />
        {isEva && (
          <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text2)' }}>
            👁 {t('View Help as')}
            <select className="filter-select" value={persona} onChange={e => setPersona(e.target.value as Persona)}>
              {PERSONA_OPTIONS.map(o => <option key={o.id} value={o.id}>{L(o.label)}</option>)}
            </select>
          </label>
        )}
      </div>
      {isEva && persona !== 'me' && (
        <div className="page-sub fi" style={{ marginTop: -4, marginBottom: 8, fontSize: 12, fontStyle: 'italic' }}>
          {t('Previewing the Help Center as this user would see it.')}
        </div>
      )}
      {showMspNote && (
        <div className="fi" style={{ margin: '0 0 14px', padding: '11px 14px', borderRadius: 10,
          border: '1px solid var(--border-l)', borderLeft: '4px solid #7C3AED', background: 'var(--card)', fontSize: 13, color: 'var(--text2)', lineHeight: 1.55 }}>
          🏢 {t('Your organization is managed by an MSP, so your evidence is pre-reviewed by your MSP before it reaches EVA. After you submit, it goes to your MSP first — they approve and forward it, or return it to you with feedback.')}
        </div>
      )}

      {HELP_CATEGORIES.map(cat => {
        const arts = visible.filter(a => a.category === cat.id)
        if (arts.length === 0) return null
        if (cat.id === 'faq') {
          return (
            <div key={cat.id} className="detail-section fi" style={{ marginBottom: 16 }}>
              <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{L(cat.title)}</span></div>
              {arts.map(a => (
                <details key={a.id} style={{ border: '1px solid var(--border-l)', borderRadius: 10, background: 'var(--card)', marginBottom: 8, overflow: 'hidden' }}>
                  <summary style={{ cursor: 'pointer', listStyle: 'none', padding: '11px 14px', display: 'flex', alignItems: 'center', gap: 8, fontSize: 13.5, fontWeight: 600 }}>
                    <Ico e={a.icon} size={15} /> {L(a.title)}
                  </summary>
                  <div style={{ padding: '0 14px 12px 36px' }}><Body text={L(a.body)} /></div>
                </details>
              ))}
            </div>
          )
        }
        return (
          <div key={cat.id} className="detail-section fi" style={{ marginBottom: 16 }}>
            <div className="card-hdr" style={{ marginBottom: 10 }}><span className="card-title">{L(cat.title)}</span></div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(260px, 1fr))', gap: 10 }}>
              {arts.map(a => (
                <div key={a.id} onClick={() => setOpen(a)} style={{
                  cursor: 'pointer', border: '1px solid var(--border-l)', borderRadius: 10, padding: '12px 14px', background: 'var(--card)',
                }}>
                  <div style={{ fontSize: 13.5, fontWeight: 600, marginBottom: 4, display: 'flex', alignItems: 'center', gap: 7 }}><Ico e={a.icon} size={15} /> {L(a.title)}</div>
                  <div style={{ fontSize: 11.5, color: 'var(--text3)', lineHeight: 1.5 }}>{L(a.summary)}</div>
                </div>
              ))}
            </div>
          </div>
        )
      })}
      {visible.length === 0 && <div className="page-sub fi">{t('No help articles match your search.')}</div>}
    </>
  )
}
