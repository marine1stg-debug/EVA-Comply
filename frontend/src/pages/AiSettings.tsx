import { useEffect, useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { api } from '../lib/api'
import { useT } from '../lib/i18n'

interface Provider {
  key: string; name: string; desc: string
  default_base: string; needs_key: boolean; model_hint: string
}
interface LlmSettings {
  provider: string; base_url: string; model: string; enabled: boolean
  timeout_seconds: number; extra_header_name: string
  has_key: boolean; key_hint: string | null
  last_tested_at: string | null; last_test_ok: boolean | null; last_test_msg: string | null
  providers: Provider[]
}
interface TestResult { ok: boolean; message: string; latency_ms: number | null }

const KEEP = '__KEEP__'

export default function AiSettingsPage() {
  const qc = useQueryClient()
  const t = useT()
  const { data, isLoading, isError, error } = useQuery<LlmSettings>({
    queryKey: ['llm-settings'],
    queryFn: async () => (await api.get('/llm/settings')).data,
  })

  const [provider, setProvider] = useState('openai')
  const [baseUrl, setBaseUrl] = useState('')
  const [model, setModel] = useState('')
  const [enabled, setEnabled] = useState(false)
  const [timeout, setTimeoutS] = useState(30)
  const [hdrName, setHdrName] = useState('')
  const [hdrVal, setHdrVal] = useState('')
  // key: null => keep stored; string => replace (or '' to clear)
  const [keyInput, setKeyInput] = useState<string | null>(null)

  useEffect(() => {
    if (!data) return
    setProvider(data.provider)
    setBaseUrl(data.base_url)
    setModel(data.model)
    setEnabled(data.enabled)
    setTimeoutS(data.timeout_seconds)
    setHdrName(data.extra_header_name)
    setHdrVal('')
    setKeyInput(null)
  }, [data])

  const prov = data?.providers.find(p => p.key === provider)

  const save = useMutation({
    mutationFn: async () => (await api.put('/llm/settings', {
      provider, base_url: baseUrl, model, enabled, timeout_seconds: timeout,
      extra_header_name: hdrName, extra_header_value: hdrVal,
      api_key: keyInput === null ? KEEP : keyInput,
    })).data as LlmSettings,
    onSuccess: () => { toast.success(t('Saved')); qc.invalidateQueries({ queryKey: ['llm-settings'] }) },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Save failed')),
  })

  const test = useMutation({
    mutationFn: async () => (await api.post('/llm/test')).data as TestResult,
    onSuccess: (r) => {
      r.ok ? toast.success(r.message) : toast.error(r.message)
      qc.invalidateQueries({ queryKey: ['llm-settings'] })
    },
    onError: (e: any) => toast.error(e?.response?.data?.detail || t('Test failed')),
  })

  if (isLoading) return <div className="page-sub">{t('Loading…')}</div>
  if (isError) {
    const s = (error as any)?.response?.status
    return <div className="page-sub" style={{ color: s === 403 ? 'var(--text2)' : 'var(--red)' }}>
      {s === 403 ? t('The AI connector is a Super Admin setting.') : t('Failed to load AI settings.')}
    </div>
  }
  if (!data) return null

  const dirty =
    provider !== data.provider || baseUrl !== data.base_url || model !== data.model ||
    enabled !== data.enabled || timeout !== data.timeout_seconds ||
    hdrName !== data.extra_header_name || hdrVal !== '' || keyInput !== null

  return (
    <>
      <div className="page-hdr fi">
        <div>
          <div className="page-title">{t('AI Connector')}</div>
          <div className="page-sub">{t('Connect a private or hosted LLM for AI-assisted evidence review and recommendations.')}</div>
        </div>
        <div className="page-actions">
          <button className="tb-btn" disabled={test.isPending || dirty} onClick={() => test.mutate()}
            title={dirty ? t('Save changes before testing') : t('Send one test request')}>
            {test.isPending ? t('Testing…') : t('⚡ Test connection')}
          </button>
          <button className="submit-btn" disabled={save.isPending || !dirty} onClick={() => save.mutate()}>
            {save.isPending ? t('Saving…') : t('Save')}
          </button>
        </div>
      </div>

      <div className="detail-section fi" style={{ maxWidth: 720 }}>
        <div className="card-hdr"><span className="card-title">{t('Connection')}</span>
          <span className={`badge ${enabled ? 'b-green' : 'b-gray'}`}>{enabled ? t('Enabled') : t('Disabled')}</span>
        </div>

        <div className="form-row">
          <label className="form-label">{t('Provider')}</label>
          <select className="form-input" value={provider} onChange={e => {
            const p = e.target.value
            setProvider(p)
            const def = data.providers.find(x => x.key === p)
            if (def && !baseUrl) setBaseUrl(def.default_base)
          }}>
            {data.providers.map(p => <option key={p.key} value={p.key}>{p.name}</option>)}
          </select>
          {prov && <div className="page-sub" style={{ fontSize: 11, marginTop: 4 }}>{prov.desc}</div>}
        </div>

        <div style={{ display: 'flex', gap: 10 }}>
          <div className="form-row" style={{ flex: 2 }}>
            <label className="form-label">{t('Base URL')}</label>
            <input className="form-input" value={baseUrl} placeholder={prov?.default_base || ''}
              onChange={e => setBaseUrl(e.target.value)} />
          </div>
          <div className="form-row" style={{ flex: 1 }}>
            <label className="form-label">{t('Model')}</label>
            <input className="form-input" value={model} placeholder={prov?.model_hint || ''}
              onChange={e => setModel(e.target.value)} />
          </div>
        </div>

        <div className="form-row">
          <label className="form-label">
            {t('API key')} {prov && !prov.needs_key && <span style={{ color: 'var(--text3)', fontWeight: 400 }}>{t('(optional for {name})', { name: prov.name })}</span>}
          </label>
          {keyInput === null && data.has_key ? (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <code style={{ flex: 1, padding: '8px 10px', background: 'var(--surface-2)', borderRadius: 7, fontSize: 12 }}>{data.key_hint}</code>
              <button className="tb-btn" onClick={() => setKeyInput('')}>{t('Replace key')}</button>
            </div>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <input className="form-input" type="password" autoComplete="off" value={keyInput || ''}
                placeholder={t('Paste key - stored encrypted server-side, never shown again')}
                onChange={e => setKeyInput(e.target.value)} style={{ flex: 1 }} />
              {data.has_key && <button className="tb-btn" onClick={() => setKeyInput(null)}>{t('Cancel')}</button>}
            </div>
          )}
          <div className="page-sub" style={{ fontSize: 11, marginTop: 4 }}>
            {t('The key is held server-side only and is never returned to the browser or exposed to client tenants.')}
          </div>
        </div>

        <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
          <div className="form-row" style={{ width: 140 }}>
            <label className="form-label">{t('Timeout (s)')}</label>
            <input className="form-input" type="number" min={5} max={300} value={timeout}
              onChange={e => setTimeoutS(Number(e.target.value))} />
          </div>
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '8px 0', cursor: 'pointer' }}>
            <input type="checkbox" checked={enabled} onChange={e => setEnabled(e.target.checked)} />
            <span style={{ fontSize: 13, fontWeight: 600 }}>{t('Enable connector')}</span>
          </label>
        </div>

        <details style={{ marginTop: 4 }}>
          <summary style={{ cursor: 'pointer', fontSize: 12, color: 'var(--text2)' }}>{t('Advanced - custom auth header')}</summary>
          <div style={{ display: 'flex', gap: 10, marginTop: 8 }}>
            <div className="form-row" style={{ flex: 1 }}>
              <label className="form-label">{t('Header name')}</label>
              <input className="form-input" value={hdrName} placeholder="e.g. x-api-key" onChange={e => setHdrName(e.target.value)} />
            </div>
            <div className="form-row" style={{ flex: 1 }}>
              <label className="form-label">{t('Header value')}</label>
              <input className="form-input" type="password" autoComplete="off" value={hdrVal}
                placeholder={data.extra_header_name ? '•••• (set)' : ''} onChange={e => setHdrVal(e.target.value)} />
            </div>
          </div>
        </details>
      </div>

      <div className="detail-section fi" style={{ maxWidth: 720 }}>
        <div className="card-hdr"><span className="card-title">{t('Last test')}</span></div>
        {data.last_tested_at ? (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <span className={`badge ${data.last_test_ok ? 'b-green' : 'b-red'}`}>{data.last_test_ok ? t('✓ OK') : t('✕ Failed')}</span>
            <span style={{ fontSize: 12, color: 'var(--text2)' }}>{data.last_test_msg}</span>
            <span style={{ fontSize: 11, color: 'var(--text3)', marginLeft: 'auto' }}>{new Date(data.last_tested_at).toLocaleString()}</span>
          </div>
        ) : (
          <div className="page-sub" style={{ fontSize: 12 }}>{t('Not tested yet. Save your settings, then run a test.')}</div>
        )}
        <div className="page-sub" style={{ fontSize: 11, marginTop: 8 }}>
          {t('This connector powers AI-assisted evidence review and one-click recommendation generation. It is platform-wide and visible to Super Admins only.')}
        </div>
      </div>
    </>
  )
}
