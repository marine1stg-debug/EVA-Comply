import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { api } from './api'
import { useT } from './i18n'

export interface VideoRef { kind: 'link' | 'file' | null; url: string | null; file: string | null }

/** Convert a Vimeo/YouTube watch URL into an embeddable player URL, else null. */
export function embedUrl(url: string | null): string | null {
  if (!url) return null
  const u = url.trim()
  let m = u.match(/(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([\w-]{6,})/)
  if (m) return `https://www.youtube.com/embed/${m[1]}`
  m = u.match(/vimeo\.com\/(?:video\/)?(\d+)/)
  if (m) return `https://player.vimeo.com/video/${m[1]}`
  return null
}

/** Renders a training video: embedded iframe for Vimeo/YouTube, HTML5 <video>
 * for app-hosted files (fetched as a blob so the bearer token is sent), or a
 * plain link for other URLs. An "Expand" button opens it in a large window. */
export function VideoPlayer({ video, height = 220 }: { video?: VideoRef | null; height?: number }) {
  const t = useT()
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  const [big, setBig] = useState(false)
  useEffect(() => {
    let made: string | null = null
    setBlobUrl(null)
    if (video?.kind === 'file' && video.file) {
      api.get(video.file, { responseType: 'blob' })
        .then(r => { made = URL.createObjectURL(r.data); setBlobUrl(made) })
        .catch(() => {})
    }
    return () => { if (made) URL.revokeObjectURL(made) }
  }, [video?.file, video?.kind])

  if (!video || !video.kind) return null

  const emb = video.kind === 'link' ? embedUrl(video.url) : null

  const media = (h: number) => {
    if (video.kind === 'file') {
      return blobUrl
        ? <video src={blobUrl} controls style={{ width: '100%', maxHeight: h, borderRadius: 8, background: '#000' }} />
        : <div className="page-sub">{t('Loading…')}</div>
    }
    if (emb) return <iframe title="video" src={emb} style={{ width: '100%', height: h, border: 0, borderRadius: 8 }}
      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen />
    return <a href={video.url || '#'} target="_blank" rel="noreferrer" style={{ color: 'var(--brand)', fontSize: 12 }}>▶ {video.url}</a>
  }

  const canExpand = video.kind === 'file' || !!emb
  return (
    <div style={{ position: 'relative' }}>
      {media(height)}
      {canExpand && (
        <button onClick={() => setBig(true)} title={t('Expand')}
          style={{ position: 'absolute', top: 6, right: 6, background: 'rgba(0,0,0,.55)', color: '#fff',
            border: 'none', borderRadius: 6, fontSize: 12, padding: '2px 7px', cursor: 'pointer' }}>⤢</button>
      )}
      {big && createPortal(
        <div onClick={() => setBig(false)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)', zIndex: 80, display: 'flex',
            alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <div onClick={e => e.stopPropagation()} style={{ width: 'min(1000px, 92vw)' }}>
            {video.kind === 'file'
              ? (blobUrl ? <video src={blobUrl} controls autoPlay style={{ width: '100%', maxHeight: '82vh', borderRadius: 10, background: '#000' }} /> : <div className="page-sub" style={{ color: '#fff' }}>{t('Loading…')}</div>)
              : (emb ? <iframe title="video" src={emb} style={{ width: '100%', height: '78vh', border: 0, borderRadius: 10 }}
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowFullScreen /> : null)}
            <div style={{ textAlign: 'right', marginTop: 8 }}>
              <button onClick={() => setBig(false)} style={{ background: '#fff', border: 'none', borderRadius: 6, padding: '5px 12px', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}>{t('Close')}</button>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  )
}
