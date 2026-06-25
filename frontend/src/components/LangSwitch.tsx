import { useI18n } from '../lib/i18n'

/**
 * Floating EN/FR language toggle for the public (pre-login) pages, which don't
 * have the app top-bar. The choice is persisted (localStorage) by the store.
 */
export default function LangSwitch() {
  const { lang, setLang } = useI18n()
  const btn = (active: boolean): React.CSSProperties => ({
    border: 'none', cursor: 'pointer', padding: '5px 12px', fontSize: 12, fontWeight: 700,
    background: active ? '#1A8FD1' : 'transparent', color: active ? '#fff' : '#7DD3FC',
  })
  return (
    <div style={{
      position: 'fixed', top: 16, right: 16, zIndex: 50, display: 'flex',
      border: '1px solid rgba(255,255,255,.15)', borderRadius: 999, overflow: 'hidden',
      background: 'rgba(17,30,53,.85)', backdropFilter: 'blur(4px)',
    }}>
      <button type="button" style={btn(lang === 'en')} onClick={() => setLang('en')} aria-label="English">EN</button>
      <button type="button" style={btn(lang === 'fr')} onClick={() => setLang('fr')} aria-label="Français">FR</button>
    </div>
  )
}
