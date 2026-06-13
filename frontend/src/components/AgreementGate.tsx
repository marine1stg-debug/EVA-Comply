import { useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Agreement {
  version: string; title: string; body_html: string
  needs_acceptance: boolean; account_type: string
}

function printAgreement(title: string, html: string, t: (s: string) => string) {
  const w = window.open('', '_blank')
  if (!w) { toast.error(t('Allow pop-ups to print.')); return }
  w.document.write(
    `<html><head><meta charset="utf-8"><title>${title}</title>` +
    `<style>body{font-family:Arial,Helvetica,sans-serif;max-width:820px;margin:28px auto;` +
    `line-height:1.55;color:#111;padding:0 16px} h2{margin-top:30px} h3{margin-top:18px} ` +
    `hr{margin:34px 0;border:none;border-top:1px solid #ccc} ul{margin:6px 0 6px 18px}</style>` +
    `</head><body>${html}</body></html>`)
  w.document.close(); w.focus()
  setTimeout(() => { w.print() }, 200)
}

/* Presentational agreement panel: shows the contract, requires scroll-to-read +
   checkbox, records acceptance, then calls onAccepted. Used by the post-login
   gate and by the signup flow (before first login). */
export function AgreementView({ onAccepted }: { onAccepted: () => void }) {
  const t = useT()
  const { data, isLoading, isError, refetch } = useQuery<Agreement>({
    queryKey: ['agreement-me'],
    queryFn: async () => (await api.get('/agreement/me')).data,
    retry: 1,
  })
  const [read, setRead] = useState(false)
  const [agree, setAgree] = useState(false)
  const [busy, setBusy] = useState(false)

  if (isLoading) {
    return <div className="modal-card" style={{ maxWidth: 480, margin: 'auto', padding: 24 }}>
      <div className="page-sub">{t('Loading…')}</div></div>
  }
  if (isError || !data) {
    return <div className="modal-card" style={{ maxWidth: 480, margin: 'auto', padding: 24 }}>
      <div className="card-title" style={{ marginBottom: 8 }}>{t('Please review and accept the agreement')}</div>
      <div className="page-sub" style={{ marginBottom: 12 }}>{t('The agreement could not be loaded. Please retry.')}</div>
      <button className="submit-btn" onClick={() => refetch()}>{t('Retry')}</button>
    </div>
  }

  const onScroll = (e: React.UIEvent<HTMLDivElement>) => {
    const el = e.currentTarget
    if (el.scrollHeight - el.scrollTop - el.clientHeight < 48) setRead(true)
  }
  const accept = async () => {
    setBusy(true)
    try {
      await api.post('/agreement/accept')
      onAccepted()
    } catch { toast.error(t('Could not record acceptance')) }
    finally { setBusy(false) }
  }

  return (
    <div className="modal-card" style={{ maxWidth: 900, width: '100%', maxHeight: '92vh', margin: 'auto' }}>
      <div className="modal-hdr">
        <span className="card-title">{t('Please review and accept the agreement')}</span>
        <button className="tb-btn" onClick={() => printAgreement(data.title, data.body_html, t)}>🖨 {t('Print')}</button>
      </div>
      <div className="modal-body" style={{ overflow: 'auto' }} onScroll={onScroll}>
        <div className="agreement-body" dangerouslySetInnerHTML={{ __html: data.body_html }} />
      </div>
      <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border-l)', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
        {!read && <span className="page-sub" style={{ margin: 0 }}>{t('Scroll to the bottom to enable acceptance.')}</span>}
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13, opacity: read ? 1 : 0.5 }}>
          <input type="checkbox" disabled={!read} checked={agree} onChange={e => setAgree(e.target.checked)} />
          {t('I have read, understood and accept this agreement.')}
        </label>
        <button className="submit-btn" style={{ marginLeft: 'auto' }} disabled={!agree || busy} onClick={accept}>
          {busy ? t('Saving…') : t('Accept & continue')}
        </button>
      </div>
    </div>
  )
}

/* Full-screen blocking gate used inside the app (fallback for invited users or
   anyone who reaches the app without having accepted the current version). */
export default function AgreementGate() {
  const qc = useQueryClient()
  const { data } = useQuery<Agreement>({
    queryKey: ['agreement-me'],
    queryFn: async () => (await api.get('/agreement/me')).data,
  })
  if (!data || !data.needs_acceptance) return null
  return (
    <div className="modal-overlay" style={{ zIndex: 80, padding: 24 }}>
      <AgreementView onAccepted={() => qc.invalidateQueries({ queryKey: ['agreement-me'] })} />
    </div>
  )
}
