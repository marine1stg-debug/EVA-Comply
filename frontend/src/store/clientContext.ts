import { create } from 'zustand'
import { persist } from 'zustand/middleware'

// Which client a reviewer (EVA / MSP) is currently viewing. Sent on every API
// call as the X-Client-Id header so client-scoped screens follow the selection.
interface ClientContextState {
  clientId: string | null
  clientName: string | null
  setClient: (id: string | null, name: string | null) => void
}

export const useClientContext = create<ClientContextState>()(
  persist(
    (set) => ({
      clientId: null,
      clientName: null,
      setClient: (clientId, clientName) => set({ clientId, clientName }),
    }),
    { name: 'eva-client-ctx' }
  )
)
