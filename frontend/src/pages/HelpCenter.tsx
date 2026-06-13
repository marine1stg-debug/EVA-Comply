import { useState } from 'react'
import { useAuthStore } from '../store/auth'
import { useT, useI18n } from '../lib/i18n'
import { HELP_ARTICLES, HELP_CATEGORIES, audiencesForRole, type HelpArticle, type Audience } from '../lib/helpContent'
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
  const myAud = audiencesForRole(role)
  const [showAll, setShowAll] = useState(false)
  const [q, setQ] = useState('')
  const [open, setOpen] = useState<HelpArticle | null>(null)

  const L = (b: { en: string; fr: string }) => (lang === 'fr' ? b.fr : b.en)
  const inScope = (a: HelpArticle) => showAll || a.audience.some(x => myAud.includes(x as Audience))
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

      <div className="filter-bar fi">
        <input className="form-input" style={{ maxWidth: 320, fontSize: 13 }} placeholder={t('Search help…')} value={q} onChange={e => setQ(e.target.value)} />
        <label style={{ marginLeft: 'auto', display: 'flex', alignItems: 'center', gap: 6, fontSize: 12, color: 'var(--text2)' }}>
          <input type="checkbox" checked={showAll} onChange={e => setShowAll(e.target.checked)} /> {t('Show all roles')}
        </label>
      </div>

      {HELP_CATEGORIES.map(cat => {
        const arts = visible.filter(a => a.category === cat.id)
        if (arts.length === 0) return null
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
