import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import axios from 'axios'

interface User {
  id: string
  email: string
  display_name: string
  role: string
  tenant_id: string
}

interface AuthState {
  token: string | null
  user: User | null
  login: (email: string, password: string) => Promise<{ requires_mfa: boolean; temp_token?: string }>
  verifyMFA: (code: string, tempToken: string) => Promise<void>
  setSession: (token: string, user: User) => void
  logout: () => void
}

const api = axios.create({ baseURL: '/api/v1' })

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      token: null,
      user: null,

      login: async (email, password) => {
        const { data } = await api.post('/auth/login', { email, password })
        if (data.requires_mfa) {
          return { requires_mfa: true, temp_token: data.temp_token }
        }
        set({ token: data.access_token, user: data.user })
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
        return { requires_mfa: false }
      },

      verifyMFA: async (code, tempToken) => {
        const { data } = await api.post('/auth/mfa/verify', { code, temp_token: tempToken })
        set({ token: data.access_token, user: data.user })
        api.defaults.headers.common['Authorization'] = `Bearer ${data.access_token}`
      },

      setSession: (token, user) => {
        set({ token, user })
        api.defaults.headers.common['Authorization'] = `Bearer ${token}`
      },

      logout: () => {
        set({ token: null, user: null })
        delete api.defaults.headers.common['Authorization']
      },
    }),
    { name: 'eva-auth' }
  )
)
