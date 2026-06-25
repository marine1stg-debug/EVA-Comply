import { create } from 'zustand'
import { FR } from './translations'

export type Lang = 'en' | 'fr'

function initialLang(): Lang {
  try {
    const saved = localStorage.getItem('eva-lang')
    if (saved === 'en' || saved === 'fr') return saved
  } catch { /* ignore */ }
  return 'fr'  // French by default; users can switch to EN (choice is remembered)
}

interface I18nState {
  lang: Lang
  setLang: (l: Lang) => void
  toggle: () => void
}

export const useI18n = create<I18nState>((set, get) => ({
  lang: initialLang(),
  setLang: (l) => { try { localStorage.setItem('eva-lang', l) } catch { /* ignore */ } ; set({ lang: l }) },
  toggle: () => {
    const l: Lang = get().lang === 'en' ? 'fr' : 'en'
    try { localStorage.setItem('eva-lang', l) } catch { /* ignore */ }
    set({ lang: l })
  },
}))

/**
 * Translation helper. English text is the key; French comes from the FR dict.
 * Missing translations fall back to the English key, so the UI never breaks —
 * untranslated strings simply stay in English until added to translations.ts.
 *
 *   const t = useT()
 *   t('Dashboard')
 *   t('Welcome back, {name}', { name: 'Sarah' })
 */
export function useT() {
  const lang = useI18n(s => s.lang)
  return (en: string, vars?: Record<string, string | number>) => {
    let s = lang === 'fr' ? (FR[en] ?? en) : en
    if (vars) for (const k in vars) s = s.replace(new RegExp(`\\{${k}\\}`, 'g'), String(vars[k]))
    return s
  }
}

/** Non-hook accessor for use outside React render (e.g. utility modules). */
export function translate(en: string, vars?: Record<string, string | number>) {
  const lang = useI18n.getState().lang
  let s = lang === 'fr' ? (FR[en] ?? en) : en
  if (vars) for (const k in vars) s = s.replace(new RegExp(`\\{${k}\\}`, 'g'), String(vars[k]))
  return s
}
