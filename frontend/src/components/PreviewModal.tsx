import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { api } from '../lib/api'
import { fetchBlobUrl, downloadEvidence } from '../lib/files'

interface PreviewData {
  kind: 'image' | 'pdf' | 'table' | 'text' | 'none'
  file_name?: string
  columns?: string[]
  rows?: string[][]
  content?: string
}

export default function PreviewModal({ id, title, onClose }: { id: string; title: string; onClose: () => void }) {
  const { data, isLoading, isError } = useQuery<PreviewData>({
    queryKey: ['preview', id],
    queryFn: async () => (await api.get(`/evidence/${id}/preview`)).data,
  })
  const [blobUrl, setBlobUrl] = useState<string | null>(null)

  useEffect(() => {
    let url: string | null = null
    if (data && (data.kind === 'image' || data.kind === 'pdf')) {
      fetchBlobUrl(id).then(u => { url = u; setBlobUrl(u) }).catch(() => {})
    }
    return () => { if (url) URL.revokeObjectURL(url) }
  }, [data, id])

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-card" onClick={e => e.stopPropagation()}>
        <div className="modal-hdr">
          <span className="card-title" style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{title}</span>
          <div style={{ display: 'flex', gap: 8, flexShrink: 0 }}>
            <button className="ev-action-btn download" onClick={() => downloadEvidence(id, title)}>⬇ Download</button>
            <button className="ev-action-btn" onClick={onClose}>✕ Close</button>
          </div>
        </div>
        <div className="modal-body">
          {isLoading && <div className="page-sub">Loading preview…</div>}
          {isError && <div className="page-sub" style={{ color: 'var(--red)' }}>Could not load preview.</div>}
          {data?.kind === 'image' && (blobUrl ? <img src={blobUrl} alt={title} style={{ maxWidth: '100%', borderRadius: 8 }} /> : <div className="page-sub">Loading image…</div>)}
          {data?.kind === 'pdf' && (blobUrl ? <iframe title={title} src={blobUrl} style={{ width: '100%', height: '72vh', border: 'none', borderRadius: 8 }} /> : <div className="page-sub">Loading PDF…</div>)}
          {data?.kind === 'text' && <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, fontFamily: 'var(--mono)', color: 'var(--text)' }}>{data.content}</pre>}
          {data?.kind === 'table' && (
            <table className="tenant-table">
              <thead><tr>{(data.columns || []).map((c, i) => <th key={i}>{c}</th>)}</tr></thead>
              <tbody>{(data.rows || []).map((r, i) => <tr key={i}>{r.map((c, j) => <td key={j}>{c}</td>)}</tr>)}</tbody>
            </table>
          )}
          {data?.kind === 'none' && <div className="page-sub">No inline preview for this file type — use Download to view it.</div>}
        </div>
      </div>
    </div>
  )
}
