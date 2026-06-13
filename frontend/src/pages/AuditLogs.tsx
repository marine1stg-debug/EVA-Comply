import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Entry { icon: string; type: string; actor: string; tenant: string; text: string; time: string }

export default function AuditLogsPage() {
  const t = useT()
  const { data, isLoading, isError, error } = useQuery<{ entries: Entry[]; total: number }>({
    queryKey: ['audit-logs'],
    queryFn: async () => (await api.get('/audit/logs')).data,
  })
  if (isLoading) return <div className="page-sub">{t('Loading audit log…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('Audit logs require admin access.') : t('Failed to load audit log.')}
    </div>
  }
  if (!data) return null

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('Audit Logs')}</div>
          <div className="page-sub">{t('{n} recent activity events across your organizations', { n: data.total })}</div>
        </div>
      </div>
      <div className="detail-section fi">
        {data.entries.length === 0 && <div className="page-sub">{t('No activity recorded yet.')}</div>}
        {data.entries.map((e, i) => (
          <div key={i} className="hist-item">
            <span className="hist-icon">{e.icon}</span>
            <div className="hist-text">
              {e.text}
              <span style={{ color: 'var(--text3)' }}> · {e.actor} · {e.tenant}</span>
            </div>
            <div className="hist-time">{e.time}</div>
          </div>
        ))}
      </div>
    </>
  )
}
