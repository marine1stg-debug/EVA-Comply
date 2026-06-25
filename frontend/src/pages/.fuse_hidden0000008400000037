import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import { useAuthStore } from '../store/auth'

/* Isolated, mobile-first view: consult cases, create a case, declare an urgent
   incident. Deliberately standalone (no sidebar) so it works on a phone. */
interface Case { id: string; subject: string; category: string; status: string; created_at?: string }

export default function MobileQuick() {
  const t = useT()
  const qc = useQueryClient()
  const navigate = useNavigate()
  const logout = useAuthStore(s => s.logout)
  const [tab, setTab] = useState<'cases' | 'new' | 'incident'>('cases')
  const [subject, setSubject] = useState('')
  const [message, setMessage] = useState('')
  const [category, setCategory] = useState('Question')

  const { data } = useQuery<{ cases: Case[] }>({
    queryKey: ['support-cases-mine'], queryFn: async () => (await api.get('/support/cases')).data,
  })

  const submit = useMutation({
    mutationFn: async (incident: boolean) => {
      const fd = new FormData()
      fd.append('subject', incident ? `🚨 ${subject || t('Urgent incident')}` : subject)
      fd.append('message', message)
      fd.append('category', incident ? 'Incident' : category)
      return (await api.post('/support/cases', fd)).data
    },
    onSuccess: (_d, incident) => {
      toast.success(incident ? t('Incident declared — we’ll respond urgently') : t('Case submitted'))
      setSubject(''); setMessage(''); setTab('cases')
      qc.invalidateQueries({ queryKey: ['support-cases-mine'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Could not submit')),
  })

  const cases = data?.cases || []
  const badge = (s: string) => s === 'resolved' || s === 'closed' ? 'b-green' : s === 'in_progress' ? 'b-blue' : 'b-amber'

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg, #0B1629)', color: 'var(--text, #0F172A)' }}>
      <div style={{ position: 'sticky', top: 0, background: 'var(--card, #fff)', borderBottom: '1px solid var(--border-l, #e2e8f0)', padding: '12px 16px', display: 'flex', alignItems: 'center', gap: 10 }}>
        <span style={{ fontWeight: 800, color: 'var(--eva-blue2, #1A8FD1)' }}>EVA</span>
        <span style={{ fontWeight: 600 }}>{t('Quick access')}</span>
        <button onClick={() => navigate('/dashboard')} style={{ marginLeft: 'auto', border: 'none', background: 'none', color: 'var(--text2, #475569)', fontSize: 13 }}>{t('Full app')} →</button>
      </div>

      <div style={{ padding: 16, maxWidth: 560, margin: '0 auto' }}>
        {/* Big incident button always visible */}
        <button onClick={() => setTab('incident')}
          style={{ width: '100%', padding: '16px', borderRadius: 12, border: 'none', background: '#DC2626', color: '#fff', fontSize: 16, fontWeight: 700, marginBottom: 14 }}>
          🚨 {t('Declare an incident')}
        </button>

        <div style={{ display: 'flex', gap: 8, marginBottom: 14 }}>
          <button onClick={() => setTab('cases')} style={tabStyle(tab === 'cases')}>{t('My cases')}</button>
          <button onClick={() => setTab('new')} style={tabStyle(tab === 'new')}>{t('New case')}</button>
        </div>

        {tab === 'cases' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {cases.length === 0 && <div style={{ color: 'var(--text3, #94a3b8)', fontSize: 14 }}>{t('No cases yet.')}</div>}
            {cases.map(c => (
              <div key={c.id} style={{ background: 'var(--card, #fff)', border: '1px solid var(--border-l, #e2e8f0)', borderRadius: 10, padding: '12px 14px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <span style={{ fontWeight: 600, fontSize: 14, flex: 1 }}>{c.subject}</span>
                  <span className={`badge ${badge(c.status)}`} style={{ fontSize: 10 }}>{c.status}</span>
                </div>
                <div style={{ fontSize: 11, color: 'var(--text3, #94a3b8)', marginTop: 2 }}>{c.category}{c.created_at ? ` · ${c.created_at.slice(0, 10)}` : ''}</div>
              </div>
            ))}
          </div>
        )}

        {(tab === 'new' || tab === 'incident') && (
          <div style={{ background: 'var(--card, #fff)', border: '1px solid var(--border-l, #e2e8f0)', borderRadius: 12, padding: 14 }}>
            {tab === 'incident' && <div style={{ color: '#DC2626', fontWeight: 700, marginBottom: 8 }}>🚨 {t('Urgent incident')}</div>}
            {tab === 'new' && (
              <select value={category} onChange={e => setCategory(e.target.value)} style={inp}>
                {['Question', 'Bug', 'Billing', 'Feature request', 'Other'].map(c => <option key={c} value={c}>{t(c)}</option>)}
              </select>
            )}
            <input value={subject} onChange={e => setSubject(e.target.value)} placeholder={t('Subject')} style={inp} />
            <textarea value={message} onChange={e => setMessage(e.target.value)} placeholder={t('Describe what is happening…')} rows={5} style={{ ...inp, resize: 'vertical' }} />
            <button disabled={!message.trim() || submit.isPending} onClick={() => submit.mutate(tab === 'incident')}
              style={{ width: '100%', padding: '13px', borderRadius: 10, border: 'none', color: '#fff', fontWeight: 700, fontSize: 15, opacity: (!message.trim() || submit.isPending) ? 0.5 : 1, background: tab === 'incident' ? '#DC2626' : 'var(--eva-blue2, #1A8FD1)' }}>
              {submit.isPending ? t('Sending…') : tab === 'incident' ? t('Declare incident') : t('Submit case')}
            </button>
          </div>
        )}

        <button onClick={() => { logout(); navigate('/login') }}
          style={{ width: '100%', marginTop: 18, border: 'none', background: 'none', color: 'var(--text3, #94a3b8)', fontSize: 13 }}>
          {t('Sign out')}
        </button>
      </div>
    </div>
  )
}

const inp: React.CSSProperties = { width: '100%', padding: '11px 12px', marginBottom: 10, borderRadius: 8, border: '1px solid var(--border-l, #e2e8f0)', fontSize: 15, boxSizing: 'border-box' }
function tabStyle(active: boolean): React.CSSProperties {
  return { flex: 1, padding: '10px', borderRadius: 8, border: '1px solid var(--border-l, #e2e8f0)', fontSize: 14, fontWeight: 600, background: active ? 'var(--eva-blue2, #1A8FD1)' : 'transparent', color: active ? '#fff' : 'var(--text2, #475569)' }
}
