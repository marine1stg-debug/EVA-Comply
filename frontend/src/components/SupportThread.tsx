import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

export interface SupportCommentT {
  id: string; author_name: string; author_role: string; is_eva: boolean; body: string; created_at: string
}

/** Read-only comment thread + an append-only reply box. Nobody can edit
 *  existing comments (including EVA's) — replies are added, never overwritten. */
export default function SupportThread({ caseId, comments, invalidateKey }: {
  caseId: string; comments: SupportCommentT[]; invalidateKey: (string | undefined)[]
}) {
  const t = useT()
  const qc = useQueryClient()
  const [text, setText] = useState('')

  const add = useMutation({
    mutationFn: async () => (await api.post(`/support/cases/${caseId}/comments`, { body: text })).data,
    onSuccess: () => {
      setText(''); toast.success(t('Comment added'))
      qc.invalidateQueries({ queryKey: invalidateKey })
      qc.invalidateQueries({ queryKey: ['notifications'] })
    },
    onError: () => toast.error(t('Could not add comment')),
  })

  return (
    <div style={{ marginTop: 8 }}>
      {comments.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginBottom: 8 }}>
          {comments.map(cm => (
            <div key={cm.id} style={{
              borderRadius: 8, padding: '8px 11px',
              background: cm.is_eva ? 'var(--soft)' : 'var(--surface)',
              borderLeft: `3px solid ${cm.is_eva ? 'var(--brand)' : 'var(--border-l)'}`,
            }}>
              <div style={{ fontSize: 10, fontWeight: 700, color: cm.is_eva ? 'var(--brand)' : 'var(--text2)', marginBottom: 2 }}>
                {cm.is_eva ? 'EVA' : cm.author_name}
                <span style={{ fontWeight: 400, color: 'var(--text3)', textTransform: 'capitalize' }}> · {t(cm.author_role.replace(/_/g, ' '))} · {cm.created_at}</span>
              </div>
              <div style={{ fontSize: 12.5, color: 'var(--text)', lineHeight: 1.5, whiteSpace: 'pre-wrap' }}>{cm.body}</div>
            </div>
          ))}
        </div>
      )}
      <div style={{ display: 'flex', gap: 8 }}>
        <input className="form-input" style={{ flex: 1 }} value={text} onChange={e => setText(e.target.value)}
          placeholder={t('Add a reply…')}
          onKeyDown={e => { if (e.key === 'Enter' && text.trim()) add.mutate() }} />
        <button className="submit-btn" disabled={!text.trim() || add.isPending} onClick={() => add.mutate()}>
          {add.isPending ? t('Sending…') : t('Reply')}
        </button>
      </div>
    </div>
  )
}
