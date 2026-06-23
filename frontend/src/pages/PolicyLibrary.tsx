import { useState, useRef, useMemo } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'
import { Download, Search, Plus, Pencil, Upload, Trash2, X } from 'lucide-react'

interface Policy {
  id: string; name: string; category: string; description: string
  is_active: boolean; has_file: boolean
  name_en?: string; name_fr?: string; category_en?: string; category_fr?: string
  keywords?: string; source?: string
}
interface Resp { policies: Policy[]; categories: string[]; can_manage: boolean }

const EMPTY_FORM = { name: '', name_fr: '', category: '', category_fr: '', keywords: '', description: '' }

export default function PolicyLibraryPage() {
  const t = useT()
  const qc = useQueryClient()
  const [search, setSearch] = useState('')
  const [cat, setCat] = useState('')
  const [addOpen, setAddOpen] = useState(false)
  const [editing, setEditing] = useState<Policy | null>(null)
  const [form, setForm] = useState(EMPTY_FORM)
  const addFile = useRef<HTMLInputElement | null>(null)
  const replaceFile = useRef<HTMLInputElement | null>(null)
  const replacingId = useRef<string | null>(null)

  const { data, isLoading, isError, error } = useQuery<Resp>({
    queryKey: ['policies'],
    queryFn: async () => (await api.get('/policy-templates/')).data,
  })

  const refresh = () => { qc.invalidateQueries({ queryKey: ['policies'] }); qc.invalidateQueries({ queryKey: ['controls'] }) }

  const download = async (p: Policy) => {
    try {
      const res = await api.get(`/policy-templates/${p.id}/file`, { responseType: 'blob' })
      const url = URL.createObjectURL(res.data)
      const a = document.createElement('a')
      a.href = url; a.download = `${p.name}.docx`; a.click()
      URL.revokeObjectURL(url)
    } catch { toast.error(t('No file available for this policy yet')) }
  }

  const toggle = useMutation({
    mutationFn: async (p: Policy) => (await api.patch(`/policy-templates/${p.id}`, { is_active: !p.is_active })).data,
    onSuccess: refresh,
  })
  const save = useMutation({
    mutationFn: async (v: { id?: string; body: typeof EMPTY_FORM; file?: File }) => {
      if (v.id) return (await api.patch(`/policy-templates/${v.id}`, v.body)).data
      const fd = new FormData()
      Object.entries(v.body).forEach(([k, val]) => fd.append(k, val))
      if (v.file) fd.append('file', v.file)
      return (await api.post('/policy-templates/', fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data
    },
    onSuccess: () => { refresh(); setAddOpen(false); setEditing(null); setForm(EMPTY_FORM); toast.success(t('Saved')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })
  const doReplace = useMutation({
    mutationFn: async (v: { id: string; file: File }) => {
      const fd = new FormData(); fd.append('file', v.file)
      return (await api.post(`/policy-templates/${v.id}/file`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })).data
    },
    onSuccess: () => { refresh(); toast.success(t('File replaced')) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Replace failed')),
  })
  const del = useMutation({
    mutationFn: async (id: string) => (await api.delete(`/policy-templates/${id}`)).data,
    onSuccess: () => { refresh(); toast.success(t('Policy deleted')) },
  })

  const filtered = useMemo(() => {
    const list = data?.policies || []
    const s = search.toLowerCase()
    return list.filter(p =>
      (!cat || p.category === cat) &&
      (!s || p.name.toLowerCase().includes(s) || (p.description || '').toLowerCase().includes(s) || (p.category || '').toLowerCase().includes(s) || (p.keywords || '').toLowerCase().includes(s)))
  }, [data, search, cat])

  if (isLoading) return <div className="page-sub">{t('Loading policies…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: 'var(--red)' }}>{s === 403 ? t('Not authorized.') : t('Failed to load policies.')}</div>
  }
  const canManage = !!data?.can_manage

  const openEdit = (p: Policy) => {
    setEditing(p)
    setForm({ name: p.name_en || p.name, name_fr: p.name_fr || '', category: p.category_en || p.category,
      category_fr: p.category_fr || '', keywords: p.keywords || '', description: p.description || '' })
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 10 }}>
        <div>
          <div className="page-title">{t('Policy Library')}</div>
          <div className="page-sub">{canManage ? t('Browse, download, and manage policy templates.') : t('Browse and download the policy templates available to you.')}</div>
        </div>
        {canManage && (
          <button className="submit-btn" onClick={() => { setForm(EMPTY_FORM); setAddOpen(true) }}>
            <Plus size={14} aria-hidden /> {t('Add policy')}
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', margin: '14px 0' }}>
        <div style={{ position: 'relative', flex: '1 1 240px' }}>
          <Search size={14} aria-hidden style={{ position: 'absolute', left: 10, top: 9, color: 'var(--text3)' }} />
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder={t('Search a topic, control family, or keyword…')}
            style={{ width: '100%', padding: '7px 10px 7px 30px', borderRadius: 8, border: '1px solid var(--border, rgba(255,255,255,.12))', background: 'var(--card2, rgba(255,255,255,.04))', color: 'var(--text)' }} />
        </div>
        <select className="filter-select" value={cat} onChange={e => setCat(e.target.value)}>
          <option value="">{t('All categories')}</option>
          {(data?.categories || []).map(c => <option key={c} value={c}>{c}</option>)}
        </select>
        <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto', alignSelf: 'center' }}>{t('{n} policies', { n: filtered.length })}</span>
      </div>

      <div style={{ display: 'grid', gap: 10 }}>
        {filtered.map(p => (
          <div key={p.id} className="card" style={{ padding: 14, display: 'flex', alignItems: 'flex-start', gap: 12, opacity: p.is_active ? 1 : 0.55 }}>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                <span style={{ fontWeight: 600, color: 'var(--text)' }}>{p.name}</span>
                <span className="badge b-blue" style={{ fontSize: 10 }}>{p.category}</span>
                {!p.is_active && <span className="badge b-gray" style={{ fontSize: 10 }}>{t('Unavailable')}</span>}
                {!p.has_file && <span className="badge b-amber" style={{ fontSize: 10 }}>{t('No file')}</span>}
              </div>
              {p.description && <div style={{ fontSize: 12, color: 'var(--text2)', marginTop: 4 }}>{p.description}</div>}
            </div>
            <div style={{ display: 'flex', gap: 6, flexShrink: 0, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
              <button className="tb-btn" onClick={() => download(p)} disabled={!p.has_file}><Download size={13} aria-hidden /> {t('Download')}</button>
              {canManage && <>
                <button className="tb-btn" onClick={() => openEdit(p)} title={t('Edit')}><Pencil size={13} aria-hidden /></button>
                <button className="tb-btn" onClick={() => { replacingId.current = p.id; replaceFile.current?.click() }} title={t('Replace file')}><Upload size={13} aria-hidden /></button>
                <button className="tb-btn" onClick={() => toggle.mutate(p)} title={p.is_active ? t('Make unavailable') : t('Make available')}>{p.is_active ? t('Hide') : t('Show')}</button>
                <button className="tb-btn" style={{ color: 'var(--red)' }} onClick={() => { if (confirm(t('Delete this policy?'))) del.mutate(p.id) }} title={t('Delete')}><Trash2 size={13} aria-hidden /></button>
              </>}
            </div>
          </div>
        ))}
        {!filtered.length && <div className="page-sub">{t('No policies match your search.')}</div>}
      </div>

      <input ref={replaceFile} type="file" accept=".docx" style={{ display: 'none' }}
        onChange={e => { const f = e.target.files?.[0]; const id = replacingId.current; if (f && id) doReplace.mutate({ id, file: f }); e.target.value = ''; replacingId.current = null }} />

      {(addOpen || editing) && (
        <div className="modal-overlay" style={{ zIndex: 60 }} onClick={() => { setAddOpen(false); setEditing(null) }}>
          <div className="modal-card" style={{ maxWidth: 540 }} onClick={e => e.stopPropagation()}>
            <div className="modal-body" style={{ padding: 22 }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
                <div style={{ fontSize: 15, fontWeight: 700, color: 'var(--text)' }}>{editing ? t('Edit policy') : t('Add policy')}</div>
                <button className="tb-btn" style={{ padding: 4 }} onClick={() => { setAddOpen(false); setEditing(null) }}><X size={16} aria-hidden /></button>
              </div>
              {([
                ['name', t('Name (English)')], ['name_fr', t('Name (French)')],
                ['category', t('Category (English)')], ['category_fr', t('Category (French)')],
                ['keywords', t('Control-family keywords (comma-separated, e.g. access,control)')],
                ['description', t('Description')],
              ] as [keyof typeof EMPTY_FORM, string][]).map(([k, label]) => (
                <div key={k} style={{ marginBottom: 8 }}>
                  <label style={{ fontSize: 11, color: 'var(--text3)' }}>{label}</label>
                  <input value={form[k]} onChange={e => setForm(f => ({ ...f, [k]: e.target.value }))}
                    style={{ width: '100%', padding: '7px 10px', borderRadius: 8, border: '1px solid var(--border, rgba(255,255,255,.12))', background: 'var(--card2, rgba(255,255,255,.04))', color: 'var(--text)' }} />
                </div>
              ))}
              {!editing && (
                <div style={{ marginBottom: 10 }}>
                  <label style={{ fontSize: 11, color: 'var(--text3)' }}>{t('Policy document (.docx)')}</label>
                  <input ref={addFile} type="file" accept=".docx" style={{ display: 'block', marginTop: 4, color: 'var(--text2)' }} />
                </div>
              )}
              <button className="submit-btn" style={{ width: '100%', justifyContent: 'center', marginTop: 6 }}
                disabled={save.isPending || (!editing && !form.name)}
                onClick={() => {
                  if (!editing && !addFile.current?.files?.[0]) { toast.error(t('Please choose a .docx file')); return }
                  save.mutate({ id: editing?.id, body: form, file: editing ? undefined : addFile.current?.files?.[0] })
                }}>
                {save.isPending ? t('Saving…') : t('Save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
