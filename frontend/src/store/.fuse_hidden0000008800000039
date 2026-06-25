import { create } from 'zustand'

/* Lets a page register unsaved changes + a save() callback so cross-cutting
   actions (e.g. switching the selected client) can prompt to save first.
   save() must run while the ORIGINAL context is still active (the caller awaits
   it before changing anything). */
interface UnsavedGuardState {
  dirty: boolean
  save: null | (() => Promise<unknown>)
  setGuard: (dirty: boolean, save: (() => Promise<unknown>) | null) => void
  clear: () => void
}

export const useUnsavedGuard = create<UnsavedGuardState>((set) => ({
  dirty: false,
  save: null,
  setGuard: (dirty, save) => set({ dirty, save }),
  clear: () => set({ dirty: false, save: null }),
}))
