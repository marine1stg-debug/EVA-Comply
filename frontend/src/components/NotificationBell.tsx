import { useState, useRef, useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface NotifItem { key: string; severity: string; count: number; link: string }
interface NotifResp { items: NotifItem[]; total: number }

const IcBell = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" /><path d="M13.73 21a2 2 0 0 1-3.46 0" />
  </svg>
)

const DOT: Record<string, string> = { warning: 'var(--amber)', danger: 'var(--red)', info: 'var(--brand)' }

// Map the backend's stable key → an English sentence (the i18n layer localises it).
const LABEL: Record<string, string> = {
  client_returned: '{n} evidence item(s) returned for your action',
  msp_pending: '{n} item(s) awaiting your pre-review',
  msp_eva_returned: '{n} client item(s) returned by EVA',
  eva_pending: '{n} item(s) awaiting EVA decision',
  support_open: '{n} open support request(s)',
}

export default function NotificationBell() {
  const t = useT()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const wrapRef = useRef<HTMLDivElement>(null)

  const { data } = useQuery<NotifResp>({
    queryKey: ['notifications'],
    queryFn: async () => (await api.get('/notifications/')).data,
    refetchInterval: 60000,
    refetchOnWindowFocus: true,
  })
  const items = data?.items || []
  const total = data?.total || 0

  useEffect(() => {
    const onDoc = (e: MouseEvent) => { if (wrapRef.current && !wrapRef.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', onDoc)
    return () => document.removeEventListener('mousedown', onDoc)
  }, [])

  const go = (link: string) => { setOpen(false); navigate(link) }

  return (
    <div className="notif-wrap" ref={wrapRef}>
      <button className="icon-btn" title={t('Notifications')} onClick={() => setOpen(o => !o)}>
        <IcBell />
        {total > 0 && <span className="notif-badge">{total > 99 ? '99+' : total}</span>}
      </button>
      {open && (
        <div className="notif-panel">
          <div className="notif-hdr">{t('Action required')}</div>
          {items.length === 0 ? (
            <div className="notif-empty">✅ {t('You’re all caught up')}</div>
          ) : (
            items.map(it => (
              <button key={it.key} className="notif-item" onClick={() => go(it.link)}>
                <span className="notif-dot" style={{ background: DOT[it.severity] || 'var(--brand)' }} />
                <span className="notif-text">{t(LABEL[it.key] || it.key, { n: it.count })}</span>
                <span className="notif-count">{it.count}</span>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  )
}
